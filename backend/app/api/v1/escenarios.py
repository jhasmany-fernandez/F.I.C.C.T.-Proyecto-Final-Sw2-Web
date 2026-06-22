"""Endpoints Sprint 5: IA, comparación y reportes."""

from __future__ import annotations

import hashlib
import secrets
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.ai.optimizador_ap_service import OptimizadorAPService
from app.api.v1.heatmaps import _mapa_out
from app.core.config import settings
from app.core.database import get_db
from app.core.security import require_admin
from app.models.escenario import EscenarioOptimizado, Reporte, ValorProyectadoPunto
from app.models.heatmap import ConjuntoAP, MapaCalor
from app.models.inventario_rf import APFisico, BSSIDRadio, RadioAP
from app.models.medicion import MedicionWifi, PuntoMedicion
from app.models.plano import Plano
from app.models.proyecto import Proyecto
from app.models.usuario import Usuario
from app.repositories.escenario_repository import EscenarioRepository, ReporteRepository
from app.repositories.heatmap_repository import MapaCalorRepository
from app.repositories.medicion_repository import MedicionRepository
from app.repositories.proyecto_repository import ProyectoRepository
from app.schemas.escenario import (
    CambiarEstadoEscenarioIn,
    ComparacionEscenarioOut,
    EscenarioOptimizadoOut,
    EscenariosGeneradosOut,
    ReporteCrearIn,
    ReporteOut,
    RestriccionesEscenarioIn,
    ResumenComparacionOut,
    ValorProyectadoPuntoOut,
)
from app.services.interpolacion_service import (
    ESCALA_CWNA,
    HeatmapImageService,
    InterpolacionService,
    PuntoRSSI,
)
from app.services.reporte_service import ReporteService
from app.storage import LocalFilesystemStorage, generar_url_firmada, verificar_firma

router_proyectos_escenarios = APIRouter(prefix="/proyectos", tags=["escenarios"])
router_escenarios = APIRouter(prefix="/escenarios", tags=["escenarios"])
router_reportes = APIRouter(prefix="/reportes", tags=["reportes"])


def _storage() -> LocalFilesystemStorage:
    return LocalFilesystemStorage(root=settings.storage_root)


def _firmar_descarga(ruta: str) -> str:
    return generar_url_firmada(
        ruta_relativa=ruta,
        secret=settings.storage_url_secret,
        base_url=settings.public_api_url,
        ttl_seconds=24 * 3600,
    ).replace("/planos/archivo/", "/reportes/archivo/", 1)


def _proyecto_tecnico(
    *,
    proyecto_id: int,
    current_user: Usuario,
    db: Session,
) -> Proyecto:
    proyecto = ProyectoRepository(db).obtener_por_id(
        proyecto_id=proyecto_id,
        tecnico_id=current_user.id,
    )
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    return proyecto


def _proyecto_admin(
    *,
    proyecto_id: int,
    current_user: Usuario,
    db: Session,
) -> Proyecto:
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La generación IA está restringida al panel web admin.",
        )
    proyecto = ProyectoRepository(db).obtener_por_id_admin(proyecto_id=proyecto_id)
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    return proyecto


def _escenario_tecnico(
    *,
    escenario_id: int,
    current_user: Usuario,
    db: Session,
) -> EscenarioOptimizado:
    escenario = EscenarioRepository(db).obtener_por_id(escenario_id=escenario_id)
    if escenario is None:
        raise HTTPException(status_code=404, detail="Escenario no encontrado.")
    _proyecto_tecnico(
        proyecto_id=escenario.proyecto_id,
        current_user=current_user,
        db=db,
    )
    return escenario


def _escenario_admin(
    *,
    escenario_id: int,
    current_user: Usuario,
    db: Session,
) -> EscenarioOptimizado:
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los escenarios IA están restringidos al panel web admin.",
        )
    escenario = EscenarioRepository(db).obtener_por_id(escenario_id=escenario_id)
    if escenario is None:
        raise HTTPException(status_code=404, detail="Escenario no encontrado.")
    _proyecto_admin(
        proyecto_id=escenario.proyecto_id,
        current_user=current_user,
        db=db,
    )
    return escenario


def _reporte_tecnico(
    *,
    reporte_id: int,
    current_user: Usuario,
    db: Session,
) -> Reporte:
    reporte = ReporteRepository(db).obtener_por_id(reporte_id=reporte_id)
    if reporte is None:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    _proyecto_tecnico(
        proyecto_id=reporte.proyecto_id,
        current_user=current_user,
        db=db,
    )
    return reporte


def _reporte_admin(
    *,
    reporte_id: int,
    current_user: Usuario,
    db: Session,
) -> Reporte:
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Los reportes IA están restringidos al panel web admin.",
        )
    reporte = ReporteRepository(db).obtener_por_id(reporte_id=reporte_id)
    if reporte is None:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    _proyecto_admin(
        proyecto_id=reporte.proyecto_id,
        current_user=current_user,
        db=db,
    )
    return reporte


def _plano_base(proyecto: Proyecto) -> Plano:
    planos = sorted(proyecto.planos, key=lambda p: p.created_at or p.id, reverse=True)
    plano = next((p for p in planos if p.calibrado), None)
    if plano is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El proyecto requiere al menos un plano calibrado.",
        )
    return plano


def _plano_escenario(
    *,
    proyecto: Proyecto,
    plano_id: int | None,
    db: Session,
) -> Plano:
    if plano_id is None:
        return _plano_base(proyecto)
    plano = (
        db.query(Plano)
        .filter(Plano.id == plano_id, Plano.proyecto_id == proyecto.id)
        .first()
    )
    if plano is None:
        raise HTTPException(status_code=404, detail="Plano no encontrado.")
    if not plano.calibrado:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El plano seleccionado debe estar calibrado.",
        )
    return plano


def _aps_existentes_para_ia(
    *,
    plano_id: int,
    body: RestriccionesEscenarioIn,
    db: Session,
) -> list[dict]:
    query = db.query(APFisico).filter(APFisico.plano_id == plano_id)
    fuente = body.fuente_entrada
    if fuente is not None and fuente.tipo == "SELECCION_APS_MAPA":
        if fuente.bssids:
            return []
        ap_ids = list(dict.fromkeys(fuente.ap_ids))
        if not ap_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Debe seleccionar al menos un AP del mapa.",
            )
        query = query.filter(APFisico.id.in_(ap_ids))
    elif fuente is not None and fuente.tipo == "CONJUNTO_EXISTENTE":
        conjunto = _conjunto_fuente_entrada(
            plano_id=plano_id,
            body=body,
            db=db,
        )
        bssids = [item.bssid.lower() for item in conjunto.items]
        query = (
            query.join(RadioAP, RadioAP.ap_fisico_id == APFisico.id)
            .join(BSSIDRadio, BSSIDRadio.radio_id == RadioAP.id)
            .filter(BSSIDRadio.bssid.in_(bssids))
            .distinct()
        )
    aps = query.order_by(APFisico.id.asc()).all()
    if fuente is not None and fuente.tipo == "SELECCION_APS_MAPA":
        encontrados = {ap.id for ap in aps}
        faltantes = [
            ap_id for ap_id in dict.fromkeys(fuente.ap_ids) if ap_id not in encontrados
        ]
        if faltantes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La selección contiene APs que no pertenecen al plano.",
            )
    return [
        {
            "id": ap.id,
            "coord_x": ap.coord_x,
            "coord_y": ap.coord_y,
            "altura_m": ap.altura_m,
            "tipo_montaje": ap.tipo_montaje,
            "restriccion_movimiento": ap.restriccion_movimiento,
            "verificado": ap.verificado,
        }
        for ap in aps
    ]


def _bssids_fuente_entrada(
    *,
    plano: Plano,
    body: RestriccionesEscenarioIn,
    db: Session,
) -> list[str] | None:
    fuente = body.fuente_entrada
    if fuente is not None and fuente.tipo == "CONJUNTO_EXISTENTE":
        conjunto = _conjunto_fuente_entrada(
            plano_id=plano.id,
            body=body,
            db=db,
        )
        solicitados = [item.bssid.lower() for item in conjunto.items]
    elif fuente is not None and fuente.tipo == "SELECCION_APS_MAPA" and fuente.bssids:
        solicitados = [bssid.lower() for bssid in dict.fromkeys(fuente.bssids)]
    else:
        return None
    disponibles = {
        ap["bssid"]
        for ap in MedicionRepository(db).listar_aps_por_plano(plano_id=plano.id)
    }
    faltantes = [bssid for bssid in solicitados if bssid not in disponibles]
    if faltantes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La selección contiene APs que no pertenecen al plano.",
        )
    return solicitados


def _conjunto_fuente_entrada(
    *, plano_id: int, body: RestriccionesEscenarioIn, db: Session
) -> ConjuntoAP:
    fuente = body.fuente_entrada
    if fuente is None or fuente.tipo != "CONJUNTO_EXISTENTE":
        raise HTTPException(
            status_code=422,
            detail="La fuente no es un conjunto existente.",
        )
    if fuente.conjunto_id is None:
        raise HTTPException(
            status_code=422,
            detail="Debe seleccionar un conjunto de APs existente.",
        )
    conjunto = (
        db.query(ConjuntoAP)
        .filter(ConjuntoAP.id == fuente.conjunto_id, ConjuntoAP.plano_id == plano_id)
        .first()
    )
    if conjunto is None:
        raise HTTPException(
            status_code=422,
            detail="El conjunto seleccionado no pertenece al plano.",
        )
    if not conjunto.items:
        raise HTTPException(
            status_code=422,
            detail="El conjunto seleccionado no contiene APs.",
        )
    return conjunto


def _mapa_actual(
    *,
    plano: Plano,
    db: Session,
    bssids_seleccionados: list[str] | None = None,
) -> tuple[MapaCalor, list[PuntoRSSI]]:
    mapa_repo = MapaCalorRepository(db)
    med_repo = MedicionRepository(db)
    mapa = next(
        (
            item
            for item in mapa_repo.listar_recientes_por_plano(plano_id=plano.id)
            if item.modo_generacion != "PROYECTADO"
        ),
        None,
    )
    aps = med_repo.listar_aps_por_plano(plano_id=plano.id)
    bssids = bssids_seleccionados or [ap["bssid"] for ap in aps]
    if not bssids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No hay APs medidos para generar escenarios.",
        )
    puntos = med_repo.listar_puntos_rssi_heatmap(plano_id=plano.id, bssids=bssids)
    if len(puntos) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Se requieren al menos 5 puntos de medición para IA.",
        )
    if mapa is not None and bssids_seleccionados is None:
        return mapa, puntos

    matriz = InterpolacionService().interpolar(
        puntos=puntos,
        ancho_px=plano.ancho_px,
        alto_px=plano.alto_px,
        resolucion=64,
        algoritmo="IDW",
    )
    ruta = f"heatmaps/sp5_actual_{plano.id}_{secrets.token_hex(8)}.png"
    _storage().save(HeatmapImageService().render_png(matriz), ruta)
    firma = hashlib.sha1(
        f"sp5-actual:{plano.id}:{med_repo.firma_mediciones_plano(plano_id=plano.id)}".encode(),
        usedforsecurity=False,
    ).hexdigest()
    aps_interes = [ap for ap in aps if ap["bssid"] in set(bssids)]
    mapa = mapa_repo.crear(
        plano_id=plano.id,
        modo_generacion="SUBCONJUNTO",
        algoritmo="IDW",
        resolucion=64,
        bssid=aps_interes[0]["bssid"],
        ssid=aps_interes[0]["ssid"],
        ap_pos_x=aps_interes[0]["pos_x"],
        ap_pos_y=aps_interes[0]["pos_y"],
        aps_interes=aps_interes,
        bssids_generacion=bssids,
        matriz=matriz,
        escala=ESCALA_CWNA,
        ruta_imagen=ruta,
        cantidad_puntos=len(puntos),
        rssi_min=min(min(fila) for fila in matriz),
        rssi_max=max(max(fila) for fila in matriz),
        firma_mediciones=firma,
    )
    return mapa, puntos


@router_proyectos_escenarios.post(
    "/{proyecto_id}/escenarios",
    response_model=EscenariosGeneradosOut,
    status_code=status.HTTP_201_CREATED,
)
def generar_escenarios(
    proyecto_id: int,
    body: RestriccionesEscenarioIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> EscenariosGeneradosOut:
    proyecto = _proyecto_admin(
        proyecto_id=proyecto_id, current_user=current_user, db=db
    )
    plano = _plano_escenario(proyecto=proyecto, plano_id=body.plano_id, db=db)
    conjunto_fuente = (
        _conjunto_fuente_entrada(plano_id=plano.id, body=body, db=db)
        if body.fuente_entrada is not None
        and body.fuente_entrada.tipo == "CONJUNTO_EXISTENTE"
        else None
    )
    bssids_seleccionados = _bssids_fuente_entrada(plano=plano, body=body, db=db)
    mapa_actual, puntos = _mapa_actual(
        plano=plano,
        db=db,
        bssids_seleccionados=bssids_seleccionados,
    )
    mapas_actuales_por_banda = _mapas_actuales_por_banda(
        plano=plano,
        bandas=body.bandas,
        resolucion=body.resolucion,
        db=db,
        bssids_seleccionados=bssids_seleccionados,
    )
    optimizador = OptimizadorAPService()
    aps_existentes = _aps_existentes_para_ia(plano_id=plano.id, body=body, db=db)
    banda_objetivo = "5" if "5" in body.bandas else body.bandas[0]
    alternativas = optimizador.optimizar(
        puntos_actuales=puntos,
        matriz_actual=mapa_actual.matriz,
        ancho_px=plano.ancho_px,
        alto_px=plano.alto_px,
        metros_por_pixel=plano.escala_m_por_px or 1.0,
        max_aps=body.max_aps,
        banda=banda_objetivo,
        resolucion=body.resolucion,
        umbral_objetivo_dbm=body.umbral_objetivo_dbm,
        bandas=body.bandas,
        aps_existentes=aps_existentes,
    )
    observados_por_banda = _observados_por_punto_y_banda(db=db, plano_id=plano.id)
    mapa_repo = MapaCalorRepository(db)
    escenario_repo = EscenarioRepository(db)
    escenarios: list[EscenarioOptimizado] = []
    for idx, alternativa in enumerate(alternativas, start=1):
        for valor in alternativa.valores_proyectados:
            observado = observados_por_banda.get(
                (valor["punto_medicion_id"], valor["banda"])
            )
            valor["rssi_observado_dbm"] = observado
            valor["diferencia_db"] = (
                round(valor["rssi_proyectado_dbm"] - observado, 2)
                if observado is not None
                else None
            )
        ruta = f"heatmaps/sp5_proyectado_{proyecto.id}_{idx}_{secrets.token_hex(8)}.png"
        _storage().save(HeatmapImageService().render_png(alternativa.matriz), ruta)
        firma = hashlib.sha1(
            f"sp5-proyectado:{proyecto.id}:{idx}:{secrets.token_hex(8)}".encode(),
            usedforsecurity=False,
        ).hexdigest()
        mapa_proyectado = mapa_repo.crear(
            plano_id=plano.id,
            modo_generacion="PROYECTADO",
            algoritmo="FSPL",
            resolucion=body.resolucion,
            bssid=f"sp5:{idx:02d}:00:00:00",
            ssid=alternativa.nombre,
            ap_pos_x=alternativa.recomendaciones[0]["coord_x"],
            ap_pos_y=alternativa.recomendaciones[0]["coord_y"],
            aps_interes=[
                {
                    "bssid": f"sp5:{idx:02d}:{rec_idx:02d}:00:00",
                    "ssid": rec["modelo_ap"],
                    "canal": None,
                    "frecuencia_mhz": None,
                    "rssi_promedio": rec["rssi_proyectado"],
                    "pos_x": rec["coord_x"],
                    "pos_y": rec["coord_y"],
                    "cantidad_puntos": len(puntos),
                }
                for rec_idx, rec in enumerate(alternativa.recomendaciones, start=1)
            ],
            bssids_generacion=[
                f"sp5:{idx:02d}:{rec_idx:02d}:00:00"
                for rec_idx, _ in enumerate(alternativa.recomendaciones, start=1)
            ],
            matriz=alternativa.matriz,
            escala=ESCALA_CWNA,
            ruta_imagen=ruta,
            cantidad_puntos=len(puntos),
            rssi_min=min(min(fila) for fila in alternativa.matriz),
            rssi_max=max(max(fila) for fila in alternativa.matriz),
            firma_mediciones=firma,
        )
        escenario = escenario_repo.crear(
            proyecto_id=proyecto.id,
            plano_id=plano.id,
            mapa_actual_id=mapa_actual.id,
            mapa_proyectado_id=mapa_proyectado.id,
            conjunto_base_id=conjunto_fuente.id if conjunto_fuente else None,
            generado_por_id=current_user.id,
            nombre=alternativa.nombre,
            banda=alternativa.banda,
            modelo_ap=alternativa.modelo_ap,
            pct_cobertura_actual=alternativa.pct_cobertura_actual,
            pct_cobertura=alternativa.pct_cobertura,
            costo_estimado=alternativa.costo_estimado,
            cantidad_aps=alternativa.cantidad_aps,
            resumen=alternativa.resumen,
            restricciones=body.model_dump(),
            metricas=alternativa.metricas,
            recomendaciones=alternativa.recomendaciones,
            tipo_negocio="OPTIMIZACION_COBERTURA",
            perfil="MAXIMIZAR_COBERTURA",
            politica_combinacion="COBERTURA_POR_BANDA",
            bandas=body.bandas,
            mapas_por_banda=alternativa.mapas_por_banda,
            mapas_actuales_por_banda=mapas_actuales_por_banda,
            supuestos=alternativa.supuestos,
            confianza=alternativa.confianza,
            valores_proyectados=alternativa.valores_proyectados,
        )
        escenarios.append(escenario)
    return EscenariosGeneradosOut(
        escenarios=[EscenarioOptimizadoOut.model_validate(e) for e in escenarios]
    )


@router_proyectos_escenarios.get(
    "/{proyecto_id}/escenarios",
    response_model=list[EscenarioOptimizadoOut],
)
def listar_escenarios_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> list[EscenarioOptimizadoOut]:
    proyecto = _proyecto_admin(
        proyecto_id=proyecto_id, current_user=current_user, db=db
    )
    escenarios = EscenarioRepository(db).listar_por_proyecto(proyecto_id=proyecto.id)
    return [EscenarioOptimizadoOut.model_validate(e) for e in escenarios]


@router_proyectos_escenarios.delete("/{proyecto_id}/escenarios")
def eliminar_escenarios_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> dict[str, int]:
    proyecto = _proyecto_admin(
        proyecto_id=proyecto_id,
        current_user=current_user,
        db=db,
    )
    eliminados = EscenarioRepository(db).eliminar_por_proyecto(
        proyecto_id=proyecto.id,
    )
    return {"eliminados": eliminados}


@router_escenarios.get(
    "/{escenario_id}/comparacion", response_model=ComparacionEscenarioOut
)
def comparar_escenario(
    escenario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> ComparacionEscenarioOut:
    escenario = _escenario_admin(
        escenario_id=escenario_id, current_user=current_user, db=db
    )
    if escenario.mapa_actual is None or escenario.mapa_proyectado is None:
        raise HTTPException(
            status_code=409, detail="El escenario no tiene mapas asociados."
        )
    actual = escenario.mapa_actual.matriz
    proyectado = escenario.mapa_proyectado.matriz
    filas = min(len(actual), len(proyectado))
    cols = min(len(actual[0]), len(proyectado[0])) if filas else 0
    diferencia = [
        [round(proyectado[y][x] - actual[y][x], 2) for x in range(cols)]
        for y in range(filas)
    ]
    delta_muertas = _contar_zonas_muertas(proyectado) - _contar_zonas_muertas(actual)
    comparacion_por_banda = {}
    for banda, matriz in (escenario.mapas_por_banda or {}).items():
        actual_banda = (escenario.mapas_actuales_por_banda or {}).get(banda)
        filas_banda = min(len(actual_banda or []), len(matriz))
        cols_banda = (
            min(len(actual_banda[0]), len(matriz[0]))
            if filas_banda and actual_banda
            else 0
        )
        comparacion_por_banda[banda] = {
            "matriz_actual": actual_banda,
            "matriz_proyectada": matriz,
            "matriz_diferencia": (
                [
                    [
                        round(matriz[y][x] - actual_banda[y][x], 2)
                        for x in range(cols_banda)
                    ]
                    for y in range(filas_banda)
                ]
                if actual_banda
                else None
            ),
            "pct_cobertura_proyectada": escenario.metricas.get(
                "pct_cobertura_por_banda", {}
            ).get(banda),
        }
    return ComparacionEscenarioOut(
        escenario=EscenarioOptimizadoOut.model_validate(escenario),
        heatmap_actual=_mapa_out(escenario.mapa_actual, request),
        heatmap_proyectado=_mapa_out(escenario.mapa_proyectado, request),
        matriz_diferencia=diferencia,
        comparacion_por_banda=comparacion_por_banda,
        resumen=ResumenComparacionOut(
            delta_pct_cobertura=round(
                escenario.pct_cobertura - escenario.pct_cobertura_actual,
                2,
            ),
            delta_zonas_muertas=delta_muertas,
            costo_estimado=escenario.costo_estimado,
            cantidad_cambios=len(escenario.recomendaciones),
            lectura="verde = mejora RSSI, rojo = degradacion",
        ),
    )


@router_escenarios.get(
    "/{escenario_id}/puntos-proyectados",
    response_model=list[ValorProyectadoPuntoOut],
)
def listar_puntos_proyectados(
    escenario_id: int,
    banda: str | None = Query(default=None, pattern=r"^(2\.4|5)$"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> list[ValorProyectadoPuntoOut]:
    _escenario_admin(escenario_id=escenario_id, current_user=current_user, db=db)
    query = db.query(ValorProyectadoPunto).filter(
        ValorProyectadoPunto.escenario_id == escenario_id
    )
    if banda:
        query = query.filter(ValorProyectadoPunto.banda == banda)
    valores = query.order_by(
        ValorProyectadoPunto.punto_medicion_id.asc(),
        ValorProyectadoPunto.banda.asc(),
    ).all()
    return [ValorProyectadoPuntoOut.model_validate(item) for item in valores]


@router_escenarios.patch(
    "/{escenario_id}/estado", response_model=EscenarioOptimizadoOut
)
def cambiar_estado_escenario(
    escenario_id: int,
    body: CambiarEstadoEscenarioIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> EscenarioOptimizadoOut:
    escenario = _escenario_admin(
        escenario_id=escenario_id, current_user=current_user, db=db
    )
    actualizado = EscenarioRepository(db).cambiar_estado(
        escenario=escenario,
        estado_gobernanza=body.estado_gobernanza,
        usuario_id=current_user.id,
    )
    return EscenarioOptimizadoOut.model_validate(actualizado)


@router_escenarios.delete("/{escenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_escenario(
    escenario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> Response:
    escenario = _escenario_admin(
        escenario_id=escenario_id,
        current_user=current_user,
        db=db,
    )
    EscenarioRepository(db).eliminar(escenario=escenario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router_proyectos_escenarios.post(
    "/{proyecto_id}/reportes", response_model=ReporteOut, status_code=201
)
def crear_reporte(
    proyecto_id: int,
    body: ReporteCrearIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> ReporteOut:
    proyecto = _proyecto_admin(
        proyecto_id=proyecto_id, current_user=current_user, db=db
    )
    escenario = None
    if body.escenario_id is not None:
        escenario = _escenario_admin(
            escenario_id=body.escenario_id,
            current_user=current_user,
            db=db,
        )
    repo = ReporteRepository(db)
    reporte = repo.crear_procesando(
        proyecto_id=proyecto.id, escenario_id=body.escenario_id
    )
    try:
        escenarios = EscenarioRepository(db).listar_por_proyecto(
            proyecto_id=proyecto.id
        )
        cantidad_mediciones = sum(
            len(p.mediciones)
            for plano in proyecto.planos
            for p in plano.puntos_medicion
        )
        generado = ReporteService().generar(
            proyecto=proyecto,
            escenarios=escenarios,
            escenario_seleccionado=escenario,
            cantidad_mediciones=cantidad_mediciones,
        )
        ruta = f"reportes/proyecto_{proyecto.id}/reporte_{reporte.id}.pdf"
        _storage().save(generado.contenido, ruta)
        reporte = repo.marcar_listo(
            reporte=reporte,
            ruta_pdf=ruta,
            sha256=generado.sha256,
            tamanio_bytes=generado.tamanio_bytes,
        )
    except Exception as exc:
        reporte = repo.marcar_error(reporte=reporte, error=str(exc))
    return _reporte_out(reporte)


@router_proyectos_escenarios.get(
    "/{proyecto_id}/reportes", response_model=list[ReporteOut]
)
def listar_reportes_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> list[ReporteOut]:
    proyecto = _proyecto_admin(
        proyecto_id=proyecto_id, current_user=current_user, db=db
    )
    return [
        _reporte_out(reporte)
        for reporte in ReporteRepository(db).listar_por_proyecto(
            proyecto_id=proyecto.id
        )
    ]


@router_reportes.get("/archivo/{ruta:path}")
def descargar_reporte_firmado(
    ruta: str,
    exp: int = Query(...),
    sig: str = Query(...),
) -> Response:
    ruta_relativa = unquote(ruta)
    if not ruta_relativa.startswith("reportes/"):
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    if not verificar_firma(
        ruta_relativa=ruta_relativa,
        secret=settings.storage_url_secret,
        exp=exp,
        sig=sig,
    ):
        raise HTTPException(status_code=403, detail="URL expirada o invalida.")
    storage = _storage()
    if not storage.exists(ruta_relativa):
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    return Response(
        content=storage.read(ruta_relativa),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{Path(ruta_relativa).name}"'
        },
    )


@router_reportes.get("/{reporte_id}", response_model=ReporteOut)
def obtener_reporte(
    reporte_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> ReporteOut:
    reporte = _reporte_admin(reporte_id=reporte_id, current_user=current_user, db=db)
    return _reporte_out(reporte)


@router_reportes.get("/{reporte_id}/descargar")
def descargar_reporte(
    reporte_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin),
) -> Response:
    reporte = _reporte_admin(reporte_id=reporte_id, current_user=current_user, db=db)
    if reporte.estado != "LISTO" or not reporte.ruta_pdf:
        raise HTTPException(status_code=409, detail="El reporte aun no esta listo.")
    contenido = _storage().read(reporte.ruta_pdf)
    return Response(
        content=contenido,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="reporte-{reporte.id}.pdf"'
        },
    )


def _contar_zonas_muertas(matriz: list[list[float]]) -> int:
    return sum(1 for fila in matriz for valor in fila if valor < -90)


def _observados_por_punto_y_banda(
    *, db: Session, plano_id: int
) -> dict[tuple[int, str], float]:
    """Promedia lecturas reales por punto y banda sin alterar su persistencia."""
    filas = (
        db.query(MedicionWifi)
        .join(PuntoMedicion, MedicionWifi.punto_id == PuntoMedicion.id)
        .filter(PuntoMedicion.plano_id == plano_id)
        .all()
    )
    acumulados: dict[tuple[int, str], list[float]] = {}
    for medicion in filas:
        if medicion.frecuencia_mhz is None:
            continue
        banda = "2.4" if medicion.frecuencia_mhz < 3000 else "5"
        acumulados.setdefault((medicion.punto_id, banda), []).append(
            float(medicion.rssi)
        )
    return {
        clave: round(sum(valores) / len(valores), 2)
        for clave, valores in acumulados.items()
    }


def _mapas_actuales_por_banda(
    *,
    plano: Plano,
    bandas: list[str],
    resolucion: int,
    db: Session,
    bssids_seleccionados: list[str] | None = None,
) -> dict[str, list[list[float]] | None]:
    """Construye baselines observados independientes por banda."""
    repo = MedicionRepository(db)
    aps = repo.listar_aps_por_plano(plano_id=plano.id)
    resultado: dict[str, list[list[float]] | None] = {}
    for banda in bandas:
        bssids = [
            ap["bssid"]
            for ap in aps
            if (bssids_seleccionados is None or ap["bssid"] in bssids_seleccionados)
            if ap.get("frecuencia_mhz") is not None
            and (
                (banda == "2.4" and ap["frecuencia_mhz"] < 3000)
                or (banda == "5" and ap["frecuencia_mhz"] >= 3000)
            )
        ]
        puntos = repo.listar_puntos_rssi_heatmap(plano_id=plano.id, bssids=bssids)
        resultado[banda] = (
            InterpolacionService().interpolar(
                puntos=puntos,
                ancho_px=plano.ancho_px,
                alto_px=plano.alto_px,
                resolucion=resolucion,
                algoritmo="IDW",
            )
            if len(puntos) >= 5
            else None
        )
    return resultado


def _reporte_out(reporte: Reporte) -> ReporteOut:
    return ReporteOut(
        id=reporte.id,
        proyecto_id=reporte.proyecto_id,
        escenario_id=reporte.escenario_id,
        estado=reporte.estado,
        url_descarga=_firmar_descarga(reporte.ruta_pdf) if reporte.ruta_pdf else None,
        sha256=reporte.sha256,
        tamanio_bytes=reporte.tamanio_bytes,
        error=reporte.error,
        created_at=reporte.created_at,
        updated_at=reporte.updated_at,
    )
