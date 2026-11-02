"""Create deterministic synthetic devices for the isolated browser test database."""

import os
from datetime import date
from urllib.parse import urlparse

from app.database import SessionLocal
from app.models import AccessoryModel, LaptopModel, SourceEvidence

if os.getenv("PORTPILOT_E2E") != "1":
    raise RuntimeError("Refusing to create E2E fixtures without PORTPILOT_E2E=1.")

database_url = os.getenv("DATABASE_URL", "")
database = urlparse(database_url)
if (
    not database_url.startswith("postgresql+")
    or database.hostname not in {"localhost", "127.0.0.1", "::1"}
    or database.path != "/portpilot_e2e"
):
    raise RuntimeError("E2E fixtures require the local portpilot_e2e PostgreSQL database.")

LAPTOP_IDS = ("e2e-good-laptop", "e2e-bad-laptop", "e2e-unknown-laptop", "e2e-hidden-laptop")
ACCESSORY_IDS = ("e2e-good-hub", "e2e-hidden-hub")
CHECKED_ON = date(2026, 11, 2)


def evidence(record_id: str, capability: str, status: str = "verified") -> SourceEvidence:
    return SourceEvidence(
        id=f"{record_id}:{capability}",
        capability_key=capability,
        source_title="Synthetic E2E manufacturer specification",
        source_url="https://example.invalid/portpilot-e2e",
        excerpt=f"Synthetic E2E fixture documents {capability}.",
        checked_on=CHECKED_ON,
        review_status=status,
    )


def laptop(record_id: str, name: str, *, video: bool | None, status: str = "verified") -> LaptopModel:
    record = LaptopModel(
        id=record_id,
        brand="PortPilot Test Fixture",
        name=name,
        model_code=record_id.upper(),
        usb_c_port_count=1,
        usb_c_video_supported=video,
        usb_c_dp_version="1.4" if video else None,
        usb_c_pd_input_min_w=45,
        usb_c_pd_input_max_w=65,
        maximum_external_displays=1,
        usb_c_max_resolution="3840x2160" if record_id != "e2e-unknown-laptop" else None,
        usb_c_max_refresh_hz=60 if record_id != "e2e-unknown-laptop" else None,
        review_status=status,
    )
    record.evidence = [
        evidence(record_id, "model_code"),
        evidence(record_id, "usb_c_video_supported", "needs_review"),
    ]
    if status == "verified":
        record.evidence.append(evidence(record_id, "usb_c_port_count"))
    return record


def accessory(record_id: str, name: str, *, status: str = "verified") -> AccessoryModel:
    record = AccessoryModel(
        id=record_id,
        brand="PortPilot Test Fixture",
        name=name,
        model_code=record_id.upper(),
        category="usb_c_hub",
        host_connection="USB-C",
        requires_usb_c_dp_alt_mode=True,
        hdmi_port_count=1,
        hdmi_max_resolution="3840x2160",
        hdmi_max_refresh_hz=60,
        pd_pass_through_max_w=65,
        review_status=status,
    )
    record.evidence = [
        evidence(record_id, "model_code"),
        evidence(record_id, "host_connection"),
        evidence(record_id, "requires_usb_c_dp_alt_mode"),
        evidence(record_id, "hdmi_port_count"),
    ]
    return record


def main() -> None:
    with SessionLocal.begin() as session:
        session.query(SourceEvidence).filter(
            (SourceEvidence.laptop_id.in_(LAPTOP_IDS)) | (SourceEvidence.accessory_id.in_(ACCESSORY_IDS))
        ).delete(synchronize_session=False)
        session.query(LaptopModel).filter(LaptopModel.id.in_(LAPTOP_IDS)).delete(synchronize_session=False)
        session.query(AccessoryModel).filter(AccessoryModel.id.in_(ACCESSORY_IDS)).delete(
            synchronize_session=False
        )
        session.add_all(
            [
                laptop("e2e-good-laptop", "E2E Supported Laptop", video=True),
                laptop("e2e-bad-laptop", "E2E No Video Laptop", video=False),
                laptop("e2e-unknown-laptop", "E2E Unknown Mode Laptop", video=True),
                laptop("e2e-hidden-laptop", "E2E Unreviewed Laptop", video=True, status="needs_review"),
                accessory("e2e-good-hub", "E2E Supported Hub"),
                accessory("e2e-hidden-hub", "E2E Unreviewed Hub", status="needs_review"),
            ]
        )


if __name__ == "__main__":
    main()
