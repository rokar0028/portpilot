import logging
import os
from time import perf_counter
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from .catalog_admin import router as catalog_admin_router
from .database import get_session
from .models import AccessoryModel, LaptopModel, SourceEvidence
from .observability import current_request_id, log_event, metrics, request_id_context
from .rules import evaluate
from .schemas import (
    AccessoryRead,
    CatalogRead,
    CheckRequest,
    CheckResponse,
    LaptopRead,
    SetupParseRequest,
    SetupParseResponse,
    SourceEvidenceRead,
)
from .setup_parser import ParserInvalidResponse, ParserUnavailable, parse_setup

load_dotenv()

app = FastAPI(
    title="PortPilot API",
    version="0.2.0",
    description="Evidence-backed laptop and accessory compatibility checks.",
)
frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").split(",")
    if origin.strip()
]
# Next.js uses the next available port when 3000 is occupied. Permit that
# alternate local development port when the configured origin is localhost.
if any(origin in {"http://localhost:3000", "http://127.0.0.1:3000"} for origin in frontend_origins):
    frontend_origins.extend(
        origin
        for origin in (
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        )
        if origin not in frontend_origins
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)
app.include_router(catalog_admin_router)


@app.middleware("http")
async def observe_request(request: Request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    request_context_token = request_id_context.set(request_id)
    started_at = perf_counter()
    error_type: str | None = None
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as error:
        error_type = type(error).__name__
        status_code = 500
        response = JSONResponse(
            status_code=status_code,
            content={"detail": "Internal server error."},
        )

    elapsed_ms = round((perf_counter() - started_at) * 1000, 2)
    route = request.scope.get("route")
    route_template = getattr(route, "path", "unmatched")
    response.headers["X-Request-ID"] = request_id
    metrics.record_request(request.method, route_template, status_code)
    log_event(
        "http_request",
        level=logging.ERROR
        if status_code >= 500
        else logging.WARNING
        if status_code >= 400
        else logging.INFO,
        request_id=request_id,
        method=request.method,
        path=route_template,
        route=route_template,
        status_code=status_code,
        elapsed_ms=elapsed_ms,
        **({"error_type": error_type} if error_type else {}),
    )
    request_id_context.reset(request_context_token)
    return response


def evidence_read(record: SourceEvidence) -> SourceEvidenceRead:
    return SourceEvidenceRead(
        id=record.id,
        capability_key=record.capability_key,
        title=record.source_title,
        url=record.source_url,
        excerpt=record.excerpt,
        checked_on=record.checked_on,
        status=record.review_status,
    )


def laptop_read(record: LaptopModel) -> LaptopRead:
    return LaptopRead(
        **{column.name: getattr(record, column.name) for column in LaptopModel.__table__.columns},
        evidence=[evidence_read(source) for source in record.evidence if source.review_status == "verified"],
    )


def accessory_read(record: AccessoryModel) -> AccessoryRead:
    return AccessoryRead(
        **{column.name: getattr(record, column.name) for column in AccessoryModel.__table__.columns},
        evidence=[evidence_read(source) for source in record.evidence if source.review_status == "verified"],
    )


def laptop_rule_record(record: LaptopModel) -> dict:
    return {
        "ports": {
            "usb_c_port_count": record.usb_c_port_count,
            "usb_c_video": f"DisplayPort {record.usb_c_dp_version}" if record.usb_c_dp_version else None,
            "usb_c_video_supported": record.usb_c_video_supported,
            "usb_c_pd_input_min_w": record.usb_c_pd_input_min_w,
            "usb_c_pd_input_max_w": record.usb_c_pd_input_max_w,
            "maximum_external_displays": record.maximum_external_displays,
            "usb_c_max_resolution": record.usb_c_max_resolution,
            "usb_c_max_refresh_hz": record.usb_c_max_refresh_hz,
            "hdmi_max_resolution": record.hdmi_max_resolution,
            "hdmi_max_refresh_hz": record.hdmi_max_refresh_hz,
        },
        "evidence": [],
    }


def accessory_rule_record(record: AccessoryModel) -> dict:
    return {
        "host_connection": record.host_connection,
        "requirements": {"host_usb_c_video": record.requires_usb_c_dp_alt_mode},
        "outputs": {
            "display_count": record.hdmi_port_count,
            "hdmi_max_resolution": record.hdmi_max_resolution,
            "hdmi_max_refresh_hz": record.hdmi_max_refresh_hz,
            "charging_output_watts": (
                record.usb_c_output_max_w
                if record.category == "usb_c_charger"
                else record.pd_pass_through_max_w
            ),
        },
        "evidence": [],
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", response_model=None)
def readiness(session: Session = Depends(get_session)) -> dict[str, str] | JSONResponse:
    try:
        session.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def application_metrics() -> PlainTextResponse:
    return PlainTextResponse(metrics.render(), media_type="text/plain; version=0.0.4")


@app.get("/devices", response_model=CatalogRead)
def devices(session: Session = Depends(get_session)) -> CatalogRead:
    laptops = session.scalars(
        select(LaptopModel)
        .where(LaptopModel.review_status == "verified")
        .options(selectinload(LaptopModel.evidence))
    ).all()
    accessories = session.scalars(
        select(AccessoryModel)
        .where(AccessoryModel.review_status == "verified")
        .options(selectinload(AccessoryModel.evidence))
    ).all()
    return CatalogRead(
        laptops=[laptop_read(laptop) for laptop in laptops],
        accessories=[accessory_read(accessory) for accessory in accessories],
    )


@app.post("/setup-requests/parse", response_model=SetupParseResponse)
def parse_setup_request(request: SetupParseRequest) -> SetupParseResponse:
    try:
        response = parse_setup(request.description)
    except ParserUnavailable as error:
        raise HTTPException(
            status_code=503,
            detail={"code": "setup_parser_unavailable", "message": str(error)},
        ) from error
    except ParserInvalidResponse as error:
        raise HTTPException(
            status_code=502,
            detail={"code": "setup_parser_invalid_response", "message": str(error)},
        ) from error
    log_event(
        "setup_request_parsed",
        needs_clarification=response.needs_clarification,
        unsupported_count=len(response.unsupported_requests),
    )
    return response


@app.get("/devices/laptops/{device_id}", response_model=LaptopRead)
def laptop_detail(device_id: str, session: Session = Depends(get_session)) -> LaptopRead:
    record = session.scalar(
        select(LaptopModel)
        .where(LaptopModel.id == device_id, LaptopModel.review_status == "verified")
        .options(selectinload(LaptopModel.evidence))
    )
    if record is None:
        raise HTTPException(
            status_code=404, detail={"code": "laptop_not_found", "message": "Laptop not found."}
        )
    return laptop_read(record)


@app.get("/devices/accessories/{device_id}", response_model=AccessoryRead)
def accessory_detail(device_id: str, session: Session = Depends(get_session)) -> AccessoryRead:
    record = session.scalar(
        select(AccessoryModel)
        .where(AccessoryModel.id == device_id, AccessoryModel.review_status == "verified")
        .options(selectinload(AccessoryModel.evidence))
    )
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "accessory_not_found", "message": "Accessory not found."},
        )
    return accessory_read(record)


@app.post("/checks", response_model=CheckResponse)
def check_compatibility(
    request: CheckRequest,
    session: Session = Depends(get_session),
) -> CheckResponse:
    laptop = session.scalar(
        select(LaptopModel)
        .where(LaptopModel.id == request.laptop_id, LaptopModel.review_status == "verified")
        .options(selectinload(LaptopModel.evidence))
    )
    accessory = session.scalar(
        select(AccessoryModel)
        .where(AccessoryModel.id == request.accessory_id, AccessoryModel.review_status == "verified")
        .options(selectinload(AccessoryModel.evidence))
    )
    if laptop is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "laptop_not_found", "message": "Laptop not found in the PortPilot catalogue."},
        )
    if accessory is None:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "accessory_not_found",
                "message": "Accessory not found in the PortPilot catalogue.",
            },
        )

    result = evaluate(request, laptop_rule_record(laptop), accessory_rule_record(accessory))
    result["evidence"] = [
        evidence_read(item)
        for item in [*laptop.evidence, *accessory.evidence]
        if item.review_status == "verified"
    ]
    metrics.record_check(result["verdict"], result["rule_engine_version"])
    check_log_fields = {
        "verdict": result["verdict"],
        "rule_engine_version": result["rule_engine_version"],
    }
    if request_id := current_request_id():
        check_log_fields["request_id"] = request_id
    log_event("compatibility_check", **check_log_fields)
    return CheckResponse(**result)
