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


def test_request_duration_histogram_distribution_and_scrape_format() -> None:
    from app.observability import Metrics

    m = Metrics()
    # 0.003s is <= 0.005
    m.record_request("GET", "/ready", 200, duration_seconds=0.003)
    # 0.030s is <= 0.05
    m.record_request("GET", "/ready", 200, duration_seconds=0.030)
    # 0.600s is <= 1.0 (exceeds 0.5s SLO threshold)
    m.record_request("GET", "/ready", 200, duration_seconds=0.600)

    rendered = m.render()

    assert "# TYPE portpilot_http_request_duration_seconds histogram" in rendered
    assert "# HELP portpilot_http_request_duration_seconds Process-local" in rendered

    # Check cumulative bucket counts
    assert (
        "portpilot_http_request_duration_seconds_bucket{"
        'method="GET",route="/ready",status="200",le="0.005"} 1' in rendered
    )
    assert (
        "portpilot_http_request_duration_seconds_bucket{"
        'method="GET",route="/ready",status="200",le="0.025"} 1' in rendered
    )
    assert (
        'portpilot_http_request_duration_seconds_bucket{method="GET",route="/ready",status="200",le="0.05"} 2'
        in rendered
    )
    assert (
        'portpilot_http_request_duration_seconds_bucket{method="GET",route="/ready",status="200",le="0.5"} 2'
        in rendered
    )
    assert (
        'portpilot_http_request_duration_seconds_bucket{method="GET",route="/ready",status="200",le="1.0"} 3'
        in rendered
    )
    assert (
        'portpilot_http_request_duration_seconds_bucket{method="GET",route="/ready",status="200",le="+Inf"} 3'
        in rendered
    )

    # Check count and sum
    assert (
        'portpilot_http_request_duration_seconds_count{method="GET",route="/ready",status="200"} 3'
        in rendered
    )
    assert (
        'portpilot_http_request_duration_seconds_sum{method="GET",route="/ready",status="200"} 0.633000'
        in rendered
    )

    # Check total request counter
    assert 'portpilot_http_requests_total{method="GET",route="/ready",status="200"} 3' in rendered


def test_slow_request_logging_emits_only_above_threshold_with_safe_fields(caplog, monkeypatch) -> None:
    from app import main

    # Set threshold to 10 ms for test verification
    monkeypatch.setattr(main, "SLOW_REQUEST_THRESHOLD_MS", 10.0)

    secret = "authorization-secret"
    body_sentinel = "sensitive-request-prose-body"
    client_ip = "192.0.2.1"

    scope_fast = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/checks",
        "raw_path": b"/checks",
        "query_string": b"secret_param=forbidden-value",
        "root_path": "",
        "headers": [(b"authorization", f"Bearer {secret}".encode())],
        "server": ("testserver", 80),
        "client": (client_ip, 54321),
        "route": SimpleNamespace(path="/checks"),
    }
    request_fast = Request(scope_fast)

    async def fast_handler(_request: Request):
        return JSONResponse(status_code=200, content={"status": "ok"})

    # Fast request: should log http_request, should NOT log http_slow_request
    with caplog.at_level("INFO", logger="portpilot.api"):
        caplog.clear()
        response = run_inline(observe_request(request_fast, fast_handler))
        assert response.status_code == 200
        event_names = [getattr(r, "event_name", None) for r in caplog.records]
        assert "http_request" in event_names
        assert "http_slow_request" not in event_names

    # Slow request: simulate delay >= 10 ms
    import time

    async def slow_handler(_request: Request):
        time.sleep(0.015)
        return JSONResponse(status_code=200, content={"status": "slow_done"})

    with caplog.at_level("INFO", logger="portpilot.api"):
        caplog.clear()
        response_slow = run_inline(observe_request(request_fast, slow_handler))
        assert response_slow.status_code == 200
        event_names = [getattr(r, "event_name", None) for r in caplog.records]
        assert "http_request" in event_names
        assert "http_slow_request" in event_names

        slow_log = next(r for r in caplog.records if getattr(r, "event_name", None) == "http_slow_request")
        assert slow_log.request_id == response_slow.headers["X-Request-ID"]
        assert slow_log.method == "POST"
        assert slow_log.route == "/checks"
        assert slow_log.status_code == 200
        assert slow_log.elapsed_ms >= 10.0

        # Verify no sensitive data leaked into caplog
        assert secret not in caplog.text
        assert "forbidden-value" not in caplog.text
        assert body_sentinel not in caplog.text
        assert client_ip not in caplog.text


def test_exception_path_observability_and_safe_error_logging(caplog) -> None:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/devices/laptops/ex-1",
        "raw_path": b"/devices/laptops/ex-1",
        "query_string": b"param=123",
        "root_path": "",
        "headers": [],
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 1234),
        "route": SimpleNamespace(path="/devices/laptops/{device_id}"),
    }
    request = Request(scope)

    async def crashing_handler(_request: Request):
        raise RuntimeError("database password failure internal detail")

    with caplog.at_level("INFO", logger="portpilot.api"):
        caplog.clear()
        response = run_inline(observe_request(request, crashing_handler))

    assert response.status_code == 500
    assert response.headers["X-Request-ID"]

    error_log = next(r for r in caplog.records if getattr(r, "event_name", None) == "http_request")
    assert error_log.status_code == 500
    assert error_log.error_type == "RuntimeError"
    assert error_log.route == "/devices/laptops/{device_id}"

    # Verify sensitive error detail is not leaked in the structured log
    assert "database password failure" not in caplog.text
