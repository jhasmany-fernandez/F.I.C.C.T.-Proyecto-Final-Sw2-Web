"""sp4_heatmap_por_ap

Ajusta PB-05 para generar mapas de calor por AP de interés:
el heatmap queda asociado a un BSSID/SSID y a la ubicación del AP sobre el plano.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-06-15 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "e6f7a8b9c0d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "mapa_calor",
        sa.Column("bssid", sa.String(length=17), nullable=False, server_default=""),
    )
    op.add_column(
        "mapa_calor",
        sa.Column("ssid", sa.String(length=255), nullable=False, server_default=""),
    )
    op.add_column(
        "mapa_calor",
        sa.Column("ap_pos_x", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "mapa_calor",
        sa.Column("ap_pos_y", sa.Float(), nullable=False, server_default="0"),
    )
    op.alter_column("mapa_calor", "bssid", server_default=None)
    op.alter_column("mapa_calor", "ssid", server_default=None)
    op.alter_column("mapa_calor", "ap_pos_x", server_default=None)
    op.alter_column("mapa_calor", "ap_pos_y", server_default=None)


def downgrade() -> None:
    op.drop_column("mapa_calor", "ap_pos_y")
    op.drop_column("mapa_calor", "ap_pos_x")
    op.drop_column("mapa_calor", "ssid")
    op.drop_column("mapa_calor", "bssid")
