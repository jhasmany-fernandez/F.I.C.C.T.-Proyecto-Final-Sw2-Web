"""Gobernanza para escenarios IA.

Revision ID: a5b6c7d8e9f0
Revises: a4b5c6d7e8f9
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a5b6c7d8e9f0"
down_revision: str | None = "a4b5c6d7e8f9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "escenario_optimizado",
        sa.Column("conjunto_base_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column("origen", sa.String(30), nullable=False, server_default="ia"),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column(
            "estado_gobernanza",
            sa.String(30),
            nullable=False,
            server_default="pendiente_revision",
        ),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column("generado_por_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column("aprobado_por_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column("publicado_por_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column("aprobado_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column("publicado_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_escenario_conjunto_base",
        "escenario_optimizado",
        "conjunto_ap",
        ["conjunto_base_id"],
        ["id"],
        ondelete="SET NULL",
    )
    for columna in (
        "conjunto_base_id",
        "estado_gobernanza",
        "generado_por_id",
        "aprobado_por_id",
        "publicado_por_id",
    ):
        op.create_index(
            f"ix_escenario_optimizado_{columna}",
            "escenario_optimizado",
            [columna],
        )
    for columna, nombre_fk in (
        ("generado_por_id", "fk_escenario_generado_por"),
        ("aprobado_por_id", "fk_escenario_aprobado_por"),
        ("publicado_por_id", "fk_escenario_publicado_por"),
    ):
        op.create_foreign_key(
            nombre_fk,
            "escenario_optimizado",
            "usuario",
            [columna],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    for nombre_fk in (
        "fk_escenario_publicado_por",
        "fk_escenario_aprobado_por",
        "fk_escenario_generado_por",
        "fk_escenario_conjunto_base",
    ):
        op.drop_constraint(nombre_fk, "escenario_optimizado", type_="foreignkey")
    for columna in (
        "publicado_por_id",
        "aprobado_por_id",
        "generado_por_id",
        "estado_gobernanza",
        "conjunto_base_id",
    ):
        op.drop_index(f"ix_escenario_optimizado_{columna}", table_name="escenario_optimizado")
    for columna in (
        "publicado_at",
        "aprobado_at",
        "publicado_por_id",
        "aprobado_por_id",
        "generado_por_id",
        "estado_gobernanza",
        "origen",
        "conjunto_base_id",
    ):
        op.drop_column("escenario_optimizado", columna)
