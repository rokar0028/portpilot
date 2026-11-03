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
