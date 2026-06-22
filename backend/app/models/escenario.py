"""Modelos ORM de Sprint 5: IA, escenarios y reportes.

PB-07, PB-12 y PB-08 implementan optimización IA, comparación de escenarios
y reportes PDF persistidos en el backend.
"""

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class EscenarioOptimizado(Base):
    """Alternativa de red propuesta por el optimizador de APs."""

    __tablename__ = "escenario_optimizado"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plano_id = Column(
        Integer,
        ForeignKey("plano.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mapa_actual_id = Column(
        Integer,
        ForeignKey("mapa_calor.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    mapa_proyectado_id = Column(
        Integer,
        ForeignKey("mapa_calor.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    conjunto_base_id = Column(
        Integer,
        ForeignKey("conjunto_ap.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    origen = Column(String(30), nullable=False, default="ia")
    estado_gobernanza = Column(
        String(30), nullable=False, default="pendiente_revision", index=True
    )
    generado_por_id = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    aprobado_por_id = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    publicado_por_id = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    aprobado_at = Column(DateTime(timezone=True), nullable=True)
    publicado_at = Column(DateTime(timezone=True), nullable=True)
    nombre = Column(String(120), nullable=False)
    tipo_negocio = Column(String(30), nullable=False, default="INSTALACION_NUEVA")
    perfil = Column(String(40), nullable=False, default="COBERTURA_EQUILIBRADA")
    politica_combinacion = Column(
        String(50),
        nullable=False,
        default="PREFERIR_5_GHZ_SI_CUMPLE_UMBRAL",
    )
    banda = Column(String(10), nullable=False, default="5")
    bandas = Column(
        sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False, default=list
    )
    modelo_ap = Column(String(120), nullable=False)
    pct_cobertura_actual = Column(Float, nullable=False, default=0)
    pct_cobertura = Column(Float, nullable=False)
    costo_estimado = Column(Float, nullable=False, default=0)
    cantidad_aps = Column(Integer, nullable=False)
    resumen = Column(Text, nullable=False)
    restricciones = Column(sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False)
    metricas = Column(sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False)
    mapas_por_banda = Column(
        sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False, default=dict
    )
    mapas_actuales_por_banda = Column(
        sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False, default=dict
    )
    supuestos = Column(
        sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False, default=list
    )
    confianza = Column(String(15), nullable=False, default="MEDIA")
    version_motor = Column(String(30), nullable=False, default="rf-hibrido-1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    proyecto = relationship("Proyecto", back_populates="escenarios")
    plano = relationship("Plano")
    mapa_actual = relationship("MapaCalor", foreign_keys=[mapa_actual_id])
    mapa_proyectado = relationship("MapaCalor", foreign_keys=[mapa_proyectado_id])
    recomendaciones = relationship(
        "RecomendacionAP",
        back_populates="escenario",
        cascade="all, delete-orphan",
        order_by="RecomendacionAP.orden.asc()",
    )
    valores_proyectados = relationship(
        "ValorProyectadoPunto",
        back_populates="escenario",
        cascade="all, delete-orphan",
        order_by="ValorProyectadoPunto.punto_medicion_id.asc()",
    )


class RecomendacionAP(Base):
    """Acción sugerida sobre un AP para mejorar la cobertura."""

    __tablename__ = "recomendacion_ap"

    id = Column(Integer, primary_key=True, index=True)
    escenario_id = Column(
        Integer,
        ForeignKey("escenario_optimizado.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    orden = Column(Integer, nullable=False, default=1)
    ap_fisico_id = Column(
        Integer,
        ForeignKey("ap_fisico.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    accion = Column(String(30), nullable=False)
    coord_x = Column(Float, nullable=False)
    coord_y = Column(Float, nullable=False)
    altura_m = Column(Float, nullable=False, default=2.5)
    tipo_montaje = Column(String(30), nullable=False, default="TECHO")
    banda = Column(String(10), nullable=False, default="5")
    modelo_ap = Column(String(120), nullable=False)
    costo_estimado = Column(Float, nullable=False, default=0)
    rssi_proyectado = Column(Float, nullable=False)
    radios = Column(
        sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False, default=list
    )
    justificacion = Column(Text, nullable=False)

    escenario = relationship("EscenarioOptimizado", back_populates="recomendaciones")


class ValorProyectadoPunto(Base):
    """Predicción por escenario, punto real y banda; no altera la medición."""

    __tablename__ = "valor_proyectado_punto"

    id = Column(Integer, primary_key=True, index=True)
    escenario_id = Column(
        Integer,
        ForeignKey("escenario_optimizado.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    punto_medicion_id = Column(
        Integer,
        ForeignKey("punto_medicion.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    banda = Column(String(10), nullable=False)
    rssi_observado_dbm = Column(Float, nullable=True)
    rssi_proyectado_dbm = Column(Float, nullable=False)
    diferencia_db = Column(Float, nullable=True)
    radio_primaria = Column(String(80), nullable=False)
    radio_secundaria = Column(String(80), nullable=True)
    rssi_secundario_dbm = Column(Float, nullable=True)
    snr_proyectado_db = Column(Float, nullable=True)
    incertidumbre_db = Column(Float, nullable=False, default=6.0)

    escenario = relationship(
        "EscenarioOptimizado", back_populates="valores_proyectados"
    )

    __table_args__ = (
        sa.UniqueConstraint(
            "escenario_id",
            "punto_medicion_id",
            "banda",
            name="uq_valor_proyectado_escenario_punto_banda",
        ),
    )


class Reporte(Base):
    """Reporte técnico PDF generado para un proyecto."""

    __tablename__ = "reporte"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyecto.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    escenario_id = Column(
        Integer,
        ForeignKey("escenario_optimizado.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    estado = Column(String(20), nullable=False, default="LISTO")
    ruta_pdf = Column(String(500), nullable=True, unique=True)
    sha256 = Column(String(64), nullable=True)
    tamanio_bytes = Column(Integer, nullable=False, default=0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    proyecto = relationship("Proyecto", back_populates="reportes")
    escenario = relationship("EscenarioOptimizado")
