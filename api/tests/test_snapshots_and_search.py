from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_session
from app.main import app
from app.models import AccessoryModel, LaptopModel, SourceEvidence


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with sessions() as sess:
        laptop = LaptopModel(
            id="apple-macbook-pro-14",
            brand="Apple",
            name="MacBook Pro 14 M3",
            model_code="A2992",
            usb_c_port_count=2,
            usb_c_video_supported=True,
            usb_c_dp_version="1.4",
            usb_c_pd_input_min_w=45,
            usb_c_pd_input_max_w=70,
            maximum_external_displays=2,
            usb_c_max_resolution="6K",
            usb_c_max_refresh_hz=60,
            review_status="verified",
        )
        hub = AccessoryModel(
            id="caldigit-ts4",
            brand="CalDigit",
            name="TS4 Thunderbolt 4 Dock",
            model_code="TS4-US",
            category="usb_c_dock",
            host_connection="Thunderbolt 4",
            requires_usb_c_dp_alt_mode=True,
            hdmi_port_count=1,
            hdmi_max_resolution="8K",
            hdmi_max_refresh_hz=60,
            pd_pass_through_max_w=98,
            review_status="verified",
        )
        charger = AccessoryModel(
            id="anker-737-charger",
            brand="Anker",
            name="737 GaNPrime 120W Charger",
            category="usb_c_charger",
            host_connection="USB-C",
            requires_usb_c_dp_alt_mode=False,
            usb_c_output_max_w=120,
            review_status="verified",
        )
        sess.add_all([laptop, hub, charger])
        sess.flush()

        # Add evidence (one fresh, one stale)
        fresh_evidence = SourceEvidence(
            id="ev-1",
            laptop_id=laptop.id,
            capability_key="usb_c_video_supported",
            source_title="Apple Specs",
            source_url="https://apple.com/specs",
            excerpt="Supports one external display",
            checked_on=date.today() - timedelta(days=30),
            review_status="verified",
        )
        stale_evidence = SourceEvidence(
            id="ev-2",
            accessory_id=hub.id,
            capability_key="pd_pass_through_max_w",
            source_title="CalDigit TS4 Specs",
            source_url="https://caldigit.com/ts4",
            excerpt="98W host charging",
            checked_on=date.today() - timedelta(days=220),
            review_status="verified",
        )
        sess.add_all([fresh_evidence, stale_evidence])
        sess.commit()
        yield sess
        sess.close()


@pytest.fixture
def client(session):
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ==================== Item 5: Result Snapshots Tests ====================


def test_create_and_retrieve_result_snapshot(client):
    payload = {
        "laptop_id": "apple-macbook-pro-14",
        "accessory_id": "caldigit-ts4",
        "setup": {
            "external_displays": 2,
            "resolution": "4K",
            "refresh_rate_hz": 60,
            "laptop_charging": True,
        },
        "verdict": "compatible",
        "summary": "Compatible setup with full charging.",
        "limits": ["Limit A"],
        "requirements": [{"requirement": "Thunderbolt 4 cable required"}],
        "evidence": [],
        "rule_engine_version": "v0.5.0",
    }

    create_resp = client.post("/result-snapshots", json=payload)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    snapshot_id = created_data["id"]
    assert snapshot_id.startswith("snap-")
    assert created_data["laptop_id"] == "apple-macbook-pro-14"
    assert created_data["accessory_id"] == "caldigit-ts4"
    assert created_data["setup"]["external_displays"] == 2
    assert created_data["verdict"] == "compatible"
    assert created_data["summary"] == "Compatible setup with full charging."

    # Retrieve snapshot
    get_resp = client.get(f"/result-snapshots/{snapshot_id}")
    assert get_resp.status_code == 200
    retrieved_data = get_resp.json()
    assert retrieved_data["id"] == snapshot_id
    assert retrieved_data["verdict"] == "compatible"
    assert retrieved_data["summary"] == "Compatible setup with full charging."


def test_get_nonexistent_snapshot_returns_404(client):
    resp = client.get("/result-snapshots/nonexist")
    assert resp.status_code == 404
    detail = resp.json()["detail"]
    assert "not found" in detail.get("message", "").lower() or "not_found" in detail.get("code", "")


# ==================== Item 6: Catalogue Search Tests ====================


def test_catalogue_search_across_all(client):
    resp = client.get("/devices/search?q=macbook")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(item["id"] == "apple-macbook-pro-14" for item in data["laptops"])


def test_catalogue_search_filter_by_kind(client):
    # Search for "caldigit" under accessories
    resp = client.get("/devices/search?q=caldigit&kind=accessory")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["accessories"][0]["id"] == "caldigit-ts4"
    assert len(data["laptops"]) == 0

    # Search for "caldigit" under laptops should yield 0
    resp_laptops = client.get("/devices/search?q=caldigit&kind=laptop")
    assert resp_laptops.status_code == 200
    assert resp_laptops.json()["total"] == 0
    assert len(resp_laptops.json()["laptops"]) == 0


def test_catalogue_search_filter_by_category(client):
    resp = client.get("/devices/search?category=usb_c_charger")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["accessories"][0]["id"] == "anker-737-charger"


def test_catalogue_search_empty_results(client):
    resp = client.get("/devices/search?q=nonexistentproductname")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["laptops"] == []
    assert data["accessories"] == []


def test_catalogue_fuzzy_search_normalizes_spaces_and_hyphens(client):
    # Searching with hyphen/space matches model_code "TS4-US" or "A2992"
    resp = client.get("/devices/search?q=ts4us")
    assert resp.status_code == 200
    assert any(item["id"] == "caldigit-ts4" for item in resp.json()["accessories"])

    resp2 = client.get("/devices/search?q=ts-4")
    assert resp2.status_code == 200
    assert any(item["id"] == "caldigit-ts4" for item in resp2.json()["accessories"])

    resp3 = client.get("/devices/search?q=mac-book")
    assert resp3.status_code == 200
    assert any(item["id"] == "apple-macbook-pro-14" for item in resp3.json()["laptops"])


# ==================== Item 7: Stale Evidence Audit Tests ====================


def test_stale_evidence_endpoint(client, monkeypatch):
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token")
    headers = {"Authorization": "Bearer test-admin-token"}

    # Stale threshold 180 days: stale_evidence (220 days) should appear, fresh (30 days) should not
    resp = client.get("/admin/evidence/stale?max_age_days=180", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_stale"] == 1
    stale_item = data["stale_items"][0]
    assert stale_item["device_id"] == "caldigit-ts4"
    assert stale_item["capability_key"] == "pd_pass_through_max_w"
    assert stale_item["age_days"] >= 200

    # Threshold 365 days: nothing should be stale
    resp_365 = client.get("/admin/evidence/stale?max_age_days=365", headers=headers)
    assert resp_365.status_code == 200
    assert resp_365.json()["total_stale"] == 0
