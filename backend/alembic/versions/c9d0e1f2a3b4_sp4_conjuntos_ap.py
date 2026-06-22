"""sp4 conjuntos ap

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06-19 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _json_type():
    return postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite")


def upgrade() -> None:
    op.create_table(
        "conjunto_ap",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "plano_id",
            sa.Integer(),
            sa.ForeignKey("plano.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("proposito", sa.String(length=255), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("es_principal", sa.Boolean(), nullable=False, server_default=sa.false()),
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
        sa.UniqueConstraint(
            "plano_id",
            "nombre",
            name="uq_conjunto_ap_plano_nombre",
        ),
    )
    op.create_index("ix_conjunto_ap_plano_id", "conjunto_ap", ["plano_id"])
    op.create_index(
        "ix_conjunto_ap_plano_updated",
        "conjunto_ap",
        ["plano_id", "updated_at"],
    )

    op.create_table(
        "conjunto_ap_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "conjunto_ap_id",
            sa.Integer(),
            sa.ForeignKey("conjunto_ap.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("bssid", sa.String(length=17), nullable=False),
        sa.Column("ssid_snapshot", sa.String(length=255), nullable=True),
        sa.Column("canal_snapshot", sa.Integer(), nullable=True),
        sa.Column("rssi_promedio_snapshot", sa.Float(), nullable=True),
        sa.UniqueConstraint(
            "conjunto_ap_id",
            "bssid",
            name="uq_conjunto_ap_item_bssid",
        ),
    )
    op.create_index(
        "ix_conjunto_ap_item_conjunto_ap_id",
        "conjunto_ap_item",
        ["conjunto_ap_id"],
    )
    op.create_index("ix_conjunto_ap_item_bssid", "conjunto_ap_item", ["bssid"])

    op.add_column(
        "mapa_calor",
        sa.Column("conjunto_ap_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "mapa_calor",
        sa.Column(
            "modo_generacion",
            sa.String(length=20),
            nullable=False,
            server_default="SUBCONJUNTO",
        ),
    )
    op.add_column(
        "mapa_calor",
        sa.Column("bssids_generacion", _json_type(), nullable=True),
    )
    op.create_foreign_key(
        "fk_mapa_calor_conjunto_ap_id",
        "mapa_calor",
        "conjunto_ap",
        ["conjunto_ap_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_mapa_calor_conjunto_ap_id",
        "mapa_calor",
        ["conjunto_ap_id"],
    )
    op.alter_column("mapa_calor", "modo_generacion", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_mapa_calor_conjunto_ap_id", table_name="mapa_calor")
    op.drop_constraint(
        "fk_mapa_calor_conjunto_ap_id",
        "mapa_calor",
        type_="foreignkey",
    )
    op.drop_column("mapa_calor", "bssids_generacion")
    op.drop_column("mapa_calor", "modo_generacion")
    op.drop_column("mapa_calor", "conjunto_ap_id")
    op.drop_index("ix_conjunto_ap_item_bssid", table_name="conjunto_ap_item")
    op.drop_index(
        "ix_conjunto_ap_item_conjunto_ap_id",
        table_name="conjunto_ap_item",
    )
    op.drop_table("conjunto_ap_item")
    op.drop_index("ix_conjunto_ap_plano_updated", table_name="conjunto_ap")
    op.drop_index("ix_conjunto_ap_plano_id", table_name="conjunto_ap")
    op.drop_table("conjunto_ap")
