import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from scripts.verify_preview_deployment import (
    CheckResult,
    PreviewVerificationReport,
    PreviewVerifier,
    write_reports,
)


def test_preview_verifier_report_generation():
    results = [
        CheckResult(
            name="API Liveness",
            category="Liveness & Readiness",
            status="PASS",
            duration_ms=12.5,
            details="API responded status: ok",
        ),
        CheckResult(
            name="Database Readiness",
            category="Liveness & Readiness",
            status="PASS",
            duration_ms=18.2,
            details="Database connectivity confirmed",
        ),
    ]
    report = PreviewVerificationReport(
        timestamp="2026-11-03T12:00:00Z",
        api_url="http://127.0.0.1:8000",
        web_url="http://127.0.0.1:3000",
        total_checks=2,
        passed_checks=2,
        failed_checks=0,
        skipped_checks=0,
        overall_status="PASS",
        results=results,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        json_path = Path(tmpdir) / "report.json"
        md_path = Path(tmpdir) / "report.md"

        write_reports(report, str(json_path), str(md_path))

        assert json_path.exists()
        assert md_path.exists()

        data = json.loads(json_path.read_text(encoding="utf-8"))
        assert data["overall_status"] == "PASS"
        assert len(data["results"]) == 2

        md_content = md_path.read_text(encoding="utf-8")
        assert "PortPilot Preview Deployment Verification Report" in md_content
        assert "API Liveness" in md_content


def test_preview_verifier_mock_full_success():
    verifier = PreviewVerifier(api_url="http://mock-preview:8000", web_url="http://mock-preview:3000")

    def mock_http(base_url, path, method="GET", payload=None, expected_statuses=(200,)):
        if path == "/health":
            return 200, {"status": "ok"}, 5.0
        if path == "/ready":
            return 200, {"status": "ready"}, 6.0
        if path == "/devices":
            return (
                200,
                {
                    "laptops": [
                        {
                            "id": "mock-lap-1",
                            "brand": "Dell",
                            "name": "XPS 13",
                            "model_code": "9315",
                            "review_status": "verified",
                        }
                    ],
                    "accessories": [
                        {
                            "id": "mock-acc-1",
                            "brand": "Anker",
                            "name": "555 Hub",
                            "category": "usb_c_hub",
                            "review_status": "verified",
                        }
                    ],
                },
                15.0,
            )
        if path.startswith("/devices/laptops/"):
            return 200, {"id": "mock-lap-1", "brand": "Dell"}, 10.0
        if path.startswith("/devices/accessories/"):
            return 200, {"id": "mock-acc-1", "brand": "Anker"}, 10.0
        if path == "/checks":
            return (
                200,
                {
                    "verdict": "compatible",
                    "summary": "Fully compatible",
                    "limits": [],
                    "requirements": [],
                    "evidence": [],
                    "rule_engine_version": "v2",
                },
                20.0,
            )
        if path == "/result-reports":
            return 201, {"id": "rep-123", "status": "received"}, 12.0
        if path == "/setup-requests/parse":
            return 200, {"setup": {"external_displays": 2}, "needs_clarification": False}, 45.0
        if path == "/metrics":
            return (
                200,
                "# HELP portpilot_http_requests_total\n"
                "portpilot_http_requests_total 10\n"
                "portpilot_http_request_duration_seconds_bucket{le='0.05'} 10\n"
                "portpilot_http_request_duration_seconds_count 10\n"
                "portpilot_http_request_duration_seconds_sum 0.1\n",
                8.0,
            )
        if path == "/":
            return 200, "<!DOCTYPE html><html><head><title>PortPilot</title></head></html>", 10.0
        if path == "/coverage":
            return 200, "<!DOCTYPE html><html><head><title>PortPilot Coverage</title></head></html>", 10.0
        raise AssertionError(f"Unhandled mock path: {path}")

    with patch.object(verifier, "_http_request", side_effect=mock_http):
        report = verifier.run_all()

    assert report.overall_status == "PASS"
    assert report.failed_checks == 0
    assert report.passed_checks == 12


def test_preview_verifier_detects_catalogue_leak():
    verifier = PreviewVerifier(api_url="http://mock-preview:8000")

    def mock_http(base_url, path, method="GET", payload=None, expected_statuses=(200,)):
        if path == "/health":
            return 200, {"status": "ok"}, 5.0
        if path == "/ready":
            return 200, {"status": "ready"}, 6.0
        if path == "/devices":
            return (
                200,
                {
                    "laptops": [
                        {
                            "id": "draft-lap",
                            "brand": "Dell",
                            "name": "Draft XPS",
                            "model_code": "9315",
                            "review_status": "draft",  # LEAK!
                        }
                    ],
                    "accessories": [],
                },
                10.0,
            )
        return 200, {}, 5.0

    with patch.object(verifier, "_http_request", side_effect=mock_http):
        report = verifier.run_all()

    assert report.overall_status == "FAIL"
    failed_names = [r.name for r in report.results if r.status == "FAIL"]
    assert "Catalogue Data Integrity & Filtering (GET /devices)" in failed_names


def test_preview_verifier_unconfigured_parser_handling():
    # When not required, 503 from parser results in SKIP, not FAIL
    verifier = PreviewVerifier(api_url="http://mock-preview:8000", require_live_parser=False)

    def mock_http(base_url, path, method="GET", payload=None, expected_statuses=(200,)):
        if path == "/setup-requests/parse":
            return 503, {"detail": "SETUP_PARSER_API_KEY not configured"}, 5.0
        if path == "/health":
            return 200, {"status": "ok"}, 5.0
        if path == "/ready":
            return 200, {"status": "ready"}, 6.0
        if path == "/devices":
            return (
                200,
                {
                    "laptops": [
                        {
                            "id": "lap1",
                            "brand": "A",
                            "name": "B",
                            "model_code": "C",
                            "review_status": "verified",
                        }
                    ],
                    "accessories": [
                        {
                            "id": "acc1",
                            "brand": "X",
                            "name": "Y",
                            "category": "hub",
                            "review_status": "verified",
                        }
                    ],
                },
                5.0,
            )
        if path.startswith("/devices/laptops/"):
            return 200, {"id": "lap1"}, 5.0
        if path.startswith("/devices/accessories/"):
            return 200, {"id": "acc1"}, 5.0
        if path == "/checks":
            return (
                200,
                {
                    "verdict": "compatible",
                    "summary": "",
                    "limits": [],
                    "requirements": [],
                    "evidence": [],
                    "rule_engine_version": "v2",
                },
                5.0,
            )
        if path == "/result-reports":
            return 201, {"id": "1", "status": "received"}, 5.0
        if path == "/metrics":
            metric_text = (
                "portpilot_http_requests_total 1\n"
                "portpilot_http_request_duration_seconds_bucket 1\n"
                "portpilot_http_request_duration_seconds_count 1\n"
                "portpilot_http_request_duration_seconds_sum 1"
            )
            return 200, metric_text, 5.0
        return 200, {}, 5.0

    with patch.object(verifier, "_http_request", side_effect=mock_http):
        report = verifier.run_all()

    parser_res = next(r for r in report.results if "Setup Parser" in r.name)
    assert parser_res.status == "SKIP"
    assert report.overall_status == "PASS"


def test_preview_verifier_metrics_leak_detection():
    verifier = PreviewVerifier(api_url="http://mock-preview:8000")

    def mock_http(base_url, path, method="GET", payload=None, expected_statuses=(200,)):
        if path == "/metrics":
            return (
                200,
                "portpilot_http_requests_total 1\n"
                "portpilot_http_request_duration_seconds_bucket 1\n"
                "portpilot_http_request_duration_seconds_count 1\n"
                "portpilot_http_request_duration_seconds_sum 1\n"
                "# leaked: Authorization: Bearer super_secret_token_1234567890\n",
                5.0,
            )
        return 200, {"status": "ok"}, 5.0

    with patch.object(verifier, "_http_request", side_effect=mock_http):
        verifier.verify_metrics_and_observability()

    metrics_res = next(r for r in verifier.results if "Observability" in r.name)
    assert metrics_res.status == "FAIL"
    assert "leak" in metrics_res.details
