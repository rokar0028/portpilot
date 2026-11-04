from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import accessory_rule_record, check_compatibility, create_result_report, laptop_rule_record
from app.models import AccessoryModel, LaptopModel, ResultReport, SourceEvidence
from app.rules import RULE_ENGINE_VERSION
from app.schemas import CheckRequest, ResultReportWrite


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with sessions() as session:
        laptop = LaptopModel(
            id="api-laptop",
            brand="Example",
            name="Example laptop",
            usb_c_port_count=1,
            usb_c_video_supported=True,
            usb_c_dp_version="1.4",
            usb_c_pd_input_min_w=45,
            usb_c_pd_input_max_w=65,
            maximum_external_displays=2,
            usb_c_max_resolution="4K",
            usb_c_max_refresh_hz=60,
        )
        accessory = AccessoryModel(
            id="api-hub",
            brand="Example",
            name="Example hub",
            category="usb_c_hub",
            host_connection="USB-C",
            requires_usb_c_dp_alt_mode=True,
            hdmi_port_count=1,
            hdmi_max_resolution="4K",
            hdmi_max_refresh_hz=60,
            pd_pass_through_max_w=50,
        )
        laptop.evidence.append(
            SourceEvidence(
                id="laptop-video-source",
                capability_key="usb_c_video_supported",
                source_title="Example laptop specifications",
                source_url="https://example.com/laptop",
                excerpt="USB-C supports DisplayPort video output.",
                checked_on=date(2026, 11, 2),
                review_status="verified",
            )
        )
        accessory.evidence.append(
            SourceEvidence(
                id="hub-source",
                capability_key="pd_pass_through_max_w",
                source_title="Example hub specifications",
                source_url="https://example.com/hub",
                excerpt="Power pass-through up to 50 W.",
                checked_on=date(2026, 11, 2),
                review_status="verified",
            )
        )
        session.add_all([laptop, accessory])
        session.commit()

    try:
        with sessions() as session:
            yield session
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_check_endpoint_handler_returns_verdict_and_device_evidence(client) -> None:
    response = check_compatibility(
        CheckRequest(
            laptop_id="api-laptop",
            accessory_id="api-hub",
            setup={
                "external_displays": 1,
                "resolution": "1920x1080",
                "refresh_rate_hz": 60,
                "laptop_charging": True,
            },
        ),
        client,
    )

    assert response.verdict == "compatible_with_limits"
    assert response.rule_engine_version == RULE_ENGINE_VERSION
    assert {item["status"] for item in response.requirements} == {"passed"}
    assert len(response.evidence) == 2
    assert response.limits


def test_check_endpoint_preserves_structured_not_found_response(client) -> None:
    with pytest.raises(HTTPException) as error:
        check_compatibility(
            CheckRequest(laptop_id="missing", accessory_id="api-hub"),
            client,
        )
    assert error.value.status_code == 404
    assert error.value.detail["code"] == "laptop_not_found"


def test_result_report_persists_only_bounded_context(client) -> None:
    report = create_result_report(
        ResultReportWrite(
            laptop_id="api-laptop",
            accessory_id="api-hub",
            setup={"external_displays": 1, "resolution": "1920x1080", "refresh_rate_hz": 60},
            verdict="compatible_with_limits",
            rule_engine_version=RULE_ENGINE_VERSION,
            note="The display mode seems incorrect.",
        ),
        client,
    )

    stored = client.get(ResultReport, report.id)
    assert report.status == "received"
    assert stored.laptop_id == "api-laptop"
    assert stored.setup["resolution"] == "1920x1080"
    assert stored.note == "The display mode seems incorrect."


def test_charger_uses_its_usb_c_output_rating_for_charging() -> None:
    charger = AccessoryModel(
        id="charger",
        brand="Example",
        name="Example charger",
        category="usb_c_charger",
        host_connection="USB-C",
        usb_c_output_max_w=65,
    )

    assert accessory_rule_record(charger)["outputs"]["charging_output_watts"] == 65


def test_documented_display_configurations_reach_the_rules_adapter() -> None:
    configuration = {
        "displays": [
            {"resolution": "3840x2160", "refresh_rate_hz": 60, "connection": "HDMI"},
            {"resolution": "1920x1080", "refresh_rate_hz": 60, "connection": "DisplayPort"},
        ],
        "topology": "extended",
    }
    laptop = LaptopModel(
        id="adapter-laptop",
        brand="Example",
        name="Example laptop",
        display_configurations=[configuration],
    )
    accessory = AccessoryModel(
        id="adapter-accessory",
        brand="Example",
        name="Example dock",
        category="usb_c_dock",
        display_configurations=[configuration],
    )

    assert laptop_rule_record(laptop)["ports"]["display_configurations"] == [configuration]
    assert accessory_rule_record(accessory)["outputs"]["display_configurations"] == [configuration]


def test_unknown_setup_requirements_produce_insufficient_data(client) -> None:
    result = check_compatibility(
        CheckRequest(
            laptop_id="api-laptop",
            accessory_id="api-hub",
            setup={
                "external_displays": None,
                "resolution": None,
                "refresh_rate_hz": None,
                "laptop_charging": None,
            },
        ),
        client,
    )

    assert result.verdict == "insufficient_data"
    assert any(item["status"] == "unknown" for item in result.requirements)


def test_empty_or_whitespace_device_ids_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CheckRequest(laptop_id="", accessory_id="api-hub")

    with pytest.raises(ValidationError):
        CheckRequest(laptop_id="api-laptop", accessory_id="   ")
