"""sp4_heatmap_y_analisis

Sprint 4 — PB-05 (mapa_calor) y PB-06 (analisis_cobertura, ap_detectado).

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e6f7a8b9c0d1"
down_revision: Union[str, None] = "d5e6f7a8b9c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _json_type():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "mapa_calor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plano_id",
            sa.Integer(),
            sa.ForeignKey("plano.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("algoritmo", sa.String(length=20), nullable=False),
        sa.Column("resolucion", sa.Integer(), nullable=False),
        sa.Column("matriz", _json_type(), nullable=False),
        sa.Column("escala", _json_type(), nullable=False),
        sa.Column("ruta_imagen", sa.String(length=500), nullable=False, unique=True),
        sa.Column("cantidad_puntos", sa.Integer(), nullable=False),
        sa.Column("rssi_min", sa.Float(), nullable=False),
        sa.Column("rssi_max", sa.Float(), nullable=False),
        sa.Column("firma_mediciones", sa.String(length=120), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "plano_id",
            "algoritmo",
            "resolucion",
            "firma_mediciones",
            name="uq_mapa_calor_cache",
        ),
    )
    op.create_index("ix_mapa_calor_plano_id", "mapa_calor", ["plano_id"])

    op.create_table(
        "analisis_cobertura",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "mapa_calor_id",
            sa.Integer(),
            sa.ForeignKey("mapa_calor.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("pct_cobertura", sa.Float(), nullable=False),
        sa.Column("pct_zonas_muertas", sa.Float(), nullable=False),
        sa.Column("celdas_zonas_muertas", sa.Integer(), nullable=False),
        sa.Column("cantidad_solapamientos", sa.Integer(), nullable=False),
        sa.Column("cantidad_interferencias", sa.Integer(), nullable=False),
        sa.Column("hallazgos", _json_type(), nullable=False),
        sa.Column("resumen", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_analisis_cobertura_mapa_calor_id",
        "analisis_cobertura",
        ["mapa_calor_id"],
    )

    op.create_table(
        "ap_detectado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "analisis_id",
            sa.Integer(),
            sa.ForeignKey("analisis_cobertura.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bssid", sa.String(length=17), nullable=False),
        sa.Column("ssid", sa.String(length=255), nullable=False),
        sa.Column("canal", sa.Integer(), nullable=True),
        sa.Column("frecuencia_mhz", sa.Integer(), nullable=True),
        sa.Column("rssi_promedio", sa.Float(), nullable=False),
        sa.Column("pos_x", sa.Float(), nullable=False),
        sa.Column("pos_y", sa.Float(), nullable=False),
        sa.Column("confirmado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ap_detectado_analisis_id", "ap_detectado", ["analisis_id"])


def downgrade() -> None:
    op.drop_index("ix_ap_detectado_analisis_id", table_name="ap_detectado")
    op.drop_table("ap_detectado")
    op.drop_index(
        "ix_analisis_cobertura_mapa_calor_id",
        table_name="analisis_cobertura",
    )
    op.drop_table("analisis_cobertura")
    op.drop_index("ix_mapa_calor_plano_id", table_name="mapa_calor")
    op.drop_table("mapa_calor")
