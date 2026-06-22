"""Repositorio de acceso a datos para mediciones WiFi.

Sprint 3 — PB-03 (Captura WiFi en línea), PB-04 (Marcar puntos de medición).
"""

from collections import Counter, defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.medicion import MedicionWifi, PuntoMedicion, clasificar_nivel
from app.schemas.medicion import MedicionItemIn
from app.services.interpolacion_service import PuntoRSSI


class MedicionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    # ------------------------------------------------------------------
    # Escritura — PB-03 (POST /api/mediciones)
    # ------------------------------------------------------------------

    def crear_lote(
        self,
        *,
        plano_id: int,
        pos_x: float,
        pos_y: float,
        items: list[MedicionItemIn],
    ) -> PuntoMedicion:
        """Persiste el lote completo en una sola transacción.

        1. Calcula el ``nivel`` de cada medición individual.
        2. Determina el peor nivel del lote (el del punto).
        3. Inserta ``punto_medicion`` + N filas ``medicion_wifi``.
        """
        # Clasificar individualmente cada ítem
        niveles_rssi = [clasificar_nivel(item.rssi) for item in items]
        _ORDEN = {"verde": 0, "amarillo": 1, "naranja": 2, "rojo": 3, "negro": 4}
        nivel_punto = max(niveles_rssi, key=lambda n: _ORDEN[n])

        punto = PuntoMedicion(
            plano_id=plano_id,
            pos_x=pos_x,
            pos_y=pos_y,
            nivel=nivel_punto,
        )
        self._db.add(punto)
        self._db.flush()  # obtiene punto.id sin cerrar la transacción

        for item, nivel_item in zip(items, niveles_rssi):
            medicion = MedicionWifi(
                punto_id=punto.id,
                ssid=item.ssid,
                bssid=item.bssid.lower(),
                rssi=item.rssi,
                canal=item.canal,
                frecuencia_mhz=item.frecuencia_mhz,
                nivel=nivel_item,
                numero_lectura=1,
            )
            self._db.add(medicion)

        self._db.commit()
        self._db.refresh(punto)
        return punto

    # ------------------------------------------------------------------
    # Escritura — modo continuo (POST /api/puntos/{id}/mediciones)
    # ------------------------------------------------------------------

    def agregar_mediciones(
        self,
        *,
        punto: PuntoMedicion,
        items: list[MedicionItemIn],
    ) -> PuntoMedicion:
        """Agrega un nuevo lote de mediciones a un punto existente.

        Recalcula el ``nivel`` del punto tomando el peor RSSI
        de **todas** las mediciones acumuladas (anteriores + nuevas).
        El ``numero_lectura`` se incrementa respecto al lote anterior.
        """
        _ORDEN = {"verde": 0, "amarillo": 1, "naranja": 2, "rojo": 3, "negro": 4}

        # Determinar el siguiente número de lectura
        siguiente_lectura = (
            max((m.numero_lectura for m in punto.mediciones), default=0) + 1
        )

        for item in items:
            nivel_item = clasificar_nivel(item.rssi)
            medicion = MedicionWifi(
                punto_id=punto.id,
                ssid=item.ssid,
                bssid=item.bssid.lower(),
                rssi=item.rssi,
                canal=item.canal,
                frecuencia_mhz=item.frecuencia_mhz,
                nivel=nivel_item,
                numero_lectura=siguiente_lectura,
            )
            self._db.add(medicion)

        self._db.flush()  # inserta las nuevas filas sin cerrar la transacción
        self._db.refresh(punto)  # recarga la relación mediciones

        todos_niveles = [m.nivel for m in punto.mediciones]
        punto.nivel = max(todos_niveles, key=lambda n: _ORDEN[n])

        self._db.commit()
        self._db.refresh(punto)
        return punto

    # ------------------------------------------------------------------
    # Lectura — PB-04 (GET /api/planos/{id}/puntos, GET /api/puntos/{id})
    # ------------------------------------------------------------------

    def listar_puntos_por_plano(self, *, plano_id: int) -> list[PuntoMedicion]:
        """Retorna todos los puntos de medición de un plano, más recientes primero."""
        return (
            self._db.query(PuntoMedicion)
            .filter(PuntoMedicion.plano_id == plano_id)
            .order_by(PuntoMedicion.created_at.desc())
            .all()
        )

    def listar_mediciones_por_plano(self, *, plano_id: int) -> list[MedicionWifi]:
        """Retorna mediciones de todos los puntos del plano con el punto cargado."""
        return (
            self._db.query(MedicionWifi)
            .join(PuntoMedicion, MedicionWifi.punto_id == PuntoMedicion.id)
            .filter(PuntoMedicion.plano_id == plano_id)
            .order_by(MedicionWifi.bssid.asc(), MedicionWifi.rssi.desc())
            .all()
        )

    def listar_aps_por_plano(self, *, plano_id: int) -> list[dict]:
        """Agrupa mediciones por BSSID para seleccionar APs de interés."""
        mediciones = self.listar_mediciones_por_plano(plano_id=plano_id)
        por_bssid: dict[str, list[MedicionWifi]] = defaultdict(list)
        for medicion in mediciones:
            por_bssid[medicion.bssid].append(medicion)

        aps: list[dict] = []
        for bssid, items in por_bssid.items():
            ssid = Counter(item.ssid for item in items).most_common(1)[0][0]
            canales = [item.canal for item in items if item.canal is not None]
            frecuencias = [
                item.frecuencia_mhz for item in items if item.frecuencia_mhz is not None
            ]
            peso_total = 0.0
            suma_x = 0.0
            suma_y = 0.0
            puntos_unicos = {item.punto_id for item in items}
            for item in items:
                peso = max(1.0, item.rssi + 120.0)
                peso_total += peso
                suma_x += item.punto.pos_x * peso
                suma_y += item.punto.pos_y * peso

            aps.append(
                {
                    "bssid": bssid,
                    "ssid": ssid,
                    "canal": Counter(canales).most_common(1)[0][0]
                    if canales
                    else None,
                    "frecuencia_mhz": Counter(frecuencias).most_common(1)[0][0]
                    if frecuencias
                    else None,
                    "rssi_promedio": round(
                        sum(item.rssi for item in items) / len(items),
                        2,
                    ),
                    "pos_x": round(suma_x / peso_total, 2),
                    "pos_y": round(suma_y / peso_total, 2),
                    "cantidad_puntos": len(puntos_unicos),
                }
            )
        return sorted(aps, key=lambda ap: ap["rssi_promedio"], reverse=True)

    def obtener_ap_por_bssid(self, *, plano_id: int, bssid: str) -> dict | None:
        bssid_norm = bssid.lower()
        for ap in self.listar_aps_por_plano(plano_id=plano_id):
            if ap["bssid"] == bssid_norm:
                return ap
        return None

    def listar_puntos_rssi_heatmap(
        self,
        *,
        plano_id: int,
        bssids: list[str],
    ) -> list[PuntoRSSI]:
        """Agrega cada punto al mejor RSSI de los APs de interés seleccionados."""
        bssids_norm = {bssid.lower() for bssid in bssids}
        puntos = self.listar_puntos_por_plano(plano_id=plano_id)
        resultado: list[PuntoRSSI] = []
        for punto in puntos:
            rssi_por_bssid: dict[str, list[int]] = defaultdict(list)
            for medicion in punto.mediciones:
                if medicion.bssid in bssids_norm:
                    rssi_por_bssid[medicion.bssid].append(medicion.rssi)
            if not rssi_por_bssid:
                continue
            mejor_rssi = max(
                sum(valores) / len(valores)
                for valores in rssi_por_bssid.values()
            )
            resultado.append(
                PuntoRSSI(
                    punto_id=punto.id,
                    x=punto.pos_x,
                    y=punto.pos_y,
                    rssi=float(mejor_rssi),
                )
            )
        return resultado

    def listar_puntos_rssi_por_bssid_heatmap(
        self,
        *,
        plano_id: int,
        bssids: list[str],
    ) -> dict[str, list[PuntoRSSI]]:
        """Agrupa lecturas RSSI por AP de interés y punto de medición."""
        bssids_norm = {bssid.lower() for bssid in bssids}
        puntos = self.listar_puntos_por_plano(plano_id=plano_id)
        resultado: dict[str, list[PuntoRSSI]] = {bssid: [] for bssid in bssids_norm}
        for punto in puntos:
            rssi_por_bssid: dict[str, list[int]] = defaultdict(list)
            for medicion in punto.mediciones:
                if medicion.bssid in bssids_norm:
                    rssi_por_bssid[medicion.bssid].append(medicion.rssi)

            for bssid, valores in rssi_por_bssid.items():
                resultado[bssid].append(
                    PuntoRSSI(
                        punto_id=punto.id,
                        x=punto.pos_x,
                        y=punto.pos_y,
                        rssi=float(sum(valores) / len(valores)),
                    )
                )
        return resultado

    def rssi_maximo_por_bssid(
        self,
        *,
        plano_id: int,
        bssids: list[str],
    ) -> dict[str, float]:
        """Retorna el RSSI máximo observado para cada AP de interés."""
        filas = (
            self._db.query(MedicionWifi.bssid, func.max(MedicionWifi.rssi))
            .join(PuntoMedicion, MedicionWifi.punto_id == PuntoMedicion.id)
            .filter(PuntoMedicion.plano_id == plano_id)
            .filter(MedicionWifi.bssid.in_([bssid.lower() for bssid in bssids]))
            .group_by(MedicionWifi.bssid)
            .all()
        )
        return {bssid: float(rssi) for bssid, rssi in filas if rssi is not None}

    def firma_mediciones_plano(
        self,
        *,
        plano_id: int,
        bssids: list[str] | None = None,
    ) -> str:
        """Firma liviana del estado de mediciones usada para cache del heatmap."""
        query = (
            self._db.query(
                func.count(MedicionWifi.id),
                func.max(PuntoMedicion.id),
                func.max(MedicionWifi.id),
            )
            .join(PuntoMedicion, MedicionWifi.punto_id == PuntoMedicion.id)
            .filter(PuntoMedicion.plano_id == plano_id)
        )
        if bssids is not None:
            query = query.filter(
                MedicionWifi.bssid.in_([bssid.lower() for bssid in bssids])
            )
        conteo, max_punto, max_medicion = query.one()
        return f"{conteo or 0}:{max_punto or 0}:{max_medicion or 0}"

    def obtener_punto_por_id(self, *, punto_id: int) -> PuntoMedicion | None:
        """Retorna el punto con sus mediciones cargadas (eager via relationship)."""
        return (
            self._db.query(PuntoMedicion)
            .filter(PuntoMedicion.id == punto_id)
            .first()
        )

    def actualizar_posicion(
        self,
        *,
        punto: PuntoMedicion,
        pos_x: float,
        pos_y: float,
    ) -> PuntoMedicion:
        """Actualiza la posición de un punto sin alterar sus mediciones."""
        punto.pos_x = pos_x
        punto.pos_y = pos_y
        self._db.flush()
        return punto

    # ------------------------------------------------------------------
    # Eliminación — PB-04 (DELETE /api/puntos/{id})
    # ------------------------------------------------------------------

    def eliminar_punto(self, *, punto: PuntoMedicion) -> None:
        """Elimina el punto y sus mediciones en cascada."""
        self._db.delete(punto)
        self._db.commit()
