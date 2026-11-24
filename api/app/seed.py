import json
from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .capabilities import publication_requirements
from .database import SessionLocal
from .models import AccessoryModel, LaptopModel, SourceEvidence

CHECKED_ON = date(2026, 11, 2)

SEED_IDENTITY_FIELDS = {
    "id",
    "brand",
    "name",
    "region_variant",
    "hardware_revision",
    "review_status",
}

SPECS_DIR = Path(__file__).resolve().parent.parent / "specs"


def validate_seed_record(record: dict[str, Any]) -> None:
    """Fail closed if a verified seed record lacks evidence for a populated field."""
    if record.get("review_status") not in {"verified", "draft", "needs_review"}:
        raise ValueError(f"Seed record {record.get('id')} has an invalid review status.")
    required_metadata = ("source_title", "source_url", "excerpt")
    if any(not record.get(field) for field in required_metadata):
        raise ValueError(f"Seed record {record.get('id')} is missing source metadata.")

    if record.get("review_status") == "verified":
        if not record.get("model_code") or "model_code" not in record.get("evidence", []):
            raise ValueError(
                f"Verified seed record {record.get('id')} needs an evidenced manufacturer model code."
            )
        owner_kind = "accessory" if "category" in record else "laptop"
        required_fields = publication_requirements(owner_kind, record.get("category"))
        for req in required_fields:
            if record.get(req) is None or req not in record.get("evidence", []):
                raise ValueError(
                    f"Verified seed record {record.get('id')} lacks required "
                    f"publication field or evidence for: {req}."
                )

    evidence_keys = record.get("evidence", [])
    if len(evidence_keys) != len(set(evidence_keys)):
        raise ValueError(f"Seed record {record.get('id')} has duplicate evidence capabilities.")
    excerpts = record.get("evidence_excerpts", {})
    for key in evidence_keys:
        if key in excerpts and not excerpts[key].strip():
            raise ValueError(f"Seed record {record.get('id')} has an empty capability excerpt for {key}.")

    missing = sorted(
        key
        for key, value in record.items()
        if value is not None
        and key not in SEED_IDENTITY_FIELDS
        and key not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts", "kind"}
        and key not in evidence_keys
    )
    if missing:
        raise ValueError(
            f"Seed record {record.get('id')} has populated fields without evidence: {', '.join(missing)}."
        )


def load_specs_from_directory(directory: Path) -> list[dict[str, Any]]:
    """Load JSON specifications from a directory, sorted by device ID."""
    if not directory.exists():
        return []
    records: list[dict[str, Any]] = []
    for file_path in sorted(directory.glob("*.json")):
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
            data.pop("kind", None)
            data.pop("entity_type", None)
            records.append(data)
    return records


LAPTOPS = load_specs_from_directory(SPECS_DIR / "laptops")
ACCESSORIES = load_specs_from_directory(SPECS_DIR / "accessories")


def upsert_records(session: Session) -> None:
    for source in LAPTOPS:
        validate_seed_record(source)
        values = {
            key: value
            for key, value in source.items()
            if key not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts", "kind"}
        }
        record = session.merge(LaptopModel(**values))
        expected_evidence_ids = {f"{source['id']}:{key}" for key in source["evidence"]}
        session.query(SourceEvidence).filter(
            SourceEvidence.laptop_id == record.id,
            SourceEvidence.id.notin_(expected_evidence_ids),
        ).delete(synchronize_session=False)
        for capability_key in source["evidence"]:
            evidence = SourceEvidence(
                id=f"{source['id']}:{capability_key}",
                laptop_id=record.id,
                capability_key=capability_key,
                source_title=source["source_title"],
                source_url=source["source_url"],
                excerpt=source.get("evidence_excerpts", {}).get(capability_key, source["excerpt"]),
                checked_on=CHECKED_ON,
                review_status=source.get("review_status", "verified"),
            )
            session.merge(evidence)

    for source in ACCESSORIES:
        validate_seed_record(source)
        values = {
            key: value
            for key, value in source.items()
            if key not in {"source_title", "source_url", "excerpt", "evidence", "evidence_excerpts", "kind"}
        }
        record = session.merge(AccessoryModel(**values))
        expected_evidence_ids = {f"{source['id']}:{key}" for key in source["evidence"]}
        session.query(SourceEvidence).filter(
            SourceEvidence.accessory_id == record.id,
            SourceEvidence.id.notin_(expected_evidence_ids),
        ).delete(synchronize_session=False)
        for capability_key in source["evidence"]:
            evidence = SourceEvidence(
                id=f"{source['id']}:{capability_key}",
                accessory_id=record.id,
                capability_key=capability_key,
                source_title=source["source_title"],
                source_url=source["source_url"],
                excerpt=source.get("evidence_excerpts", {}).get(capability_key, source["excerpt"]),
                checked_on=CHECKED_ON,
                review_status=source.get("review_status", "verified"),
            )
            session.merge(evidence)


def seed() -> None:
    with SessionLocal() as session:
        upsert_records(session)
        session.commit()


if __name__ == "__main__":
    seed()
    print(f"Seeded {len(LAPTOPS)} laptops and {len(ACCESSORIES)} accessories from {SPECS_DIR}.")
