"""Modelos ORM del módulo de heatmap y análisis.

Sprint 4 — PB-05 (Generar mapa de calor), PB-06 (Analizar cobertura).
"""

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class MapaCalor(Base):
    """Resultado de interpolación generado desde las mediciones de un plano."""

    __tablename__ = "mapa_calor"

    id = Column(Integer, primary_key=True, index=True)
    plano_id = Column(
        Integer,
        ForeignKey("plano.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conjunto_ap_id = Column(
        Integer,
        ForeignKey("conjunto_ap.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    algoritmo = Column(String(20), nullable=False, default="IDW")
    resolucion = Column(Integer, nullable=False, default=128)
    modo_generacion = Column(String(20), nullable=False, default="SUBCONJUNTO")
    bssid = Column(String(17), nullable=False)
    ssid = Column(String(255), nullable=False)
    ap_pos_x = Column(Float, nullable=False)
    ap_pos_y = Column(Float, nullable=False)
    aps_interes = Column(sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=True)
    bssids_generacion = Column(
        sa.JSON().with_variant(sa.JSON, "sqlite"),
        nullable=True,
    )
    matriz = Column(sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False)
    escala = Column(sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False)
    ruta_imagen = Column(String(500), nullable=False, unique=True)
    cantidad_puntos = Column(Integer, nullable=False)
    rssi_min = Column(Float, nullable=False)
    rssi_max = Column(Float, nullable=False)
    firma_mediciones = Column(String(120), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    plano = relationship("Plano", back_populates="mapas_calor")
    conjunto_ap = relationship("ConjuntoAP", back_populates="mapas_calor")
    analisis = relationship(
        "AnalisisCobertura",
        back_populates="mapa",
        cascade="all, delete-orphan",
        uselist=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "plano_id",
            "algoritmo",
            "resolucion",
            "firma_mediciones",
            name="uq_mapa_calor_cache",
        ),
        {"sqlite_autoincrement": True},
    )


class ConjuntoAP(Base):
    """Conjunto persistente de APs con propósito dentro de un plano."""

    __tablename__ = "conjunto_ap"

    id = Column(Integer, primary_key=True, index=True)
    plano_id = Column(
        Integer,
        ForeignKey("plano.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre = Column(String(100), nullable=False)
    proposito = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    es_principal = Column(Boolean, nullable=False, default=False)
    origen = Column(String(30), nullable=False, default="manual_movil", index=True)
    estado_gobernanza = Column(
        String(30), nullable=False, default="borrador_tecnico", index=True
    )
    creado_por_id = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    plano = relationship("Plano", back_populates="conjuntos_ap")
    creado_por = relationship("Usuario")
    items = relationship(
        "ConjuntoAPItem",
        back_populates="conjunto",
        cascade="all, delete-orphan",
        order_by="ConjuntoAPItem.id.asc()",
    )
    mapas_calor = relationship("MapaCalor", back_populates="conjunto_ap")

    __table_args__ = (
        UniqueConstraint(
            "plano_id",
            "nombre",
            name="uq_conjunto_ap_plano_nombre",
        ),
        {"sqlite_autoincrement": True},
    )


class ConjuntoAPItem(Base):
    """AP incluido en un conjunto, con snapshot de datos al momento de guardar."""

    __tablename__ = "conjunto_ap_item"

    id = Column(Integer, primary_key=True, index=True)
    conjunto_ap_id = Column(
        Integer,
        ForeignKey("conjunto_ap.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bssid = Column(String(17), nullable=False, index=True)
    ssid_snapshot = Column(String(255), nullable=True)
    canal_snapshot = Column(Integer, nullable=True)
    rssi_promedio_snapshot = Column(Float, nullable=True)
    pos_x = Column(Float, nullable=True)
    pos_y = Column(Float, nullable=True)

    conjunto = relationship("ConjuntoAP", back_populates="items")

    __table_args__ = (
        UniqueConstraint(
            "conjunto_ap_id",
            "bssid",
            name="uq_conjunto_ap_item_bssid",
        ),
        {"sqlite_autoincrement": True},
    )


class AnalisisCobertura(Base):
    """Diagnóstico automático generado a partir de un mapa de calor."""

    __tablename__ = "analisis_cobertura"

    id = Column(Integer, primary_key=True, index=True)
    mapa_calor_id = Column(
        Integer,
        ForeignKey("mapa_calor.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    pct_cobertura = Column(Float, nullable=False)
    pct_zonas_muertas = Column(Float, nullable=False)
    celdas_zonas_muertas = Column(Integer, nullable=False)
    cantidad_solapamientos = Column(Integer, nullable=False)
    cantidad_interferencias = Column(Integer, nullable=False)
    hallazgos = Column(sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False)
    resumen = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    mapa = relationship("MapaCalor", back_populates="analisis")
    aps_detectados = relationship(
        "APDetectado",
        back_populates="analisis",
        cascade="all, delete-orphan",
        order_by="APDetectado.rssi_promedio.desc()",
    )


class APDetectado(Base):
    """Access point detectado durante el relevamiento de un plano."""

    __tablename__ = "ap_detectado"

    id = Column(Integer, primary_key=True, index=True)
    analisis_id = Column(
        Integer,
        ForeignKey("analisis_cobertura.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bssid = Column(String(17), nullable=False)
    ssid = Column(String(255), nullable=False)
    canal = Column(Integer, nullable=True)
    frecuencia_mhz = Column(Integer, nullable=True)
    rssi_promedio = Column(Float, nullable=False)
    pos_x = Column(Float, nullable=False)
    pos_y = Column(Float, nullable=False)
    confirmado = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    analisis = relationship("AnalisisCobertura", back_populates="aps_detectados")
