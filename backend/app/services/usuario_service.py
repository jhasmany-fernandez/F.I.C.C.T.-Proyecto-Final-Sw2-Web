"""Servicio de gestión de usuarios (panel admin).

PB-13 — Sprint 1 (Sp1-05, Sp1-06).
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate


class UsuarioService:
    def __init__(self, db: Session) -> None:
        self._repo = UsuarioRepository(db)
        self._token_repo = RefreshTokenRepository(db)

    def crear(self, datos: UsuarioCreate) -> UsuarioOut:
        """Crea un nuevo usuario. PB-13 (CA-1, CA-3)."""
        existente = self._repo.obtener_por_email(datos.email)
        if existente is not None:
            # CA-3: 409 Conflict con mensaje claro
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El email '{datos.email}' ya está registrado",
            )
        usuario = self._repo.crear(
            nombre=datos.nombre,
            email=datos.email,
            password_hash=hash_password(datos.password),
            rol=datos.rol,
        )
        return UsuarioOut.model_validate(usuario)

    def listar(self, solo_activos: bool = False) -> list[UsuarioOut]:
        """Lista todos los usuarios del sistema."""
        usuarios = self._repo.listar(solo_activos=solo_activos)
        return [UsuarioOut.model_validate(u) for u in usuarios]

    def actualizar(self, usuario_id: int, datos: UsuarioUpdate) -> UsuarioOut:
        """Edita datos personales, estado o contraseña. PB-13 (CA-2, Sp1-06)."""
        usuario = self._repo.obtener_por_id(usuario_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado",
            )

        if datos.nombre is not None:
            usuario.nombre = datos.nombre

        if datos.email is not None:
            existente = self._repo.obtener_por_email(datos.email)
            if existente is not None and existente.id != usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El email '{datos.email}' ya está registrado",
                )
            usuario.email = datos.email

        if datos.rol is not None:
            usuario.rol = datos.rol

        if datos.activo is not None:
            usuario.activo = datos.activo
            # CA-2: desactivar invalida los tokens activos en el siguiente request
            if not datos.activo:
                self._token_repo.revocar_todos_del_usuario(usuario_id)

        if datos.password is not None:
            usuario.password_hash = hash_password(datos.password)

        usuario = self._repo.guardar(usuario)
        return UsuarioOut.model_validate(usuario)
