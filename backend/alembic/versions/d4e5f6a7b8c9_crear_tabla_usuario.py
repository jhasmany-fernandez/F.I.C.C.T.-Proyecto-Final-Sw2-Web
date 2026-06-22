"""crear_tabla_usuario

Revision ID: d4e5f6a7b8c9
Revises: a3d77185c343
Create Date: 2026-04-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "073ed4d23a33"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("rol", sa.String(length=30), nullable=False, server_default="tecnico"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_usuario_id"), "usuario", ["id"], unique=False)
    op.create_index(op.f("ix_usuario_email"), "usuario", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_usuario_email"), table_name="usuario")
    op.drop_index(op.f("ix_usuario_id"), table_name="usuario")
    op.drop_table("usuario")
