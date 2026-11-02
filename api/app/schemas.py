from typing import Literal

from pydantic import BaseModel, Field


class Setup(BaseModel):
    external_displays: int = Field(default=1, ge=0, le=4)
    resolution: str = "1920x1080"
    refresh_rate_hz: int = Field(default=60, ge=24, le=240)
    laptop_charging: bool = True


class CheckRequest(BaseModel):
    laptop_id: str
    accessory_id: str
    setup: Setup = Field(default_factory=Setup)


class CheckResponse(BaseModel):
    verdict: Literal["compatible", "compatible_with_limits", "incompatible", "insufficient_data"]
    summary: str
    limits: list[str]
    requirements: list[dict[str, str]]
    evidence: list[dict[str, str]]
    rule_engine_version: str
