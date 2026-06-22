"""sp4 posiciones conjunto ap

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-06-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d0e1f2a3b4c5"
down_revision: str | None = "c9d0e1f2a3b4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("conjunto_ap_item", sa.Column("pos_x", sa.Float(), nullable=True))
    op.add_column("conjunto_ap_item", sa.Column("pos_y", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("conjunto_ap_item", "pos_y")
    op.drop_column("conjunto_ap_item", "pos_x")
