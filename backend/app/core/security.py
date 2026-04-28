"""Utilidades de seguridad: hashing de contraseñas y JWT.

PB-09, PB-13 — Sprint 1
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

if TYPE_CHECKING:
    from app.models.usuario import Usuario

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """Devuelve el hash bcrypt de *password*."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica que *plain* coincide con el hash almacenado *hashed*."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Genera un JWT de acceso con expiración corta (por defecto ACCESS_TOKEN_EXPIRE_MINUTES)."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def _decode_token_raw(token: str) -> dict[str, Any]:
    """Decodifica un JWT; lanza JWTError si es inválido (uso interno)."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> "Usuario":
    """Dependencia FastAPI: valida el Bearer JWT y retorna el usuario activo."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = _decode_token_raw(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    # Import tardío para evitar ciclos de importación
    from app.models.usuario import Usuario  # noqa: PLC0415

    user: Usuario | None = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if user is None:
        raise credentials_exc
    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )
    return user


def require_admin(
    current_user: "Usuario" = Depends(get_current_user),
) -> "Usuario":
    """Dependencia FastAPI: exige que el usuario tenga rol 'admin'."""
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido al rol admin",
        )
    return current_user
