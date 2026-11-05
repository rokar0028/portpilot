"""Create result_snapshots table for pinned shareable verification records."""

import sqlalchemy as sa
from alembic import op

revision = "20261105_0008"
down_revision = "20261105_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "result_snapshots",
        sa.Column("id", sa.String(length=180), primary_key=True),
        sa.Column("laptop_id", sa.String(length=120), nullable=False),
        sa.Column("accessory_id", sa.String(length=120), nullable=False),
        sa.Column("setup", sa.JSON(), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("limits", sa.JSON(), nullable=False),
        sa.Column("requirements", sa.JSON(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("rule_engine_version", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("result_snapshots")
