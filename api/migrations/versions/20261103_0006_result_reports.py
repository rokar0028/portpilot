"""Store low-data user reports about compatibility results."""

import sqlalchemy as sa
from alembic import op

revision = "20261103_0006"
down_revision = "20261103_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "result_reports",
        sa.Column("id", sa.String(length=180), primary_key=True),
        sa.Column("laptop_id", sa.String(length=120), nullable=False),
        sa.Column("accessory_id", sa.String(length=120), nullable=False),
        sa.Column("setup", sa.JSON(), nullable=False),
        sa.Column("verdict", sa.String(length=32), nullable=False),
        sa.Column("rule_engine_version", sa.String(length=40), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(note) <= 1000", name="ck_result_report_note_length"),
    )


def downgrade() -> None:
    op.drop_table("result_reports")
