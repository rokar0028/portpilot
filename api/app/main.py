import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .catalog import CATALOG, list_devices
from .rules import evaluate
from .schemas import CheckRequest, CheckResponse

app = FastAPI(
    title="PortPilot API",
    version="0.1.0",
    description="Evidence-backed laptop and accessory compatibility checks.",
)
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/devices")
def devices() -> dict[str, list[dict]]:
    return {"laptops": list_devices("laptops"), "accessories": list_devices("accessories")}


@app.post("/checks", response_model=CheckResponse)
def check_compatibility(request: CheckRequest) -> dict:
    laptop = CATALOG["laptops"].get(request.laptop_id)
    accessory = CATALOG["accessories"].get(request.accessory_id)
    if laptop is None:
        raise HTTPException(status_code=404, detail="Laptop not found in the PortPilot catalogue.")
    if accessory is None:
        raise HTTPException(status_code=404, detail="Accessory not found in the PortPilot catalogue.")
    return evaluate(request, laptop, accessory)
