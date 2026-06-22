"""Token de enlace público para cliente.

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7d8e9f0a1b2"
down_revision: str | None = "b6c7d8e9f0a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "token_enlace_cliente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proyecto_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(160), nullable=False),
        sa.Column("contenido", sa.JSON(), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_por_id", sa.Integer(), nullable=True),
        sa.Column("accesos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_ultimo_acceso", sa.String(80), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["proyecto_id"], ["proyecto.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creado_por_id"], ["usuario.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("token", name="uq_token_enlace_cliente_token"),
    )
    op.create_index(
        "ix_token_enlace_cliente_proyecto_id",
        "token_enlace_cliente",
        ["proyecto_id"],
    )
    op.create_index("ix_token_enlace_cliente_token", "token_enlace_cliente", ["token"])
    op.create_index(
        "ix_token_enlace_cliente_expira_en",
        "token_enlace_cliente",
        ["expira_en"],
    )
    op.create_index(
        "ix_token_enlace_cliente_revocado",
        "token_enlace_cliente",
        ["revocado"],
    )
    op.create_index(
        "ix_token_enlace_cliente_creado_por_id",
        "token_enlace_cliente",
        ["creado_por_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_token_enlace_cliente_creado_por_id",
        table_name="token_enlace_cliente",
    )
    op.drop_index(
        "ix_token_enlace_cliente_revocado",
        table_name="token_enlace_cliente",
    )
    op.drop_index(
        "ix_token_enlace_cliente_expira_en",
        table_name="token_enlace_cliente",
    )
    op.drop_index("ix_token_enlace_cliente_token", table_name="token_enlace_cliente")
    op.drop_index(
        "ix_token_enlace_cliente_proyecto_id",
        table_name="token_enlace_cliente",
    )
    op.drop_table("token_enlace_cliente")
