"""Add evidence conflict and catalogue correction history."""

import sqlalchemy as sa
from alembic import op

revision = "20261103_0004"
down_revision = "20261102_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_conflicts",
        sa.Column("id", sa.String(length=180), primary_key=True),
        sa.Column("laptop_id", sa.String(length=120), sa.ForeignKey("laptops.id", ondelete="CASCADE")),
        sa.Column("accessory_id", sa.String(length=120), sa.ForeignKey("accessories.id", ondelete="CASCADE")),
        sa.Column("capability_key", sa.String(length=80), nullable=False),
        sa.Column("claim_a_value", sa.Text(), nullable=False),
        sa.Column("claim_a_url", sa.Text(), nullable=False),
        sa.Column("claim_a_quality", sa.String(length=40), nullable=False),
        sa.Column("claim_b_value", sa.Text(), nullable=False),
        sa.Column("claim_b_url", sa.Text(), nullable=False),
        sa.Column("claim_b_quality", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("selected_value", sa.Text()),
        sa.Column("rationale", sa.Text()),
        sa.Column("reviewer", sa.String(length=120)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("status IN ('open', 'resolved')", name="ck_conflict_status"),
        sa.CheckConstraint(
            "(laptop_id IS NOT NULL AND accessory_id IS NULL) OR "
            "(laptop_id IS NULL AND accessory_id IS NOT NULL)",
            name="ck_conflict_exactly_one_owner",
        ),
    )
    op.create_index("ix_conflict_status_created", "evidence_conflicts", ["status", "created_at"])
    op.create_table(
        "catalogue_corrections",
        sa.Column("id", sa.String(length=180), primary_key=True),
        sa.Column("entity_type", sa.String(length=20), nullable=False),
        sa.Column("device_id", sa.String(length=120), nullable=False),
        sa.Column("capability_key", sa.String(length=80), nullable=False),
        sa.Column("previous_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence_references", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_correction_device_created", "catalogue_corrections", ["entity_type", "device_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_correction_device_created", table_name="catalogue_corrections")
    op.drop_table("catalogue_corrections")
    op.drop_index("ix_conflict_status_created", table_name="evidence_conflicts")
    op.drop_table("evidence_conflicts")
