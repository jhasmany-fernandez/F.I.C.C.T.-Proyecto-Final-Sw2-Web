"""sp3_mediciones

Sprint 3 — PB-03 (Captura WiFi en línea), PB-04 (Marcar puntos de medición).
Crea las tablas ``punto_medicion`` y ``medicion_wifi`` con relaciones
en cascada desde ``plano``.

Revision ID: c3d4e5f6a7b8
Revises: a1b2c3d4e5f6
Create Date: 2026-05-21 08:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Valores de nivel de señal (umbrales CWNA-107)
_NIVEL_VALUES = ("verde", "amarillo", "naranja", "rojo", "negro")


def upgrade() -> None:
    nivel_enum = postgresql.ENUM(
        *_NIVEL_VALUES,
        name="nivel_senal",
        create_type=False,
    )
    nivel_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "punto_medicion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plano_id",
            sa.Integer(),
            sa.ForeignKey("plano.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pos_x", sa.Float(), nullable=False),
        sa.Column("pos_y", sa.Float(), nullable=False),
        sa.Column(
            "nivel",
            postgresql.ENUM(*_NIVEL_VALUES, name="nivel_senal", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_punto_medicion_plano_id", "punto_medicion", ["plano_id"])

    op.create_table(
        "medicion_wifi",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "punto_id",
            sa.Integer(),
            sa.ForeignKey("punto_medicion.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ssid", sa.String(length=255), nullable=False),
        sa.Column("bssid", sa.String(length=17), nullable=False),
        sa.Column("rssi", sa.Integer(), nullable=False),
        sa.Column("canal", sa.Integer(), nullable=True),
        sa.Column("frecuencia_mhz", sa.Integer(), nullable=True),
        sa.Column(
            "nivel",
            postgresql.ENUM(*_NIVEL_VALUES, name="nivel_senal", create_type=False),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_medicion_wifi_punto_id", "medicion_wifi", ["punto_id"])


def downgrade() -> None:
    op.drop_index("ix_medicion_wifi_punto_id", table_name="medicion_wifi")
    op.drop_table("medicion_wifi")
    op.drop_index("ix_punto_medicion_plano_id", table_name="punto_medicion")
    op.drop_table("punto_medicion")
    op.execute("DROP TYPE IF EXISTS nivel_senal")
