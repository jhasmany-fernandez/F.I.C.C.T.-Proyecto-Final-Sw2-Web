"""Sp1-29: crear tabla cliente y migrar proyecto.cliente → proyecto.cliente_id (FK).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-24
Sprint 1 — PB-19 (catálogo de clientes gestionado por el admin)

Orden de operaciones:
  1. Crear tabla `cliente`.
  2. Insertar filas únicas de cliente desde los valores de texto existentes
     en proyecto.cliente (migración de datos).
  3. Agregar columna proyecto.cliente_id (nullable).
  4. Actualizar proyecto.cliente_id haciendo match por nombre.
  5. Crear índice en proyecto.cliente_id.
  6. Eliminar columna proyecto.cliente (texto libre).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Crear tabla cliente
    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column(
            "activo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_index(op.f("ix_cliente_id"), "cliente", ["id"], unique=False)

    # 2. Migrar datos: insertar clientes únicos desde proyecto.cliente (texto)
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            INSERT INTO cliente (nombre)
            SELECT DISTINCT TRIM(cliente)
            FROM proyecto
            WHERE cliente IS NOT NULL AND TRIM(cliente) <> ''
            ON CONFLICT (nombre) DO NOTHING
            """
        )
    )

    # 3. Agregar columna cliente_id (nullable, sin FK todavía)
    op.add_column(
        "proyecto",
        sa.Column("cliente_id", sa.Integer(), nullable=True),
    )

    # 4. Actualizar cliente_id haciendo join por nombre
    bind.execute(
        sa.text(
            """
            UPDATE proyecto p
            SET cliente_id = c.id
            FROM cliente c
            WHERE TRIM(p.cliente) = c.nombre
            """
        )
    )

    # 5. Crear FK e índice
    op.create_foreign_key(
        "fk_proyecto_cliente_id",
        "proyecto",
        "cliente",
        ["cliente_id"],
        ["id"],
    )
    op.create_index(
        op.f("ix_proyecto_cliente_id"),
        "proyecto",
        ["cliente_id"],
        unique=False,
    )

    # 6. Eliminar la columna texto cliente
    op.drop_column("proyecto", "cliente")


def downgrade() -> None:
    # Restaurar columna texto cliente
    op.add_column(
        "proyecto",
        sa.Column("cliente", sa.String(length=200), nullable=True),
    )

    # Recuperar nombres desde la FK
    bind = op.get_bind()
    bind.execute(
        sa.text(
            """
            UPDATE proyecto p
            SET cliente = c.nombre
            FROM cliente c
            WHERE p.cliente_id = c.id
            """
        )
    )

    # Eliminar FK e índice
    op.drop_index(op.f("ix_proyecto_cliente_id"), table_name="proyecto")
    op.drop_constraint("fk_proyecto_cliente_id", "proyecto", type_="foreignkey")
    op.drop_column("proyecto", "cliente_id")

    # Eliminar tabla cliente
    op.drop_index(op.f("ix_cliente_id"), table_name="cliente")
    op.drop_table("cliente")
