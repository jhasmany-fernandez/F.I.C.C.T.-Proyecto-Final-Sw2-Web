"""Dispositivos habilitados para recibir notificaciones push por FCM."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class DispositivoPush(Base):
    __tablename__ = "dispositivo_push"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(512), unique=True, nullable=False)
    plataforma = Column(String(20), nullable=False, server_default="android")
    activo = Column(Boolean, nullable=False, server_default="true", index=True)
    ultimo_registro = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    usuario = relationship("Usuario", back_populates="dispositivos_push")
