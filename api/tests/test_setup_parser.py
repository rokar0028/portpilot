import json

import pytest
from fastapi import HTTPException

from app import setup_parser
from app.main import parse_setup_request
from app.schemas import SetupParseRequest
from app.setup_parser import ParserInvalidResponse, ParserUnavailable


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.payload


def configure_provider(monkeypatch):
    monkeypatch.setenv("SETUP_PARSER_BASE_URL", "https://provider.example/v1")
    monkeypatch.setenv("SETUP_PARSER_MODEL", "test-model")
    monkeypatch.setenv("SETUP_PARSER_API_KEY", "test-secret")


def test_parser_extracts_setup_and_only_sends_user_description(monkeypatch):
    configure_provider(monkeypatch)
    captured = {}

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "setup": {
                                        "external_displays": 2,
                                        "resolution": "3840x2160",
                                        "refresh_rate_hz": 60,
                                        "laptop_charging": True,
                                    },
                                    "needs_clarification": False,
                                    "clarification_questions": [],
                                    "unsupported_requests": [],
                                }
                            )
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(setup_parser, "urlopen", fake_urlopen)
    parsed = setup_parser.parse_setup("Two 4K monitors at 60 Hz and charge my laptop")

    assert parsed.setup.external_displays == 2
    assert parsed.setup.resolution == "3840x2160"
    assert captured["authorization"] == "Bearer test-secret"
    assert captured["timeout"] == 15
    assert [message["role"] for message in captured["payload"]["messages"]] == ["system", "user"]
    assert captured["payload"]["messages"][1]["content"] == ("Two 4K monitors at 60 Hz and charge my laptop")
    assert "laptop_id" not in json.dumps(captured["payload"])


def test_ambiguous_and_unsupported_fields_are_explicit(monkeypatch):
    configure_provider(monkeypatch)
    monkeypatch.setattr(
        setup_parser,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "setup": {
                                        "external_displays": None,
                                        "resolution": None,
                                        "refresh_rate_hz": None,
                                        "laptop_charging": None,
                                    },
                                    "needs_clarification": True,
                                    "clarification_questions": ["How many displays?"],
                                    "unsupported_requests": ["Ethernet"],
                                }
                            )
                        }
                    }
                ]
            }
        ),
    )

    parsed = setup_parser.parse_setup("Connect my usual setup and network")

    assert parsed.needs_clarification is True
    assert parsed.setup.external_displays is None
    assert parsed.clarification_questions == ["How many displays?"]
    assert parsed.unsupported_requests == ["Ethernet"]


def test_malformed_or_out_of_range_provider_output_is_rejected(monkeypatch):
    configure_provider(monkeypatch)
    monkeypatch.setattr(
        setup_parser,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            {"choices": [{"message": {"content": '{"setup":{"external_displays":99}'}}]}
        ),
    )

    with pytest.raises(ParserInvalidResponse):
        setup_parser.parse_setup("One display")


def test_null_or_non_string_message_content_is_safely_rejected(monkeypatch):
    configure_provider(monkeypatch)
    for invalid_content in (None, 123, False, []):
        monkeypatch.setattr(
            setup_parser,
            "urlopen",
            lambda *_args, **_kwargs: FakeResponse(
                {"choices": [{"message": {"content": invalid_content}}]}
            ),
        )
        with pytest.raises(ParserInvalidResponse):
            setup_parser.parse_setup("One display")


def test_unconfigured_provider_is_explicitly_unavailable(monkeypatch):
    monkeypatch.delenv("SETUP_PARSER_BASE_URL", raising=False)
    monkeypatch.delenv("SETUP_PARSER_MODEL", raising=False)

    with pytest.raises(ParserUnavailable):
        setup_parser.parse_setup("One display")

    with pytest.raises(HTTPException) as error:
        parse_setup_request(SetupParseRequest(description="One display"))
    assert error.value.status_code == 503
    assert error.value.detail["code"] == "setup_parser_unavailable"


def test_provider_transport_failure_maps_to_safe_503(monkeypatch):
    def unavailable(_text):
        raise ParserUnavailable("The setup parser provider is unavailable. Use manual setup fields.")

    monkeypatch.setattr(setup_parser, "parse_setup", unavailable)

    with pytest.raises(HTTPException) as error:
        parse_setup_request(SetupParseRequest(description="One display"))
    assert error.value.status_code == 503
    assert "manual" in error.value.detail["message"]


def test_v2_prompts_benchmark_schema_and_categories() -> None:
    from pathlib import Path

    benchmark_path = Path(__file__).resolve().parents[1] / "evaluations" / "v2_setup_prompts.json"
    assert benchmark_path.is_file()

    cases = json.loads(benchmark_path.read_text(encoding="utf-8"))
    assert len(cases) >= 25

    expected_categories = {
        "standard_single",
        "high_refresh",
        "multi_display",
        "underspecified",
        "ambiguous",
        "unsupported_peripheral",
        "safety_adversarial",
    }
    actual_categories = {c.get("category") for c in cases}
    assert expected_categories.issubset(actual_categories)

    for case in cases:
        assert "id" in case
        assert "prompt" in case and len(case["prompt"]) >= 5
        assert "expected" in case
        exp = case["expected"]
        assert "external_displays" in exp
        assert "resolution" in exp
        assert "refresh_rate_hz" in exp
        assert "laptop_charging" in exp


def test_evaluation_runner_mock_execution() -> None:
    import sys
    from pathlib import Path

    api_root = Path(__file__).resolve().parents[1]
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from scripts.evaluate_setup_parser import load_cases, render_markdown, run_evaluation

    benchmark_path = api_root / "evaluations" / "v2_setup_prompts.json"
    cases = load_cases(benchmark_path)
    report = run_evaluation(cases, mock=True)

    assert report["mode"] == "mock"
    assert report["total_cases"] == len(cases)
    assert report["overall_exact_match_rate"] == 1.0
    assert report["failure_count"] == 0
    assert report["clarification"]["recall"] == 1.0
    assert report["unsupported"]["recall"] == 1.0
    for field in ("external_displays", "resolution", "refresh_rate_hz", "laptop_charging"):
        assert report["fields"][field]["accuracy"] == 1.0

    markdown = render_markdown(report)
    assert "# PortPilot Setup Parser Evaluation Report" in markdown
    assert "Execution Mode:** `MOCK`" in markdown
    assert "Hardware compatibility verdicts are 100% deterministic" in markdown


def test_evaluation_runner_detects_and_records_failures() -> None:
    import sys
    from pathlib import Path

    api_root = Path(__file__).resolve().parents[1]
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from scripts.evaluate_setup_parser import run_evaluation

    synthetic_failing_case = [
        {
            "id": "synthetic-mismatch",
            "category": "standard_single",
            "prompt": "One 1080p display at 60 Hz",
            # Intentionally mismatch expected with mock's generated output for testing failure recording
            "expected": {
                "external_displays": 99,  # Mock returns None or valid bounded, so this mismatches
                "resolution": "1920x1080",
                "refresh_rate_hz": 60,
                "laptop_charging": True,
            },
            "expect_clarification": False,
            "expect_unsupported": False,
        }
    ]

    report = run_evaluation(synthetic_failing_case, mock=True)
    assert report["failure_count"] >= 1
    assert report["failures"][0]["id"] == "synthetic-mismatch"
    assert report["failures"][0]["expected"]["external_displays"] == 99


def test_parser_handles_markdown_code_fenced_json(monkeypatch):
    configure_provider(monkeypatch)
    raw_json = json.dumps(
        {
            "setup": {
                "external_displays": 1,
                "resolution": "1920x1080",
                "refresh_rate_hz": 60,
                "laptop_charging": True,
            },
            "needs_clarification": False,
            "clarification_questions": [],
            "unsupported_requests": [],
        }
    )
    fenced_content = f"```json\n{raw_json}\n```"

    monkeypatch.setattr(
        setup_parser,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse({"choices": [{"message": {"content": fenced_content}}]}),
    )
    parsed = setup_parser.parse_setup("One 1080p monitor and charging")
    assert parsed.setup.external_displays == 1
    assert parsed.setup.resolution == "1920x1080"
    assert parsed.setup.laptop_charging is True
