"""Modelo ORM para la entidad Cliente.

Sprint 1 — PB-19: catálogo de clientes gestionado por el administrador.
Los técnicos seleccionan el cliente al crear/editar un proyecto.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    activo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    proyectos = relationship("Proyecto", back_populates="cliente")
