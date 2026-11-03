"""Store evidence-backed simultaneous display configurations."""

import sqlalchemy as sa
from alembic import op

revision = "20261103_0005"
down_revision = "20261103_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("laptops", sa.Column("display_configurations", sa.JSON(), nullable=True))
    op.add_column("accessories", sa.Column("display_configurations", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("accessories", "display_configurations")
    op.drop_column("laptops", "display_configurations")
