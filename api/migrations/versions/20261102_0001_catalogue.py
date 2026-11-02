"""Create the evidence-backed device catalogue."""

import sqlalchemy as sa
from alembic import op

revision = "20261102_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "laptops",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("brand", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("model_code", sa.String(length=120)),
        sa.Column("region_variant", sa.String(length=120)),
        sa.Column("operating_system", sa.String(length=80)),
        sa.Column("usb_c_port_count", sa.Integer()),
        sa.Column("usb_c_data_rate_gbps", sa.Integer()),
        sa.Column("usb_c_dp_version", sa.String(length=20)),
        sa.Column("usb_c_pd_input_min_w", sa.Integer()),
        sa.Column("usb_c_pd_input_max_w", sa.Integer()),
        sa.Column("hdmi_version", sa.String(length=20)),
        sa.Column("hdmi_max_resolution", sa.String(length=30)),
        sa.Column("hdmi_max_refresh_hz", sa.Integer()),
        sa.Column("maximum_external_displays", sa.Integer()),
        sa.Column("usb_c_max_resolution", sa.String(length=30)),
        sa.Column("usb_c_max_refresh_hz", sa.Integer()),
        sa.Column("review_status", sa.String(length=20), nullable=False, server_default="verified"),
        sa.CheckConstraint("usb_c_port_count IS NULL OR usb_c_port_count >= 0", name="ck_laptop_usb_c_count"),
        sa.CheckConstraint(
            "usb_c_pd_input_min_w IS NULL OR usb_c_pd_input_max_w IS NULL "
            "OR usb_c_pd_input_min_w <= usb_c_pd_input_max_w",
            name="ck_laptop_pd_range",
        ),
        sa.CheckConstraint(
            "review_status IN ('draft', 'verified', 'needs_review')", name="ck_laptop_review_status"
        ),
    )
    op.create_table(
        "accessories",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("brand", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("model_code", sa.String(length=120)),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("host_connection", sa.String(length=80)),
        sa.Column("requires_usb_c_dp_alt_mode", sa.Boolean()),
        sa.Column("hdmi_port_count", sa.Integer()),
        sa.Column("hdmi_max_resolution", sa.String(length=30)),
        sa.Column("hdmi_max_refresh_hz", sa.Integer()),
        sa.Column("pd_input_max_w", sa.Integer()),
        sa.Column("pd_pass_through_max_w", sa.Integer()),
        sa.Column("usb_c_output_max_w", sa.Integer()),
        sa.Column("usb_a_port_count", sa.Integer()),
        sa.Column("ethernet_max_gbps", sa.Integer()),
        sa.Column("review_status", sa.String(length=20), nullable=False, server_default="verified"),
        sa.CheckConstraint(
            "category IN ('usb_c_hub', 'usb_c_dock', 'usb_c_charger', "
            "'portable_monitor', 'external_display')",
            name="ck_accessory_category",
        ),
        sa.CheckConstraint("hdmi_port_count IS NULL OR hdmi_port_count >= 0", name="ck_accessory_hdmi_count"),
        sa.CheckConstraint(
            "review_status IN ('draft', 'verified', 'needs_review')", name="ck_accessory_review_status"
        ),
    )
    op.create_table(
        "source_evidence",
        sa.Column("id", sa.String(length=180), primary_key=True),
        sa.Column("laptop_id", sa.String(length=120), sa.ForeignKey("laptops.id", ondelete="CASCADE")),
        sa.Column("accessory_id", sa.String(length=120), sa.ForeignKey("accessories.id", ondelete="CASCADE")),
        sa.Column("capability_key", sa.String(length=80), nullable=False),
        sa.Column("source_title", sa.String(length=220), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("checked_on", sa.Date(), nullable=False),
        sa.Column("review_status", sa.String(length=20), nullable=False, server_default="verified"),
        sa.CheckConstraint(
            "(laptop_id IS NOT NULL AND accessory_id IS NULL) OR "
            "(laptop_id IS NULL AND accessory_id IS NOT NULL)",
            name="ck_evidence_exactly_one_owner",
        ),
        sa.CheckConstraint(
            "review_status IN ('draft', 'verified', 'needs_review')", name="ck_evidence_review_status"
        ),
    )
    op.create_index("ix_source_evidence_laptop_id", "source_evidence", ["laptop_id"])
    op.create_index("ix_source_evidence_accessory_id", "source_evidence", ["accessory_id"])
    op.create_index("ix_source_evidence_capability_key", "source_evidence", ["capability_key"])


def downgrade() -> None:
    op.drop_index("ix_source_evidence_capability_key", table_name="source_evidence")
    op.drop_index("ix_source_evidence_accessory_id", table_name="source_evidence")
    op.drop_index("ix_source_evidence_laptop_id", table_name="source_evidence")
    op.drop_table("source_evidence")
    op.drop_table("accessories")
    op.drop_table("laptops")
