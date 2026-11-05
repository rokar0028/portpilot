from datetime import date

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_session
from app.main import app, laptop_compatible_accessories
from app.models import AccessoryModel, LaptopModel, SourceEvidence
from app.rules import RULE_ENGINE_VERSION


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
            id="test-laptop",
            brand="TestBrand",
            name="Test Laptop 14",
            usb_c_port_count=1,
            usb_c_video_supported=True,
            usb_c_dp_version="1.4",
            usb_c_pd_input_min_w=45,
            usb_c_pd_input_max_w=65,
            maximum_external_displays=2,
            usb_c_max_resolution="4K",
            usb_c_max_refresh_hz=60,
            review_status="verified",
        )
        hub = AccessoryModel(
            id="test-hub",
            brand="TestBrand",
            name="Test Hub 7-in-1",
            category="usb_c_hub",
            host_connection="USB-C",
            requires_usb_c_dp_alt_mode=True,
            hdmi_port_count=1,
            hdmi_max_resolution="4K",
            hdmi_max_refresh_hz=60,
            pd_pass_through_max_w=50,
            review_status="verified",
        )
        charger = AccessoryModel(
            id="test-charger",
            brand="TestBrand",
            name="Test Charger 65W",
            category="usb_c_charger",
            host_connection="USB-C",
            requires_usb_c_dp_alt_mode=False,
            usb_c_output_max_w=65,
            review_status="verified",
        )
        draft_acc = AccessoryModel(
            id="draft-hub",
            brand="TestBrand",
            name="Draft Hub",
            category="usb_c_hub",
            host_connection="USB-C",
            review_status="draft",
        )
        laptop.evidence.append(
            SourceEvidence(
                id="laptop-ev",
                capability_key="usb_c_video_supported",
                source_title="Laptop Specs",
                source_url="https://example.com/laptop",
                excerpt="DisplayPort 1.4 supported.",
                checked_on=date(2026, 11, 2),
                review_status="verified",
            )
        )
        hub.evidence.append(
            SourceEvidence(
                id="hub-ev",
                capability_key="hdmi_max_resolution",
                source_title="Hub Specs",
                source_url="https://example.com/hub",
                excerpt="Supports 4K at 60Hz.",
                checked_on=date(2026, 11, 2),
                review_status="verified",
            )
        )
        sess.add_all([laptop, hub, charger, draft_acc])
        sess.commit()

    try:
        with sessions() as sess:
            yield sess
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_compatible_accessories_returns_batch_evaluation(session) -> None:
    resp = laptop_compatible_accessories(
        device_id="test-laptop",
        displays=1,
        resolution="1920x1080",
        refresh_rate_hz=60,
        laptop_charging=True,
        category=None,
        verdict=None,
        session=session,
    )
    assert resp.laptop_id == "test-laptop"
    assert resp.laptop_name == "Test Laptop 14"
    assert resp.total_evaluated == 2  # Only verified accessories, draft is excluded
    assert "draft-hub" not in [r.accessory.id for r in resp.results]
    assert resp.counts["compatible_with_limits"] >= 1
    assert resp.counts["incompatible"] >= 1  # charger provides 0 video outputs

    hub_item = next(r for r in resp.results if r.accessory.id == "test-hub")
    assert hub_item.verdict == "compatible_with_limits"
    assert hub_item.rule_engine_version == RULE_ENGINE_VERSION
    assert hub_item.limits


def test_compatible_accessories_filters_by_category(session) -> None:
    resp = laptop_compatible_accessories(
        device_id="test-laptop",
        category="usb_c_charger",
        session=session,
    )
    assert resp.total_evaluated == 1
    assert len(resp.results) == 1
    assert resp.results[0].accessory.id == "test-charger"


def test_compatible_accessories_filters_by_verdict(session) -> None:
    resp = laptop_compatible_accessories(
        device_id="test-laptop",
        verdict="compatible_with_limits",
        session=session,
    )
    assert all(r.verdict == "compatible_with_limits" for r in resp.results)
    assert not any(r.accessory.id == "test-charger" for r in resp.results)


def test_compatible_accessories_not_found(session) -> None:
    with pytest.raises(HTTPException) as exc:
        laptop_compatible_accessories(
            device_id="nonexistent-laptop",
            session=session,
        )
    assert exc.value.status_code == 404
    assert exc.value.detail["code"] == "laptop_not_found"


def test_compatible_accessories_via_testclient(session) -> None:
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        client = TestClient(app)
        res = client.get("/devices/laptops/test-laptop/compatible-accessories?category=usb_c_hub")
        assert res.status_code == 200
        data = res.json()
        assert data["laptop_id"] == "test-laptop"
        assert len(data["results"]) == 1
        assert data["results"][0]["accessory"]["id"] == "test-hub"
    finally:
        app.dependency_overrides.pop(get_session, None)
