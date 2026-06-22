"""Gobernanza para conjuntos AP.

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b6c7d8e9f0a1"
down_revision: str | None = "a5b6c7d8e9f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "conjunto_ap",
        sa.Column(
            "origen",
            sa.String(30),
            nullable=False,
            server_default="manual_movil",
        ),
    )
    op.add_column(
        "conjunto_ap",
        sa.Column(
            "estado_gobernanza",
            sa.String(30),
            nullable=False,
            server_default="borrador_tecnico",
        ),
    )
    op.add_column(
        "conjunto_ap",
        sa.Column("creado_por_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_conjunto_ap_origen", "conjunto_ap", ["origen"])
    op.create_index(
        "ix_conjunto_ap_estado_gobernanza",
        "conjunto_ap",
        ["estado_gobernanza"],
    )
    op.create_index("ix_conjunto_ap_creado_por_id", "conjunto_ap", ["creado_por_id"])
    op.create_foreign_key(
        "fk_conjunto_ap_creado_por",
        "conjunto_ap",
        "usuario",
        ["creado_por_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_conjunto_ap_creado_por", "conjunto_ap", type_="foreignkey")
    op.drop_index("ix_conjunto_ap_creado_por_id", table_name="conjunto_ap")
    op.drop_index("ix_conjunto_ap_estado_gobernanza", table_name="conjunto_ap")
    op.drop_index("ix_conjunto_ap_origen", table_name="conjunto_ap")
    op.drop_column("conjunto_ap", "creado_por_id")
    op.drop_column("conjunto_ap", "estado_gobernanza")
    op.drop_column("conjunto_ap", "origen")
