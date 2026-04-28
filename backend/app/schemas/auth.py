from pydantic import BaseModel, EmailStr

from app.schemas.usuario import UsuarioOut


class LoginRequest(BaseModel):
    """Credenciales de inicio de sesión. PB-09 (CA-1, CA-2)."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Respuesta completa de login: tokens + perfil del usuario. PB-09."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class RefreshRequest(BaseModel):
    """Request para renovar el access_token. PB-09 (AuthInterceptor)."""

    refresh_token: str


class AccessTokenResponse(BaseModel):
    """Respuesta del endpoint /auth/refresh. PB-09."""

    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    """Request para revocar el refresh_token activo. PB-09 (CA-4)."""

    refresh_token: str
