"""Inventario RF, configuración por radio y valores proyectados.

Revision ID: f3a4b5c6d7e8
Revises: e2f3a4b5c6d7
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f3a4b5c6d7e8"
down_revision: str | None = "e2f3a4b5c6d7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ap_fisico",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plano_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("fabricante", sa.String(100), nullable=False),
        sa.Column("modelo", sa.String(120), nullable=False),
        sa.Column("rol", sa.String(20), nullable=False, server_default="EXISTENTE"),
        sa.Column(
            "restriccion_movimiento",
            sa.String(20),
            nullable=False,
            server_default="MOVIBLE",
        ),
        sa.Column("coord_x", sa.Float(), nullable=False),
        sa.Column("coord_y", sa.Float(), nullable=False),
        sa.Column("altura_m", sa.Float(), nullable=False, server_default="2.5"),
        sa.Column(
            "tipo_montaje", sa.String(30), nullable=False, server_default="TECHO"
        ),
        sa.Column("costo_referencial", sa.Float(), nullable=True),
        sa.Column(
            "procedencia",
            sa.String(30),
            nullable=False,
            server_default="INGRESADA_TECNICO",
        ),
        sa.Column(
            "verificado", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["plano_id"], ["plano.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ap_fisico_plano_id", "ap_fisico", ["plano_id"])
    op.create_table(
        "radio_ap",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ap_fisico_id", sa.Integer(), nullable=False),
        sa.Column("banda", sa.String(10), nullable=False),
        sa.Column("habilitada", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("canal", sa.Integer(), nullable=False),
        sa.Column("ancho_canal_mhz", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("potencia_original", sa.Float(), nullable=False),
        sa.Column("unidad_potencia_original", sa.String(10), nullable=False),
        sa.Column("referencia_potencia", sa.String(15), nullable=False),
        sa.Column("potencia_dbm", sa.Float(), nullable=False),
        sa.Column("potencia_max_dbm", sa.Float(), nullable=False),
        sa.Column("modo_gestion_rf", sa.String(15), nullable=False),
        sa.Column(
            "dfs_permitido", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "dominio_regulatorio", sa.String(10), nullable=False, server_default="BO"
        ),
        sa.Column("tipo_antena", sa.String(30), nullable=False),
        sa.Column("modelo_antena", sa.String(120), nullable=True),
        sa.Column("ganancia_dbi", sa.Float(), nullable=False),
        sa.Column("beamwidth_horizontal", sa.Float(), nullable=False),
        sa.Column("beamwidth_vertical", sa.Float(), nullable=False),
        sa.Column("azimut_grados", sa.Float(), nullable=False),
        sa.Column("inclinacion_grados", sa.Float(), nullable=False),
        sa.Column("perdida_cable_db", sa.Float(), nullable=False),
        sa.Column("procedencia", sa.String(30), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["ap_fisico_id"], ["ap_fisico.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("ap_fisico_id", "banda", name="uq_radio_ap_banda"),
    )
    op.create_index("ix_radio_ap_ap_fisico_id", "radio_ap", ["ap_fisico_id"])
    op.create_table(
        "bssid_radio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("radio_id", sa.Integer(), nullable=False),
        sa.Column("bssid", sa.String(17), nullable=False),
        sa.Column("ssid", sa.String(255), nullable=False),
        sa.Column("observado", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("procedencia", sa.String(30), nullable=False),
        sa.ForeignKeyConstraint(["radio_id"], ["radio_ap.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("bssid"),
    )
    op.create_index("ix_bssid_radio_radio_id", "bssid_radio", ["radio_id"])
    op.create_index("ix_bssid_radio_bssid", "bssid_radio", ["bssid"])
    op.create_table(
        "instantanea_configuracion_rf",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("radio_id", sa.Integer(), nullable=True),
        sa.Column("datos", sa.JSON(), nullable=False),
        sa.Column("procedencia", sa.String(30), nullable=False),
        sa.Column("completitud", sa.Float(), nullable=False),
        sa.Column(
            "capturada_en", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["radio_id"], ["radio_ap.id"], ondelete="SET NULL"),
    )
    op.add_column(
        "medicion_wifi", sa.Column("instantanea_rf_id", sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        "fk_medicion_wifi_instantanea_rf",
        "medicion_wifi",
        "instantanea_configuracion_rf",
        ["instantanea_rf_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_medicion_wifi_instantanea_rf_id", "medicion_wifi", ["instantanea_rf_id"]
    )

    for nombre, tipo, defecto in (
        ("tipo_negocio", sa.String(30), "INSTALACION_NUEVA"),
        ("perfil", sa.String(40), "COBERTURA_EQUILIBRADA"),
        ("politica_combinacion", sa.String(50), "PREFERIR_5_GHZ_SI_CUMPLE_UMBRAL"),
        ("confianza", sa.String(15), "MEDIA"),
        ("version_motor", sa.String(30), "rf-hibrido-1.0"),
    ):
        op.add_column(
            "escenario_optimizado",
            sa.Column(nombre, tipo, nullable=False, server_default=defecto),
        )
    op.add_column(
        "escenario_optimizado",
        sa.Column("bandas", sa.JSON(), nullable=False, server_default='["2.4", "5"]'),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column("mapas_por_banda", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "escenario_optimizado",
        sa.Column("supuestos", sa.JSON(), nullable=False, server_default="[]"),
    )

    op.add_column(
        "recomendacion_ap", sa.Column("ap_fisico_id", sa.Integer(), nullable=True)
    )
    op.add_column(
        "recomendacion_ap",
        sa.Column("altura_m", sa.Float(), nullable=False, server_default="2.5"),
    )
    op.add_column(
        "recomendacion_ap",
        sa.Column(
            "tipo_montaje", sa.String(30), nullable=False, server_default="TECHO"
        ),
    )
    op.add_column(
        "recomendacion_ap",
        sa.Column("radios", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.create_foreign_key(
        "fk_recomendacion_ap_ap_fisico",
        "recomendacion_ap",
        "ap_fisico",
        ["ap_fisico_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_recomendacion_ap_ap_fisico_id", "recomendacion_ap", ["ap_fisico_id"]
    )

    op.create_table(
        "valor_proyectado_punto",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("escenario_id", sa.Integer(), nullable=False),
        sa.Column("punto_medicion_id", sa.Integer(), nullable=False),
        sa.Column("banda", sa.String(10), nullable=False),
        sa.Column("rssi_observado_dbm", sa.Float(), nullable=True),
        sa.Column("rssi_proyectado_dbm", sa.Float(), nullable=False),
        sa.Column("diferencia_db", sa.Float(), nullable=True),
        sa.Column("radio_primaria", sa.String(80), nullable=False),
        sa.Column("radio_secundaria", sa.String(80), nullable=True),
        sa.Column("rssi_secundario_dbm", sa.Float(), nullable=True),
        sa.Column("snr_proyectado_db", sa.Float(), nullable=True),
        sa.Column("incertidumbre_db", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["escenario_id"], ["escenario_optimizado.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["punto_medicion_id"], ["punto_medicion.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "escenario_id",
            "punto_medicion_id",
            "banda",
            name="uq_valor_proyectado_escenario_punto_banda",
        ),
    )
    op.create_index(
        "ix_valor_proyectado_escenario_id", "valor_proyectado_punto", ["escenario_id"]
    )
    op.create_index(
        "ix_valor_proyectado_punto_medicion_id",
        "valor_proyectado_punto",
        ["punto_medicion_id"],
    )


def downgrade() -> None:
    op.drop_table("valor_proyectado_punto")
    op.drop_column("recomendacion_ap", "radios")
    op.drop_column("recomendacion_ap", "tipo_montaje")
    op.drop_column("recomendacion_ap", "altura_m")
    op.drop_column("recomendacion_ap", "ap_fisico_id")
    for nombre in (
        "supuestos",
        "mapas_por_banda",
        "bandas",
        "version_motor",
        "confianza",
        "politica_combinacion",
        "perfil",
        "tipo_negocio",
    ):
        op.drop_column("escenario_optimizado", nombre)
    op.drop_column("medicion_wifi", "instantanea_rf_id")
    op.drop_table("instantanea_configuracion_rf")
    op.drop_table("bssid_radio")
    op.drop_table("radio_ap")
    op.drop_table("ap_fisico")
