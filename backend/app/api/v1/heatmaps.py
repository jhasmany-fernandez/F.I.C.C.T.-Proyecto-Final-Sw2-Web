"""Endpoints de heatmap y análisis de cobertura.

Sprint 4 — PB-05 (Generar mapa de calor), PB-06 (Analizar cobertura).
"""

import hashlib
import json
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.heatmap import MapaCalor
from app.models.usuario import Usuario
from app.repositories.heatmap_repository import (
    AnalisisCoberturaRepository,
    ConjuntoAPRepository,
    MapaCalorRepository,
)
from app.repositories.medicion_repository import MedicionRepository
from app.repositories.plano_repository import PlanoRepository
from app.repositories.proyecto_repository import ProyectoRepository
from app.schemas.heatmap import (
    ActualizarUbicacionAPConjuntoIn,
    AnalisisCoberturaOut,
    APDetectadoOut,
    APDisponibleOut,
    ConfirmarAPIn,
    ConjuntoAPActualizarIn,
    ConjuntoAPCrearIn,
    ConjuntoAPItemOut,
    ConjuntoAPOut,
    GenerarHeatmapConjuntoIn,
    MapaCalorOut,
    PuntoLecturaHeatmapOut,
)
from app.services.analisis_cobertura_service import AnalisisCoberturaService
from app.services.interpolacion_service import (
    ESCALA_CWNA,
    HeatmapImageService,
    InterpolacionService,
    PuntoRSSI,
)
from app.storage import LocalFilesystemStorage, generar_url_firmada, verificar_firma

router_planos_heatmap = APIRouter(prefix="/planos", tags=["heatmaps"])
router_mapas = APIRouter(prefix="/mapas", tags=["heatmaps"])
router_aps = APIRouter(prefix="/aps", tags=["heatmaps"])
router_conjuntos_ap = APIRouter(prefix="/conjuntos-ap", tags=["heatmaps"])


def _storage() -> LocalFilesystemStorage:
    return LocalFilesystemStorage(root=settings.storage_root)


def _firmar(ruta: str, request: Request) -> str:
    url = generar_url_firmada(
        ruta_relativa=ruta,
        secret=settings.storage_url_secret,
        base_url=settings.public_api_url,
        ttl_seconds=settings.storage_url_ttl_seconds,
    )
    return url.replace("/planos/archivo/", "/mapas/archivo/", 1)


def _verificar_ownership_plano(
    *,
    plano_id: int,
    current_user: Usuario,
    db: Session,
):
    plano = PlanoRepository(db).obtener_por_id(plano_id=plano_id)
    if plano is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano no encontrado.",
        )
    proyecto_repo = ProyectoRepository(db)
    proyecto = (
        proyecto_repo.obtener_por_id_admin(proyecto_id=plano.proyecto_id)
        if current_user.rol == "admin"
        else proyecto_repo.obtener_por_id(
            proyecto_id=plano.proyecto_id,
            tecnico_id=current_user.id,
        )
    )
    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano no encontrado.",
        )
    return plano


def _verificar_ownership_mapa(
    *,
    mapa_id: int,
    current_user: Usuario,
    db: Session,
) -> MapaCalor:
    mapa = MapaCalorRepository(db).obtener_por_id(mapa_id=mapa_id)
    if mapa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa de calor no encontrado.",
        )
    _verificar_ownership_plano(
        plano_id=mapa.plano_id,
        current_user=current_user,
        db=db,
    )
    return mapa


def _mapa_out(
    mapa: MapaCalor,
    request: Request,
    *,
    puntos: list[PuntoRSSI] | None = None,
) -> MapaCalorOut:
    aps_interes = mapa.aps_interes or [
        {
            "bssid": mapa.bssid,
            "ssid": mapa.ssid,
            "canal": None,
            "frecuencia_mhz": None,
            "rssi_promedio": 0,
            "pos_x": mapa.ap_pos_x,
            "pos_y": mapa.ap_pos_y,
            "cantidad_puntos": mapa.cantidad_puntos,
        }
    ]
    puntos_lectura = puntos or []
    rssi_promedio = (
        sum(punto.rssi for punto in puntos_lectura) / len(puntos_lectura)
        if puntos_lectura
        else (mapa.rssi_min + mapa.rssi_max) / 2
    )
    return MapaCalorOut(
        id=mapa.id,
        plano_id=mapa.plano_id,
        conjunto_ap_id=mapa.conjunto_ap_id,
        analisis_id=mapa.analisis.id if mapa.analisis is not None else None,
        modo_generacion=mapa.modo_generacion,
        algoritmo=mapa.algoritmo,
        resolucion=mapa.resolucion,
        bssid=mapa.bssid,
        ssid=mapa.ssid,
        ap_pos_x=mapa.ap_pos_x,
        ap_pos_y=mapa.ap_pos_y,
        aps_interes=aps_interes,
        bssids_generacion=mapa.bssids_generacion or [ap["bssid"] for ap in aps_interes],
        url_imagen=_firmar(mapa.ruta_imagen, request),
        matriz=mapa.matriz,
        escala=mapa.escala,
        cantidad_puntos=mapa.cantidad_puntos,
        rssi_min=mapa.rssi_min,
        rssi_max=mapa.rssi_max,
        rssi_promedio=round(rssi_promedio, 2),
        puntos_lectura=[
            PuntoLecturaHeatmapOut(
                punto_id=punto.punto_id,
                pos_x=punto.x,
                pos_y=punto.y,
                rssi=punto.rssi,
            )
            for punto in puntos_lectura
        ],
        advertencias=_advertencias_heatmap(
            cantidad_puntos=len(puntos_lectura) or mapa.cantidad_puntos,
            aps_interes=aps_interes,
        ),
        created_at=mapa.created_at,
    )


def _advertencias_heatmap(
    *,
    cantidad_puntos: int,
    aps_interes: list[dict],
) -> list[str]:
    advertencias: list[str] = []
    if cantidad_puntos < 10:
        advertencias.append(
            "Baja densidad de muestras: el heatmap puede verse uniforme. "
            "Agrega más puntos de lectura distribuidos sobre el plano."
        )
    aps_con_pocas_muestras = [
        ap["ssid"] or ap["bssid"]
        for ap in aps_interes
        if int(ap.get("cantidad_puntos") or 0) < 5
    ]
    if aps_con_pocas_muestras:
        advertencias.append(
            "Uno o más APs seleccionados tienen pocas lecturas: "
            + ", ".join(aps_con_pocas_muestras)
            + "."
        )
    return advertencias


def _normalizar_bssids(bssids: list[str]) -> list[str]:
    normalizados: list[str] = []
    for bssid in bssids:
        valor = bssid.strip().lower()
        if valor and valor not in normalizados:
            normalizados.append(valor)
    return normalizados


def _resolver_aps_interes(
    *,
    aps: list[dict],
    bssids: list[str],
    ap_pos_x: list[float] | None,
    ap_pos_y: list[float] | None,
) -> list[dict]:
    if (ap_pos_x is None) != (ap_pos_y is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Las coordenadas X/Y de los APs de interés deben enviarse juntas.",
        )
    if ap_pos_x is not None and len(ap_pos_x) != len(bssids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La cantidad de coordenadas X no coincide con los APs seleccionados."
            ),
        )
    if ap_pos_y is not None and len(ap_pos_y) != len(bssids):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "La cantidad de coordenadas Y no coincide con los APs seleccionados."
            ),
        )
    if ap_pos_x is not None and any(pos < 0 for pos in ap_pos_x):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Las coordenadas X de los APs de interés no pueden ser negativas.",
        )
    if ap_pos_y is not None and any(pos < 0 for pos in ap_pos_y):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Las coordenadas Y de los APs de interés no pueden ser negativas.",
        )

    por_bssid = {ap["bssid"]: ap for ap in aps}
    faltantes = [bssid for bssid in bssids if bssid not in por_bssid]
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Uno o más APs seleccionados no existen en las mediciones del plano."
            ),
        )

    seleccionados: list[dict] = []
    for idx, bssid in enumerate(bssids):
        ap = por_bssid[bssid]
        seleccionados.append(
            {
                "bssid": bssid,
                "ssid": ap["ssid"],
                "canal": ap["canal"],
                "frecuencia_mhz": ap["frecuencia_mhz"],
                "rssi_promedio": ap["rssi_promedio"],
                "pos_x": ap_pos_x[idx] if ap_pos_x is not None else ap["pos_x"],
                "pos_y": ap_pos_y[idx] if ap_pos_y is not None else ap["pos_y"],
                "cantidad_puntos": ap["cantidad_puntos"],
            }
        )
    return seleccionados


def _resolver_items_conjunto(*, aps: list[dict], bssids: list[str]) -> list[dict]:
    bssids_norm = _normalizar_bssids(bssids)
    if not bssids_norm:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe seleccionar al menos un AP para el conjunto.",
        )
    por_bssid = {ap["bssid"]: ap for ap in aps}
    faltantes = [bssid for bssid in bssids_norm if bssid not in por_bssid]
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uno o más APs no existen en las mediciones del plano.",
        )
    return [
        {
            "bssid": bssid,
            "ssid_snapshot": por_bssid[bssid]["ssid"],
            "canal_snapshot": por_bssid[bssid]["canal"],
            "rssi_promedio_snapshot": por_bssid[bssid]["rssi_promedio"],
            "pos_x": por_bssid[bssid]["pos_x"],
            "pos_y": por_bssid[bssid]["pos_y"],
        }
        for bssid in bssids_norm
    ]


def _conjunto_out(conjunto) -> ConjuntoAPOut:
    items = [
        ConjuntoAPItemOut(
            bssid=item.bssid,
            ssid=item.ssid_snapshot or "",
            canal=item.canal_snapshot,
            rssi_promedio=item.rssi_promedio_snapshot,
            pos_x=item.pos_x,
            pos_y=item.pos_y,
        )
        for item in conjunto.items
    ]
    return ConjuntoAPOut(
        id=conjunto.id,
        plano_id=conjunto.plano_id,
        nombre=conjunto.nombre,
        proposito=conjunto.proposito,
        descripcion=conjunto.descripcion,
        es_principal=conjunto.es_principal,
        origen=conjunto.origen,
        estado_gobernanza=conjunto.estado_gobernanza,
        creado_por_id=conjunto.creado_por_id,
        cantidad_aps=len(items),
        items=items,
        created_at=conjunto.created_at,
        updated_at=conjunto.updated_at,
    )


def _verificar_ownership_conjunto(
    *,
    conjunto_id: int,
    current_user: Usuario,
    db: Session,
):
    conjunto = ConjuntoAPRepository(db).obtener_por_id(conjunto_id=conjunto_id)
    if conjunto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conjunto de APs no encontrado.",
        )
    _verificar_ownership_plano(
        plano_id=conjunto.plano_id,
        current_user=current_user,
        db=db,
    )
    return conjunto


def _firma_aps_interes(
    *,
    firma_base: str,
    aps_interes: list[dict],
    conjunto_ap_id: int | None = None,
    modo_generacion: str = "SUBCONJUNTO",
) -> str:
    payload = {
        "modelo": "aps-interes-mediciones-v8",
        "firma_base": firma_base,
        "conjunto_ap_id": conjunto_ap_id,
        "modo_generacion": modo_generacion,
        "aps": [
            {
                "bssid": ap["bssid"],
                "pos_x": round(float(ap["pos_x"]), 2),
                "pos_y": round(float(ap["pos_y"]), 2),
            }
            for ap in aps_interes
        ],
    }
    serializado = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"aps:{hashlib.sha256(serializado.encode()).hexdigest()}"


@router_planos_heatmap.get(
    "/{plano_id}/aps",
    response_model=list[APDisponibleOut],
    summary="Listar APs detectados del plano",
    description=(
        "Agrupa las mediciones por BSSID para que el técnico seleccione los APs "
        "de interés antes de generar mapas de calor."
    ),
)
def listar_aps_disponibles(
    plano_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[APDisponibleOut]:
    _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )
    aps = MedicionRepository(db).listar_aps_por_plano(plano_id=plano_id)
    mapas_recientes = MapaCalorRepository(db).listar_recientes_por_plano(
        plano_id=plano_id,
    )
    if mapas_recientes:
        ultimo_mapa = mapas_recientes[0]
        aps_ultimo_mapa = ultimo_mapa.aps_interes or [{"bssid": ultimo_mapa.bssid}]
    else:
        aps_ultimo_mapa = []
    bssids_ultimo_mapa = {ap["bssid"] for ap in aps_ultimo_mapa}
    posiciones_previas: dict[str, dict] = {}
    for mapa in mapas_recientes:
        for ap in mapa.aps_interes or []:
            posiciones_previas.setdefault(ap["bssid"], ap)
    for ap in aps:
        posicion = posiciones_previas.get(ap["bssid"])
        if posicion is None:
            continue
        ap["pos_x"] = posicion["pos_x"]
        ap["pos_y"] = posicion["pos_y"]
        ap["seleccionado"] = ap["bssid"] in bssids_ultimo_mapa
    return [APDisponibleOut(**ap) for ap in aps]


def _generar_heatmap_core(
    *,
    plano_id: int,
    request: Request,
    bssid: list[str],
    ap_pos_x: list[float] | None,
    ap_pos_y: list[float] | None,
    algoritmo: str,
    resolucion: int,
    db: Session,
    current_user: Usuario,
    conjunto_ap_id: int | None = None,
    modo_generacion: str | None = None,
) -> MapaCalorOut:
    plano = _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )
    if not plano.calibrado:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El plano debe estar calibrado antes de generar el heatmap.",
        )

    med_repo = MedicionRepository(db)
    bssids_norm = _normalizar_bssids(bssid)
    if not bssids_norm:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Debe seleccionar al menos un AP de interés.",
        )
    aps_disponibles = med_repo.listar_aps_por_plano(plano_id=plano_id)
    aps_interes = _resolver_aps_interes(
        aps=aps_disponibles,
        bssids=bssids_norm,
        ap_pos_x=ap_pos_x,
        ap_pos_y=ap_pos_y,
    )

    puntos = med_repo.listar_puntos_rssi_heatmap(
        plano_id=plano_id,
        bssids=bssids_norm,
    )
    if len(puntos) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Se requieren al menos 5 puntos de los APs seleccionados.",
        )

    algoritmo_norm = algoritmo.upper()
    modo_norm = modo_generacion or (
        "INDIVIDUAL" if len(bssids_norm) == 1 else "SUBCONJUNTO"
    )
    firma_base = med_repo.firma_mediciones_plano(
        plano_id=plano_id,
        bssids=bssids_norm,
    )
    firma = _firma_aps_interes(
        firma_base=firma_base,
        aps_interes=aps_interes,
        conjunto_ap_id=conjunto_ap_id,
        modo_generacion=modo_norm,
    )
    mapa_repo = MapaCalorRepository(db)
    cache = mapa_repo.obtener_cache(
        plano_id=plano_id,
        algoritmo=algoritmo_norm,
        resolucion=resolucion,
        firma_mediciones=firma,
    )
    if cache is not None:
        return _mapa_out(cache, request, puntos=puntos)

    ap_principal = aps_interes[0]
    matriz = InterpolacionService().interpolar(
        puntos=puntos,
        ancho_px=plano.ancho_px,
        alto_px=plano.alto_px,
        resolucion=resolucion,
        algoritmo=algoritmo_norm,
    )
    png = HeatmapImageService().render_png(matriz)
    ruta = (
        f"heatmaps/{plano_id}/"
        f"{secrets.token_hex(8)}_{algoritmo_norm.lower()}_{resolucion}.png"
    )
    _storage().save(png, ruta)

    mapa = mapa_repo.crear(
        plano_id=plano_id,
        conjunto_ap_id=conjunto_ap_id,
        modo_generacion=modo_norm,
        algoritmo=algoritmo_norm,
        resolucion=resolucion,
        bssid=ap_principal["bssid"],
        ssid=ap_principal["ssid"],
        ap_pos_x=ap_principal["pos_x"],
        ap_pos_y=ap_principal["pos_y"],
        aps_interes=aps_interes,
        bssids_generacion=bssids_norm,
        matriz=matriz,
        escala=ESCALA_CWNA,
        ruta_imagen=ruta,
        cantidad_puntos=len(puntos),
        rssi_min=min(p.rssi for p in puntos),
        rssi_max=max(p.rssi for p in puntos),
        firma_mediciones=firma,
    )
    return _mapa_out(mapa, request, puntos=puntos)


@router_planos_heatmap.get(
    "/{plano_id}/heatmap",
    response_model=MapaCalorOut,
    summary="Generar mapa de calor",
    description=(
        "Genera o reutiliza el heatmap cacheado del plano mediante IDW. "
        "PB-05 — CA-1 a CA-6."
    ),
)
def generar_heatmap(
    plano_id: int,
    request: Request,
    bssid: list[str] = Query(..., description="BSSID de cada AP de interés"),
    ap_pos_x: list[float] | None = Query(
        default=None,
        description="Ubicación X confirmada de cada AP sobre el plano",
    ),
    ap_pos_y: list[float] | None = Query(
        default=None,
        description="Ubicación Y confirmada de cada AP sobre el plano",
    ),
    algoritmo: str = Query(default="IDW", pattern="^(IDW|KRIGING|idw|kriging)$"),
    resolucion: int = Query(default=128, enum=[64, 128, 256]),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> MapaCalorOut:
    return _generar_heatmap_core(
        plano_id=plano_id,
        request=request,
        bssid=bssid,
        ap_pos_x=ap_pos_x,
        ap_pos_y=ap_pos_y,
        algoritmo=algoritmo,
        resolucion=resolucion,
        db=db,
        current_user=current_user,
    )


@router_planos_heatmap.get(
    "/{plano_id}/mapas",
    response_model=list[MapaCalorOut],
    summary="Listar mapas de calor del plano",
)
def listar_mapas_plano(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[MapaCalorOut]:
    _verificar_ownership_plano(plano_id=plano_id, current_user=current_user, db=db)
    mapas = MapaCalorRepository(db).listar_recientes_por_plano(plano_id=plano_id)
    return [_mapa_out(mapa, request) for mapa in mapas]


@router_planos_heatmap.get(
    "/{plano_id}/conjuntos-ap",
    response_model=list[ConjuntoAPOut],
    summary="Listar conjuntos de APs del plano",
)
def listar_conjuntos_ap(
    plano_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[ConjuntoAPOut]:
    _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )
    conjuntos = ConjuntoAPRepository(db).listar_por_plano(plano_id=plano_id)
    return [_conjunto_out(conjunto) for conjunto in conjuntos]


@router_planos_heatmap.post(
    "/{plano_id}/conjuntos-ap",
    response_model=ConjuntoAPOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear conjunto de APs del plano",
)
def crear_conjunto_ap(
    plano_id: int,
    body: ConjuntoAPCrearIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ConjuntoAPOut:
    _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )
    repo = ConjuntoAPRepository(db)
    nombre = body.nombre.strip()
    proposito = body.proposito.strip()
    if repo.existe_nombre(plano_id=plano_id, nombre=nombre):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un conjunto de APs con ese nombre en el plano.",
        )
    aps = MedicionRepository(db).listar_aps_por_plano(plano_id=plano_id)
    items = _resolver_items_conjunto(aps=aps, bssids=body.bssids)
    conjunto = repo.crear(
        plano_id=plano_id,
        nombre=nombre,
        proposito=proposito,
        descripcion=body.descripcion,
        es_principal=body.es_principal,
        items=items,
        origen="manual_web" if current_user.rol == "admin" else "manual_movil",
        estado_gobernanza=(
            "pendiente_revision" if current_user.rol == "admin" else "borrador_tecnico"
        ),
        creado_por_id=current_user.id,
    )
    return _conjunto_out(conjunto)


@router_conjuntos_ap.get(
    "/{conjunto_id}",
    response_model=ConjuntoAPOut,
    summary="Obtener conjunto de APs",
)
def obtener_conjunto_ap(
    conjunto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ConjuntoAPOut:
    conjunto = _verificar_ownership_conjunto(
        conjunto_id=conjunto_id,
        current_user=current_user,
        db=db,
    )
    return _conjunto_out(conjunto)


@router_conjuntos_ap.patch(
    "/{conjunto_id}",
    response_model=ConjuntoAPOut,
    summary="Actualizar conjunto de APs",
)
def actualizar_conjunto_ap(
    conjunto_id: int,
    body: ConjuntoAPActualizarIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ConjuntoAPOut:
    conjunto = _verificar_ownership_conjunto(
        conjunto_id=conjunto_id,
        current_user=current_user,
        db=db,
    )
    repo = ConjuntoAPRepository(db)
    nombre = body.nombre.strip() if body.nombre is not None else None
    if nombre is not None and repo.existe_nombre(
        plano_id=conjunto.plano_id,
        nombre=nombre,
        excluir_id=conjunto.id,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un conjunto de APs con ese nombre en el plano.",
        )
    items = None
    if body.bssids is not None:
        aps = MedicionRepository(db).listar_aps_por_plano(plano_id=conjunto.plano_id)
        items = _resolver_items_conjunto(aps=aps, bssids=body.bssids)
    if body.estado_gobernanza is not None and current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el panel web admin puede cambiar el estado del conjunto.",
        )
    descripcion = (
        body.descripcion
        if "descripcion" in body.model_fields_set
        else conjunto.descripcion
    )
    actualizado = repo.actualizar(
        conjunto=conjunto,
        nombre=nombre,
        proposito=body.proposito.strip() if body.proposito is not None else None,
        descripcion=descripcion,
        es_principal=body.es_principal,
        items=items,
        estado_gobernanza=body.estado_gobernanza,
    )
    return _conjunto_out(actualizado)


@router_conjuntos_ap.delete(
    "/{conjunto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar conjunto de APs",
)
def eliminar_conjunto_ap(
    conjunto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> Response:
    conjunto = _verificar_ownership_conjunto(
        conjunto_id=conjunto_id,
        current_user=current_user,
        db=db,
    )
    ConjuntoAPRepository(db).eliminar(conjunto=conjunto)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_conjuntos_ap.patch(
    "/{conjunto_id}/ubicacion-ap",
    response_model=ConjuntoAPOut,
    summary="Actualizar ubicación de un AP dentro del conjunto",
)
def actualizar_ubicacion_ap_conjunto(
    conjunto_id: int,
    body: ActualizarUbicacionAPConjuntoIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> ConjuntoAPOut:
    conjunto = _verificar_ownership_conjunto(
        conjunto_id=conjunto_id,
        current_user=current_user,
        db=db,
    )
    repo = ConjuntoAPRepository(db)
    actualizado = repo.actualizar_ubicacion_ap(
        conjunto=conjunto,
        bssid=body.bssid.lower(),
        pos_x=body.pos_x,
        pos_y=body.pos_y,
    )
    if actualizado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El AP no pertenece al conjunto.",
        )
    return _conjunto_out(actualizado)


@router_conjuntos_ap.post(
    "/{conjunto_id}/heatmaps",
    response_model=MapaCalorOut,
    summary="Generar heatmap desde conjunto de APs",
)
def generar_heatmap_conjunto(
    conjunto_id: int,
    body: GenerarHeatmapConjuntoIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> MapaCalorOut:
    conjunto = _verificar_ownership_conjunto(
        conjunto_id=conjunto_id,
        current_user=current_user,
        db=db,
    )
    bssids_conjunto = [item.bssid for item in conjunto.items]
    bssids_solicitados = _normalizar_bssids(body.bssids or [])
    if body.modo == "CONJUNTO_COMPLETO":
        bssids_generacion = bssids_conjunto
    elif body.modo == "INDIVIDUAL":
        if len(bssids_solicitados) != 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El modo INDIVIDUAL requiere exactamente un AP del conjunto.",
            )
        bssids_generacion = bssids_solicitados
    else:
        if not bssids_solicitados:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El modo SUBCONJUNTO requiere al menos un AP del conjunto.",
            )
        bssids_generacion = bssids_solicitados

    fuera_del_conjunto = [
        bssid for bssid in bssids_generacion if bssid not in bssids_conjunto
    ]
    if fuera_del_conjunto:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uno o más APs seleccionados no pertenecen al conjunto.",
        )

    if (body.ap_pos_x is None) != (body.ap_pos_y is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Las coordenadas X/Y de los APs del conjunto deben enviarse juntas.",
        )
    posiciones_request_completas = (
        body.ap_pos_x is not None
        and body.ap_pos_y is not None
        and len(body.ap_pos_x) == len(bssids_generacion)
        and len(body.ap_pos_y) == len(bssids_generacion)
    )
    if body.ap_pos_x is not None and not posiciones_request_completas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La cantidad de coordenadas no coincide con los APs seleccionados.",
        )
    if posiciones_request_completas:
        ap_pos_x = body.ap_pos_x
        ap_pos_y = body.ap_pos_y
    else:
        items_por_bssid = {item.bssid: item for item in conjunto.items}
        ap_pos_x = [
            items_por_bssid[bssid].pos_x
            for bssid in bssids_generacion
            if items_por_bssid[bssid].pos_x is not None
        ]
        ap_pos_y = [
            items_por_bssid[bssid].pos_y
            for bssid in bssids_generacion
            if items_por_bssid[bssid].pos_y is not None
        ]
    posiciones_completas = len(ap_pos_x) == len(bssids_generacion) and len(
        ap_pos_y
    ) == len(bssids_generacion)

    return _generar_heatmap_core(
        plano_id=conjunto.plano_id,
        request=request,
        bssid=bssids_generacion,
        ap_pos_x=ap_pos_x if posiciones_completas else None,
        ap_pos_y=ap_pos_y if posiciones_completas else None,
        algoritmo=body.algoritmo,
        resolucion=body.resolucion,
        db=db,
        current_user=current_user,
        conjunto_ap_id=conjunto.id,
        modo_generacion=body.modo,
    )


@router_mapas.post(
    "/{mapa_id}/analisis",
    response_model=AnalisisCoberturaOut,
    summary="Analizar cobertura del mapa",
    description="Regenera de forma idempotente el análisis automático. PB-06.",
)
def analizar_mapa(
    mapa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> AnalisisCoberturaOut:
    mapa = _verificar_ownership_mapa(
        mapa_id=mapa_id,
        current_user=current_user,
        db=db,
    )
    plano = mapa.plano
    aps_referencia = mapa.aps_interes or [
        {
            "bssid": mapa.bssid,
            "pos_x": mapa.ap_pos_x,
            "pos_y": mapa.ap_pos_y,
        }
    ]
    bssids_interes = {ap["bssid"] for ap in aps_referencia}
    mediciones = [
        medicion
        for medicion in MedicionRepository(db).listar_mediciones_por_plano(
            plano_id=mapa.plano_id,
        )
        if medicion.bssid in bssids_interes
    ]
    datos = AnalisisCoberturaService().analizar(
        matriz=mapa.matriz,
        mediciones=mediciones,
        ancho_px=plano.ancho_px,
        alto_px=plano.alto_px,
        aps_referencia=aps_referencia,
    )
    analisis = AnalisisCoberturaRepository(db).reemplazar(
        mapa=mapa,
        pct_cobertura=datos["pct_cobertura"],
        pct_zonas_muertas=datos["pct_zonas_muertas"],
        celdas_zonas_muertas=datos["celdas_zonas_muertas"],
        cantidad_solapamientos=datos["cantidad_solapamientos"],
        cantidad_interferencias=datos["cantidad_interferencias"],
        hallazgos=datos["hallazgos"],
        resumen=datos["resumen"],
        aps_detectados=datos["aps_detectados"],
    )
    return AnalisisCoberturaOut.model_validate(analisis)


@router_aps.patch(
    "/{ap_id}",
    response_model=APDetectadoOut,
    summary="Confirmar ubicación estimada de AP",
)
def confirmar_ap(
    ap_id: int,
    body: ConfirmarAPIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> APDetectadoOut:
    repo = AnalisisCoberturaRepository(db)
    ap = repo.obtener_ap_por_id(ap_id=ap_id)
    if ap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AP detectado no encontrado.",
        )
    _verificar_ownership_mapa(
        mapa_id=ap.analisis.mapa_calor_id,
        current_user=current_user,
        db=db,
    )
    actualizado = repo.confirmar_ap(
        ap=ap,
        pos_x=body.pos_x,
        pos_y=body.pos_y,
        confirmado=body.confirmado,
    )
    return APDetectadoOut.model_validate(actualizado)


@router_mapas.get(
    "/archivo/{ruta:path}",
    summary="Descargar imagen de heatmap (URL firmada)",
)
def descargar_imagen_heatmap(
    ruta: str,
    exp: int = Query(...),
    sig: str = Query(...),
    db: Session = Depends(get_db),
) -> Response:
    if not verificar_firma(
        ruta_relativa=ruta,
        secret=settings.storage_url_secret,
        exp=exp,
        sig=sig,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Firma inválida o URL expirada.",
        )

    mapa = MapaCalorRepository(db).obtener_por_ruta(ruta_imagen=ruta)
    if mapa is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mapa de calor no encontrado.",
        )
    storage = _storage()
    if not storage.exists(ruta):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada en storage.",
        )
    media_type = (
        "image/png"
        if Path(ruta).suffix.lower() == ".png"
        else "application/octet-stream"
    )
    return Response(content=storage.read(ruta), media_type=media_type)
