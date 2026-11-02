"""Store known support separately from unknown USB-C video data."""

import sqlalchemy as sa
from alembic import op

revision = "20261102_0002"
down_revision = "20261102_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("laptops", sa.Column("usb_c_video_supported", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("laptops", "usb_c_video_supported")
