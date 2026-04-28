"""Modelo ORM para proyectos de relevamiento WiFi.

Sprint 1 — PB-18 (listado para el admin panel).
Sprint 1 — PB-19: se agrega FK cliente_id (tabla cliente).
El modelo se expande en Sprint 2 (PB-01/PB-10) con planos y mediciones.
"""

import sqlalchemy as sa
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base

# Tipo ENUM PostgreSQL para el campo estado de proyecto.
# Valores: nuevo | en_progreso | completado | archivado
# Referencia UML: «enumeration» EstadoProyecto — guia-staruml-modelos-navegables.md
estado_proyecto_enum = sa.Enum(
    "nuevo",
    "en_progreso",
    "completado",
    "archivado",
    name="estado_proyecto",
)


class Proyecto(Base):
    __tablename__ = "proyecto"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(String(500), nullable=True)
    cliente_id = Column(
        Integer,
        ForeignKey("cliente.id"),
        nullable=True,
        index=True,
    )
    estado = Column(estado_proyecto_enum, nullable=False, server_default="nuevo")
    tecnico_id = Column(
        Integer,
        ForeignKey("usuario.id"),
        nullable=False,
        index=True,
    )
    ultima_actividad = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    cantidad_puntos = Column(Integer, nullable=False, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tecnico = relationship("Usuario", back_populates="proyectos")
    cliente = relationship("Cliente", back_populates="proyectos")
