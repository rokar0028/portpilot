from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .admin_auth import require_admin
from .database import get_session
from .models import AccessoryModel, LaptopModel, SourceEvidence
from .schemas import (
    AccessoryRead,
    AccessoryWrite,
    LaptopRead,
    LaptopWrite,
    SourceEvidenceRead,
    SourceEvidenceWrite,
)

router = APIRouter(prefix="/admin", tags=["catalogue administration"], dependencies=[Depends(require_admin)])

LAPTOP_PUBLISH_FIELDS = ("model_code", "usb_c_port_count")
ACCESSORY_PUBLISH_FIELDS = {
    "usb_c_hub": ("model_code", "host_connection", "requires_usb_c_dp_alt_mode", "hdmi_port_count"),
    "usb_c_dock": ("model_code", "host_connection", "requires_usb_c_dp_alt_mode", "hdmi_port_count"),
    "usb_c_charger": ("model_code", "host_connection", "usb_c_output_max_w"),
    "portable_monitor": ("model_code", "host_connection", "hdmi_max_resolution", "hdmi_max_refresh_hz"),
    "external_display": ("model_code", "host_connection", "hdmi_max_resolution", "hdmi_max_refresh_hz"),
}
NON_CAPABILITY_FIELDS = {"id", "brand", "name", "review_status", "evidence"}


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


def _laptop_read(record: LaptopModel) -> LaptopRead:
    values = {column.name: getattr(record, column.name) for column in LaptopModel.__table__.columns}
    return LaptopRead(**values, evidence=[_evidence_read(item) for item in record.evidence])


def _accessory_read(record: AccessoryModel) -> AccessoryRead:
    values = {column.name: getattr(record, column.name) for column in AccessoryModel.__table__.columns}
    return AccessoryRead(**values, evidence=[_evidence_read(item) for item in record.evidence])


def _validate_write(kind: str, payload: LaptopWrite | AccessoryWrite) -> None:
    values = payload.model_dump()
    evidence = values["evidence"]
    allowed_capabilities = set(values) - {"id", "review_status", "evidence"}
    invalid_keys = sorted({item["capability_key"] for item in evidence} - allowed_capabilities)
    if invalid_keys:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_evidence_capability",
                "message": "Evidence must point to a field on this device.",
                "fields": invalid_keys,
            },
        )

    if values["review_status"] != "verified":
        return

    if kind == "laptop":
        required_fields = LAPTOP_PUBLISH_FIELDS
    else:
        required_fields = ACCESSORY_PUBLISH_FIELDS[values["category"]]

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
    values = payload.model_dump(exclude={"evidence"})
    record = LaptopModel(**values)
    record.evidence = _source_records(payload.id, payload.evidence, owner="laptop")
    _save(session, record)
    return _laptop_read(record)


@router.put("/laptops/{device_id}", response_model=LaptopRead)
def update_laptop(
    device_id: str, payload: LaptopWrite, session: Session = Depends(get_session)
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
    for field, value in payload.model_dump(exclude={"id", "evidence"}).items():
        setattr(record, field, value)
    record.evidence = _source_records(device_id, payload.evidence, owner="laptop")
    _save(session, record)
    return _laptop_read(record)


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
    values = payload.model_dump(exclude={"evidence"})
    record = AccessoryModel(**values)
    record.evidence = _source_records(payload.id, payload.evidence, owner="accessory")
    _save(session, record)
    return _accessory_read(record)


@router.put("/accessories/{device_id}", response_model=AccessoryRead)
def update_accessory(
    device_id: str,
    payload: AccessoryWrite,
    session: Session = Depends(get_session),
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
    for field, value in payload.model_dump(exclude={"id", "evidence"}).items():
        setattr(record, field, value)
    record.evidence = _source_records(device_id, payload.evidence, owner="accessory")
    _save(session, record)
    return _accessory_read(record)
