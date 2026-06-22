"""Endpoints de supervisión de proyectos para el panel admin.

PB-18 — Sprint 1 (Sp1-23): listado paginado y filtrado.
PB-18 — Sprint 1 (Sp1-51..Sp1-52): archivar y reasignar técnico (acciones admin).
Tags OpenAPI: admin/proyectos
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.usuario import Usuario
from app.repositories.proyecto_repository import ProyectoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.proyecto import ProyectoListOut, ProyectosPageOut

router = APIRouter(prefix="/admin/proyectos", tags=["admin/proyectos"])


class ReasignarTecnicoIn(BaseModel):
    """DTO de entrada para reasignar un proyecto a otro técnico. PB-18."""

    tecnico_id: int


@router.patch(
    "/{proyecto_id}/archivar",
    response_model=ProyectoListOut,
    summary="Archivar proyecto (admin)",
    description="El administrador archiva cualquier proyecto de la organización. PB-18.",
)
def archivar_proyecto_admin(
    proyecto_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> ProyectoListOut:
    repo = ProyectoRepository(db)
    proyecto = repo.obtener_por_id_admin(proyecto_id=proyecto_id)
    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado."
        )
    if proyecto.estado == "archivado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El proyecto ya está archivado.",
        )
    proyecto = repo.archivar(proyecto=proyecto)
    return ProyectoListOut.model_validate(proyecto)


@router.patch(
    "/{proyecto_id}/reasignar",
    response_model=ProyectoListOut,
    summary="Reasignar técnico (admin)",
    description="El administrador reasigna el proyecto a otro técnico activo. PB-18.",
)
def reasignar_tecnico(
    proyecto_id: int,
    body: ReasignarTecnicoIn,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> ProyectoListOut:
    repo_proyecto = ProyectoRepository(db)
    repo_usuario = UsuarioRepository(db)

    proyecto = repo_proyecto.obtener_por_id_admin(proyecto_id=proyecto_id)
    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado."
        )

    nuevo_tecnico = repo_usuario.obtener_por_id(body.tecnico_id)
    if nuevo_tecnico is None or not nuevo_tecnico.activo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El técnico indicado no existe o está inactivo.",
        )

    proyecto = repo_proyecto.reasignar_tecnico(
        proyecto=proyecto, nuevo_tecnico_id=body.tecnico_id
    )
    return ProyectoListOut.model_validate(proyecto)


@router.get(
    "",
    response_model=ProyectosPageOut,
    summary="Listar proyectos de la organización",
    description="Lista todos los proyectos de todos los técnicos con paginación y filtros. "
    "Solo rol ADMIN. PB-18 — CA-1, CA-2, CA-3, CA-5.",
)
def listar_proyectos(
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Ítems por página"),
    tecnico_id: int | None = Query(default=None, description="Filtrar por técnico"),
    estado: str | None = Query(default=None, description="Filtrar por estado"),
    fecha_desde: date | None = Query(
        default=None, description="Filtrar desde esta fecha"
    ),
    fecha_hasta: date | None = Query(
        default=None, description="Filtrar hasta esta fecha"
    ),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> ProyectosPageOut:
    repo = ProyectoRepository(db)
    items, total = repo.listar_paginado(
        page=page,
        page_size=page_size,
        tecnico_id=tecnico_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return ProyectosPageOut(
        items=items,  # type: ignore[arg-type]
        total=total,
        page=page,
        page_size=page_size,
    )
