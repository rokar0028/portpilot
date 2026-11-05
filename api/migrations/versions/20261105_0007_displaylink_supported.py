"""Add displaylink_supported to accessories table."""

import sqlalchemy as sa
from alembic import op

revision = "20261105_0007"
down_revision = "20261103_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("accessories", sa.Column("displaylink_supported", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("accessories", "displaylink_supported")
