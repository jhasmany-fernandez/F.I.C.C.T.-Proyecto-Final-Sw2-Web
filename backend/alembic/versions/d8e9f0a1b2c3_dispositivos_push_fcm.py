"""Dispositivos habilitados para notificaciones FCM.

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8e9f0a1b2c3"
down_revision: str | None = "c7d8e9f0a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "dispositivo_push",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(512), nullable=False),
        sa.Column("plataforma", sa.String(20), nullable=False, server_default="android"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "ultimo_registro",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token", name="uq_dispositivo_push_token"),
    )
    op.create_index("ix_dispositivo_push_usuario_id", "dispositivo_push", ["usuario_id"])
    op.create_index("ix_dispositivo_push_activo", "dispositivo_push", ["activo"])


def downgrade() -> None:
    op.drop_index("ix_dispositivo_push_activo", table_name="dispositivo_push")
    op.drop_index("ix_dispositivo_push_usuario_id", table_name="dispositivo_push")
    op.drop_table("dispositivo_push")
