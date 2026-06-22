"""Endpoints de enlaces públicos para cliente.

Sprint 6 — PB-15/PB-16/PB-17.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.v1.escenarios import _firmar_descarga
from app.api.v1.heatmaps import _conjunto_out, _mapa_out
from app.api.v1.planos import _firmar as _firmar_plano
from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_admin
from app.models.escenario import EscenarioOptimizado, Reporte
from app.models.heatmap import AnalisisCobertura, ConjuntoAP, MapaCalor
from app.models.plano import Plano
from app.models.proyecto import Proyecto
from app.models.share import TokenEnlaceCliente
from app.models.usuario import Usuario
from app.repositories.proyecto_repository import ProyectoRepository
from app.schemas.escenario import EscenarioOptimizadoOut
from app.schemas.heatmap import AnalisisCoberturaOut
from app.schemas.plano import PlanoOut
from app.schemas.share import (
    ContenidoEnlaceIn,
    EnlaceClienteActualizarIn,
    EnlaceClienteCrearIn,
    EnlaceClienteOut,
    PortalClienteOut,
    ProyectoPortalOut,
)

router = APIRouter(prefix="/share", tags=["portal-cliente"])


def _generar_token() -> str:
    base = str(uuid.uuid4())
    firma = hmac.new(
        settings.storage_url_secret.encode("utf-8"),
        base.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"{base}.{firma}"


def _token_valido_formato(token: str) -> bool:
    partes = token.split(".")
    if len(partes) != 2:
        return False
    base, firma = partes
    esperada = hmac.new(
        settings.storage_url_secret.encode("utf-8"),
        base.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(esperada, firma)


def _url_publica(token: str) -> str:
    return f"/portal/{token}"


def _contenido_dict(contenido: ContenidoEnlaceIn) -> dict:
    return {
        "conjunto_ids": list(dict.fromkeys(contenido.conjunto_ids)),
        "mapa_ids": list(dict.fromkeys(contenido.mapa_ids)),
        "analisis_ids": list(dict.fromkeys(contenido.analisis_ids)),
        "escenario_ids": list(dict.fromkeys(contenido.escenario_ids)),
        "reporte_id": contenido.reporte_id,
    }


def _contenido_from_model(enlace: TokenEnlaceCliente) -> ContenidoEnlaceIn:
    return ContenidoEnlaceIn(**(enlace.contenido or {}))


def _asegurar_utc(valor: datetime) -> datetime:
    if valor.tzinfo is None:
        return valor.replace(tzinfo=UTC)
    return valor.astimezone(UTC)


def _enlace_out(enlace: TokenEnlaceCliente) -> EnlaceClienteOut:
    return EnlaceClienteOut(
        id=enlace.id,
        proyecto_id=enlace.proyecto_id,
        url_publica=_url_publica(enlace.token),
        expira_en=enlace.expira_en,
        revocado=enlace.revocado,
        accesos=enlace.accesos,
        ultimo_acceso=enlace.ultimo_acceso,
        ip_ultimo_acceso=enlace.ip_ultimo_acceso,
        contenido=_contenido_from_model(enlace),
        created_at=enlace.created_at,
    )


def _proyecto_admin(
    *, proyecto_id: int, current_user: Usuario, db: Session
) -> Proyecto:
    proyecto = ProyectoRepository(db).obtener_por_id_admin(proyecto_id=proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    return proyecto


def _validar_contenido(
    *, proyecto: Proyecto, contenido: ContenidoEnlaceIn, db: Session
) -> ContenidoEnlaceIn:
    plano_ids = {plano.id for plano in proyecto.planos}
    escenario_ids = set(contenido.escenario_ids)
    mapa_ids = set(contenido.mapa_ids)
    conjunto_ids = set(contenido.conjunto_ids)
    analisis_ids = set(contenido.analisis_ids)

    reporte_id = contenido.reporte_id

    contenido = ContenidoEnlaceIn(
        conjunto_ids=sorted(conjunto_ids),
        mapa_ids=sorted(mapa_ids),
        analisis_ids=sorted(analisis_ids),
        escenario_ids=sorted(escenario_ids),
        reporte_id=reporte_id,
    )

    conjuntos = (
        db.query(ConjuntoAP).filter(ConjuntoAP.id.in_(contenido.conjunto_ids)).all()
        if contenido.conjunto_ids
        else []
    )
    if {item.id for item in conjuntos} != set(contenido.conjunto_ids) or any(
        item.plano_id not in plano_ids for item in conjuntos
    ):
        raise HTTPException(
            status_code=422,
            detail="Conjunto no pertenece al proyecto.",
        )
    if any(item.estado_gobernanza != "publicado_cliente" for item in conjuntos):
        raise HTTPException(
            status_code=422,
            detail="Conjunto no publicado para cliente.",
        )

    mapas = (
        db.query(MapaCalor).filter(MapaCalor.id.in_(contenido.mapa_ids)).all()
        if contenido.mapa_ids
        else []
    )
    if {item.id for item in mapas} != set(contenido.mapa_ids) or any(
        item.plano_id not in plano_ids for item in mapas
    ):
        raise HTTPException(status_code=422, detail="Mapa no pertenece al proyecto.")

    analisis = (
        db.query(AnalisisCobertura)
        .join(MapaCalor, AnalisisCobertura.mapa_calor_id == MapaCalor.id)
        .filter(AnalisisCobertura.id.in_(contenido.analisis_ids))
        .all()
        if contenido.analisis_ids
        else []
    )
    if {item.id for item in analisis} != set(contenido.analisis_ids) or any(
        item.mapa.plano_id not in plano_ids for item in analisis
    ):
        raise HTTPException(
            status_code=422,
            detail="Análisis no pertenece al proyecto.",
        )

    escenarios = (
        db.query(EscenarioOptimizado)
        .filter(EscenarioOptimizado.id.in_(contenido.escenario_ids))
        .all()
        if contenido.escenario_ids
        else []
    )
    if {item.id for item in escenarios} != set(contenido.escenario_ids) or any(
        item.proyecto_id != proyecto.id for item in escenarios
    ):
        raise HTTPException(
            status_code=422,
            detail="Escenario no pertenece al proyecto.",
        )
    if any(item.estado_gobernanza != "publicado_cliente" for item in escenarios):
        raise HTTPException(
            status_code=422,
            detail="Escenario no publicado para cliente.",
        )

    if contenido.reporte_id is not None:
        reporte = db.query(Reporte).filter(Reporte.id == contenido.reporte_id).first()
        if reporte is None or reporte.proyecto_id != proyecto.id:
            raise HTTPException(
                status_code=422,
                detail="Reporte no pertenece al proyecto.",
            )

    return ContenidoEnlaceIn(**_contenido_dict(contenido))


def _obtener_enlace_publico(
    *, token: str, db: Session, request: Request | None = None
) -> TokenEnlaceCliente:
    if not _token_valido_formato(token):
        raise HTTPException(status_code=404, detail="Enlace no válido o expirado.")
    enlace = (
        db.query(TokenEnlaceCliente).filter(TokenEnlaceCliente.token == token).first()
    )
    ahora = datetime.now(UTC)
    if enlace is None or enlace.revocado or _asegurar_utc(enlace.expira_en) < ahora:
        raise HTTPException(status_code=404, detail="Enlace no válido o expirado.")
    if request is not None:
        enlace.accesos += 1
        enlace.ultimo_acceso = ahora
        enlace.ip_ultimo_acceso = request.client.host if request.client else None
        db.commit()
        db.refresh(enlace)
    return enlace


@router.post(
    "/proyectos/{proyecto_id}/enlaces",
    response_model=EnlaceClienteOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_enlace_cliente(
    proyecto_id: int,
    body: EnlaceClienteCrearIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> EnlaceClienteOut:
    proyecto = _proyecto_admin(
        proyecto_id=proyecto_id,
        current_user=current_user,
        db=db,
    )
    contenido = _validar_contenido(
        proyecto=proyecto,
        contenido=body.contenido,
        db=db,
    )
    enlace = TokenEnlaceCliente(
        proyecto_id=proyecto.id,
        token=_generar_token(),
        contenido=_contenido_dict(contenido),
        expira_en=datetime.now(UTC) + timedelta(days=body.expira_en_dias),
        creado_por_id=current_user.id,
    )
    db.add(enlace)
    db.commit()
    db.refresh(enlace)
    return _enlace_out(enlace)


@router.get("/proyectos/{proyecto_id}/enlaces", response_model=list[EnlaceClienteOut])
def listar_enlaces_cliente(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> list[EnlaceClienteOut]:
    proyecto = _proyecto_admin(
        proyecto_id=proyecto_id,
        current_user=current_user,
        db=db,
    )
    enlaces = (
        db.query(TokenEnlaceCliente)
        .filter(TokenEnlaceCliente.proyecto_id == proyecto.id)
        .order_by(TokenEnlaceCliente.created_at.desc(), TokenEnlaceCliente.id.desc())
        .all()
    )
    return [_enlace_out(enlace) for enlace in enlaces]


@router.patch("/enlaces/{enlace_id}", response_model=EnlaceClienteOut)
def actualizar_enlace_cliente(
    enlace_id: int,
    body: EnlaceClienteActualizarIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> EnlaceClienteOut:
    enlace = (
        db.query(TokenEnlaceCliente).filter(TokenEnlaceCliente.id == enlace_id).first()
    )
    if enlace is None:
        raise HTTPException(status_code=404, detail="Enlace no encontrado.")
    _proyecto_admin(proyecto_id=enlace.proyecto_id, current_user=current_user, db=db)
    enlace.revocado = body.revocado
    db.commit()
    db.refresh(enlace)
    return _enlace_out(enlace)


@router.get("/{token}", response_model=PortalClienteOut)
def obtener_portal_cliente(
    token: str,
    request: Request,
    db: Session = Depends(get_db),
) -> PortalClienteOut:
    enlace = _obtener_enlace_publico(token=token, db=db, request=request)
    contenido = _contenido_from_model(enlace)
    proyecto = enlace.proyecto
    plano_ids = {plano.id for plano in proyecto.planos}
    mapas = (
        db.query(MapaCalor)
        .filter(MapaCalor.id.in_(contenido.mapa_ids), MapaCalor.plano_id.in_(plano_ids))
        .order_by(MapaCalor.created_at.desc(), MapaCalor.id.desc())
        .all()
        if contenido.mapa_ids
        else []
    )
    planos_mapa = {mapa.plano_id for mapa in mapas}
    escenarios = (
        db.query(EscenarioOptimizado)
        .filter(
            EscenarioOptimizado.id.in_(contenido.escenario_ids),
            EscenarioOptimizado.proyecto_id == proyecto.id,
            EscenarioOptimizado.estado_gobernanza == "publicado_cliente",
        )
        .order_by(EscenarioOptimizado.pct_cobertura.desc())
        .all()
        if contenido.escenario_ids
        else []
    )
    conjuntos = (
        db.query(ConjuntoAP)
        .filter(
            ConjuntoAP.id.in_(contenido.conjunto_ids),
            ConjuntoAP.plano_id.in_(plano_ids),
            ConjuntoAP.estado_gobernanza == "publicado_cliente",
        )
        .all()
        if contenido.conjunto_ids
        else []
    )
    analisis = (
        db.query(AnalisisCobertura)
        .join(MapaCalor, AnalisisCobertura.mapa_calor_id == MapaCalor.id)
        .filter(
            AnalisisCobertura.id.in_(contenido.analisis_ids),
            MapaCalor.plano_id.in_(plano_ids),
        )
        .all()
        if contenido.analisis_ids
        else []
    )
    planos = (
        db.query(Plano)
        .filter(Plano.id.in_(planos_mapa))
        .order_by(Plano.created_at.desc(), Plano.id.desc())
        .all()
        if planos_mapa
        else []
    )
    reporte_disponible = False
    if contenido.reporte_id is not None:
        reporte_disponible = (
            db.query(Reporte)
            .filter(
                Reporte.id == contenido.reporte_id,
                Reporte.proyecto_id == proyecto.id,
                Reporte.estado == "LISTO",
            )
            .first()
            is not None
        )
    return PortalClienteOut(
        proyecto=ProyectoPortalOut(
            id=proyecto.id,
            nombre=proyecto.nombre,
            cliente=proyecto.cliente.nombre if proyecto.cliente else None,
            descripcion=proyecto.descripcion,
        ),
        planos=[
            PlanoOut.from_plano(
                plano,
                url_firmada=_firmar_plano(plano.ruta_storage, request),
            )
            for plano in planos
        ],
        conjuntos=[_conjunto_out(conjunto) for conjunto in conjuntos],
        heatmaps=[_mapa_out(mapa, request) for mapa in mapas],
        analisis=[AnalisisCoberturaOut.model_validate(item) for item in analisis],
        escenarios=[EscenarioOptimizadoOut.model_validate(item) for item in escenarios],
        reporte_disponible=reporte_disponible,
    )


@router.get("/{token}/reporte")
def descargar_reporte_portal(
    token: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    enlace = _obtener_enlace_publico(token=token, db=db)
    contenido = _contenido_from_model(enlace)
    if contenido.reporte_id is None:
        raise HTTPException(status_code=404, detail="Reporte no disponible.")
    reporte = (
        db.query(Reporte)
        .filter(
            Reporte.id == contenido.reporte_id,
            Reporte.proyecto_id == enlace.proyecto_id,
            Reporte.estado == "LISTO",
        )
        .first()
    )
    if reporte is None or not reporte.ruta_pdf:
        raise HTTPException(status_code=404, detail="Reporte no disponible.")
    return RedirectResponse(url=_firmar_descarga(reporte.ruta_pdf), status_code=302)
