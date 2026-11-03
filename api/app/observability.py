import json
import logging
import os
import sys
from collections import Counter
from contextvars import ContextVar
from datetime import UTC, datetime
from threading import Lock


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "event": getattr(record, "event_name", record.getMessage()),
        }
        for key in (
            "request_id",
            "method",
            "path",
            "route",
            "status_code",
            "elapsed_ms",
            "error_type",
            "verdict",
            "rule_engine_version",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        return json.dumps(payload, separators=(",", ":"))


logger = logging.getLogger("portpilot.api")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
logger.propagate = False
if not any(getattr(handler, "_portpilot_json", False) for handler in logger.handlers):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler._portpilot_json = True
    logger.addHandler(handler)

request_id_context: ContextVar[str | None] = ContextVar("portpilot_request_id", default=None)


def current_request_id() -> str | None:
    return request_id_context.get()


def log_event(event: str, level: int = logging.INFO, **fields: str | int | float) -> None:
    logger.log(level, event, extra={"event_name": event, **fields})


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


HISTOGRAM_BUCKETS: tuple[float, ...] = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)


class Metrics:
    """Small process-local counters and request-duration distributions in Prometheus text format."""

    def __init__(self, buckets: tuple[float, ...] = HISTOGRAM_BUCKETS) -> None:
        self._lock = Lock()
        self._buckets = tuple(sorted(buckets))
        self._bucket_pairs = [(b, str(b)) for b in self._buckets]
        self._http_requests: Counter[tuple[str, str, str]] = Counter()
        self._checks: Counter[tuple[str, str]] = Counter()
        self._http_duration_buckets: Counter[tuple[str, str, str, str]] = Counter()
        self._http_duration_counts: Counter[tuple[str, str, str]] = Counter()
        self._http_duration_sums: Counter[tuple[str, str, str]] = Counter()

    def record_request(
        self,
        method: str,
        route: str,
        status_code: int | str,
        duration_seconds: float | None = None,
    ) -> None:
        status_str = str(status_code)
        key = (method, route, status_str)
        with self._lock:
            self._http_requests[key] += 1
            if duration_seconds is not None:
                duration = max(0.0, float(duration_seconds))
                self._http_duration_counts[key] += 1
                self._http_duration_sums[key] += duration
                for threshold, label in self._bucket_pairs:
                    if duration <= threshold:
                        self._http_duration_buckets[(method, route, status_str, label)] += 1
                self._http_duration_buckets[(method, route, status_str, "+Inf")] += 1

    def record_check(self, verdict: str, rule_engine_version: str) -> None:
        with self._lock:
            self._checks[(verdict, rule_engine_version)] += 1

    def render(self) -> str:
        with self._lock:
            requests = self._http_requests.copy()
            checks = self._checks.copy()
            duration_buckets = self._http_duration_buckets.copy()
            duration_counts = self._http_duration_counts.copy()
            duration_sums = self._http_duration_sums.copy()

        lines = [
            "# HELP portpilot_http_requests_total Process-local API requests by method, route, and status.",
            "# TYPE portpilot_http_requests_total counter",
        ]
        for (method, route, status_code), count in sorted(requests.items()):
            labels = (
                f'method="{_escape_label(method)}",route="{_escape_label(route)}",'
                f'status="{_escape_label(status_code)}"'
            )
            lines.append(f"portpilot_http_requests_total{{{labels}}} {count}")

        lines.extend(
            [
                "# HELP portpilot_http_request_duration_seconds Process-local HTTP request duration "
                "in seconds by method, route, and status.",
                "# TYPE portpilot_http_request_duration_seconds histogram",
            ]
        )
        for (method, route, status_code), count in sorted(duration_counts.items()):
            labels_base = (
                f'method="{_escape_label(method)}",route="{_escape_label(route)}",'
                f'status="{_escape_label(status_code)}"'
            )
            for _, label in self._bucket_pairs:
                bucket_count = duration_buckets.get((method, route, status_code, label), 0)
                bucket_entry = (
                    f'portpilot_http_request_duration_seconds_bucket{{{labels_base},le="{label}"}} '
                    f"{bucket_count}"
                )
                lines.append(bucket_entry)
            inf_count = duration_buckets.get((method, route, status_code, "+Inf"), count)
            lines.append(
                f'portpilot_http_request_duration_seconds_bucket{{{labels_base},le="+Inf"}} {inf_count}'
            )
            total_sum = duration_sums.get((method, route, status_code), 0.0)
            lines.append(f"portpilot_http_request_duration_seconds_sum{{{labels_base}}} {total_sum:.6f}")
            lines.append(f"portpilot_http_request_duration_seconds_count{{{labels_base}}} {count}")

        lines.extend(
            [
                "# HELP portpilot_compatibility_checks_total Compatibility checks by verdict and "
                "rule version.",
                "# TYPE portpilot_compatibility_checks_total counter",
            ]
        )
        for (verdict, version), count in sorted(checks.items()):
            labels = f'verdict="{_escape_label(verdict)}",rule_engine_version="{_escape_label(version)}"'
            lines.append(f"portpilot_compatibility_checks_total{{{labels}}} {count}")
        return "\n".join(lines) + "\n"


metrics = Metrics()
