"""sp3_numero_lectura_medicion

Agrega ``numero_lectura`` a ``medicion_wifi`` para identificar a qué
ciclo de escaneo pertenece cada resultado.
  1 = primer escaneo (modo puntual o primer ciclo continuo)
  2 = segundo ciclo continuo, etc.

Revision ID: d5e6f7a8b9c0
Revises: c3d4e5f6a7b8
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d5e6f7a8b9c0"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "medicion_wifi",
        sa.Column(
            "numero_lectura",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )


def downgrade() -> None:
    op.drop_column("medicion_wifi", "numero_lectura")
