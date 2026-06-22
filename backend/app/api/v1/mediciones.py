"""Endpoints de mediciones WiFi y puntos de medición.

Sprint 3 — PB-03 (Captura WiFi en línea), PB-04 (Marcar puntos de medición).

Rutas expuestas:
  POST   /api/mediciones                    — ingesta de lote (Sp3-04)
  GET    /api/planos/{plano_id}/puntos      — listar puntos de un plano (Sp3-14)
  GET    /api/puntos/{punto_id}             — detalle de punto (Sp3-14)
  DELETE /api/puntos/{punto_id}             — eliminar punto con cascada (Sp3-15)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.repositories.medicion_repository import MedicionRepository
from app.repositories.plano_repository import PlanoRepository
from app.repositories.proyecto_repository import ProyectoRepository
from app.schemas.medicion import (
    AgregarMedicionesIn,
    LoteMedicionIn,
    LoteMedicionOut,
    MedicionWifiOut,
    PuntoMedicionDetalleOut,
    PuntoMedicionOut,
)

router_mediciones = APIRouter(prefix="/mediciones", tags=["mediciones"])
router_puntos = APIRouter(prefix="/puntos", tags=["mediciones"])
router_planos_puntos = APIRouter(prefix="/planos", tags=["mediciones"])


# ---------------------------------------------------------------------------
# Helper de ownership
# ---------------------------------------------------------------------------


def _verificar_ownership_plano(
    *,
    plano_id: int,
    current_user: Usuario,
    db: Session,
):
    """Verifica que el plano exista y pertenezca a un proyecto del técnico."""
    plano_repo = PlanoRepository(db)
    plano = plano_repo.obtener_por_id(plano_id=plano_id)
    if plano is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano no encontrado.",
        )
    proyecto_repo = ProyectoRepository(db)
    proyecto = proyecto_repo.obtener_por_id(
        proyecto_id=plano.proyecto_id,
        tecnico_id=current_user.id,
    )
    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano no encontrado.",
        )
    return plano


def _verificar_ownership_punto(
    *,
    punto_id: int,
    current_user: Usuario,
    db: Session,
):
    """Verifica que el punto exista y pertenezca a un plano del técnico."""
    med_repo = MedicionRepository(db)
    punto = med_repo.obtener_punto_por_id(punto_id=punto_id)
    if punto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Punto de medición no encontrado.",
        )
    _verificar_ownership_plano(
        plano_id=punto.plano_id,
        current_user=current_user,
        db=db,
    )
    return punto


# ---------------------------------------------------------------------------
# POST /api/mediciones — Sp3-04
# ---------------------------------------------------------------------------


@router_mediciones.post(
    "",
    response_model=LoteMedicionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ingresar lote de medición",
    description=(
        "Recibe un lote de mediciones WiFi (un punto del plano + N escaneos). "
        "Valida ownership del plano, RSSI en rango [-120, 0] y BSSID formato MAC. "
        "Clasifica el nivel de señal por umbrales CWNA-107. "
        "PB-03 — CA-1, CA-2, CA-6."
    ),
)
def ingresar_lote_medicion(
    body: LoteMedicionIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LoteMedicionOut:
    plano = _verificar_ownership_plano(
        plano_id=body.plano_id,
        current_user=current_user,
        db=db,
    )
    if not plano.calibrado:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El plano no está calibrado. Calibre el plano antes de capturar.",
        )

    repo = MedicionRepository(db)
    punto = repo.crear_lote(
        plano_id=body.plano_id,
        pos_x=body.pos_x,
        pos_y=body.pos_y,
        items=body.mediciones,
    )
    return LoteMedicionOut(
        punto_id=punto.id,
        nivel=punto.nivel,
        mediciones=[MedicionWifiOut.model_validate(m) for m in punto.mediciones],
    )


# ---------------------------------------------------------------------------
# GET /api/planos/{plano_id}/puntos — Sp3-14
# ---------------------------------------------------------------------------


@router_planos_puntos.get(
    "/{plano_id}/puntos",
    response_model=list[PuntoMedicionOut],
    summary="Listar puntos de un plano",
    description=(
        "Retorna todos los puntos de medición de un plano, más recientes primero. "
        "PB-04 — CA-1."
    ),
)
def listar_puntos(
    plano_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[PuntoMedicionOut]:
    _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )
    repo = MedicionRepository(db)
    puntos = repo.listar_puntos_por_plano(plano_id=plano_id)
    return [PuntoMedicionOut.model_validate(p) for p in puntos]


# ---------------------------------------------------------------------------
# GET /api/puntos/{punto_id} — Sp3-14
# ---------------------------------------------------------------------------


@router_puntos.get(
    "/{punto_id}",
    response_model=PuntoMedicionDetalleOut,
    summary="Detalle de un punto de medición",
    description=(
        "Retorna el punto con todas sus mediciones WiFi ordenadas por RSSI desc. "
        "PB-04 — CA-4."
    ),
)
def obtener_punto(
    punto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PuntoMedicionDetalleOut:
    punto = _verificar_ownership_punto(
        punto_id=punto_id,
        current_user=current_user,
        db=db,
    )
    return PuntoMedicionDetalleOut.model_validate(punto)


# ---------------------------------------------------------------------------
# POST /api/puntos/{punto_id}/mediciones — modo continuo
# ---------------------------------------------------------------------------


@router_puntos.post(
    "/{punto_id}/mediciones",
    response_model=PuntoMedicionDetalleOut,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar mediciones a un punto existente",
    description=(
        "Agrega un nuevo lote de mediciones WiFi al punto indicado (modo continuo). "
        "Recalcula el nivel del punto con el peor RSSI acumulado. "
        "PB-03 — modo continuo."
    ),
)
def agregar_mediciones_a_punto(
    punto_id: int,
    body: AgregarMedicionesIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PuntoMedicionDetalleOut:
    punto = _verificar_ownership_punto(
        punto_id=punto_id,
        current_user=current_user,
        db=db,
    )
    repo = MedicionRepository(db)
    punto = repo.agregar_mediciones(punto=punto, items=body.mediciones)
    return PuntoMedicionDetalleOut.model_validate(punto)


# ---------------------------------------------------------------------------
# DELETE /api/puntos/{punto_id} — Sp3-15
# ---------------------------------------------------------------------------


@router_puntos.delete(
    "/{punto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar punto de medición",
    description=("Elimina el punto y sus mediciones en cascada. PB-04 — CA-5."),
)
def eliminar_punto(
    punto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    punto = _verificar_ownership_punto(
        punto_id=punto_id,
        current_user=current_user,
        db=db,
    )
    repo = MedicionRepository(db)
    repo.eliminar_punto(punto=punto)
