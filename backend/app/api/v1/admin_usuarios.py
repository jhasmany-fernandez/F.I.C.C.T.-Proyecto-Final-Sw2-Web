"""Endpoints de gestión de usuarios para el panel admin.

PB-13 — Sprint 1 (Sp1-05, Sp1-06).
Tags OpenAPI: admin/usuarios
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/admin/usuarios", tags=["admin/usuarios"])


def _get_service(db: Session = Depends(get_db)) -> UsuarioService:
    return UsuarioService(db)


@router.post(
    "",
    response_model=UsuarioOut,
    status_code=201,
    summary="Crear usuario",
    description="Crea una cuenta de técnico o admin. Solo accesible por rol ADMIN. "
    "PB-13 — CA-1, CA-3, CA-4, CA-5.",
)
def crear_usuario(
    body: UsuarioCreate,
    service: UsuarioService = Depends(_get_service),
    _admin: Usuario = Depends(require_admin),
) -> UsuarioOut:
    return service.crear(body)


@router.get(
    "",
    response_model=list[UsuarioOut],
    summary="Listar usuarios",
    description="Lista todos los usuarios del sistema. Solo accesible por rol ADMIN. PB-13.",
)
def listar_usuarios(
    solo_activos: bool = False,
    service: UsuarioService = Depends(_get_service),
    _admin: Usuario = Depends(require_admin),
) -> list[UsuarioOut]:
    return service.listar(solo_activos=solo_activos)


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioOut,
    summary="Actualizar usuario",
    description="Activa/desactiva usuario o resetea su contraseña. Solo rol ADMIN. "
    "PB-13 — CA-2 (desactivar invalida tokens).",
)
def actualizar_usuario(
    usuario_id: int,
    body: UsuarioUpdate,
    service: UsuarioService = Depends(_get_service),
    _admin: Usuario = Depends(require_admin),
) -> UsuarioOut:
    return service.actualizar(usuario_id, body)
