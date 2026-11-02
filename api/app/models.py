from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class LaptopModel(Base):
    __tablename__ = "laptops"
    __table_args__ = (
        CheckConstraint("usb_c_port_count IS NULL OR usb_c_port_count >= 0", name="ck_laptop_usb_c_count"),
        CheckConstraint(
            "review_status IN ('draft', 'verified', 'needs_review')", name="ck_laptop_review_status"
        ),
        CheckConstraint(
            "usb_c_pd_input_min_w IS NULL OR usb_c_pd_input_max_w IS NULL "
            "OR usb_c_pd_input_min_w <= usb_c_pd_input_max_w",
            name="ck_laptop_pd_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    model_code: Mapped[str | None] = mapped_column(String(120))
    region_variant: Mapped[str | None] = mapped_column(String(120))
    operating_system: Mapped[str | None] = mapped_column(String(80))
    usb_c_port_count: Mapped[int | None] = mapped_column(Integer)
    usb_c_data_rate_gbps: Mapped[int | None] = mapped_column(Integer)
    usb_c_video_supported: Mapped[bool | None] = mapped_column(nullable=True)
    usb_c_dp_version: Mapped[str | None] = mapped_column(String(20))
    usb_c_pd_input_min_w: Mapped[int | None] = mapped_column(Integer)
    usb_c_pd_input_max_w: Mapped[int | None] = mapped_column(Integer)
    hdmi_version: Mapped[str | None] = mapped_column(String(20))
    hdmi_max_resolution: Mapped[str | None] = mapped_column(String(30))
    hdmi_max_refresh_hz: Mapped[int | None] = mapped_column(Integer)
    maximum_external_displays: Mapped[int | None] = mapped_column(Integer)
    usb_c_max_resolution: Mapped[str | None] = mapped_column(String(30))
    usb_c_max_refresh_hz: Mapped[int | None] = mapped_column(Integer)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="verified")

    evidence: Mapped[list["SourceEvidence"]] = relationship(
        back_populates="laptop", cascade="all, delete-orphan"
    )


class AccessoryModel(Base):
    __tablename__ = "accessories"
    __table_args__ = (
        CheckConstraint(
            "category IN ('usb_c_hub', 'usb_c_dock', 'usb_c_charger', "
            "'portable_monitor', 'external_display')",
            name="ck_accessory_category",
        ),
        CheckConstraint("hdmi_port_count IS NULL OR hdmi_port_count >= 0", name="ck_accessory_hdmi_count"),
        CheckConstraint(
            "review_status IN ('draft', 'verified', 'needs_review')", name="ck_accessory_review_status"
        ),
    )

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    brand: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    model_code: Mapped[str | None] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    host_connection: Mapped[str | None] = mapped_column(String(80))
    requires_usb_c_dp_alt_mode: Mapped[bool | None] = mapped_column(nullable=True)
    hdmi_port_count: Mapped[int | None] = mapped_column(Integer)
    hdmi_max_resolution: Mapped[str | None] = mapped_column(String(30))
    hdmi_max_refresh_hz: Mapped[int | None] = mapped_column(Integer)
    pd_input_max_w: Mapped[int | None] = mapped_column(Integer)
    pd_pass_through_max_w: Mapped[int | None] = mapped_column(Integer)
    usb_c_output_max_w: Mapped[int | None] = mapped_column(Integer)
    usb_a_port_count: Mapped[int | None] = mapped_column(Integer)
    ethernet_max_gbps: Mapped[int | None] = mapped_column(Integer)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="verified")

    evidence: Mapped[list["SourceEvidence"]] = relationship(
        back_populates="accessory", cascade="all, delete-orphan"
    )


class SourceEvidence(Base):
    __tablename__ = "source_evidence"
    __table_args__ = (
        CheckConstraint(
            "(laptop_id IS NOT NULL AND accessory_id IS NULL) OR "
            "(laptop_id IS NULL AND accessory_id IS NOT NULL)",
            name="ck_evidence_exactly_one_owner",
        ),
        CheckConstraint(
            "review_status IN ('draft', 'verified', 'needs_review')", name="ck_evidence_review_status"
        ),
    )

    id: Mapped[str] = mapped_column(String(180), primary_key=True)
    laptop_id: Mapped[str | None] = mapped_column(ForeignKey("laptops.id", ondelete="CASCADE"))
    accessory_id: Mapped[str | None] = mapped_column(ForeignKey("accessories.id", ondelete="CASCADE"))
    capability_key: Mapped[str] = mapped_column(String(80), nullable=False)
    source_title: Mapped[str] = mapped_column(String(220), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    checked_on: Mapped[date] = mapped_column(Date, nullable=False)
    review_status: Mapped[str] = mapped_column(String(20), nullable=False, default="verified")

    laptop: Mapped[LaptopModel | None] = relationship(back_populates="evidence")
    accessory: Mapped[AccessoryModel | None] = relationship(back_populates="evidence")
