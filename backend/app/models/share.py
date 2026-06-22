"""Modelos ORM para enlaces públicos de cliente.

Sprint 6 — PB-15/PB-16/PB-17.
"""

import sqlalchemy as sa
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class TokenEnlaceCliente(Base):
    """Enlace público, revocable y acotado a contenido seleccionado."""

    __tablename__ = "token_enlace_cliente"

    id = Column(Integer, primary_key=True, index=True)
    proyecto_id = Column(
        Integer,
        ForeignKey("proyecto.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(160), nullable=False, unique=True, index=True)
    contenido = Column(sa.JSON().with_variant(sa.JSON, "sqlite"), nullable=False)
    expira_en = Column(DateTime(timezone=True), nullable=False, index=True)
    revocado = Column(Boolean, nullable=False, server_default=sa.false(), index=True)
    creado_por_id = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    accesos = Column(Integer, nullable=False, server_default="0")
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    ip_ultimo_acceso = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    proyecto = relationship("Proyecto", back_populates="enlaces_cliente")
    creado_por = relationship("Usuario")
