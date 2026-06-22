"""ABM y supervisión de proyectos para el panel administrador."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.usuario import Usuario
from app.repositories.cliente_repository import ClienteRepository
from app.repositories.escenario_repository import ReporteRepository
from app.repositories.proyecto_repository import ProyectoRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.proyecto import (
    ProyectoAdminCreate,
    ProyectoAdminUpdate,
    ProyectoListOut,
    ProyectosPageOut,
)
from app.services.notificacion_push_service import (
    NotificacionPushService,
    get_notificacion_push_service,
)

router = APIRouter(prefix="/admin/proyectos", tags=["admin/proyectos"])


class ReasignarTecnicoIn(BaseModel):
    tecnico_id: int


def _validar_tecnico(db: Session, tecnico_id: int) -> Usuario:
    tecnico = UsuarioRepository(db).obtener_por_id(tecnico_id)
    if tecnico is None or not tecnico.activo or tecnico.rol != "tecnico":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El técnico indicado no existe, está inactivo o no tiene rol técnico."
            ),
        )
    return tecnico


def _validar_cliente(db: Session, cliente_id: int | None) -> None:
    if cliente_id is None:
        return
    cliente = ClienteRepository(db).obtener_por_id(cliente_id)
    if cliente is None or not cliente.activo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El cliente indicado no existe o está inactivo.",
        )


@router.get(
    "",
    response_model=ProyectosPageOut,
    summary="Listar proyectos de la organización",
)
def listar_proyectos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    tecnico_id: int | None = Query(default=None),
    estado: str | None = Query(default=None),
    fecha_desde: date | None = Query(default=None),
    fecha_hasta: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> ProyectosPageOut:
    items, total = ProyectoRepository(db).listar_paginado(
        page=page,
        page_size=page_size,
        tecnico_id=tecnico_id,
        estado=estado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    return ProyectosPageOut(items=items, total=total, page=page, page_size=page_size)  # type: ignore[arg-type]


@router.post(
    "",
    response_model=ProyectoListOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear y asignar proyecto",
)
def crear_proyecto_admin(
    body: ProyectoAdminCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
    notificador: NotificacionPushService = Depends(get_notificacion_push_service),
) -> ProyectoListOut:
    _validar_tecnico(db, body.tecnico_id)
    _validar_cliente(db, body.cliente_id)
    proyecto = ProyectoRepository(db).crear(
        nombre=body.nombre.strip(),
        tecnico_id=body.tecnico_id,
        cliente_id=body.cliente_id,
        descripcion=body.descripcion,
        estado=body.estado,
    )
    proyecto = ProyectoRepository(db).obtener_por_id_admin(proyecto_id=proyecto.id)
    assert proyecto is not None
    notificador.notificar_asignacion(
        db=db,
        tecnico_id=body.tecnico_id,
        proyecto_id=proyecto.id,
        proyecto_nombre=proyecto.nombre,
    )
    return ProyectoListOut.model_validate(proyecto)


@router.put("/{proyecto_id}", response_model=ProyectoListOut, summary="Editar proyecto")
def actualizar_proyecto_admin(
    proyecto_id: int,
    body: ProyectoAdminUpdate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
    notificador: NotificacionPushService = Depends(get_notificacion_push_service),
) -> ProyectoListOut:
    repo = ProyectoRepository(db)
    proyecto = repo.obtener_por_id_admin(proyecto_id=proyecto_id)
    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )

    campos = body.model_fields_set
    tecnico_anterior = proyecto.tecnico_id
    if "nombre" in campos and body.nombre is not None:
        proyecto.nombre = body.nombre.strip()
    if "cliente_id" in campos:
        _validar_cliente(db, body.cliente_id)
        proyecto.cliente_id = body.cliente_id
    if "descripcion" in campos:
        proyecto.descripcion = body.descripcion
    if "estado" in campos and body.estado is not None:
        proyecto.estado = body.estado
    if "tecnico_id" in campos and body.tecnico_id is not None:
        _validar_tecnico(db, body.tecnico_id)
        proyecto.tecnico_id = body.tecnico_id

    proyecto = repo.guardar_admin(proyecto=proyecto)
    if proyecto.tecnico_id != tecnico_anterior:
        notificador.notificar_asignacion(
            db=db,
            tecnico_id=proyecto.tecnico_id,
            proyecto_id=proyecto.id,
            proyecto_nombre=proyecto.nombre,
        )
    return ProyectoListOut.model_validate(proyecto)


@router.patch(
    "/{proyecto_id}/archivar",
    response_model=ProyectoListOut,
    summary="Archivar proyecto",
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    if proyecto.estado == "archivado":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El proyecto ya está archivado.",
        )
    return ProyectoListOut.model_validate(repo.archivar(proyecto=proyecto))


@router.patch(
    "/{proyecto_id}/reasignar",
    response_model=ProyectoListOut,
    summary="Reasignar técnico",
)
def reasignar_tecnico(
    proyecto_id: int,
    body: ReasignarTecnicoIn,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
    notificador: NotificacionPushService = Depends(get_notificacion_push_service),
) -> ProyectoListOut:
    repo = ProyectoRepository(db)
    proyecto = repo.obtener_por_id_admin(proyecto_id=proyecto_id)
    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    _validar_tecnico(db, body.tecnico_id)
    if proyecto.tecnico_id == body.tecnico_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El proyecto ya está asignado a ese técnico.",
        )
    proyecto = repo.reasignar_tecnico(
        proyecto=proyecto,
        nuevo_tecnico_id=body.tecnico_id,
    )
    notificador.notificar_asignacion(
        db=db,
        tecnico_id=body.tecnico_id,
        proyecto_id=proyecto.id,
        proyecto_nombre=proyecto.nombre,
    )
    return ProyectoListOut.model_validate(proyecto)


@router.delete(
    "/{proyecto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar proyecto",
)
def eliminar_proyecto_admin(
    proyecto_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> None:
    repo = ProyectoRepository(db)
    proyecto = repo.obtener_por_id_admin(proyecto_id=proyecto_id)
    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    if ReporteRepository(db).existe_para_proyecto(proyecto_id=proyecto.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un proyecto con reportes exportados.",
        )
    repo.eliminar(proyecto=proyecto)
