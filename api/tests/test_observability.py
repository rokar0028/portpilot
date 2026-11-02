from types import SimpleNamespace

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base, normalize_database_url
from app.main import (
    application_metrics,
    check_compatibility,
    health,
    observe_request,
    readiness,
)
from app.models import AccessoryModel, LaptopModel
from app.schemas import CheckRequest


def run_inline(coroutine):
    """Run a coroutine that completes without scheduling or I/O."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("Expected the request middleware test coroutine to complete inline.")


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as database:
        database.add_all(
            [
                LaptopModel(
                    id="monitoring-laptop",
                    brand="Example",
                    name="Example laptop",
                    model_code="EX-100",
                    usb_c_port_count=1,
                ),
                AccessoryModel(
                    id="monitoring-hub",
                    brand="Example",
                    name="Example hub",
                    category="usb_c_hub",
                    model_code="EX-HUB",
                    host_connection="USB-C",
                    hdmi_port_count=1,
                ),
            ]
        )
        database.commit()
        yield database
    Base.metadata.drop_all(engine)
    engine.dispose()


def test_health_is_liveness_and_readiness_checks_the_database(session: Session) -> None:
    assert health() == {"status": "ok"}
    assert readiness(session) == {"status": "ready"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("postgres://user:pass@host:5432/db", "postgresql+psycopg://user:pass@host:5432/db"),
        (
            "postgresql://user:pass@host:5432/db",
            "postgresql+psycopg://user:pass@host:5432/db",
        ),
        ("sqlite:///./portpilot.db", "sqlite:///./portpilot.db"),
    ],
)
def test_hosted_database_urls_use_psycopg3(value: str, expected: str) -> None:
    assert normalize_database_url(value) == expected


def test_readiness_does_not_disclose_database_errors() -> None:
    class FailedSession:
        def execute(self, statement):
            raise SQLAlchemyError("database password must not be disclosed")

    response = readiness(FailedSession())

    assert isinstance(response, JSONResponse)
    assert response.status_code == 503
    assert response.body == b'{"status":"not_ready"}'


def test_compatibility_verdict_is_counted_with_rule_version(session: Session) -> None:
    result = check_compatibility(
        CheckRequest(
            laptop_id="monitoring-laptop",
            accessory_id="monitoring-hub",
            setup={
                "external_displays": 1,
                "resolution": "1920x1080",
                "refresh_rate_hz": 60,
                "laptop_charging": False,
            },
        ),
        session,
    )
    metrics_response = application_metrics()
    metrics = metrics_response.body.decode()

    assert metrics_response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    assert f'verdict="{result.verdict}"' in metrics
    assert f'rule_engine_version="{result.rule_engine_version}"' in metrics
    assert "portpilot_http_requests_total" in metrics


def test_request_logs_include_correlation_but_not_query_or_credentials(caplog) -> None:
    secret = "sensitive-test-token"
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/admin/laptops",
        "raw_path": b"/admin/laptops",
        "query_string": b"do_not_log=query-secret",
        "root_path": "",
        "headers": [(b"authorization", f"Bearer {secret}".encode())],
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1234),
        "route": SimpleNamespace(path="/admin/laptops"),
    }
    request = Request(scope)

    async def unauthorized_response(_request: Request):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized."})

    with caplog.at_level("INFO", logger="portpilot.api"):
        response = run_inline(observe_request(request, unauthorized_response))

    request_id = response.headers["X-Request-ID"]
    request_log = next(
        record for record in caplog.records if getattr(record, "event_name", None) == "http_request"
    )
    assert response.status_code == 401
    assert request_log.request_id == request_id
    assert request_log.path == "/admin/laptops"
    assert request_log.status_code == 401
    assert secret not in caplog.text
    assert "query-secret" not in caplog.text
