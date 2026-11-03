"""Add explicit hardware revision identity fields."""

import sqlalchemy as sa
from alembic import op

revision = "20261102_0003"
down_revision = "20261102_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("laptops", sa.Column("hardware_revision", sa.String(length=120), nullable=True))
    op.add_column("accessories", sa.Column("region_variant", sa.String(length=120), nullable=True))
    op.add_column("accessories", sa.Column("hardware_revision", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("accessories", "hardware_revision")
    op.drop_column("accessories", "region_variant")
    op.drop_column("laptops", "hardware_revision")
