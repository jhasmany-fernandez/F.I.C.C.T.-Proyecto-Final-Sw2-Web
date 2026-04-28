from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UsuarioCreate(BaseModel):
    """DTO para crear un nuevo usuario. PB-13 (CA-1, CA-3)."""

    nombre: str
    email: EmailStr
    password: str
    rol: str = "tecnico"

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str) -> str:
        if v not in ("tecnico", "admin"):
            raise ValueError("Rol inválido; debe ser 'tecnico' o 'admin'")
        return v


class UsuarioOut(BaseModel):
    """DTO de salida para un usuario (nunca expone password_hash). PB-13 (CA-5)."""

    id: int
    nombre: str
    email: EmailStr
    rol: str
    activo: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UsuarioUpdate(BaseModel):
    """DTO para editar un usuario: datos personales, estado o contraseña. PB-13 (Sp1-06)."""

    nombre: str | None = None
    email: EmailStr | None = None
    rol: str | None = None
    activo: bool | None = None
    password: str | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v

    @field_validator("rol")
    @classmethod
    def rol_valido(cls, v: str | None) -> str | None:
        if v is not None and v not in ("tecnico", "admin"):
            raise ValueError("Rol inválido; debe ser 'tecnico' o 'admin'")
        return v
