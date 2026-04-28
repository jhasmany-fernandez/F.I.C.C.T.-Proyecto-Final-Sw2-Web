"""Modelo ORM para refresh tokens.

Sprint 1 — PB-09 (CA-4: logout revoca refresh token).
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id = Column(Integer, primary_key=True, index=True)
    # UUID4 generado en Python; almacenado como string (36 chars)
    token = Column(String(64), unique=True, nullable=False, index=True)
    usuario_id = Column(
        Integer,
        ForeignKey("usuario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="refresh_tokens")

    @staticmethod
    def generate_token() -> str:
        return str(uuid.uuid4())
