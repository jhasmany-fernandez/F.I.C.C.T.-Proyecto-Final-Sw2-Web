"""Baseline observado separado para 2,4 y 5 GHz.

Revision ID: a4b5c6d7e8f9
Revises: f3a4b5c6d7e8
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a4b5c6d7e8f9"
down_revision: str | None = "f3a4b5c6d7e8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "escenario_optimizado",
        sa.Column(
            "mapas_actuales_por_banda",
            sa.JSON(),
            nullable=False,
            server_default="{}",
        ),
    )


def downgrade() -> None:
    op.drop_column("escenario_optimizado", "mapas_actuales_por_banda")
