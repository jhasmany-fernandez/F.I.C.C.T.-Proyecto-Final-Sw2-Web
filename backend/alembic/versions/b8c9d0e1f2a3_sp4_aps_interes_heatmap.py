"""sp4 aps interes heatmap

Revision ID: b8c9d0e1f2a3
Revises: f7a8b9c0d1e2
Create Date: 2026-06-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b8c9d0e1f2a3"
down_revision: str | None = "f7a8b9c0d1e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("mapa_calor", sa.Column("aps_interes", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("mapa_calor", "aps_interes")
