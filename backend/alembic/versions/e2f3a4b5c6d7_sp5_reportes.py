"""Sprint 5: reportes PDF.

Revision ID: e2f3a4b5c6d7
Revises: e1f2a3b4c5d6
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2f3a4b5c6d7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reporte",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("proyecto_id", sa.Integer(), nullable=False),
        sa.Column("escenario_id", sa.Integer(), nullable=True),
        sa.Column("estado", sa.String(length=20), nullable=False),
        sa.Column("ruta_pdf", sa.String(length=500), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("tamanio_bytes", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(["escenario_id"], ["escenario_optimizado.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["proyecto_id"], ["proyecto.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ruta_pdf"),
    )
    op.create_index(op.f("ix_reporte_escenario_id"), "reporte", ["escenario_id"], unique=False)
    op.create_index(op.f("ix_reporte_id"), "reporte", ["id"], unique=False)
    op.create_index(op.f("ix_reporte_proyecto_id"), "reporte", ["proyecto_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reporte_proyecto_id"), table_name="reporte")
    op.drop_index(op.f("ix_reporte_id"), table_name="reporte")
    op.drop_index(op.f("ix_reporte_escenario_id"), table_name="reporte")
    op.drop_table("reporte")
