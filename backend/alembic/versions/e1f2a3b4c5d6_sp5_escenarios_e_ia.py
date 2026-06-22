"""Sprint 5: escenarios optimizados y recomendaciones IA.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "escenario_optimizado",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proyecto_id", sa.Integer(), nullable=False),
        sa.Column("plano_id", sa.Integer(), nullable=False),
        sa.Column("mapa_actual_id", sa.Integer(), nullable=True),
        sa.Column("mapa_proyectado_id", sa.Integer(), nullable=True),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("banda", sa.String(length=10), nullable=False),
        sa.Column("modelo_ap", sa.String(length=120), nullable=False),
        sa.Column("pct_cobertura_actual", sa.Float(), nullable=False),
        sa.Column("pct_cobertura", sa.Float(), nullable=False),
        sa.Column("costo_estimado", sa.Float(), nullable=False),
        sa.Column("cantidad_aps", sa.Integer(), nullable=False),
        sa.Column("resumen", sa.Text(), nullable=False),
        sa.Column("restricciones", sa.JSON(), nullable=False),
        sa.Column("metricas", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["mapa_actual_id"], ["mapa_calor.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mapa_proyectado_id"], ["mapa_calor.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plano_id"], ["plano.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["proyecto_id"], ["proyecto.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_escenario_optimizado_id"), "escenario_optimizado", ["id"], unique=False)
    op.create_index(op.f("ix_escenario_optimizado_mapa_actual_id"), "escenario_optimizado", ["mapa_actual_id"], unique=False)
    op.create_index(op.f("ix_escenario_optimizado_mapa_proyectado_id"), "escenario_optimizado", ["mapa_proyectado_id"], unique=False)
    op.create_index(op.f("ix_escenario_optimizado_plano_id"), "escenario_optimizado", ["plano_id"], unique=False)
    op.create_index(op.f("ix_escenario_optimizado_proyecto_id"), "escenario_optimizado", ["proyecto_id"], unique=False)

    op.create_table(
        "recomendacion_ap",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("escenario_id", sa.Integer(), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("accion", sa.String(length=30), nullable=False),
        sa.Column("coord_x", sa.Float(), nullable=False),
        sa.Column("coord_y", sa.Float(), nullable=False),
        sa.Column("banda", sa.String(length=10), nullable=False),
        sa.Column("modelo_ap", sa.String(length=120), nullable=False),
        sa.Column("costo_estimado", sa.Float(), nullable=False),
        sa.Column("rssi_proyectado", sa.Float(), nullable=False),
        sa.Column("justificacion", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["escenario_id"], ["escenario_optimizado.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recomendacion_ap_escenario_id"), "recomendacion_ap", ["escenario_id"], unique=False)
    op.create_index(op.f("ix_recomendacion_ap_id"), "recomendacion_ap", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recomendacion_ap_id"), table_name="recomendacion_ap")
    op.drop_index(op.f("ix_recomendacion_ap_escenario_id"), table_name="recomendacion_ap")
    op.drop_table("recomendacion_ap")
    op.drop_index(op.f("ix_escenario_optimizado_proyecto_id"), table_name="escenario_optimizado")
    op.drop_index(op.f("ix_escenario_optimizado_plano_id"), table_name="escenario_optimizado")
    op.drop_index(op.f("ix_escenario_optimizado_mapa_proyectado_id"), table_name="escenario_optimizado")
    op.drop_index(op.f("ix_escenario_optimizado_mapa_actual_id"), table_name="escenario_optimizado")
    op.drop_index(op.f("ix_escenario_optimizado_id"), table_name="escenario_optimizado")
    op.drop_table("escenario_optimizado")
