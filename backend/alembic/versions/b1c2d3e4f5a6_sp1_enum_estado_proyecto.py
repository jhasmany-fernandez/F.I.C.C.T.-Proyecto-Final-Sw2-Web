"""Sp1: convertir proyecto.estado de VARCHAR(30) a tipo ENUM estado_proyecto.

Revision ID: b1c2d3e4f5a6
Revises: 83b6c2b1a08c
Create Date: 2026-04-27
Sprint 1 — PB-01 / PB-10 / PB-18 — alineación con UML EstadoProyecto

Valores del ENUM: nuevo | en_progreso | completado | archivado
Nuevo server_default: 'nuevo' (antes era 'en_progreso').

Orden de operaciones (upgrade):
  1. Crear tipo ENUM 'estado_proyecto' en PostgreSQL.
  2. Normalizar valores existentes no contemplados en el ENUM (salvaguarda).
  3. Alterar columna proyecto.estado a usar el nuevo tipo ENUM.
  4. Cambiar server_default a 'nuevo'.

Orden de operaciones (downgrade):
  1. Alterar columna de vuelta a VARCHAR(30) con server_default 'en_progreso'.
  2. Eliminar tipo ENUM 'estado_proyecto'.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: Union[str, None] = "83b6c2b1a08c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Tipo ENUM que se creará en PostgreSQL
estado_proyecto = sa.Enum(
    "nuevo",
    "en_progreso",
    "completado",
    "archivado",
    name="estado_proyecto",
)


def upgrade() -> None:
    # 1. Crear el tipo ENUM en PostgreSQL
    estado_proyecto.create(op.get_bind(), checkfirst=True)

    # 2. Normalizar filas con valores no válidos hacia 'en_progreso' (salvaguarda)
    #    (en producción no debería haber ninguno, pero es seguro hacerlo)
    op.execute(
        sa.text(
            """
            UPDATE proyecto
            SET estado = 'en_progreso'
            WHERE estado NOT IN ('nuevo', 'en_progreso', 'completado', 'archivado')
            """
        )
    )

    # 3. Quitar el default anterior para que PostgreSQL no intente
    #    castear automaticamente el literal al nuevo tipo ENUM.
    op.execute(
        sa.text(
            "ALTER TABLE proyecto ALTER COLUMN estado DROP DEFAULT"
        )
    )

    # 4. Alterar la columna de VARCHAR(30) al tipo ENUM usando USING
    op.execute(
        sa.text(
            """
            ALTER TABLE proyecto
            ALTER COLUMN estado TYPE estado_proyecto
            USING estado::estado_proyecto
            """
        )
    )

    # 5. Actualizar el server_default a 'nuevo'
    op.execute(
        sa.text(
            "ALTER TABLE proyecto ALTER COLUMN estado SET DEFAULT 'nuevo'"
        )
    )


def downgrade() -> None:
    # 1. Quitar el default ENUM antes de volver a VARCHAR.
    op.execute(
        sa.text(
            "ALTER TABLE proyecto ALTER COLUMN estado DROP DEFAULT"
        )
    )

    # 2. Revertir la columna a VARCHAR(30) con server_default 'en_progreso'
    op.execute(
        sa.text(
            """
            ALTER TABLE proyecto
            ALTER COLUMN estado TYPE VARCHAR(30)
            USING estado::VARCHAR
            """
        )
    )
    op.execute(
        sa.text(
            "ALTER TABLE proyecto ALTER COLUMN estado SET DEFAULT 'en_progreso'"
        )
    )

    # 3. Eliminar el tipo ENUM
    estado_proyecto.drop(op.get_bind(), checkfirst=True)
