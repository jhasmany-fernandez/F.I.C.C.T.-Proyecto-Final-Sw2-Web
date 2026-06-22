from sqlalchemy import Boolean, Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Usuario(Base):
    """Modelo ORM para la entidad usuario. PB-13 / PB-09 — Sprint 1."""

    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    # Roles válidos: tecnico | admin
    rol = Column(String(30), nullable=False, server_default="tecnico")
    activo = Column(Boolean, nullable=False, server_default="true")
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones — definidas aquí para evitar importaciones circulares
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    proyectos = relationship(
        "Proyecto",
        back_populates="tecnico",
        lazy="dynamic",
    )
    dispositivos_push = relationship(
        "DispositivoPush",
        back_populates="usuario",
        cascade="all, delete-orphan",
    )
