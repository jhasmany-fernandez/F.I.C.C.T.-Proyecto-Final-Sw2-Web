"""Inventario físico y configuración RF para optimización de cobertura."""

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class APFisico(Base):
    """Equipo físico instalado, temporal o candidato dentro de un plano."""

    __tablename__ = "ap_fisico"

    id = Column(Integer, primary_key=True, index=True)
    plano_id = Column(
        Integer, ForeignKey("plano.id", ondelete="CASCADE"), nullable=False, index=True
    )
    nombre = Column(String(100), nullable=False)
    fabricante = Column(String(100), nullable=False)
    modelo = Column(String(120), nullable=False)
    rol = Column(String(20), nullable=False, default="EXISTENTE")
    restriccion_movimiento = Column(String(20), nullable=False, default="MOVIBLE")
    coord_x = Column(Float, nullable=False)
    coord_y = Column(Float, nullable=False)
    altura_m = Column(Float, nullable=False, default=2.5)
    tipo_montaje = Column(String(30), nullable=False, default="TECHO")
    costo_referencial = Column(Float, nullable=True)
    procedencia = Column(String(30), nullable=False, default="INGRESADA_TECNICO")
    verificado = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    plano = relationship("Plano", back_populates="aps_fisicos")
    radios = relationship(
        "RadioAP",
        back_populates="ap_fisico",
        cascade="all, delete-orphan",
        order_by="RadioAP.banda.asc()",
    )


class RadioAP(Base):
    """Radio configurable de un AP físico, con antena y límites normalizados."""

    __tablename__ = "radio_ap"

    id = Column(Integer, primary_key=True, index=True)
    ap_fisico_id = Column(
        Integer,
        ForeignKey("ap_fisico.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    banda = Column(String(10), nullable=False)
    habilitada = Column(Boolean, nullable=False, default=True)
    canal = Column(Integer, nullable=False)
    ancho_canal_mhz = Column(Integer, nullable=False, default=20)
    potencia_original = Column(Float, nullable=False)
    unidad_potencia_original = Column(String(10), nullable=False, default="DBM")
    referencia_potencia = Column(String(15), nullable=False, default="IR")
    potencia_dbm = Column(Float, nullable=False)
    potencia_max_dbm = Column(Float, nullable=False)
    modo_gestion_rf = Column(String(15), nullable=False, default="ESTATICO")
    dfs_permitido = Column(Boolean, nullable=False, default=False)
    dominio_regulatorio = Column(String(10), nullable=False, default="BO")
    tipo_antena = Column(String(30), nullable=False, default="OMNIDIRECCIONAL")
    modelo_antena = Column(String(120), nullable=True)
    ganancia_dbi = Column(Float, nullable=False, default=2.14)
    beamwidth_horizontal = Column(Float, nullable=False, default=360.0)
    beamwidth_vertical = Column(Float, nullable=False, default=60.0)
    azimut_grados = Column(Float, nullable=False, default=0.0)
    inclinacion_grados = Column(Float, nullable=False, default=0.0)
    perdida_cable_db = Column(Float, nullable=False, default=0.0)
    procedencia = Column(String(30), nullable=False, default="INGRESADA_TECNICO")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ap_fisico = relationship("APFisico", back_populates="radios")
    bssids = relationship(
        "BSSIDRadio",
        back_populates="radio",
        cascade="all, delete-orphan",
        order_by="BSSIDRadio.bssid.asc()",
    )

    __table_args__ = (
        sa.UniqueConstraint("ap_fisico_id", "banda", name="uq_radio_ap_banda"),
    )

    @property
    def eirp_dbm(self) -> float:
        return round(self.potencia_dbm + self.ganancia_dbi - self.perdida_cable_db, 2)


class BSSIDRadio(Base):
    """BSSID observado o declarado que pertenece a una radio."""

    __tablename__ = "bssid_radio"

    id = Column(Integer, primary_key=True, index=True)
    radio_id = Column(
        Integer,
        ForeignKey("radio_ap.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bssid = Column(String(17), nullable=False, unique=True, index=True)
    ssid = Column(String(255), nullable=False)
    observado = Column(Boolean, nullable=False, default=True)
    procedencia = Column(String(30), nullable=False, default="DETECTADA_ANDROID")

    radio = relationship("RadioAP", back_populates="bssids")


class InstantaneaConfiguracionRF(Base):
    """Configuración inmutable que contextualiza una captura WiFi."""

    __tablename__ = "instantanea_configuracion_rf"

    id = Column(Integer, primary_key=True, index=True)
    radio_id = Column(
        Integer,
        ForeignKey("radio_ap.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    datos = Column(sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False)
    procedencia = Column(String(30), nullable=False)
    completitud = Column(Float, nullable=False)
    capturada_en = Column(DateTime(timezone=True), server_default=func.now())
