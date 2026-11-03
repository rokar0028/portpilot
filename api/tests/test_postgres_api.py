"""HTTP-level checks that require the isolated PostgreSQL E2E database."""

import os
from datetime import date
from urllib.parse import urlparse
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError

from app.database import SessionLocal, get_session
from app.main import app
from app.models import AccessoryModel, LaptopModel, SourceEvidence

if os.getenv("PORTPILOT_POSTGRES_TESTS") == "1":
    database_url = os.getenv("DATABASE_URL", "")
    database = urlparse(database_url)
    if (
        not database_url.startswith("postgresql+")
        or database.hostname not in {"localhost", "127.0.0.1", "::1"}
        or database.path != "/portpilot_e2e"
    ):
        raise RuntimeError("PostgreSQL API tests require the local portpilot_e2e database.")

pytestmark = pytest.mark.skipif(
    os.getenv("PORTPILOT_POSTGRES_TESTS") != "1",
    reason="Requires the explicitly enabled disposable PostgreSQL E2E database.",
)

ADMIN_TOKEN = "portpilot-local-e2e-token"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", ADMIN_TOKEN)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def cleanup_records():
    ids: list[str] = []
    yield ids.append
    with SessionLocal.begin() as session:
        session.query(SourceEvidence).filter(
            (SourceEvidence.laptop_id.in_(ids)) | (SourceEvidence.accessory_id.in_(ids))
        ).delete(synchronize_session=False)
        session.query(LaptopModel).filter(LaptopModel.id.in_(ids)).delete(synchronize_session=False)
        session.query(AccessoryModel).filter(AccessoryModel.id.in_(ids)).delete(synchronize_session=False)


def laptop_payload(device_id: str, *, review_status: str = "verified", suffix: str = "initial") -> dict:
    return {
        "id": device_id,
        "brand": "PortPilot E2E Test",
        "name": f"Synthetic API laptop {suffix}",
        "model_code": f"{device_id}-model",
        "usb_c_port_count": 1,
        "review_status": review_status,
        "change_reason": "Verified the synthetic test record against its fixture source.",
        "evidence": [
            {
                "id": f"{device_id}:{suffix}:model",
                "capability_key": "model_code",
                "title": "Synthetic API source",
                "url": "https://example.invalid/api-test",
                "excerpt": "Synthetic model code for API integration testing.",
                "checked_on": str(date(2026, 11, 2)),
                "status": "verified",
            },
            {
                "id": f"{device_id}:{suffix}:ports",
                "capability_key": "usb_c_port_count",
                "title": "Synthetic API source",
                "url": "https://example.invalid/api-test",
                "excerpt": "One USB-C port for API integration testing.",
                "checked_on": str(date(2026, 11, 2)),
                "status": "verified",
            },
        ],
    }


def test_health_readiness_and_verified_catalogue_are_available(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}

    response = client.get("/devices")
    assert response.status_code == 200
    catalogue = response.json()
    laptop_ids = {record["id"] for record in catalogue["laptops"]}
    accessory_ids = {record["id"] for record in catalogue["accessories"]}
    assert "e2e-good-laptop" in laptop_ids
    assert "e2e-good-hub" in accessory_ids
    assert "e2e-hidden-laptop" not in laptop_ids
    assert "e2e-hidden-hub" not in accessory_ids
    assert all(
        source["status"] == "verified"
        for device in [*catalogue["laptops"], *catalogue["accessories"]]
        for source in device["evidence"]
    )


def test_readiness_reports_database_outage_and_recovers(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class UnavailableSession:
        def execute(self, _statement):
            raise OperationalError("SELECT 1", {}, ConnectionError("synthetic outage"))

        def close(self) -> None:
            pass

    def unavailable_session():
        yield UnavailableSession()

    monkeypatch.setitem(app.dependency_overrides, get_session, unavailable_session)
    assert client.get("/health").status_code == 200
    outage = client.get("/ready")
    assert outage.status_code == 503
    assert outage.json() == {"status": "not_ready"}

    monkeypatch.delitem(app.dependency_overrides, get_session)
    recovered = client.get("/ready")
    assert recovered.status_code == 200
    assert recovered.json() == {"status": "ready"}


def test_check_http_response_hides_unverified_evidence(client: TestClient) -> None:
    response = client.post(
        "/checks",
        json={
            "laptop_id": "e2e-good-laptop",
            "accessory_id": "e2e-good-hub",
            "setup": {
                "external_displays": 1,
                "resolution": "1920x1080",
                "refresh_rate_hz": 60,
                "laptop_charging": False,
            },
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["verdict"] == "compatible"
    assert result["requirements"]
    assert result["evidence"]
    assert all(source["status"] == "verified" for source in result["evidence"])


@pytest.mark.parametrize(
    ("laptop_id", "expected_verdict"),
    [("e2e-bad-laptop", "incompatible"), ("e2e-unknown-laptop", "insufficient_data")],
)
def test_check_http_preserves_incompatible_and_unknown_verdicts(
    client: TestClient, laptop_id: str, expected_verdict: str
) -> None:
    response = client.post(
        "/checks",
        json={
            "laptop_id": laptop_id,
            "accessory_id": "e2e-good-hub",
            "setup": {
                "external_displays": 1,
                "resolution": "1920x1080",
                "refresh_rate_hz": 60,
                "laptop_charging": False,
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["verdict"] == expected_verdict


def test_unverified_devices_are_not_addressable_by_public_http_routes(client: TestClient) -> None:
    response = client.get("/devices/laptops/e2e-hidden-laptop")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "laptop_not_found"

    response = client.post(
        "/checks",
        json={
            "laptop_id": "e2e-hidden-laptop",
            "accessory_id": "e2e-good-hub",
            "setup": {"laptop_charging": False},
        },
    )
    assert response.status_code == 404


def test_admin_routes_require_bearer_authentication(client: TestClient) -> None:
    assert client.get("/admin/laptops").status_code == 401
    assert client.get("/admin/laptops", headers={"Authorization": "Bearer wrong"}).status_code == 401
    response = client.get("/admin/laptops", headers={"Authorization": f"Bearer {ADMIN_TOKEN}"})
    assert response.status_code == 200
    assert any(item["id"] == "e2e-hidden-laptop" for item in response.json())


def test_cors_allows_configured_frontend_and_rejects_other_origins(client: TestClient) -> None:
    headers = {
        "Origin": "http://127.0.0.1:13000",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    }
    response = client.options("/checks", headers=headers)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:13000"

    response = client.options("/checks", headers={**headers, "Origin": "https://untrusted.invalid"})
    assert "access-control-allow-origin" not in response.headers


def test_publish_validation_and_draft_to_verified_lifecycle(client: TestClient, cleanup_records) -> None:
    device_id = f"e2e-api-laptop-{uuid4().hex}"
    cleanup_records(device_id)
    admin_headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

    draft = client.post(
        "/admin/laptops",
        headers=admin_headers,
        json={"id": device_id, "brand": "PortPilot E2E Test", "name": "Synthetic draft"},
    )
    assert draft.status_code == 201
    assert draft.json()["review_status"] == "draft"
    assert client.get(f"/devices/laptops/{device_id}").status_code == 404

    missing_evidence = laptop_payload(device_id, review_status="verified")
    missing_evidence["evidence"] = []
    rejected = client.put(f"/admin/laptops/{device_id}", headers=admin_headers, json=missing_evidence)
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["code"] == "publish_validation_failed"

    verified = laptop_payload(device_id)
    published = client.put(f"/admin/laptops/{device_id}", headers=admin_headers, json=verified)
    assert published.status_code == 200
    assert published.json()["review_status"] == "verified"
    public = client.get(f"/devices/laptops/{device_id}")
    assert public.status_code == 200
    assert public.json()["review_status"] == "verified"


def test_updating_verified_device_replaces_its_evidence(client: TestClient, cleanup_records) -> None:
    device_id = f"e2e-api-laptop-{uuid4().hex}"
    cleanup_records(device_id)
    admin_headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

    created = client.post("/admin/laptops", headers=admin_headers, json=laptop_payload(device_id))
    assert created.status_code == 201
    old_ids = {item["id"] for item in created.json()["evidence"]}

    updated_payload = laptop_payload(device_id, suffix="updated")
    updated = client.put(f"/admin/laptops/{device_id}", headers=admin_headers, json=updated_payload)
    assert updated.status_code == 200
    new_ids = {item["id"] for item in updated.json()["evidence"]}
    assert new_ids.isdisjoint(old_ids)

    with SessionLocal() as session:
        persisted_ids = set(
            session.scalars(select(SourceEvidence.id).where(SourceEvidence.laptop_id == device_id)).all()
        )
    assert persisted_ids == new_ids


def test_catalogue_seed_is_idempotent_in_postgresql() -> None:
    from app.seed import seed

    with SessionLocal() as session:
        before = (
            session.scalar(select(func.count()).select_from(LaptopModel)),
            session.scalar(select(func.count()).select_from(AccessoryModel)),
            session.scalar(select(func.count()).select_from(SourceEvidence)),
        )

    seed()
    seed()

    with SessionLocal() as session:
        after = (
            session.scalar(select(func.count()).select_from(LaptopModel)),
            session.scalar(select(func.count()).select_from(AccessoryModel)),
            session.scalar(select(func.count()).select_from(SourceEvidence)),
        )
    assert after == before
