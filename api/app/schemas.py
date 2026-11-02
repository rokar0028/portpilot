from datetime import date
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator


class Setup(BaseModel):
    external_displays: int = Field(default=1, ge=0, le=4)
    resolution: str = "1920x1080"
    refresh_rate_hz: int = Field(default=60, ge=24, le=240)
    laptop_charging: bool = True


class CheckRequest(BaseModel):
    laptop_id: str
    accessory_id: str
    setup: Setup = Field(default_factory=Setup)


class SourceEvidenceRead(BaseModel):
    id: str
    capability_key: str
    title: str
    url: str
    excerpt: str
    checked_on: date
    status: Literal["draft", "verified", "needs_review"]


class CheckResponse(BaseModel):
    verdict: Literal["compatible", "compatible_with_limits", "incompatible", "insufficient_data"]
    summary: str
    limits: list[str]
    requirements: list[dict[str, str]]
    evidence: list[SourceEvidenceRead]
    rule_engine_version: str


class LaptopRead(BaseModel):
    id: str
    brand: str
    name: str
    model_code: str | None
    region_variant: str | None
    operating_system: str | None
    usb_c_port_count: int | None
    usb_c_data_rate_gbps: int | None
    usb_c_video_supported: bool | None
    usb_c_dp_version: str | None
    usb_c_pd_input_min_w: int | None
    usb_c_pd_input_max_w: int | None
    hdmi_version: str | None
    hdmi_max_resolution: str | None
    hdmi_max_refresh_hz: int | None
    maximum_external_displays: int | None
    usb_c_max_resolution: str | None
    usb_c_max_refresh_hz: int | None
    review_status: Literal["draft", "verified", "needs_review"]
    evidence: list[SourceEvidenceRead]


class AccessoryRead(BaseModel):
    id: str
    brand: str
    name: str
    model_code: str | None
    category: Literal["usb_c_hub", "usb_c_dock", "usb_c_charger", "portable_monitor", "external_display"]
    host_connection: str | None
    requires_usb_c_dp_alt_mode: bool | None
    hdmi_port_count: int | None
    hdmi_max_resolution: str | None
    hdmi_max_refresh_hz: int | None
    pd_input_max_w: int | None
    pd_pass_through_max_w: int | None
    usb_c_output_max_w: int | None
    usb_a_port_count: int | None
    ethernet_max_gbps: int | None
    review_status: Literal["draft", "verified", "needs_review"]
    evidence: list[SourceEvidenceRead]


class CatalogRead(BaseModel):
    laptops: list[LaptopRead]
    accessories: list[AccessoryRead]


class SourceEvidenceWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str | None = Field(default=None, min_length=1, max_length=180)
    capability_key: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=220)
    url: AnyHttpUrl
    excerpt: str = Field(min_length=1)
    checked_on: date
    status: Literal["draft", "verified", "needs_review"] = "draft"


class LaptopWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=120)
    brand: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    model_code: str | None = Field(default=None, min_length=1, max_length=120)
    region_variant: str | None = Field(default=None, min_length=1, max_length=120)
    operating_system: str | None = Field(default=None, min_length=1, max_length=80)
    usb_c_port_count: int | None = Field(default=None, ge=0)
    usb_c_data_rate_gbps: int | None = Field(default=None, ge=0)
    usb_c_video_supported: bool | None = None
    usb_c_dp_version: str | None = Field(default=None, max_length=20)
    usb_c_pd_input_min_w: int | None = Field(default=None, ge=0)
    usb_c_pd_input_max_w: int | None = Field(default=None, ge=0)
    hdmi_version: str | None = Field(default=None, max_length=20)
    hdmi_max_resolution: str | None = Field(default=None, max_length=30)
    hdmi_max_refresh_hz: int | None = Field(default=None, ge=0)
    maximum_external_displays: int | None = Field(default=None, ge=0)
    usb_c_max_resolution: str | None = Field(default=None, max_length=30)
    usb_c_max_refresh_hz: int | None = Field(default=None, ge=0)
    review_status: Literal["draft", "verified", "needs_review"] = "draft"
    evidence: list[SourceEvidenceWrite] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_power_range(self) -> "LaptopWrite":
        if (
            self.usb_c_pd_input_min_w is not None
            and self.usb_c_pd_input_max_w is not None
            and self.usb_c_pd_input_min_w > self.usb_c_pd_input_max_w
        ):
            raise ValueError("usb_c_pd_input_min_w cannot exceed usb_c_pd_input_max_w")
        return self


class AccessoryWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=120)
    brand: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    model_code: str | None = Field(default=None, min_length=1, max_length=120)
    category: Literal["usb_c_hub", "usb_c_dock", "usb_c_charger", "portable_monitor", "external_display"]
    host_connection: str | None = Field(default=None, min_length=1, max_length=80)
    requires_usb_c_dp_alt_mode: bool | None = None
    hdmi_port_count: int | None = Field(default=None, ge=0)
    hdmi_max_resolution: str | None = Field(default=None, max_length=30)
    hdmi_max_refresh_hz: int | None = Field(default=None, ge=0)
    pd_input_max_w: int | None = Field(default=None, ge=0)
    pd_pass_through_max_w: int | None = Field(default=None, ge=0)
    usb_c_output_max_w: int | None = Field(default=None, ge=0)
    usb_a_port_count: int | None = Field(default=None, ge=0)
    ethernet_max_gbps: int | None = Field(default=None, ge=0)
    review_status: Literal["draft", "verified", "needs_review"] = "draft"
    evidence: list[SourceEvidenceWrite] = Field(default_factory=list)
