"""Endpoints de proyectos para el técnico autenticado.

PB-09 — Sprint 1: pantalla inicial «Mis Proyectos» de la app móvil.
PB-01 — Sprint 1: CRUD completo de proyectos (crear, editar, archivar, eliminar).
Tags OpenAPI: proyectos
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.repositories.proyecto_repository import ProyectoRepository
from app.schemas.proyecto import ProyectoIn, ProyectoTecnicoOut

router = APIRouter(prefix="/proyectos", tags=["proyectos"])


@router.get(
    "",
    response_model=list[ProyectoTecnicoOut],
    summary="Listar mis proyectos",
    description=(
        "Retorna los proyectos activos del técnico autenticado, ordenados por "
        "última actividad descendente. Sin filtro de estado excluye los archivados. "
        "PB-09 — CA-1."
    ),
)
def listar_mis_proyectos(
    estado: str | None = Query(
        default=None,
        description="Filtrar por estado (en_progreso, completado, archivado)",
    ),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[ProyectoTecnicoOut]:
    repo = ProyectoRepository(db)
    proyectos = repo.listar_por_tecnico(
        tecnico_id=current_user.id,
        estado=estado,
    )
    return [ProyectoTecnicoOut.from_proyecto(p) for p in proyectos]


@router.post(
    "",
    response_model=ProyectoTecnicoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear proyecto",
    description="Crea un nuevo proyecto de survey para el técnico autenticado. PB-01 — CA-1.",
)
def crear_proyecto(
    body: ProyectoIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ProyectoTecnicoOut:
    repo = ProyectoRepository(db)
    proyecto = repo.crear(
        nombre=body.nombre,
        tecnico_id=current_user.id,
        cliente_id=body.cliente_id,
        descripcion=body.descripcion,
    )
    return ProyectoTecnicoOut.from_proyecto(proyecto)


@router.put(
    "/{proyecto_id}",
    response_model=ProyectoTecnicoOut,
    summary="Actualizar proyecto",
    description="Actualiza nombre, cliente y descripción de un proyecto propio. PB-01 — CA-2.",
)
def actualizar_proyecto(
    proyecto_id: int,
    body: ProyectoIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ProyectoTecnicoOut:
    repo = ProyectoRepository(db)
    proyecto = repo.obtener_por_id(proyecto_id=proyecto_id, tecnico_id=current_user.id)
    if proyecto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
    proyecto = repo.actualizar(
        proyecto=proyecto,
        nombre=body.nombre,
        cliente_id=body.cliente_id,
        descripcion=body.descripcion,
    )
    return ProyectoTecnicoOut.from_proyecto(proyecto)


@router.patch(
    "/{proyecto_id}/archivar",
    response_model=ProyectoTecnicoOut,
    summary="Archivar proyecto",
    description="Cambia el estado del proyecto a 'archivado'. PB-01 — CA-3.",
)
def archivar_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ProyectoTecnicoOut:
    repo = ProyectoRepository(db)
    proyecto = repo.obtener_por_id(proyecto_id=proyecto_id, tecnico_id=current_user.id)
    if proyecto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
    proyecto = repo.archivar(proyecto=proyecto)
    return ProyectoTecnicoOut.from_proyecto(proyecto)


@router.delete(
    "/{proyecto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar proyecto",
    description="Elimina permanentemente el proyecto y todos sus datos. PB-01 — CA-4.",
)
def eliminar_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    repo = ProyectoRepository(db)
    proyecto = repo.obtener_por_id(proyecto_id=proyecto_id, tecnico_id=current_user.id)
    if proyecto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proyecto no encontrado.")
    repo.eliminar(proyecto=proyecto)
