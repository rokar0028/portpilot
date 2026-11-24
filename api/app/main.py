import logging
import os
import re
from collections import deque
from datetime import UTC, datetime
from threading import Lock
from time import monotonic, perf_counter
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from .capabilities import derived_rule_fields, rule_fields
from .catalog_admin import router as catalog_admin_router
from .database import get_session
from .models import AccessoryModel, LaptopModel, ResultReport, ResultSnapshot, SourceEvidence
from .observability import current_request_id, log_event, metrics, request_id_context
from .rules import evaluate
from .schemas import (
    AccessoryRead,
    CatalogRead,
    CheckRequest,
    CheckResponse,
    CompatibleAccessoriesResponse,
    CompatibleAccessoryItem,
    LaptopRead,
    ResultReportRead,
    ResultReportWrite,
    ResultSnapshotRead,
    ResultSnapshotWrite,
    SearchResponse,
    SetupParseRequest,
    SetupParseResponse,
    SetupRequest,
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
    origin.strip().rstrip("/")
    for origin in os.getenv("FRONTEND_ORIGIN", "http://localhost:3000").split(",")
    if origin.strip().rstrip("/")
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


SLOW_REQUEST_THRESHOLD_MS = float(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "500"))
REPORT_RATE_LIMIT_MAX = max(1, int(os.getenv("REPORT_RATE_LIMIT_MAX", "10")))
REPORT_RATE_LIMIT_WINDOW_SECONDS = max(1.0, float(os.getenv("REPORT_RATE_LIMIT_WINDOW_SECONDS", "60")))
_report_rate_limit: dict[str, deque[float]] = {}
_report_rate_limit_lock = Lock()


def enforce_report_rate_limit(request: Request) -> None:
    """Apply a small process-local abuse limit to the unauthenticated report endpoint."""
    client_key = request.client.host if request.client else "unknown"
    now = monotonic()
    cutoff = now - REPORT_RATE_LIMIT_WINDOW_SECONDS
    with _report_rate_limit_lock:
        attempts = _report_rate_limit.setdefault(client_key, deque())
        while attempts and attempts[0] <= cutoff:
            attempts.popleft()
        if len(attempts) >= REPORT_RATE_LIMIT_MAX:
            retry_after = max(1, int(attempts[0] + REPORT_RATE_LIMIT_WINDOW_SECONDS - now))
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "report_rate_limited",
                    "message": "Too many reports submitted. Try again later.",
                },
                headers={"Retry-After": str(retry_after)},
            )
        attempts.append(now)
        if len(_report_rate_limit) > 10_000:
            expired = [
                key for key, values in _report_rate_limit.items() if not values or values[-1] <= cutoff
            ]
            for key in expired:
                _report_rate_limit.pop(key, None)


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

    elapsed_seconds = perf_counter() - started_at
    elapsed_ms = round(elapsed_seconds * 1000, 2)
    route = request.scope.get("route")
    route_template = getattr(route, "path", "unmatched")
    response.headers["X-Request-ID"] = request_id
    metrics.record_request(
        request.method,
        route_template,
        status_code,
        duration_seconds=elapsed_seconds,
    )
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
    if elapsed_ms >= SLOW_REQUEST_THRESHOLD_MS:
        log_event(
            "http_slow_request",
            level=logging.ERROR if status_code >= 500 else logging.WARNING,
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
    ports = {target: getattr(record, source) for target, source in rule_fields("laptop", "ports").items()}
    ports["usb_c_video"] = f"DisplayPort {record.usb_c_dp_version}" if record.usb_c_dp_version else None
    return {
        "id": record.id,
        "brand": record.brand,
        "operating_system": record.operating_system,
        "ports": ports,
        "evidence": [],
    }


def accessory_rule_record(record: AccessoryModel) -> dict:
    requirements = {
        target: getattr(record, source) for target, source in rule_fields("accessory", "requirements").items()
    }
    outputs = {
        target: getattr(record, source) for target, source in rule_fields("accessory", "outputs").items()
    }
    for target, source in derived_rule_fields("accessory", "outputs", record.category).items():
        outputs[target] = getattr(record, source)
    return {
        "id": record.id,
        "brand": record.brand,
        "category": record.category,
        "host_connection": record.host_connection,
        "pd_input_max_w": record.pd_input_max_w,
        "requirements": requirements,
        "outputs": outputs,
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


@app.get("/devices/search", response_model=SearchResponse)
def search_devices(
    q: str = "",
    category: str | None = None,
    kind: str | None = None,
    session: Session = Depends(get_session),
) -> SearchResponse:
    query_str = q.strip()
    matched_laptops: list[LaptopRead] = []
    matched_accessories: list[AccessoryRead] = []
    pattern = f"%{query_str}%" if query_str else None
    stripped = re.sub(r"[\s\-_]+", "", query_str) if query_str else ""
    norm_pattern = f"%{stripped}%" if stripped else None

    if kind != "accessory" and not category:
        lap_stmt = select(LaptopModel).where(LaptopModel.review_status == "verified")
        if pattern:
            lap_conditions = [
                LaptopModel.name.ilike(pattern),
                LaptopModel.brand.ilike(pattern),
                LaptopModel.model_code.ilike(pattern),
            ]
            if norm_pattern:
                norm_model = func.replace(
                    func.replace(func.replace(LaptopModel.model_code, "-", ""), " ", ""), "_", ""
                )
                norm_name = func.replace(
                    func.replace(func.replace(LaptopModel.name, "-", ""), " ", ""), "_", ""
                )
                lap_conditions.extend(
                    [
                        norm_model.ilike(norm_pattern),
                        norm_name.ilike(norm_pattern),
                    ]
                )
            lap_stmt = lap_stmt.where(or_(*lap_conditions))
        elif not query_str and kind != "laptop":
            lap_stmt = None

        if lap_stmt is not None:
            laptops = session.scalars(lap_stmt.options(selectinload(LaptopModel.evidence))).all()
            matched_laptops = [laptop_read(lap) for lap in laptops]

    if kind != "laptop":
        acc_stmt = select(AccessoryModel).where(AccessoryModel.review_status == "verified")
        if pattern:
            acc_conditions = [
                AccessoryModel.name.ilike(pattern),
                AccessoryModel.brand.ilike(pattern),
                AccessoryModel.model_code.ilike(pattern),
            ]
            if norm_pattern:
                norm_model = func.replace(
                    func.replace(func.replace(AccessoryModel.model_code, "-", ""), " ", ""), "_", ""
                )
                norm_name = func.replace(
                    func.replace(func.replace(AccessoryModel.name, "-", ""), " ", ""), "_", ""
                )
                acc_conditions.extend(
                    [
                        norm_model.ilike(norm_pattern),
                        norm_name.ilike(norm_pattern),
                    ]
                )
            acc_stmt = acc_stmt.where(or_(*acc_conditions))
        if category:
            acc_stmt = acc_stmt.where(AccessoryModel.category == category)
        elif not pattern and kind != "accessory":
            acc_stmt = None

        if acc_stmt is not None:
            accessories = session.scalars(acc_stmt.options(selectinload(AccessoryModel.evidence))).all()
            matched_accessories = [accessory_read(acc) for acc in accessories]

    return SearchResponse(
        query=query_str,
        total=len(matched_laptops) + len(matched_accessories),
        laptops=matched_laptops,
        accessories=matched_accessories,
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


@app.get(
    "/devices/laptops/{device_id}/compatible-accessories",
    response_model=CompatibleAccessoriesResponse,
)
def laptop_compatible_accessories(
    device_id: str,
    displays: int | None = 1,
    resolution: str | None = "1920x1080",
    refresh_rate_hz: int | None = 60,
    laptop_charging: bool | None = True,
    category: str | None = None,
    verdict: str | None = None,
    session: Session = Depends(get_session),
) -> CompatibleAccessoriesResponse:
    laptop = session.scalar(
        select(LaptopModel)
        .where(LaptopModel.id == device_id, LaptopModel.review_status == "verified")
        .options(selectinload(LaptopModel.evidence))
    )
    if laptop is None:
        raise HTTPException(
            status_code=404, detail={"code": "laptop_not_found", "message": "Laptop not found."}
        )

    setup = SetupRequest(
        external_displays=displays,
        resolution=resolution,
        refresh_rate_hz=refresh_rate_hz,
        laptop_charging=laptop_charging,
    )

    query = (
        select(AccessoryModel)
        .where(AccessoryModel.review_status == "verified")
        .options(selectinload(AccessoryModel.evidence))
    )
    if category:
        query = query.where(AccessoryModel.category == category)

    accessories = session.scalars(query).all()
    laptop_dict = laptop_rule_record(laptop)

    results: list[CompatibleAccessoryItem] = []
    counts: dict[str, int] = {
        "compatible": 0,
        "compatible_with_limits": 0,
        "incompatible": 0,
        "insufficient_data": 0,
    }

    for acc in accessories:
        acc_dict = accessory_rule_record(acc)
        check_req = CheckRequest(
            laptop_id=laptop.id,
            accessory_id=acc.id,
            setup=setup,
        )
        check_result = evaluate(check_req, laptop_dict, acc_dict)
        verdict_val = check_result["verdict"]
        counts[verdict_val] = counts.get(verdict_val, 0) + 1

        if verdict and verdict_val != verdict:
            continue

        results.append(
            CompatibleAccessoryItem(
                accessory=accessory_read(acc),
                verdict=verdict_val,
                evaluation_tier=check_result.get("evaluation_tier", "verified"),
                summary=check_result["summary"],
                limits=check_result["limits"],
                requirements=check_result["requirements"],
                rule_engine_version=check_result["rule_engine_version"],
            )
        )

    return CompatibleAccessoriesResponse(
        laptop_id=laptop.id,
        laptop_name=laptop.name,
        setup=setup,
        total_evaluated=len(accessories),
        counts=counts,
        results=results,
    )


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


@app.post("/result-reports", response_model=ResultReportRead, status_code=201)
def create_result_report(
    payload: ResultReportWrite,
    session: Session = Depends(get_session),
    http_request: Request = None,  # type: ignore[assignment]
) -> ResultReportRead:
    if http_request is not None:
        enforce_report_rate_limit(http_request)
    report = ResultReport(
        id=f"report-{uuid4().hex}",
        laptop_id=payload.laptop_id,
        accessory_id=payload.accessory_id,
        setup=payload.setup.model_dump(mode="json"),
        verdict=payload.verdict,
        rule_engine_version=payload.rule_engine_version,
        note=payload.note,
        created_at=datetime.now(UTC),
    )
    session.add(report)
    session.commit()
    log_event("result_report_received", verdict=payload.verdict)
    return ResultReportRead(id=report.id)


@app.post("/result-snapshots", response_model=ResultSnapshotRead, status_code=201)
def create_result_snapshot(
    request: ResultSnapshotWrite,
    session: Session = Depends(get_session),
) -> ResultSnapshotRead:
    snapshot_id = f"snap-{uuid4().hex}"
    now = datetime.now(UTC)
    snapshot = ResultSnapshot(
        id=snapshot_id,
        laptop_id=request.laptop_id,
        accessory_id=request.accessory_id,
        setup=request.setup.model_dump(mode="json"),
        verdict=request.verdict,
        summary=request.summary,
        limits=request.limits,
        requirements=request.requirements,
        evidence=[e.model_dump(mode="json") for e in request.evidence],
        rule_engine_version=request.rule_engine_version,
        created_at=now,
    )
    session.add(snapshot)
    session.commit()
    log_event("result_snapshot_created", snapshot_id=snapshot_id, verdict=request.verdict)
    return ResultSnapshotRead(
        id=snapshot.id,
        laptop_id=snapshot.laptop_id,
        accessory_id=snapshot.accessory_id,
        setup=request.setup,
        verdict=snapshot.verdict,
        evaluation_tier=request.evaluation_tier,
        summary=snapshot.summary,
        limits=snapshot.limits,
        requirements=snapshot.requirements,
        evidence=request.evidence,
        rule_engine_version=snapshot.rule_engine_version,
        created_at=snapshot.created_at,
    )


@app.get("/result-snapshots/{snapshot_id}", response_model=ResultSnapshotRead)
def get_result_snapshot(
    snapshot_id: str,
    session: Session = Depends(get_session),
) -> ResultSnapshotRead:
    snapshot = session.scalar(select(ResultSnapshot).where(ResultSnapshot.id == snapshot_id))
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "snapshot_not_found", "message": "Result snapshot not found."},
        )
    tier = (
        "theoretical"
        if snapshot.laptop_id.startswith("protocol-") or snapshot.accessory_id.startswith("protocol-")
        else "verified"
    )
    return ResultSnapshotRead(
        id=snapshot.id,
        laptop_id=snapshot.laptop_id,
        accessory_id=snapshot.accessory_id,
        setup=SetupRequest.model_validate(snapshot.setup),
        verdict=snapshot.verdict,
        evaluation_tier=tier,
        summary=snapshot.summary,
        limits=snapshot.limits,
        requirements=snapshot.requirements,
        evidence=[SourceEvidenceRead.model_validate(e) for e in snapshot.evidence],
        rule_engine_version=snapshot.rule_engine_version,
        created_at=snapshot.created_at,
    )
