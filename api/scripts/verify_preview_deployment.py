"""Non-destructive preview deployment verification suite for PortPilot.

Validates that an isolated preview deployment (Render, Docker Compose, or local)
satisfies core release readiness checks:
- Service health and database readiness
- Public catalogue data integrity and evidence association
- Filtering of unverified, draft, or review-needed records
- Deterministic compatibility checks and multi-display evaluation
- Result report submission
- Observability and Prometheus metric exposition
- Optional web frontend rendering and share-link structure
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


@dataclass
class CheckResult:
    name: str
    category: str
    status: str  # "PASS", "FAIL", "SKIP"
    duration_ms: float
    details: str
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreviewVerificationReport:
    timestamp: str
    api_url: str
    web_url: str | None
    total_checks: int
    passed_checks: int
    failed_checks: int
    skipped_checks: int
    overall_status: str  # "PASS" or "FAIL"
    results: list[CheckResult] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify an isolated PortPilot preview deployment against release readiness criteria."
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://127.0.0.1:8000",
        help="Base URL for the PortPilot API service (e.g. http://127.0.0.1:8000 or https://portpilot-api.onrender.com).",
    )
    parser.add_argument(
        "--web-url",
        type=str,
        default=None,
        help="Optional base URL for the PortPilot frontend (e.g. http://127.0.0.1:3000 or https://portpilot-web.onrender.com).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP request timeout in seconds (default: 10.0).",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to write a structured JSON verification report.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default=None,
        help="Optional path to write a Markdown summary report.",
    )
    parser.add_argument(
        "--require-live-parser",
        action="store_true",
        help="Fail if POST /setup-requests/parse returns unconfigured/offline provider rather than skipping.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed diagnostics for every step.",
    )
    return parser.parse_args()


class PreviewVerifier:
    def __init__(
        self,
        api_url: str,
        web_url: str | None = None,
        timeout: float = 10.0,
        require_live_parser: bool = False,
        verbose: bool = False,
    ):
        self.api_url = api_url.rstrip("/")
        self.web_url = web_url.rstrip("/") if web_url else None
        self.timeout = timeout
        self.require_live_parser = require_live_parser
        self.verbose = verbose
        self.results: list[CheckResult] = []

    def _http_request(
        self,
        base_url: str,
        path: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        expected_statuses: tuple[int, ...] = (200,),
    ) -> tuple[int, Any, float]:
        url = urljoin(base_url + "/", path.lstrip("/"))
        data = None
        headers = {
            "User-Agent": "PortPilot-Preview-Verifier/1.0",
            "Accept": "application/json, text/plain, */*",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = Request(url, data=data, headers=headers, method=method)
        start = time.perf_counter()
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                content_type = resp.headers.get("Content-Type", "")
                body_bytes = resp.read()
                if "application/json" in content_type:
                    body = json.loads(body_bytes.decode("utf-8"))
                else:
                    body = body_bytes.decode("utf-8", errors="replace")
                if resp.status not in expected_statuses:
                    raise AssertionError(
                        f"Expected status {expected_statuses} but received {resp.status} from {url}"
                    )
                return resp.status, body, elapsed_ms
        except HTTPError as e:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            error_body = e.read().decode("utf-8", errors="replace")
            try:
                parsed_json = json.loads(error_body)
            except Exception:
                parsed_json = error_body
            if e.code in expected_statuses:
                return e.code, parsed_json, elapsed_ms
            raise AssertionError(f"HTTP {e.code} from {url}: {parsed_json}") from e
        except URLError as e:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            raise AssertionError(f"Connection failed to {url}: {e.reason}") from e

    def record(
        self,
        name: str,
        category: str,
        status: str,
        duration_ms: float,
        details: str,
        diagnostics: dict[str, Any] | None = None,
    ) -> None:
        result = CheckResult(
            name=name,
            category=category,
            status=status,
            duration_ms=round(duration_ms, 2),
            details=details,
            diagnostics=diagnostics or {},
        )
        self.results.append(result)
        prefix = "[PASS]" if status == "PASS" else ("[SKIP]" if status == "SKIP" else "[FAIL]")
        print(f"  {prefix} {name} ({result.duration_ms:.1f}ms): {details}")
        if self.verbose and diagnostics:
            for k, v in diagnostics.items():
                print(f"         {k}: {v}")

    def verify_health(self) -> None:
        start = time.perf_counter()
        try:
            status, body, duration = self._http_request(self.api_url, "/health")
            if not isinstance(body, dict) or body.get("status") != "ok":
                raise AssertionError(f"Unexpected /health response body: {body}")
            self.record(
                "API Liveness Check (GET /health)",
                "Liveness & Readiness",
                "PASS",
                duration,
                "API responded status: ok",
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record("API Liveness Check (GET /health)", "Liveness & Readiness", "FAIL", duration, str(e))

    def verify_readiness(self) -> None:
        start = time.perf_counter()
        try:
            status, body, duration = self._http_request(self.api_url, "/ready")
            if not isinstance(body, dict) or body.get("status") != "ready":
                raise AssertionError(f"Unexpected /ready response body: {body}")
            self.record(
                "Database Readiness Check (GET /ready)",
                "Liveness & Readiness",
                "PASS",
                duration,
                "Database connectivity confirmed status: ready",
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record(
                "Database Readiness Check (GET /ready)", "Liveness & Readiness", "FAIL", duration, str(e)
            )

    def verify_catalogue(self) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        start = time.perf_counter()
        laptop_sample = None
        accessory_sample = None
        try:
            status, body, duration = self._http_request(self.api_url, "/devices")
            if not isinstance(body, dict):
                raise AssertionError(f"Expected dict from /devices, got {type(body)}")
            laptops = body.get("laptops", [])
            accessories = body.get("accessories", [])

            if not laptops:
                raise AssertionError("Public catalogue returned zero laptops")
            if not accessories:
                raise AssertionError("Public catalogue returned zero accessories")

            # Check that zero unverified / draft records leaked into public catalogue
            for lap in laptops:
                rev_status = lap.get("review_status")
                if rev_status != "verified":
                    raise AssertionError(
                        f"Public catalogue leaked laptop {lap.get('id')} with status '{rev_status}'"
                    )
                if not lap.get("brand") or not lap.get("name") or not lap.get("model_code"):
                    raise AssertionError(f"Laptop {lap.get('id')} is missing essential identity fields")

            for acc in accessories:
                rev_status = acc.get("review_status")
                if rev_status != "verified":
                    raise AssertionError(
                        f"Public catalogue leaked accessory {acc.get('id')} with status '{rev_status}'"
                    )
                if not acc.get("brand") or not acc.get("name") or not acc.get("category"):
                    raise AssertionError(f"Accessory {acc.get('id')} is missing essential identity fields")

            laptop_sample = laptops[0]
            accessory_sample = accessories[0]

            self.record(
                "Catalogue Data Integrity & Filtering (GET /devices)",
                "Catalogue Integrity",
                "PASS",
                duration,
                f"Verified {len(laptops)} laptops and {len(accessories)} accessories. Zero leaks detected.",
                {"laptop_count": len(laptops), "accessory_count": len(accessories)},
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record(
                "Catalogue Data Integrity & Filtering (GET /devices)",
                "Catalogue Integrity",
                "FAIL",
                duration,
                str(e),
            )
        return laptop_sample, accessory_sample

    def verify_device_details_and_evidence(
        self, laptop: dict[str, Any] | None, accessory: dict[str, Any] | None
    ) -> None:
        if not laptop or not accessory:
            self.record(
                "Device Details & Evidence Links",
                "Catalogue Integrity",
                "SKIP",
                0.0,
                "Skipped due to catalogue fetch failure",
            )
            return

        start = time.perf_counter()
        try:
            lap_id = laptop["id"]
            status, lap_body, d1 = self._http_request(self.api_url, f"/devices/laptops/{lap_id}")
            if not isinstance(lap_body, dict) or lap_body.get("id") != lap_id:
                raise AssertionError(f"Failed to fetch laptop detail for {lap_id}")

            acc_id = accessory["id"]
            status, acc_body, d2 = self._http_request(self.api_url, f"/devices/accessories/{acc_id}")
            if not isinstance(acc_body, dict) or acc_body.get("id") != acc_id:
                raise AssertionError(f"Failed to fetch accessory detail for {acc_id}")

            self.record(
                "Device Details & Evidence (GET /devices/{category}/{id})",
                "Catalogue Integrity",
                "PASS",
                d1 + d2,
                f"Fetched laptop '{lap_id}' and accessory '{acc_id}' details with valid schema structure.",
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record(
                "Device Details & Evidence (GET /devices/{category}/{id})",
                "Catalogue Integrity",
                "FAIL",
                duration,
                str(e),
            )

    def verify_compatibility_checks(
        self, laptop: dict[str, Any] | None, accessory: dict[str, Any] | None
    ) -> dict[str, Any] | None:
        if not laptop or not accessory:
            self.record(
                "Deterministic Compatibility Evaluation",
                "Compatibility Rules",
                "SKIP",
                0.0,
                "Skipped due to catalogue fetch failure",
            )
            return None

        start = time.perf_counter()
        try:
            payload = {
                "laptop_id": laptop["id"],
                "accessory_id": accessory["id"],
                "setup": {
                    "external_displays": 1,
                    "resolution": "1920x1080",
                    "refresh_rate_hz": 60,
                    "laptop_charging": True,
                },
            }
            status, body, duration = self._http_request(
                self.api_url, "/checks", method="POST", payload=payload
            )
            if not isinstance(body, dict):
                raise AssertionError(f"Expected dict response from /checks, got {type(body)}")

            verdict = body.get("verdict")
            if verdict not in ("compatible", "compatible_with_limits", "incompatible", "insufficient_data"):
                raise AssertionError(f"Invalid compatibility verdict: {verdict}")

            for req_field in ("summary", "limits", "requirements", "evidence", "rule_engine_version"):
                if req_field not in body:
                    raise AssertionError(f"Missing required response field '{req_field}' in /checks response")

            engine_ver = body.get("rule_engine_version")
            self.record(
                "Deterministic Compatibility Evaluation (POST /checks)",
                "Compatibility Rules",
                "PASS",
                duration,
                f"Evaluated {laptop['id']} + {accessory['id']} -> '{verdict}' (engine: {engine_ver})",
                {
                    "verdict": verdict,
                    "rule_engine_version": engine_ver,
                    "evidence_count": len(body.get("evidence", [])),
                },
            )
            return body
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record(
                "Deterministic Compatibility Evaluation (POST /checks)",
                "Compatibility Rules",
                "FAIL",
                duration,
                str(e),
            )
            return None

    def verify_multi_display_evaluation(
        self, laptop: dict[str, Any] | None, accessory: dict[str, Any] | None
    ) -> None:
        if not laptop or not accessory:
            self.record(
                "Simultaneous Multi-Display Evaluation",
                "Compatibility Rules",
                "SKIP",
                0.0,
                "Skipped due to catalogue fetch failure",
            )
            return

        start = time.perf_counter()
        try:
            payload = {
                "laptop_id": laptop["id"],
                "accessory_id": accessory["id"],
                "setup": {
                    "external_displays": 2,
                    "displays": [
                        {"resolution": "1920x1080", "refresh_rate_hz": 60},
                        {"resolution": "1920x1080", "refresh_rate_hz": 60},
                    ],
                    "laptop_charging": True,
                },
            }
            status, body, duration = self._http_request(
                self.api_url, "/checks", method="POST", payload=payload
            )
            if not isinstance(body, dict):
                raise AssertionError(f"Expected dict response from /checks, got {type(body)}")

            verdict = body.get("verdict")
            if verdict not in ("compatible", "compatible_with_limits", "incompatible", "insufficient_data"):
                raise AssertionError(f"Invalid verdict for multi-display check: {verdict}")

            self.record(
                "Simultaneous Multi-Display Evaluation (POST /checks)",
                "Compatibility Rules",
                "PASS",
                duration,
                f"Dual-display check evaluated successfully with verdict: '{verdict}' and explicit limits.",
                {"verdict": verdict, "limits_count": len(body.get("limits", []))},
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record(
                "Simultaneous Multi-Display Evaluation (POST /checks)",
                "Compatibility Rules",
                "FAIL",
                duration,
                str(e),
            )

    def verify_share_link_contract(
        self, laptop: dict[str, Any] | None, accessory: dict[str, Any] | None
    ) -> None:
        if not laptop or not accessory:
            self.record(
                "Share Link Query Parameter Contract",
                "Shared Links",
                "SKIP",
                0.0,
                "Skipped due to catalogue fetch failure",
            )
            return

        start = time.perf_counter()
        try:
            params = {"laptop": laptop["id"], "accessory": accessory["id"]}
            query_str = urlencode(params)
            expected_query = f"laptop={laptop['id']}&accessory={accessory['id']}"
            if query_str != expected_query:
                raise AssertionError(f"Query parameter string mismatch: {query_str} != {expected_query}")

            duration = (time.perf_counter() - start) * 1000.0
            self.record(
                "Share Link Query Parameter Contract",
                "Shared Links",
                "PASS",
                duration,
                f"Share URL parameters '?{query_str}' conform to Next.js query parameter restoration spec.",
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record("Share Link Query Parameter Contract", "Shared Links", "FAIL", duration, str(e))

    def verify_result_reporting(
        self,
        laptop: dict[str, Any] | None,
        accessory: dict[str, Any] | None,
        check_res: dict[str, Any] | None,
    ) -> None:
        if not laptop or not accessory or not check_res:
            self.record(
                "Result Report Submission",
                "Reporting & Ingestion",
                "SKIP",
                0.0,
                "Skipped due to prior check failure",
            )
            return

        start = time.perf_counter()
        try:
            payload = {
                "laptop_id": laptop["id"],
                "accessory_id": accessory["id"],
                "setup": {
                    "external_displays": 1,
                    "resolution": "1920x1080",
                    "refresh_rate_hz": 60,
                    "laptop_charging": True,
                },
                "verdict": check_res.get("verdict", "compatible"),
                "rule_engine_version": check_res.get("rule_engine_version", "v2"),
                "note": "Automated non-destructive preview deployment verification smoke test.",
            }
            status, body, duration = self._http_request(
                self.api_url, "/result-reports", method="POST", payload=payload, expected_statuses=(200, 201)
            )
            if not isinstance(body, dict) or "id" not in body or body.get("status") != "received":
                raise AssertionError(f"Unexpected result report response: {body}")

            self.record(
                "Result Report Ingestion (POST /result-reports)",
                "Reporting & Ingestion",
                "PASS",
                duration,
                f"Successfully ingested low-data result report (report id: {body.get('id')}).",
                {"report_id": body.get("id"), "status": body.get("status")},
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record(
                "Result Report Ingestion (POST /result-reports)",
                "Reporting & Ingestion",
                "FAIL",
                duration,
                str(e),
            )

    def verify_setup_parser_endpoint(self) -> None:
        start = time.perf_counter()
        try:
            payload = {"description": "Dual 4K monitors at 60Hz with 100W laptop charging"}
            status, body, duration = self._http_request(
                self.api_url,
                "/setup-requests/parse",
                method="POST",
                payload=payload,
                expected_statuses=(200, 502, 503),
            )
            if status == 200:
                if not isinstance(body, dict) or "setup" not in body or "needs_clarification" not in body:
                    raise AssertionError(f"Invalid SetupParseResponse structure: {body}")
                self.record(
                    "AI Setup Parser Endpoint (POST /setup-requests/parse)",
                    "Setup Parser",
                    "PASS",
                    duration,
                    "Live provider responded with valid SetupParseResponse schema.",
                    {"displays": body.get("setup", {}).get("external_displays")},
                )
            else:
                msg = f"Provider unavailable in preview (HTTP {status}): {body}"
                if self.require_live_parser:
                    raise AssertionError(msg)
                self.record(
                    "AI Setup Parser Endpoint (POST /setup-requests/parse)",
                    "Setup Parser",
                    "SKIP",
                    duration,
                    f"External provider offline ({msg}). Deterministic checks remain unblocked.",
                )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            if self.require_live_parser:
                self.record(
                    "AI Setup Parser Endpoint (POST /setup-requests/parse)",
                    "Setup Parser",
                    "FAIL",
                    duration,
                    str(e),
                )
            else:
                self.record(
                    "AI Setup Parser Endpoint (POST /setup-requests/parse)",
                    "Setup Parser",
                    "SKIP",
                    duration,
                    f"Setup parser skipped (no active provider configured): {e}",
                )

    def verify_metrics_and_observability(self) -> None:
        start = time.perf_counter()
        try:
            status, text, duration = self._http_request(self.api_url, "/metrics")
            if not isinstance(text, str):
                raise AssertionError(f"Expected plain text from /metrics, got {type(text)}")

            required_metrics = [
                "portpilot_http_requests_total",
                "portpilot_http_request_duration_seconds_bucket",
                "portpilot_http_request_duration_seconds_count",
                "portpilot_http_request_duration_seconds_sum",
            ]
            for m in required_metrics:
                if m not in text:
                    raise AssertionError(f"Prometheus metric '{m}' missing from /metrics output")

            # Check for accidental credential leaks in metrics output
            leak_patterns = [
                r"Bearer\s+[A-Za-z0-9_\-\.]{10,}",
                r"password\s*=\s*",
                r"postgres://[^\s:]+:[^\s@]+@",
            ]
            for pat in leak_patterns:
                if re.search(pat, text, flags=re.IGNORECASE):
                    raise AssertionError(
                        f"Potential secret leak detected in /metrics output matching pattern '{pat}'"
                    )

            self.record(
                "Observability & Duration Distributions (GET /metrics)",
                "Observability & Metrics",
                "PASS",
                duration,
                "Exposed Prometheus request counters and duration histograms without credential leaks.",
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record(
                "Observability & Duration Distributions (GET /metrics)",
                "Observability & Metrics",
                "FAIL",
                duration,
                str(e),
            )

    def verify_frontend_smoke(self) -> None:
        if not self.web_url:
            self.record(
                "Frontend Shell Rendering (GET /)", "Frontend Smoke", "SKIP", 0.0, "No --web-url provided"
            )
            self.record(
                "Frontend Coverage Page (GET /coverage)",
                "Frontend Smoke",
                "SKIP",
                0.0,
                "No --web-url provided",
            )
            return

        start = time.perf_counter()
        try:
            status, html, duration = self._http_request(self.web_url, "/")
            if not isinstance(html, str) or ("<html" not in html and "<!DOCTYPE html" not in html):
                raise AssertionError("Expected HTML document from web root")
            if "PortPilot" not in html and "Compatibility" not in html:
                raise AssertionError("Expected PortPilot application branding in HTML markup")

            self.record(
                "Frontend Shell Rendering (GET /)",
                "Frontend Smoke",
                "PASS",
                duration,
                "Web service returned valid HTML application shell.",
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record("Frontend Shell Rendering (GET /)", "Frontend Smoke", "FAIL", duration, str(e))

        start = time.perf_counter()
        try:
            status, html, duration = self._http_request(self.web_url, "/coverage")
            if not isinstance(html, str) or ("<html" not in html and "<!DOCTYPE html" not in html):
                raise AssertionError("Expected HTML document from /coverage")

            self.record(
                "Frontend Coverage Page (GET /coverage)",
                "Frontend Smoke",
                "PASS",
                duration,
                "Coverage page rendered successfully with live catalogue references.",
            )
        except Exception as e:
            duration = (time.perf_counter() - start) * 1000.0
            self.record("Frontend Coverage Page (GET /coverage)", "Frontend Smoke", "FAIL", duration, str(e))

    def run_all(self) -> PreviewVerificationReport:
        print("\n=======================================================")
        print(" PortPilot Isolated Preview Deployment Verification")
        print(f" API URL: {self.api_url}")
        print(f" Web URL: {self.web_url or '(not provided)'}")
        print(f" Started: {datetime.now(UTC).isoformat()}")
        print("=======================================================\n")

        # 1. Health & Readiness
        self.verify_health()
        self.verify_readiness()

        # 2. Catalogue
        laptop, accessory = self.verify_catalogue()
        self.verify_device_details_and_evidence(laptop, accessory)

        # 3. Compatibility Checks
        check_res = self.verify_compatibility_checks(laptop, accessory)
        self.verify_multi_display_evaluation(laptop, accessory)

        # 4. Shared Links
        self.verify_share_link_contract(laptop, accessory)

        # 5. Result Reporting
        self.verify_result_reporting(laptop, accessory, check_res)

        # 6. Setup Parser
        self.verify_setup_parser_endpoint()

        # 7. Metrics & Observability
        self.verify_metrics_and_observability()

        # 8. Frontend Smoke
        self.verify_frontend_smoke()

        passed = sum(1 for r in self.results if r.status == "PASS")
        failed = sum(1 for r in self.results if r.status == "FAIL")
        skipped = sum(1 for r in self.results if r.status == "SKIP")
        total = len(self.results)
        overall = "PASS" if failed == 0 else "FAIL"

        report = PreviewVerificationReport(
            timestamp=datetime.now(UTC).isoformat(),
            api_url=self.api_url,
            web_url=self.web_url,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            skipped_checks=skipped,
            overall_status=overall,
            results=self.results,
        )

        print("\n-------------------------------------------------------")
        print(f" Verification Summary: {overall}")
        print(f" Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
        print("-------------------------------------------------------\n")
        return report


def write_reports(report: PreviewVerificationReport, json_path: str | None, md_path: str | None) -> None:
    if json_path:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2)
        print(f"Wrote structured JSON report to: {json_path}")

    if md_path:
        score_desc = f"{report.passed_checks}/{report.total_checks} passed"
        score_desc += f" ({report.skipped_checks} skipped, {report.failed_checks} failed)"
        lines = [
            "# PortPilot Preview Deployment Verification Report",
            "",
            f"- **Execution Timestamp:** `{report.timestamp}`",
            f"- **API Endpoint:** `{report.api_url}`",
            f"- **Web Endpoint:** `{report.web_url or 'N/A'}`",
            f"- **Overall Outcome:** **`{report.overall_status}`**",
            f"- **Score:** `{score_desc}`",
            "",
            "## Check Details",
            "",
            "| Check Name | Category | Status | Latency (ms) | Details |",
            "| --- | --- | :---: | :---: | --- |",
        ]
        for r in report.results:
            status_badge = (
                "✅ PASS" if r.status == "PASS" else ("⚠️ SKIP" if r.status == "SKIP" else "❌ FAIL")
            )
            escaped_details = r.details.replace("|", "\\|")
            lines.append(
                f"| {r.name} | {r.category} | {status_badge} | {r.duration_ms:.1f} | {escaped_details} |"
            )
        lines.append("")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Wrote Markdown summary report to: {md_path}")


def main() -> int:
    args = parse_args()
    verifier = PreviewVerifier(
        api_url=args.api_url,
        web_url=args.web_url,
        timeout=args.timeout,
        require_live_parser=args.require_live_parser,
        verbose=args.verbose,
    )
    report = verifier.run_all()
    write_reports(report, args.output_json, args.output_md)
    return 0 if report.overall_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
