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


class Metrics:
    """Small process-local counters exposed in Prometheus text format."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._http_requests: Counter[tuple[str, str, str]] = Counter()
        self._checks: Counter[tuple[str, str]] = Counter()

    def record_request(self, method: str, route: str, status_code: int) -> None:
        with self._lock:
            self._http_requests[(method, route, str(status_code))] += 1

    def record_check(self, verdict: str, rule_engine_version: str) -> None:
        with self._lock:
            self._checks[(verdict, rule_engine_version)] += 1

    def render(self) -> str:
        with self._lock:
            requests = self._http_requests.copy()
            checks = self._checks.copy()

        lines = [
            "# HELP portpilot_http_requests_total API requests by method, route, and status.",
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
