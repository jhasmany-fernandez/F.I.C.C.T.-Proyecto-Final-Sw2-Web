"""Repositorios del módulo de heatmap y análisis.

Sprint 4 — PB-05, PB-06.
"""

from sqlalchemy.orm import Session

from app.models.heatmap import (
    AnalisisCobertura,
    APDetectado,
    ConjuntoAP,
    ConjuntoAPItem,
    MapaCalor,
)


class MapaCalorRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def obtener_por_id(self, *, mapa_id: int) -> MapaCalor | None:
        return self._db.query(MapaCalor).filter(MapaCalor.id == mapa_id).first()

    def obtener_por_ruta(self, *, ruta_imagen: str) -> MapaCalor | None:
        return (
            self._db.query(MapaCalor)
            .filter(MapaCalor.ruta_imagen == ruta_imagen)
            .first()
        )

    def obtener_cache(
        self,
        *,
        plano_id: int,
        algoritmo: str,
        resolucion: int,
        firma_mediciones: str,
    ) -> MapaCalor | None:
        return (
            self._db.query(MapaCalor)
            .filter(
                MapaCalor.plano_id == plano_id,
                MapaCalor.algoritmo == algoritmo,
                MapaCalor.resolucion == resolucion,
                MapaCalor.firma_mediciones == firma_mediciones,
            )
            .order_by(MapaCalor.created_at.desc(), MapaCalor.id.desc())
            .first()
        )

    def listar_recientes_por_plano(self, *, plano_id: int) -> list[MapaCalor]:
        return (
            self._db.query(MapaCalor)
            .filter(MapaCalor.plano_id == plano_id)
            .order_by(MapaCalor.created_at.desc(), MapaCalor.id.desc())
            .all()
        )

    def crear(
        self,
        *,
        plano_id: int,
        conjunto_ap_id: int | None = None,
        modo_generacion: str = "SUBCONJUNTO",
        algoritmo: str,
        resolucion: int,
        bssid: str,
        ssid: str,
        ap_pos_x: float,
        ap_pos_y: float,
        aps_interes: list[dict],
        bssids_generacion: list[str] | None = None,
        matriz: list[list[float]],
        escala: list[dict],
        ruta_imagen: str,
        cantidad_puntos: int,
        rssi_min: float,
        rssi_max: float,
        firma_mediciones: str,
    ) -> MapaCalor:
        mapa = MapaCalor(
            plano_id=plano_id,
            conjunto_ap_id=conjunto_ap_id,
            modo_generacion=modo_generacion,
            algoritmo=algoritmo,
            resolucion=resolucion,
            bssid=bssid,
            ssid=ssid,
            ap_pos_x=ap_pos_x,
            ap_pos_y=ap_pos_y,
            aps_interes=aps_interes,
            bssids_generacion=bssids_generacion or [ap["bssid"] for ap in aps_interes],
            matriz=matriz,
            escala=escala,
            ruta_imagen=ruta_imagen,
            cantidad_puntos=cantidad_puntos,
            rssi_min=rssi_min,
            rssi_max=rssi_max,
            firma_mediciones=firma_mediciones,
        )
        self._db.add(mapa)
        self._db.commit()
        self._db.refresh(mapa)
        return mapa

    def invalidar_plano(self, *, plano_id: int) -> None:
        """Elimina mapas cacheados de un plano cuando cambian sus mediciones."""
        (
            self._db.query(MapaCalor)
            .filter(MapaCalor.plano_id == plano_id)
            .delete(synchronize_session=False)
        )


class ConjuntoAPRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def listar_por_plano(self, *, plano_id: int) -> list[ConjuntoAP]:
        return (
            self._db.query(ConjuntoAP)
            .filter(ConjuntoAP.plano_id == plano_id)
            .order_by(ConjuntoAP.updated_at.desc(), ConjuntoAP.id.desc())
            .all()
        )

    def obtener_por_id(self, *, conjunto_id: int) -> ConjuntoAP | None:
        return (
            self._db.query(ConjuntoAP)
            .filter(ConjuntoAP.id == conjunto_id)
            .first()
        )

    def existe_nombre(
        self,
        *,
        plano_id: int,
        nombre: str,
        excluir_id: int | None = None,
    ) -> bool:
        query = self._db.query(ConjuntoAP).filter(
            ConjuntoAP.plano_id == plano_id,
            ConjuntoAP.nombre == nombre,
        )
        if excluir_id is not None:
            query = query.filter(ConjuntoAP.id != excluir_id)
        return self._db.query(query.exists()).scalar() is True

    def crear(
        self,
        *,
        plano_id: int,
        nombre: str,
        proposito: str,
        descripcion: str | None,
        es_principal: bool,
        items: list[dict],
        origen: str = "manual_movil",
        estado_gobernanza: str = "borrador_tecnico",
        creado_por_id: int | None = None,
    ) -> ConjuntoAP:
        conjunto = ConjuntoAP(
            plano_id=plano_id,
            nombre=nombre,
            proposito=proposito,
            descripcion=descripcion,
            es_principal=es_principal,
            origen=origen,
            estado_gobernanza=estado_gobernanza,
            creado_por_id=creado_por_id,
        )
        self._db.add(conjunto)
        self._db.flush()
        self._reemplazar_items(conjunto=conjunto, items=items)
        self._db.commit()
        self._db.refresh(conjunto)
        return conjunto

    def actualizar(
        self,
        *,
        conjunto: ConjuntoAP,
        nombre: str | None = None,
        proposito: str | None = None,
        descripcion: str | None = None,
        es_principal: bool | None = None,
        items: list[dict] | None = None,
        estado_gobernanza: str | None = None,
    ) -> ConjuntoAP:
        if nombre is not None:
            conjunto.nombre = nombre
        if proposito is not None:
            conjunto.proposito = proposito
        if descripcion is not None:
            conjunto.descripcion = descripcion
        if es_principal is not None:
            conjunto.es_principal = es_principal
        if estado_gobernanza is not None:
            conjunto.estado_gobernanza = estado_gobernanza
        if items is not None:
            self._reemplazar_items(conjunto=conjunto, items=items)
        self._db.commit()
        self._db.refresh(conjunto)
        return conjunto

    def eliminar(self, *, conjunto: ConjuntoAP) -> None:
        self._db.delete(conjunto)
        self._db.commit()

    def actualizar_ubicacion_ap(
        self,
        *,
        conjunto: ConjuntoAP,
        bssid: str,
        pos_x: float,
        pos_y: float,
    ) -> ConjuntoAP | None:
        item = next(
            (
                item
                for item in conjunto.items
                if item.bssid.lower() == bssid.lower()
            ),
            None,
        )
        if item is None:
            return None
        item.pos_x = pos_x
        item.pos_y = pos_y
        self._db.commit()
        self._db.refresh(conjunto)
        return conjunto

    def _reemplazar_items(self, *, conjunto: ConjuntoAP, items: list[dict]) -> None:
        conjunto.items.clear()
        self._db.flush()
        for item in items:
            conjunto.items.append(ConjuntoAPItem(**item))


class AnalisisCoberturaRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def obtener_ap_por_id(self, *, ap_id: int) -> APDetectado | None:
        return self._db.query(APDetectado).filter(APDetectado.id == ap_id).first()

    def reemplazar(
        self,
        *,
        mapa: MapaCalor,
        pct_cobertura: float,
        pct_zonas_muertas: float,
        celdas_zonas_muertas: int,
        cantidad_solapamientos: int,
        cantidad_interferencias: int,
        hallazgos: dict,
        resumen: str,
        aps_detectados: list[dict],
    ) -> AnalisisCobertura:
        if mapa.analisis is not None:
            self._db.delete(mapa.analisis)
            self._db.flush()

        analisis = AnalisisCobertura(
            mapa_calor_id=mapa.id,
            pct_cobertura=pct_cobertura,
            pct_zonas_muertas=pct_zonas_muertas,
            celdas_zonas_muertas=celdas_zonas_muertas,
            cantidad_solapamientos=cantidad_solapamientos,
            cantidad_interferencias=cantidad_interferencias,
            hallazgos=hallazgos,
            resumen=resumen,
        )
        self._db.add(analisis)
        self._db.flush()

        for ap_data in aps_detectados:
            self._db.add(APDetectado(analisis_id=analisis.id, **ap_data))

        self._db.commit()
        self._db.refresh(analisis)
        return analisis

    def confirmar_ap(
        self,
        *,
        ap: APDetectado,
        pos_x: float,
        pos_y: float,
        confirmado: bool,
    ) -> APDetectado:
        ap.pos_x = pos_x
        ap.pos_y = pos_y
        ap.confirmado = confirmado
        self._db.commit()
        self._db.refresh(ap)
        return ap
