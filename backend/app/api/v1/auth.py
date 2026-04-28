"""Endpoints de autenticación: login, refresh y logout.

PB-09 — Sprint 1 (Sp1-13, Sp1-14, Sp1-15).
Tags OpenAPI: auth
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Iniciar sesión",
    description="Valida email y contraseña. Retorna access_token (15 min) + refresh_token (7 días). "
    "PB-09 — CA-1, CA-2, CA-3.",
)
def login(
    body: LoginRequest,
    service: AuthService = Depends(_get_service),
) -> TokenResponse:
    return service.login(body.email, body.password)


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Renovar access token",
    description="Dado un refresh_token válido, emite un nuevo access_token. PB-09.",
)
def refresh(
    body: RefreshRequest,
    service: AuthService = Depends(_get_service),
) -> AccessTokenResponse:
    return service.refresh(body)


@router.post(
    "/logout",
    status_code=204,
    summary="Cerrar sesión",
    description="Revoca el refresh_token activo. PB-09 — CA-4.",
)
def logout(
    body: LogoutRequest,
    service: AuthService = Depends(_get_service),
) -> None:
    service.logout(body)
