from datetime import date

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.admin_auth import require_admin
from app.catalog_admin import (
    create_accessory,
    create_evidence_conflict,
    create_laptop,
    list_corrections,
    recheck_evidence,
    resolve_evidence_conflict,
    stale_evidence,
    update_accessory,
    update_laptop,
)
from app.catalog_admin import router as admin_router
from app.database import Base
from app.main import check_compatibility, devices
from app.models import AccessoryModel, LaptopModel, SourceEvidence
from app.schemas import (
    AccessoryWrite,
    CheckRequest,
    EvidenceConflictResolve,
    EvidenceConflictWrite,
    EvidenceRecheckWrite,
    LaptopWrite,
)


@pytest.fixture
def session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as database:
        yield database
    Base.metadata.drop_all(engine)
    engine.dispose()


def evidence(capability_key: str, status: str = "verified") -> dict:
    return {
        "capability_key": capability_key,
        "title": "Manufacturer specifications",
        "url": "https://example.com/specifications",
        "excerpt": f"Manufacturer specifications document {capability_key}.",
        "checked_on": date(2026, 11, 2),
        "status": status,
    }


def verified_laptop(**overrides) -> LaptopWrite:
    values = {
        "id": "example-laptop",
        "brand": "Example",
        "name": "Example laptop",
        "model_code": "EX-100",
        "usb_c_port_count": 1,
        "review_status": "verified",
        "change_reason": "Initial evidence-backed publication.",
        "evidence": [evidence("model_code"), evidence("usb_c_port_count")],
    }
    values.update(overrides)
    return LaptopWrite(**values)


def test_admin_routes_all_require_bearer_authentication() -> None:
    admin_routes = admin_router.routes
    assert len(admin_routes) == 12
    assert all(any(item.dependency is require_admin for item in route.dependencies) for route in admin_routes)


def test_admin_auth_fails_closed_when_token_is_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("ADMIN_API_TOKEN", raising=False)
    with pytest.raises(HTTPException) as error:
        require_admin(None)
    assert error.value.status_code == 503


@pytest.mark.parametrize("provided", [None, "wrong-token", "tøkən"])
def test_admin_auth_rejects_missing_or_incorrect_token(monkeypatch, provided: str | None) -> None:
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-secret-token")
    credentials = (
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=provided) if provided is not None else None
    )
    with pytest.raises(HTTPException) as error:
        require_admin(credentials)
    assert error.value.status_code == 401


def test_admin_auth_accepts_configured_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-secret-token")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-secret-token")
    assert require_admin(credentials) is None


def test_incomplete_draft_is_editable_and_hidden_from_public_catalogue(session: Session) -> None:
    payload = LaptopWrite(id="draft-laptop", brand="Example", name="Unreviewed laptop")
    created = create_laptop(payload, session)

    assert created.review_status == "draft"
    assert created.evidence == []
    assert [item.id for item in devices(session).laptops] == []


def test_publish_requires_minimum_specifications_and_verified_capability_evidence(
    session: Session,
) -> None:
    payload = verified_laptop(evidence=[evidence("model_code")])
    with pytest.raises(HTTPException) as error:
        create_laptop(payload, session)
    assert error.value.status_code == 422
    assert error.value.detail["code"] == "publish_validation_failed"
    assert "usb_c_port_count" in error.value.detail["fields"]


def test_laptop_can_be_updated_from_draft_to_verified_and_public(session: Session) -> None:
    draft = LaptopWrite(id="example-laptop", brand="Example", name="Example laptop")
    create_laptop(draft, session)

    published = update_laptop("example-laptop", verified_laptop(), session)
    public_catalogue = devices(session)

    assert published.review_status == "verified"
    assert {item.capability_key for item in published.evidence} == {"model_code", "usb_c_port_count"}
    assert [item.id for item in public_catalogue.laptops] == ["example-laptop"]
    changes = list_corrections("laptop", "example-laptop", session)
    assert changes


def test_create_reports_likely_duplicate_without_blocking_save(session: Session) -> None:
    create_laptop(
        LaptopWrite(
            id="existing-laptop",
            brand="Example",
            name="Example Pro",
            model_code="EX-100",
            review_status="draft",
        ),
        session,
    )
    created = create_laptop(
        LaptopWrite(
            id="candidate-laptop",
            brand="EXAMPLE",
            name="Example-Pro",
            model_code="ex 100",
            review_status="draft",
        ),
        session,
    )
    assert created.identity_warnings[0].candidate_id == "existing-laptop"
    assert "same normalized manufacturer model code" in created.identity_warnings[0].reasons[0]


def test_update_duplicate_warning_excludes_current_record(session: Session) -> None:
    create_laptop(
        LaptopWrite(id="first-laptop", brand="Example", name="Example 1", model_code="EX-100"), session
    )
    create_laptop(
        LaptopWrite(id="second-laptop", brand="Example", name="Example 2", model_code="EX-200"), session
    )
    updated = update_laptop(
        "second-laptop",
        LaptopWrite(
            id="second-laptop",
            brand="Example",
            name="Example 2",
            model_code="EX-100",
            change_reason="Corrected model code after source review.",
        ),
        session,
    )
    assert [warning.candidate_id for warning in updated.identity_warnings] == ["first-laptop"]


def test_charger_publish_requires_category_specific_output_and_evidence(session: Session) -> None:
    payload = AccessoryWrite(
        id="example-charger",
        brand="Example",
        name="Example charger",
        model_code="EX-65W",
        category="usb_c_charger",
        host_connection="USB-C",
        usb_c_output_max_w=65,
        review_status="verified",
        evidence=[
            evidence("category"),
            evidence("model_code"),
            evidence("host_connection"),
            evidence("usb_c_output_max_w"),
        ],
        change_reason="Reviewed source evidence for publication.",
    )
    created = create_accessory(payload, session)
    assert created.review_status == "verified"
    assert created.usb_c_output_max_w == 65


def test_accessory_can_be_created_as_draft_then_published(session: Session) -> None:
    create_accessory(
        AccessoryWrite(
            id="example-dock",
            brand="Example",
            name="Example dock",
            category="usb_c_dock",
        ),
        session,
    )
    payload = AccessoryWrite(
        id="example-dock",
        brand="Example",
        name="Example dock",
        model_code="EX-D1",
        category="usb_c_dock",
        host_connection="USB-C",
        requires_usb_c_dp_alt_mode=True,
        hdmi_port_count=1,
        hdmi_max_resolution="4K",
        hdmi_max_refresh_hz=60,
        review_status="verified",
        evidence=[
            evidence("category"),
            evidence("model_code"),
            evidence("host_connection"),
            evidence("requires_usb_c_dp_alt_mode"),
            evidence("hdmi_port_count"),
            evidence("hdmi_max_resolution"),
            evidence("hdmi_max_refresh_hz"),
        ],
        change_reason="Verified accessory fields against the manufacturer page.",
    )

    updated = update_accessory("example-dock", payload, session)

    assert updated.review_status == "verified"
    assert len(updated.evidence) == 7


def test_conflict_lifecycle_keeps_device_hidden_until_explicit_republication(session: Session) -> None:
    laptop = create_laptop(verified_laptop(), session)
    evidence_id = next(item.id for item in laptop.evidence if item.capability_key == "usb_c_port_count")
    conflict = create_evidence_conflict(
        EvidenceConflictWrite(
            entity_type="laptop",
            device_id=laptop.id,
            capability_key="usb_c_port_count",
            claim_a_value="1",
            claim_a_url="https://example.com/a",
            claim_a_quality="manufacturer_primary",
            claim_b_value="2",
            claim_b_url="https://example.com/b",
            claim_b_quality="manufacturer_secondary",
        ),
        session,
    )
    assert conflict.status == "open"
    assert devices(session).laptops == []

    resolve_evidence_conflict(
        conflict.id,
        EvidenceConflictResolve(
            selected_value="1", rationale="Primary source identifies one port.", reviewer="maintainer"
        ),
        session,
    )
    recheck_evidence(
        evidence_id,
        EvidenceRecheckWrite(
            outcome="verified",
            checked_on=date(2026, 11, 3),
            note="Rechecked the manufacturer source and confirmed the existing value.",
            reviewer="maintainer",
        ),
        session,
    )
    assert devices(session).laptops == []


def test_stale_evidence_can_be_found_and_recheck_recorded(session: Session) -> None:
    laptop = create_laptop(verified_laptop(), session)
    evidence_id = next(item.id for item in laptop.evidence if item.capability_key == "model_code")
    old_evidence = session.get(SourceEvidence, evidence_id)
    old_evidence.checked_on = date(2024, 1, 1)
    session.commit()
    assert any(item["evidence_id"] == old_evidence.id for item in stale_evidence(365, session))
    recheck_evidence(
        old_evidence.id,
        EvidenceRecheckWrite(
            outcome="verified",
            checked_on=date(2026, 11, 3),
            note="Manufacturer page still confirms the model code.",
            reviewer="maintainer",
        ),
        session,
    )
    assert old_evidence.checked_on == date(2026, 11, 3)


def test_unreviewed_accessories_are_not_public(session: Session) -> None:
    session.add(
        AccessoryModel(
            id="draft-hub",
            brand="Example",
            name="Unreviewed hub",
            category="usb_c_hub",
            review_status="needs_review",
        )
    )
    session.commit()

    assert devices(session).accessories == []


def test_unreviewed_laptop_cannot_be_used_for_a_compatibility_check(session: Session) -> None:
    session.add_all(
        [
            LaptopModel(
                id="draft-laptop",
                brand="Example",
                name="Unreviewed laptop",
                review_status="draft",
            ),
            AccessoryModel(
                id="verified-hub",
                brand="Example",
                name="Verified hub",
                category="usb_c_hub",
                review_status="verified",
            ),
        ]
    )
    session.commit()

    with pytest.raises(HTTPException) as error:
        check_compatibility(
            CheckRequest(laptop_id="draft-laptop", accessory_id="verified-hub"),
            session,
        )

    assert error.value.status_code == 404
    assert error.value.detail["code"] == "laptop_not_found"


def test_review_status_change_creates_correction_record(session: Session) -> None:
    laptop = create_laptop(verified_laptop(), session)
    updated = update_laptop(
        laptop.id,
        LaptopWrite(
            id=laptop.id,
            brand=laptop.brand,
            name=laptop.name,
            model_code=laptop.model_code,
            usb_c_port_count=laptop.usb_c_port_count,
            review_status="needs_review",
            change_reason="Holding device for review pending new manufacturer evidence.",
            evidence=[
                evidence("model_code", "needs_review"),
                evidence("usb_c_port_count", "needs_review"),
            ],
        ),
        session,
    )
    assert updated.review_status == "needs_review"
    corrections = list_corrections("laptop", laptop.id, session)
    keys = {c.capability_key for c in corrections}
    assert "review_status" in keys


def test_conflict_marks_all_matching_evidence_as_needs_review(session: Session) -> None:
    laptop = create_laptop(
        verified_laptop(
            evidence=[
                evidence("model_code"),
                evidence("usb_c_port_count"),
                {
                    "id": "second-port-evidence",
                    "capability_key": "usb_c_port_count",
                    "title": "Secondary spec sheet",
                    "url": "https://example.com/spec-v2",
                    "excerpt": "Secondary spec sheet documents 1 USB-C port.",
                    "checked_on": date(2026, 11, 2),
                    "status": "verified",
                },
            ]
        ),
        session,
    )
    assert len(laptop.evidence) == 3
    create_evidence_conflict(
        EvidenceConflictWrite(
            entity_type="laptop",
            device_id=laptop.id,
            capability_key="usb_c_port_count",
            claim_a_value="1",
            claim_a_url="https://example.com/a",
            claim_a_quality="manufacturer_primary",
            claim_b_value="2",
            claim_b_url="https://example.com/b",
            claim_b_quality="manufacturer_secondary",
        ),
        session,
    )
    reloaded = session.get(LaptopModel, laptop.id)
    port_evidences = [ev for ev in reloaded.evidence if ev.capability_key == "usb_c_port_count"]
    assert len(port_evidences) == 2
    assert all(ev.review_status == "needs_review" for ev in port_evidences)


def test_identity_warnings_reports_both_region_and_revision_mismatch(session: Session) -> None:
    create_laptop(
        LaptopWrite(
            id="base-laptop",
            brand="Example",
            name="Example Pro",
            model_code="EX-100",
            region_variant="US",
            hardware_revision="RevA",
            review_status="draft",
        ),
        session,
    )
    created = create_laptop(
        LaptopWrite(
            id="variant-laptop",
            brand="Example",
            name="Example Pro Variant",
            model_code="EX-100",
            region_variant="EU",
            hardware_revision="RevB",
            review_status="draft",
        ),
        session,
    )
    assert created.identity_warnings
    warning_reason = created.identity_warnings[0].reasons[0]
    assert "regional variant and hardware revision differ or are unknown" in warning_reason
