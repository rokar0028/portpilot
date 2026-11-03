from datetime import date, datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator


class DisplayMode(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    resolution: str = Field(min_length=1, max_length=30)
    refresh_rate_hz: int = Field(ge=1, le=1000)
    connection: str | None = Field(default=None, min_length=1, max_length=120)


class DisplayConfiguration(BaseModel):
    """One manufacturer-documented simultaneous set of external display modes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    displays: list[DisplayMode] = Field(min_length=1, max_length=8)
    topology: str | None = Field(default=None, min_length=1, max_length=120)


class SetupRequest(BaseModel):
    """Requested setup intent, shared by manual checks and natural-language parsing."""

    model_config = ConfigDict(extra="forbid")

    external_displays: int | None = Field(default=1, ge=0, le=4)
    resolution: str | None = Field(default="1920x1080", max_length=30)
    refresh_rate_hz: int | None = Field(default=60, ge=24, le=240)
    laptop_charging: bool | None = True
    displays: list[DisplayMode] | None = Field(default=None, min_length=1, max_length=8)
    display_topology: str | None = Field(default=None, min_length=1, max_length=120)

    @model_validator(mode="after")
    def align_explicit_display_count(self) -> "SetupRequest":
        if self.displays is not None:
            self.external_displays = len(self.displays)
        return self


def default_setup_request() -> SetupRequest:
    return SetupRequest(
        external_displays=1,
        resolution="1920x1080",
        refresh_rate_hz=60,
        laptop_charging=True,
    )


class CheckRequest(BaseModel):
    laptop_id: str
    accessory_id: str
    setup: SetupRequest = Field(default_factory=default_setup_request)


class SetupParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    description: str = Field(min_length=3, max_length=1000)


class SetupParseResponse(BaseModel):
    setup: SetupRequest
    needs_clarification: bool
    clarification_questions: list[str] = Field(default_factory=list, max_length=5)
    unsupported_requests: list[str] = Field(default_factory=list, max_length=5)
    notice: str = "Review or correct these requirements before checking compatibility."


class SourceEvidenceRead(BaseModel):
    id: str
    capability_key: str
    title: str
    url: str
    excerpt: str
    checked_on: date
    status: Literal["draft", "verified", "needs_review"]


class IdentityWarning(BaseModel):
    candidate_id: str
    candidate_name: str
    reasons: list[str]


class CheckResponse(BaseModel):
    verdict: Literal["compatible", "compatible_with_limits", "incompatible", "insufficient_data"]
    summary: str
    limits: list[str]
    requirements: list[dict[str, str]]
    evidence: list[SourceEvidenceRead]
    rule_engine_version: str


class ResultReportWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    laptop_id: str = Field(min_length=1, max_length=120)
    accessory_id: str = Field(min_length=1, max_length=120)
    setup: SetupRequest
    verdict: Literal["compatible", "compatible_with_limits", "incompatible", "insufficient_data"]
    rule_engine_version: str = Field(min_length=1, max_length=40)
    note: str = Field(default="", max_length=1000)


class ResultReportRead(BaseModel):
    id: str
    status: Literal["received"] = "received"


class LaptopRead(BaseModel):
    id: str
    brand: str
    name: str
    model_code: str | None
    region_variant: str | None
    hardware_revision: str | None = None
    identity_warnings: list[IdentityWarning] = Field(default_factory=list)
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
    display_configurations: list[DisplayConfiguration] | None = None
    review_status: Literal["draft", "verified", "needs_review"]
    evidence: list[SourceEvidenceRead]


class AccessoryRead(BaseModel):
    id: str
    brand: str
    name: str
    model_code: str | None
    region_variant: str | None = None
    hardware_revision: str | None = None
    identity_warnings: list[IdentityWarning] = Field(default_factory=list)
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
    display_configurations: list[DisplayConfiguration] | None = None
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


class EvidenceConflictWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    entity_type: Literal["laptop", "accessory"]
    device_id: str = Field(min_length=1, max_length=120)
    capability_key: str = Field(min_length=1, max_length=80)
    claim_a_value: str = Field(min_length=1)
    claim_a_url: AnyHttpUrl
    claim_a_quality: Literal["manufacturer_primary", "manufacturer_secondary", "other"]
    claim_b_value: str = Field(min_length=1)
    claim_b_url: AnyHttpUrl
    claim_b_quality: Literal["manufacturer_primary", "manufacturer_secondary", "other"]


class EvidenceConflictResolve(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    selected_value: str = Field(min_length=1)
    rationale: str = Field(min_length=10)
    reviewer: str = Field(min_length=1, max_length=120)


class EvidenceConflictRead(BaseModel):
    id: str
    entity_type: Literal["laptop", "accessory"]
    device_id: str
    capability_key: str
    claim_a_value: str
    claim_a_url: str
    claim_a_quality: str
    claim_b_value: str
    claim_b_url: str
    claim_b_quality: str
    status: Literal["open", "resolved"]
    selected_value: str | None
    rationale: str | None
    reviewer: str | None
    created_at: datetime
    resolved_at: datetime | None


class EvidenceRecheckWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    outcome: Literal["verified", "needs_review"]
    checked_on: date
    note: str = Field(min_length=10)
    reviewer: str = Field(min_length=1, max_length=120)


class CatalogueCorrectionRead(BaseModel):
    id: str
    entity_type: Literal["laptop", "accessory"]
    device_id: str
    capability_key: str
    previous_value: str | None
    new_value: str | None
    reason: str
    evidence_references: list[str]
    actor: str
    created_at: datetime


class LaptopWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=120)
    brand: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=180)
    model_code: str | None = Field(default=None, min_length=1, max_length=120)
    region_variant: str | None = Field(default=None, min_length=1, max_length=120)
    hardware_revision: str | None = Field(default=None, min_length=1, max_length=120)
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
    display_configurations: list[DisplayConfiguration] | None = None
    review_status: Literal["draft", "verified", "needs_review"] = "draft"
    evidence: list[SourceEvidenceWrite] = Field(default_factory=list)
    change_reason: str | None = Field(default=None, min_length=10, max_length=1000)

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
    region_variant: str | None = Field(default=None, min_length=1, max_length=120)
    hardware_revision: str | None = Field(default=None, min_length=1, max_length=120)
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
    display_configurations: list[DisplayConfiguration] | None = None
    review_status: Literal["draft", "verified", "needs_review"] = "draft"
    evidence: list[SourceEvidenceWrite] = Field(default_factory=list)
    change_reason: str | None = Field(default=None, min_length=10, max_length=1000)
