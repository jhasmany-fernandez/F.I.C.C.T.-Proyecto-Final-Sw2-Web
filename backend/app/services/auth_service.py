"""Servicio de autenticación: login, refresh y logout.

PB-09 — Sprint 1 (Sp1-04, Sp1-13, Sp1-14, Sp1-15).
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import (
    AccessTokenResponse,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.schemas.usuario import UsuarioOut


class AuthService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._usuario_repo = UsuarioRepository(db)
        self._token_repo = RefreshTokenRepository(db)

    def login(self, email: str, password: str) -> TokenResponse:
        """Valida credenciales y emite access + refresh tokens. PB-09 (CA-1, CA-2, CA-3)."""
        usuario = self._usuario_repo.obtener_por_email(email)

        # CA-2: mismo error para email o contraseña incorrectos (no revelar qué falló)
        if usuario is None or not verify_password(password, usuario.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
            )

        # CA: cuenta desactivada → 403
        if not usuario.activo:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta desactivada",
            )

        # Actualizar último acceso (diagrama de secuencia PB-09)
        usuario.ultimo_acceso = datetime.now(UTC)
        self._db.commit()

        access_token = create_access_token({"sub": str(usuario.id)})
        refresh_token = self._token_repo.crear(usuario.id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            usuario=UsuarioOut.model_validate(usuario),
        )

    def refresh(self, request: RefreshRequest) -> AccessTokenResponse:
        """Renueva el access_token dado un refresh_token válido. PB-09 (Sp1-14)."""
        record = self._token_repo.obtener(request.refresh_token)
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido o revocado",
            )

        # Normalizar timezone para comparación (SQLite no guarda tzinfo)
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at < datetime.now(UTC):
            self._token_repo.revocar(request.refresh_token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expirado",
            )

        access_token = create_access_token({"sub": str(record.usuario_id)})
        return AccessTokenResponse(access_token=access_token)

    def logout(self, request: LogoutRequest) -> None:
        """Revoca el refresh_token activo. Operación idempotente. PB-09 (CA-4)."""
        self._token_repo.revocar(request.refresh_token)
