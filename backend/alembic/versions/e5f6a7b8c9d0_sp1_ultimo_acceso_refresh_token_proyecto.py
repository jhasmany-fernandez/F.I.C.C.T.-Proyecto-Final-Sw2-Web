"""Sp1-01 revisado: agrega ultimo_acceso a usuario + tablas refresh_token y proyecto.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-24
Sprint 1 — PB-09 (refresh tokens), PB-13 (ultimo_acceso), PB-18 (proyectos)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Agregar ultimo_acceso a la tabla usuario (Sp1-01)
    op.add_column(
        "usuario",
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Tabla refresh_token (Sp1-13/15)
    op.create_table(
        "refresh_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_refresh_token_id"), "refresh_token", ["id"], unique=False)
    op.create_index(
        op.f("ix_refresh_token_token"), "refresh_token", ["token"], unique=True
    )
    op.create_index(
        op.f("ix_refresh_token_usuario_id"),
        "refresh_token",
        ["usuario_id"],
        unique=False,
    )

    # 3. Tabla proyecto (Sp1-23 — stub Sprint 1, se expande en Sprint 2)
    op.create_table(
        "proyecto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=200), nullable=False),
        sa.Column("cliente", sa.String(length=200), nullable=True),
        sa.Column(
            "estado",
            sa.String(length=30),
            nullable=False,
            server_default="en_progreso",
        ),
        sa.Column("tecnico_id", sa.Integer(), nullable=False),
        sa.Column(
            "ultima_actividad",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "cantidad_puntos",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["tecnico_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_proyecto_id"), "proyecto", ["id"], unique=False)
    op.create_index(
        op.f("ix_proyecto_tecnico_id"), "proyecto", ["tecnico_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_proyecto_tecnico_id"), table_name="proyecto")
    op.drop_index(op.f("ix_proyecto_id"), table_name="proyecto")
    op.drop_table("proyecto")

    op.drop_index(op.f("ix_refresh_token_usuario_id"), table_name="refresh_token")
    op.drop_index(op.f("ix_refresh_token_token"), table_name="refresh_token")
    op.drop_index(op.f("ix_refresh_token_id"), table_name="refresh_token")
    op.drop_table("refresh_token")

    op.drop_column("usuario", "ultimo_acceso")
