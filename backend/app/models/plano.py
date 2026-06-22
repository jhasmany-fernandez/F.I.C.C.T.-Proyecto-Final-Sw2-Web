"""Modelo ORM para planos de edificio.

Sprint 2 — PB-02 (Importar Plano), PB-11 (Calibrar Escala).
Un proyecto puede tener múltiples planos (por locación, piso o zona).
"""

import sqlalchemy as sa
from sqlalchemy import (
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

# Formatos soportados (PNG/JPG/PDF de la primera página).
formato_plano_enum = sa.Enum(
    "png",
    "jpg",
    "pdf",
    name="formato_plano",
    create_type=False,
)


class Plano(Base):
    """Plano del edificio asociado a un proyecto.

    El archivo binario se guarda en ``storage`` (filesystem o S3) y la BD
    persiste sólo metadatos + ruta + (opcional) parámetros de calibración.
    """

    __tablename__ = "plano"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre = Column(String(255), nullable=False)
    formato = Column(formato_plano_enum, nullable=False)
    ruta_storage = Column(String(500), nullable=False, unique=True)
    ancho_px = Column(Integer, nullable=False)
    alto_px = Column(Integer, nullable=False)
    tamano_bytes = Column(Integer, nullable=False)

    # Calibración (PB-11) — todos los campos son nullable hasta que se calibre.
    calibracion_x1 = Column(Float, nullable=True)
    calibracion_y1 = Column(Float, nullable=True)
    calibracion_x2 = Column(Float, nullable=True)
    calibracion_y2 = Column(Float, nullable=True)
    distancia_real_m = Column(Float, nullable=True)
    escala_m_por_px = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    proyecto = relationship("Proyecto", back_populates="planos")
    puntos_medicion = relationship(
        "PuntoMedicion",
        back_populates="plano",
        cascade="all, delete-orphan",
    )
    mapas_calor = relationship(
        "MapaCalor",
        back_populates="plano",
        cascade="all, delete-orphan",
    )
    conjuntos_ap = relationship(
        "ConjuntoAP",
        back_populates="plano",
        cascade="all, delete-orphan",
    )
    aps_fisicos = relationship(
        "APFisico",
        back_populates="plano",
        cascade="all, delete-orphan",
    )

    @property
    def calibrado(self) -> bool:
        return self.escala_m_por_px is not None
