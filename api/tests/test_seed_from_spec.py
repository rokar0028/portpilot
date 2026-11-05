import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import AccessoryModel, SourceEvidence
from scripts.seed_from_spec import (
    determine_entity_kind,
    ingest_direct,
    load_raw_specs,
    main,
    normalize_evidence_list,
    validate_and_parse_spec,
)


def test_determine_entity_kind() -> None:
    assert determine_entity_kind({"kind": "laptop"}) == "laptop"
    assert determine_entity_kind({"entity_type": "accessory"}) == "accessory"
    assert determine_entity_kind({"category": "usb_c_hub"}) == "accessory"
    assert determine_entity_kind({"operating_system": "Windows 11"}) == "laptop"

    with pytest.raises(ValueError, match="Cannot determine device entity kind"):
        determine_entity_kind({"id": "ambiguous-device"})


def test_normalize_evidence_list() -> None:
    # Seed-style
    seed_record = {
        "id": "my-hub",
        "review_status": "verified",
        "source_title": "Hub Manual",
        "source_url": "https://example.com/hub",
        "excerpt": "Hub specs.",
        "evidence": ["hdmi_port_count", "model_code"],
        "evidence_excerpts": {"model_code": "Model: HUB1"},
    }
    ev = normalize_evidence_list(seed_record)
    assert len(ev) == 2
    assert ev[0]["capability_key"] == "hdmi_port_count"
    assert ev[0]["excerpt"] == "Hub specs."
    assert ev[1]["capability_key"] == "model_code"
    assert ev[1]["excerpt"] == "Model: HUB1"

    # Schema-style
    schema_record = {
        "id": "my-hub-2",
        "evidence": [
            {
                "capability_key": "model_code",
                "title": "T",
                "url": "https://example.com",
                "excerpt": "E",
            }
        ],
    }
    ev2 = normalize_evidence_list(schema_record)
    assert len(ev2) == 1
    assert ev2[0]["capability_key"] == "model_code"
    assert "checked_on" in ev2[0]


def test_validate_and_parse_spec_valid() -> None:
    example_path = Path(__file__).resolve().parent.parent / "specs" / "examples" / "plugable-ud-6950z.json"
    with open(example_path, encoding="utf-8") as f:
        data = json.load(f)

    kind, parsed = validate_and_parse_spec(str(example_path), data)
    assert kind == "accessory"
    assert parsed.id == "plugable-ud-6950z-dock"
    assert parsed.displaylink_supported is True
    assert parsed.model_code == "UD-6950Z"


def test_validate_and_parse_spec_missing_required_publication_field() -> None:
    bad_record = {
        "kind": "laptop",
        "id": "bad-laptop",
        "brand": "Brand",
        "name": "Bad Laptop",
        "review_status": "verified",
        # missing model_code and usb_c_port_count
    }
    with pytest.raises(ValueError, match="missing required publication field"):
        validate_and_parse_spec("test.json", bad_record)


def test_validate_and_parse_spec_unknown_capability() -> None:
    bad_record = {
        "kind": "accessory",
        "id": "unknown-cap-accessory",
        "brand": "Brand",
        "name": "Hub",
        "category": "usb_c_hub",
        "unregistered_spec_field": 123,
    }
    with pytest.raises(ValueError, match="unknown accessory capabilities"):
        validate_and_parse_spec("test.json", bad_record)


def test_load_raw_specs() -> None:
    example_path = Path(__file__).resolve().parent.parent / "specs" / "examples"
    records = load_raw_specs([str(example_path)])
    assert len(records) >= 2


def test_cli_dry_run() -> None:
    example_file = Path(__file__).resolve().parent.parent / "specs" / "examples" / "plugable-ud-6950z.json"
    code = main([str(example_file), "--dry-run", "-v"])
    assert code == 0


def test_ingest_direct_upserts_models_and_evidence(monkeypatch) -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    import scripts.seed_from_spec as seed_module

    monkeypatch.setattr(seed_module, "SessionLocal", session_factory)

    example_file = Path(__file__).resolve().parent.parent / "specs" / "examples" / "plugable-ud-6950z.json"
    with open(example_file, encoding="utf-8") as f:
        data = json.load(f)

    kind, parsed = validate_and_parse_spec(str(example_file), data)
    ingest_direct([(kind, parsed)], verbose=False)

    with session_factory() as sess:
        acc = sess.scalar(select(AccessoryModel).where(AccessoryModel.id == "plugable-ud-6950z-dock"))
        assert acc is not None
        assert acc.name == "Plugable Dual 4K Display Docking Station UD-6950Z"
        assert acc.displaylink_supported is True
        evidences = sess.scalars(select(SourceEvidence).where(SourceEvidence.accessory_id == acc.id)).all()
        assert len(evidences) >= 10
