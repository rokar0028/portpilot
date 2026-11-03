import json
import re
import unicodedata
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .admin_auth import require_admin
from .capabilities import (
    publication_requirements,
    unknown_capability_keys,
    validate_registry,
)
from .database import get_session
from .models import AccessoryModel, CatalogueCorrection, EvidenceConflict, LaptopModel, SourceEvidence
from .schemas import (
    AccessoryRead,
    AccessoryWrite,
    CatalogueCorrectionRead,
    EvidenceConflictRead,
    EvidenceConflictResolve,
    EvidenceConflictWrite,
    EvidenceRecheckWrite,
    LaptopRead,
    LaptopWrite,
    SourceEvidenceRead,
    SourceEvidenceWrite,
)

router = APIRouter(prefix="/admin", tags=["catalogue administration"], dependencies=[Depends(require_admin)])
validate_registry(
    {"laptop": LaptopModel, "accessory": AccessoryModel},
    {"laptop": LaptopWrite, "accessory": AccessoryWrite},
)

NON_CAPABILITY_FIELDS = {"id", "brand", "name", "review_status", "evidence", "change_reason"}


def _normalize_identity(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
    return re.sub(r"[^a-z0-9]", "", normalized)


def _identity_warnings(
    session: Session, kind: str, payload: LaptopWrite | AccessoryWrite, exclude_id: str | None = None
) -> list[dict]:
    model = LaptopModel if kind == "laptop" else AccessoryModel
    query = select(model)
    if exclude_id:
        query = query.where(model.id != exclude_id)
    warnings = []
    for candidate in session.scalars(query):
        if kind == "accessory" and candidate.category != payload.category:
            continue
        reasons = []
        code = _normalize_identity(payload.model_code)
        candidate_code = _normalize_identity(candidate.model_code)
        if code and candidate_code and code == candidate_code:
            if _normalize_identity(payload.region_variant) != _normalize_identity(candidate.region_variant):
                reasons.append(
                    "same normalized manufacturer model code; regional variant differs or is unknown"
                )
            elif _normalize_identity(payload.hardware_revision) != _normalize_identity(
                candidate.hardware_revision
            ):
                reasons.append(
                    "same normalized manufacturer model code; hardware revision differs or is unknown"
                )
            else:
                reasons.append("same normalized manufacturer model code")
        if _normalize_identity(payload.brand) == _normalize_identity(candidate.brand) and _normalize_identity(
            payload.name
        ) == _normalize_identity(candidate.name):
            reasons.append("same normalized brand and model name")
        if reasons:
            warnings.append(
                {"candidate_id": candidate.id, "candidate_name": candidate.name, "reasons": reasons}
            )
    return warnings


def _evidence_read(record: SourceEvidence) -> SourceEvidenceRead:
    return SourceEvidenceRead(
        id=record.id,
        capability_key=record.capability_key,
        title=record.source_title,
        url=record.source_url,
        excerpt=record.excerpt,
        checked_on=record.checked_on,
        status=record.review_status,
    )


def _laptop_read(record: LaptopModel, identity_warnings: list[dict] | None = None) -> LaptopRead:
    values = {column.name: getattr(record, column.name) for column in LaptopModel.__table__.columns}
    return LaptopRead(
        **values,
        evidence=[_evidence_read(item) for item in record.evidence],
        identity_warnings=identity_warnings or [],
    )


def _accessory_read(record: AccessoryModel, identity_warnings: list[dict] | None = None) -> AccessoryRead:
    values = {column.name: getattr(record, column.name) for column in AccessoryModel.__table__.columns}
    return AccessoryRead(
        **values,
        evidence=[_evidence_read(item) for item in record.evidence],
        identity_warnings=identity_warnings or [],
    )


def _validate_write(kind: str, payload: LaptopWrite | AccessoryWrite) -> None:
    values = payload.model_dump()
    evidence = values["evidence"]
    invalid_keys = unknown_capability_keys(kind, {item["capability_key"] for item in evidence})
    if invalid_keys:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_evidence_capability",
                "message": "Evidence must point to a registered capability for this device type.",
                "fields": invalid_keys,
            },
        )

    if values["review_status"] != "verified":
        return

    required_fields = publication_requirements(kind, values.get("category"))

    missing_fields = [field for field in required_fields if values[field] is None]
    verified_capabilities = {item["capability_key"] for item in evidence if item["status"] == "verified"}
    missing_evidence = [field for field in required_fields if field not in verified_capabilities]
    missing_evidence.extend(
        field
        for field, value in values.items()
        if field not in NON_CAPABILITY_FIELDS
        and value is not None
        and field not in verified_capabilities
        and field not in missing_evidence
    )
    if not evidence or not any(item["status"] == "verified" for item in evidence):
        missing_evidence.append("evidence")

    if missing_fields or missing_evidence:
        fields = sorted(set(missing_fields + missing_evidence))
        raise HTTPException(
            status_code=422,
            detail={
                "code": "publish_validation_failed",
                "message": "Add the required specifications and verified evidence before publishing.",
                "fields": fields,
            },
        )


def _source_records(
    device_id: str,
    items: list[SourceEvidenceWrite],
    *,
    owner: str,
) -> list[SourceEvidence]:
    records: list[SourceEvidence] = []
    for item in items:
        record_id = item.id or f"{device_id}:{item.capability_key}:{uuid4().hex[:12]}"
        fields = {
            "id": record_id,
            "capability_key": item.capability_key,
            "source_title": item.title,
            "source_url": str(item.url),
            "excerpt": item.excerpt,
            "checked_on": item.checked_on,
            "review_status": item.status,
        }
        fields["laptop_id" if owner == "laptop" else "accessory_id"] = device_id
        records.append(SourceEvidence(**fields))
    return records


def _capture_corrections(
    session: Session,
    entity_type: str,
    device_id: str,
    record: LaptopModel | AccessoryModel,
    payload: LaptopWrite | AccessoryWrite,
    actor: str,
) -> None:
    changes: list[tuple[str, object, object, list[str]]] = []
    values = payload.model_dump(exclude={"id", "evidence", "change_reason", "review_status"})
    for key, new_value in values.items():
        old_value = getattr(record, key)
        if old_value != new_value:
            evidence_refs = [item.id for item in record.evidence if item.capability_key == key]
            evidence_refs.extend(
                item.id for item in payload.evidence if item.capability_key == key and item.id
            )
            changes.append((key, old_value, new_value, evidence_refs))

    old_evidence = {item.capability_key: item for item in record.evidence}
    new_evidence = {item.capability_key: item for item in payload.evidence}
    for key in sorted(old_evidence.keys() | new_evidence.keys()):
        old_item = old_evidence.get(key)
        new_item = new_evidence.get(key)
        old_value = (
            {
                "title": old_item.source_title,
                "url": old_item.source_url,
                "excerpt": old_item.excerpt,
                "checked_on": old_item.checked_on.isoformat(),
                "status": old_item.review_status,
            }
            if old_item
            else None
        )
        new_value = (
            {
                "title": new_item.title,
                "url": str(new_item.url),
                "excerpt": new_item.excerpt,
                "checked_on": new_item.checked_on.isoformat(),
                "status": new_item.status,
            }
            if new_item
            else None
        )
        if old_value != new_value:
            refs = [
                value
                for value in (old_item.id if old_item else None, new_item.id if new_item else None)
                if value
            ]
            changes.append((f"evidence:{key}", old_value, new_value, refs))

    if changes and not payload.change_reason:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "change_reason_required",
                "message": "Provide change_reason for catalogue corrections.",
            },
        )
    actor_name = actor if isinstance(actor, str) else "admin"
    for key, old_value, new_value, refs in changes:
        session.add(
            CatalogueCorrection(
                id=f"correction:{uuid4().hex}",
                entity_type=entity_type,
                device_id=device_id,
                capability_key=key,
                previous_value=json.dumps(old_value, default=str, sort_keys=True),
                new_value=json.dumps(new_value, default=str, sort_keys=True),
                reason=payload.change_reason or "",
                evidence_references=json.dumps(refs),
                actor=actor_name,
                created_at=datetime.now(UTC),
            )
        )


def _device_model(entity_type: str):
    return LaptopModel if entity_type == "laptop" else AccessoryModel


def _device_owner(entity_type: str, device_id: str, session: Session):
    model = _device_model(entity_type)
    device = session.get(model, device_id)
    if device is None:
        raise HTTPException(
            status_code=404, detail={"code": "device_not_found", "message": "Device not found."}
        )
    return device


def _conflict_read(record: EvidenceConflict) -> EvidenceConflictRead:
    entity_type = "laptop" if record.laptop_id else "accessory"
    return EvidenceConflictRead(
        id=record.id,
        entity_type=entity_type,
        device_id=record.laptop_id or record.accessory_id or "",
        capability_key=record.capability_key,
        claim_a_value=record.claim_a_value,
        claim_a_url=record.claim_a_url,
        claim_a_quality=record.claim_a_quality,
        claim_b_value=record.claim_b_value,
        claim_b_url=record.claim_b_url,
        claim_b_quality=record.claim_b_quality,
        status=record.status,
        selected_value=record.selected_value,
        rationale=record.rationale,
        reviewer=record.reviewer,
        created_at=record.created_at,
        resolved_at=record.resolved_at,
    )


@router.get("/evidence-conflicts", response_model=list[EvidenceConflictRead])
def list_evidence_conflicts(
    conflict_status: str | None = Query(default=None, alias="status"), session: Session = Depends(get_session)
) -> list[EvidenceConflictRead]:
    query = select(EvidenceConflict).order_by(EvidenceConflict.created_at.desc())
    if conflict_status is not None:
        if conflict_status not in {"open", "resolved"}:
            raise HTTPException(status_code=422, detail="status must be open or resolved")
        query = query.where(EvidenceConflict.status == conflict_status)
    return [_conflict_read(row) for row in session.scalars(query)]


@router.post("/evidence-conflicts", response_model=EvidenceConflictRead, status_code=201)
def create_evidence_conflict(
    payload: EvidenceConflictWrite, session: Session = Depends(get_session)
) -> EvidenceConflictRead:
    invalid = unknown_capability_keys(payload.entity_type, {payload.capability_key})
    if invalid:
        raise HTTPException(status_code=422, detail={"code": "invalid_capability", "fields": invalid})
    device = _device_owner(payload.entity_type, payload.device_id, session)
    record = EvidenceConflict(
        id=f"conflict:{uuid4().hex}",
        laptop_id=payload.device_id if payload.entity_type == "laptop" else None,
        accessory_id=payload.device_id if payload.entity_type == "accessory" else None,
        capability_key=payload.capability_key,
        claim_a_value=payload.claim_a_value,
        claim_a_url=str(payload.claim_a_url),
        claim_a_quality=payload.claim_a_quality,
        claim_b_value=payload.claim_b_value,
        claim_b_url=str(payload.claim_b_url),
        claim_b_quality=payload.claim_b_quality,
        status="open",
        created_at=datetime.now(UTC),
    )
    device.review_status = "needs_review"
    evidence = next((row for row in device.evidence if row.capability_key == payload.capability_key), None)
    if evidence:
        evidence.review_status = "needs_review"
    session.add(record)
    session.commit()
    return _conflict_read(record)


@router.post("/evidence-conflicts/{conflict_id}/resolve", response_model=EvidenceConflictRead)
def resolve_evidence_conflict(
    conflict_id: str, payload: EvidenceConflictResolve, session: Session = Depends(get_session)
) -> EvidenceConflictRead:
    record = session.get(EvidenceConflict, conflict_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "conflict_not_found"})
    if record.status != "open":
        raise HTTPException(status_code=409, detail={"code": "conflict_already_resolved"})
    if payload.selected_value not in {record.claim_a_value, record.claim_b_value}:
        raise HTTPException(status_code=422, detail="selected_value must match one of the recorded claims")
    record.status = "resolved"
    record.selected_value = payload.selected_value
    record.rationale = payload.rationale
    record.reviewer = payload.reviewer
    record.resolved_at = datetime.now(UTC)
    session.commit()
    return _conflict_read(record)


@router.get("/rechecks/stale")
def stale_evidence(
    stale_after_days: int = Query(default=365, ge=1, le=3650), session: Session = Depends(get_session)
) -> list[dict]:
    cutoff = date.today() - timedelta(days=stale_after_days)
    records = session.scalars(
        select(SourceEvidence).where(
            SourceEvidence.review_status == "verified", SourceEvidence.checked_on <= cutoff
        )
    )
    return [
        {
            "evidence_id": row.id,
            "entity_type": "laptop" if row.laptop_id else "accessory",
            "device_id": row.laptop_id or row.accessory_id,
            "capability_key": row.capability_key,
            "checked_on": row.checked_on,
            "stale_days": (date.today() - row.checked_on).days,
        }
        for row in records
    ]


@router.post("/evidence/{evidence_id}/recheck")
def recheck_evidence(
    evidence_id: str,
    payload: EvidenceRecheckWrite,
    session: Session = Depends(get_session),
) -> dict:
    record = session.get(SourceEvidence, evidence_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "evidence_not_found"})
    if payload.outcome == "verified":
        unresolved = session.scalar(
            select(EvidenceConflict.id).where(
                EvidenceConflict.capability_key == record.capability_key,
                EvidenceConflict.status == "open",
                (EvidenceConflict.laptop_id == record.laptop_id)
                if record.laptop_id
                else (EvidenceConflict.accessory_id == record.accessory_id),
            )
        )
        if unresolved:
            raise HTTPException(status_code=409, detail={"code": "open_conflict_blocks_verification"})
    previous_status = record.review_status
    previous_date = record.checked_on.isoformat()
    record.checked_on = payload.checked_on
    record.review_status = payload.outcome
    owner = (
        session.get(LaptopModel, record.laptop_id)
        if record.laptop_id
        else session.get(AccessoryModel, record.accessory_id)
    )
    if payload.outcome == "needs_review" and owner:
        owner.review_status = "needs_review"
    session.add(
        CatalogueCorrection(
            id=f"correction:{uuid4().hex}",
            entity_type="laptop" if record.laptop_id else "accessory",
            device_id=record.laptop_id or record.accessory_id or "",
            capability_key=f"recheck:{record.capability_key}",
            previous_value=f"status={previous_status}; checked_on={previous_date}",
            new_value=f"status={payload.outcome}; checked_on={payload.checked_on.isoformat()}",
            reason=payload.note,
            evidence_references=json.dumps([record.id]),
            actor=payload.reviewer,
            created_at=datetime.now(UTC),
        )
    )
    session.commit()
    return {"evidence_id": record.id, "status": record.review_status, "checked_on": record.checked_on}


@router.get("/corrections/{entity_type}/{device_id}", response_model=list[CatalogueCorrectionRead])
def list_corrections(
    entity_type: str, device_id: str, session: Session = Depends(get_session)
) -> list[CatalogueCorrectionRead]:
    if entity_type not in {"laptop", "accessory"}:
        raise HTTPException(status_code=422, detail="entity_type must be laptop or accessory")
    rows = session.scalars(
        select(CatalogueCorrection)
        .where(CatalogueCorrection.entity_type == entity_type, CatalogueCorrection.device_id == device_id)
        .order_by(CatalogueCorrection.created_at.desc())
    )
    return [
        CatalogueCorrectionRead(
            id=row.id,
            entity_type=row.entity_type,
            device_id=row.device_id,
            capability_key=row.capability_key,
            previous_value=row.previous_value,
            new_value=row.new_value,
            reason=row.reason,
            evidence_references=json.loads(row.evidence_references),
            actor=row.actor,
            created_at=row.created_at,
        )
        for row in rows
    ]


def _save(session: Session, record: LaptopModel | AccessoryModel) -> None:
    try:
        session.add(record)
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "catalogue_conflict",
                "message": "A catalogue identifier or evidence ID already exists.",
            },
        ) from error
    session.refresh(record)


@router.get("/laptops", response_model=list[LaptopRead])
def admin_laptops(session: Session = Depends(get_session)) -> list[LaptopRead]:
    records = session.scalars(select(LaptopModel).options(selectinload(LaptopModel.evidence))).all()
    return [_laptop_read(item) for item in records]


@router.post("/laptops", response_model=LaptopRead, status_code=status.HTTP_201_CREATED)
def create_laptop(payload: LaptopWrite, session: Session = Depends(get_session)) -> LaptopRead:
    _validate_write("laptop", payload)
    if session.get(LaptopModel, payload.id) is not None:
        raise HTTPException(
            status_code=409, detail={"code": "device_exists", "message": "Laptop ID already exists."}
        )
    identity_warnings = _identity_warnings(session, "laptop", payload)
    values = payload.model_dump(exclude={"evidence", "change_reason"})
    record = LaptopModel(**values)
    record.evidence = _source_records(payload.id, payload.evidence, owner="laptop")
    _save(session, record)
    return _laptop_read(record, identity_warnings)


@router.put("/laptops/{device_id}", response_model=LaptopRead)
def update_laptop(
    device_id: str,
    payload: LaptopWrite,
    session: Session = Depends(get_session),
    actor: str = Header(default="admin", alias="X-Admin-Actor"),
) -> LaptopRead:
    if payload.id != device_id:
        raise HTTPException(
            status_code=422,
            detail={"code": "id_mismatch", "message": "Body ID must match the laptop ID in the URL."},
        )
    _validate_write("laptop", payload)
    record = session.scalar(
        select(LaptopModel).where(LaptopModel.id == device_id).options(selectinload(LaptopModel.evidence))
    )
    if record is None:
        raise HTTPException(
            status_code=404, detail={"code": "laptop_not_found", "message": "Laptop not found."}
        )
    identity_warnings = _identity_warnings(session, "laptop", payload, exclude_id=device_id)
    _capture_corrections(session, "laptop", device_id, record, payload, actor)
    for field, value in payload.model_dump(exclude={"id", "evidence", "change_reason"}).items():
        setattr(record, field, value)
    record.evidence = _source_records(device_id, payload.evidence, owner="laptop")
    _save(session, record)
    return _laptop_read(record, identity_warnings)


@router.get("/accessories", response_model=list[AccessoryRead])
def admin_accessories(session: Session = Depends(get_session)) -> list[AccessoryRead]:
    records = session.scalars(select(AccessoryModel).options(selectinload(AccessoryModel.evidence))).all()
    return [_accessory_read(item) for item in records]


@router.post("/accessories", response_model=AccessoryRead, status_code=status.HTTP_201_CREATED)
def create_accessory(payload: AccessoryWrite, session: Session = Depends(get_session)) -> AccessoryRead:
    _validate_write("accessory", payload)
    if session.get(AccessoryModel, payload.id) is not None:
        raise HTTPException(
            status_code=409, detail={"code": "device_exists", "message": "Accessory ID already exists."}
        )
    identity_warnings = _identity_warnings(session, "accessory", payload)
    values = payload.model_dump(exclude={"evidence", "change_reason"})
    record = AccessoryModel(**values)
    record.evidence = _source_records(payload.id, payload.evidence, owner="accessory")
    _save(session, record)
    return _accessory_read(record, identity_warnings)


@router.put("/accessories/{device_id}", response_model=AccessoryRead)
def update_accessory(
    device_id: str,
    payload: AccessoryWrite,
    session: Session = Depends(get_session),
    actor: str = Header(default="admin", alias="X-Admin-Actor"),
) -> AccessoryRead:
    if payload.id != device_id:
        raise HTTPException(
            status_code=422,
            detail={"code": "id_mismatch", "message": "Body ID must match the accessory ID in the URL."},
        )
    _validate_write("accessory", payload)
    record = session.scalar(
        select(AccessoryModel)
        .where(AccessoryModel.id == device_id)
        .options(selectinload(AccessoryModel.evidence))
    )
    if record is None:
        raise HTTPException(
            status_code=404, detail={"code": "accessory_not_found", "message": "Accessory not found."}
        )
    identity_warnings = _identity_warnings(session, "accessory", payload, exclude_id=device_id)
    _capture_corrections(session, "accessory", device_id, record, payload, actor)
    for field, value in payload.model_dump(exclude={"id", "evidence", "change_reason"}).items():
        setattr(record, field, value)
    record.evidence = _source_records(device_id, payload.evidence, owner="accessory")
    _save(session, record)
    return _accessory_read(record, identity_warnings)
