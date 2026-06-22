"""Endpoints de gestión de clientes.

- GET  /clientes              — lista activos (admin + tecnico autenticado)
- GET  /admin/clientes        — lista todos, incluye inactivos (solo admin)
- POST /admin/clientes        — crear (solo admin)
- PUT  /admin/clientes/{id}   — actualizar nombre y/o activo (solo admin)
- PATCH /admin/clientes/{id}/desactivar — desactivar (solo admin)

Sprint 1 — PB-19 (Sp1-32..Sp1-34)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.usuario import Usuario
from app.repositories.cliente_repository import ClienteRepository
from app.schemas.cliente import ClienteCreate, ClienteOut, ClienteUpdate

router = APIRouter(tags=["clientes"])


@router.get(
    "/clientes",
    response_model=list[ClienteOut],
    summary="Listar clientes activos",
    description="Devuelve el catálogo de clientes activos. Disponible para ADMIN y TECNICO. PB-19 — CA-3.",
)
def listar_clientes_activos(
    db: Session = Depends(get_db),
    _current_user: Usuario = Depends(get_current_user),
) -> list[ClienteOut]:
    repo = ClienteRepository(db)
    return repo.listar_activos()  # type: ignore[return-value]


@router.get(
    "/admin/clientes",
    response_model=list[ClienteOut],
    summary="Listar todos los clientes (admin)",
    description="Devuelve todos los clientes, incluidos los inactivos. Solo ADMIN. PB-19.",
)
def listar_todos_los_clientes(
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> list[ClienteOut]:
    repo = ClienteRepository(db)
    return repo.listar_todos()  # type: ignore[return-value]


@router.post(
    "/admin/clientes",
    response_model=ClienteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cliente",
    description="Crea un nuevo cliente en el catálogo. Solo ADMIN. PB-19 — CA-1.",
)
def crear_cliente(
    payload: ClienteCreate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> ClienteOut:
    repo = ClienteRepository(db)
    try:
        cliente = repo.crear(payload.nombre)
        db.commit()
        db.refresh(cliente)
        return cliente  # type: ignore[return-value]
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un cliente con el nombre '{payload.nombre}'",
        )


@router.put(
    "/admin/clientes/{cliente_id}",
    response_model=ClienteOut,
    summary="Actualizar cliente",
    description="Actualiza nombre y/o estado activo de un cliente. Solo ADMIN. PB-19.",
)
def actualizar_cliente(
    cliente_id: int,
    payload: ClienteUpdate,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> ClienteOut:
    repo = ClienteRepository(db)
    cliente = repo.obtener_por_id(cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado"
        )
    try:
        cliente = repo.actualizar(cliente, nombre=payload.nombre, activo=payload.activo)
        db.commit()
        db.refresh(cliente)
        return cliente  # type: ignore[return-value]
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un cliente con el nombre '{payload.nombre}'",
        )


@router.patch(
    "/admin/clientes/{cliente_id}/desactivar",
    response_model=ClienteOut,
    summary="Desactivar cliente",
    description="Marca un cliente como inactivo. No aparecerá en el selector de proyectos. Solo ADMIN. PB-19 — CA-4.",
)
def desactivar_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
    _admin: Usuario = Depends(require_admin),
) -> ClienteOut:
    repo = ClienteRepository(db)
    cliente = repo.obtener_por_id(cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado"
        )
    cliente = repo.actualizar(cliente, activo=False)
    db.commit()
    db.refresh(cliente)
    return cliente  # type: ignore[return-value]
