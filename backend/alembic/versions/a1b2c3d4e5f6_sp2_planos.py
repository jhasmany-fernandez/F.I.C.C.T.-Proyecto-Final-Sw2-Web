"""sp2_planos

Sprint 2 — PB-02 (Importar Plano), PB-11 (Calibrar Escala).
Crea la tabla ``plano`` con relación a ``proyecto`` (cascade).

Revision ID: a1b2c3d4e5f6
Revises: b1c2d3e4f5a6
Create Date: 2026-05-15 22:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    formato_enum = postgresql.ENUM(
        "png", "jpg", "pdf", name="formato_plano", create_type=False
    )
    formato_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "plano",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "proyecto_id",
            sa.Integer(),
            sa.ForeignKey("proyecto.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=255), nullable=False),
        sa.Column("formato", formato_enum, nullable=False),
        sa.Column("ruta_storage", sa.String(length=500), nullable=False, unique=True),
        sa.Column("ancho_px", sa.Integer(), nullable=False),
        sa.Column("alto_px", sa.Integer(), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("calibracion_x1", sa.Float(), nullable=True),
        sa.Column("calibracion_y1", sa.Float(), nullable=True),
        sa.Column("calibracion_x2", sa.Float(), nullable=True),
        sa.Column("calibracion_y2", sa.Float(), nullable=True),
        sa.Column("distancia_real_m", sa.Float(), nullable=True),
        sa.Column("escala_m_por_px", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_plano_proyecto_id", "plano", ["proyecto_id"])


def downgrade() -> None:
    op.drop_index("ix_plano_proyecto_id", table_name="plano")
    op.drop_table("plano")
    sa.Enum(name="formato_plano").drop(op.get_bind(), checkfirst=True)
