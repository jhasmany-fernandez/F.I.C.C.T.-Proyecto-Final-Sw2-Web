"""Repositorio de acceso a datos para mediciones WiFi.

Sprint 3 — PB-03 (Captura WiFi en línea), PB-04 (Marcar puntos de medición).
"""

from sqlalchemy.orm import Session

from app.models.medicion import MedicionWifi, PuntoMedicion, clasificar_nivel
from app.schemas.medicion import MedicionItemIn


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

    def obtener_punto_por_id(self, *, punto_id: int) -> PuntoMedicion | None:
        """Retorna el punto con sus mediciones cargadas (eager via relationship)."""
        return (
            self._db.query(PuntoMedicion).filter(PuntoMedicion.id == punto_id).first()
        )

    # ------------------------------------------------------------------
    # Eliminación — PB-04 (DELETE /api/puntos/{id})
    # ------------------------------------------------------------------

    def eliminar_punto(self, *, punto: PuntoMedicion) -> None:
        """Elimina el punto y sus mediciones en cascada."""
        self._db.delete(punto)
        self._db.commit()
