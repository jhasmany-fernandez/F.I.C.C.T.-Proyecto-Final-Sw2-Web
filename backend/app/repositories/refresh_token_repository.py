"""Repositorio de acceso a datos para refresh tokens.

PB-09 — Sprint 1 (Sp1-13 / Sp1-15): login, logout y refresh de sesión.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def crear(self, usuario_id: int) -> str:
        """Genera y persiste un nuevo refresh token. Retorna el valor del token."""
        token_value = RefreshToken.generate_token()
        expires_at = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_days
        )
        record = RefreshToken(
            token=token_value,
            usuario_id=usuario_id,
            expires_at=expires_at,
        )
        self._db.add(record)
        self._db.commit()
        return token_value

    def obtener(self, token_value: str) -> RefreshToken | None:
        return (
            self._db.query(RefreshToken)
            .filter(RefreshToken.token == token_value)
            .first()
        )

    def revocar(self, token_value: str) -> bool:
        """Elimina el token. Retorna True si existía, False si no."""
        record = self.obtener(token_value)
        if record is None:
            return False
        self._db.delete(record)
        self._db.commit()
        return True

    def revocar_todos_del_usuario(self, usuario_id: int) -> None:
        """Revoca todos los refresh tokens de un usuario (ej. al desactivarlo)."""
        self._db.query(RefreshToken).filter(
            RefreshToken.usuario_id == usuario_id
        ).delete()
        self._db.commit()
