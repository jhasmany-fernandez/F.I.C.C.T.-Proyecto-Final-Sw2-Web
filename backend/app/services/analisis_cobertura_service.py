"""Servicio de análisis automático de cobertura.

Sprint 4 — PB-06.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from app.models.medicion import MedicionWifi
from app.services.interpolacion_service import InterpolacionService, PuntoRSSI


@dataclass(frozen=True)
class APCalculado:
    bssid: str
    ssid: str
    canal: int | None
    frecuencia_mhz: int | None
    rssi_promedio: float
    pos_x: float
    pos_y: float
    area_cobertura: set[tuple[int, int]]


class AnalisisCoberturaService:
    """Calcula métricas CWNA-107, APs detectados, solapamiento y CCI/ACI."""

    def __init__(self) -> None:
        self._interpolacion = InterpolacionService()

    def analizar(
        self,
        *,
        matriz: list[list[float]],
        mediciones: list[MedicionWifi],
        ancho_px: int,
        alto_px: int,
        aps_referencia: list[dict] | None = None,
    ) -> dict:
        total_celdas = sum(len(fila) for fila in matriz)
        celdas_cobertura = sum(1 for fila in matriz for rssi in fila if rssi >= -70)
        celdas_problematicas = sum(1 for fila in matriz for rssi in fila if rssi < -75)
        celdas_muertas = sum(1 for fila in matriz for rssi in fila if rssi < -90)
        pct_cobertura = self._porcentaje(celdas_cobertura, total_celdas)
        pct_zonas_problematicas = self._porcentaje(celdas_problematicas, total_celdas)
        pct_zonas_muertas = self._porcentaje(celdas_muertas, total_celdas)

        aps = self._calcular_aps(
            mediciones=mediciones,
            ancho_px=ancho_px,
            alto_px=alto_px,
            resolucion=len(matriz),
        )
        solapamientos, interferencias = self._calcular_hallazgos_aps(aps)
        referencias_por_bssid = {
            ap["bssid"]: ap for ap in aps_referencia or []
        }

        hallazgos = {
            "zonas_muertas": {
                "celdas": celdas_muertas,
                "porcentaje": pct_zonas_muertas,
                "umbral": "RSSI < −90 dBm",
            },
            "zonas_problematicas": {
                "celdas": celdas_problematicas,
                "porcentaje": pct_zonas_problematicas,
                "umbral": "RSSI < −75 dBm",
            },
            "solapamientos_ap": solapamientos,
            "interferencias_canal": interferencias,
        }
        resumen = (
            f"Cobertura adecuada en {pct_cobertura:.2f}% del plano; "
            f"{pct_zonas_problematicas:.2f}% está bajo el umbral operativo de "
            f"−75 dBm y {pct_zonas_muertas:.2f}% corresponde a zonas muertas."
        )

        return {
            "pct_cobertura": pct_cobertura,
            "pct_zonas_muertas": pct_zonas_muertas,
            "celdas_zonas_muertas": celdas_muertas,
            "cantidad_solapamientos": len(solapamientos),
            "cantidad_interferencias": len(interferencias),
            "hallazgos": hallazgos,
            "resumen": resumen,
            "aps_detectados": [
                {
                    "bssid": ap.bssid,
                    "ssid": ap.ssid,
                    "canal": ap.canal,
                    "frecuencia_mhz": ap.frecuencia_mhz,
                    "rssi_promedio": round(ap.rssi_promedio, 2),
                    "pos_x": round(
                        referencias_por_bssid[ap.bssid]["pos_x"]
                        if ap.bssid in referencias_por_bssid
                        else ap.pos_x,
                        2,
                    ),
                    "pos_y": round(
                        referencias_por_bssid[ap.bssid]["pos_y"]
                        if ap.bssid in referencias_por_bssid
                        else ap.pos_y,
                        2,
                    ),
                    "confirmado": ap.bssid in referencias_por_bssid,
                }
                for ap in aps
            ],
        }

    def _calcular_aps(
        self,
        *,
        mediciones: list[MedicionWifi],
        ancho_px: int,
        alto_px: int,
        resolucion: int,
    ) -> list[APCalculado]:
        por_bssid: dict[str, list[MedicionWifi]] = defaultdict(list)
        for medicion in mediciones:
            por_bssid[medicion.bssid].append(medicion)

        aps: list[APCalculado] = []
        for bssid, items in por_bssid.items():
            ssid = Counter(item.ssid for item in items).most_common(1)[0][0]
            canales = [item.canal for item in items if item.canal is not None]
            frecuencias = [
                item.frecuencia_mhz for item in items if item.frecuencia_mhz is not None
            ]
            canal = Counter(canales).most_common(1)[0][0] if canales else None
            frecuencia = (
                Counter(frecuencias).most_common(1)[0][0]
                if frecuencias
                else None
            )
            rssi_promedio = sum(item.rssi for item in items) / len(items)

            peso_total = 0.0
            suma_x = 0.0
            suma_y = 0.0
            puntos_ap: list[PuntoRSSI] = []
            for item in items:
                peso = max(1.0, item.rssi + 120.0)
                peso_total += peso
                suma_x += item.punto.pos_x * peso
                suma_y += item.punto.pos_y * peso
                puntos_ap.append(
                    PuntoRSSI(
                        punto_id=item.punto_id,
                        x=item.punto.pos_x,
                        y=item.punto.pos_y,
                        rssi=float(item.rssi),
                    )
                )

            area = self._area_cobertura_ap(
                puntos=puntos_ap,
                ancho_px=ancho_px,
                alto_px=alto_px,
                resolucion=resolucion,
            )
            aps.append(
                APCalculado(
                    bssid=bssid,
                    ssid=ssid,
                    canal=canal,
                    frecuencia_mhz=frecuencia,
                    rssi_promedio=rssi_promedio,
                    pos_x=suma_x / peso_total,
                    pos_y=suma_y / peso_total,
                    area_cobertura=area,
                )
            )
        return aps

    def _area_cobertura_ap(
        self,
        *,
        puntos: list[PuntoRSSI],
        ancho_px: int,
        alto_px: int,
        resolucion: int,
    ) -> set[tuple[int, int]]:
        if len(puntos) < 2:
            return set()
        matriz_ap = self._interpolacion.interpolar(
            puntos=puntos,
            ancho_px=ancho_px,
            alto_px=alto_px,
            resolucion=resolucion,
            algoritmo="IDW",
        )
        return {
            (fila_idx, col_idx)
            for fila_idx, fila in enumerate(matriz_ap)
            for col_idx, rssi in enumerate(fila)
            if rssi >= -70
        }

    def _calcular_hallazgos_aps(
        self,
        aps: list[APCalculado],
    ) -> tuple[list[dict], list[dict]]:
        solapamientos: list[dict] = []
        interferencias: list[dict] = []

        for i, ap_a in enumerate(aps):
            for ap_b in aps[i + 1 :]:
                interseccion = ap_a.area_cobertura.intersection(ap_b.area_cobertura)
                if not interseccion:
                    continue

                solapamientos.append(
                    {
                        "bssid_a": ap_a.bssid,
                        "bssid_b": ap_b.bssid,
                        "celdas_intersectadas": len(interseccion),
                        "criterio": "RSSI ≥ −70 dBm",
                    }
                )

                tipo = self._tipo_interferencia(ap_a, ap_b)
                if tipo and ap_a.rssi_promedio >= -80 and ap_b.rssi_promedio >= -80:
                    interferencias.append(
                        {
                            "tipo": tipo,
                            "bssid_a": ap_a.bssid,
                            "bssid_b": ap_b.bssid,
                            "canal_a": ap_a.canal,
                            "canal_b": ap_b.canal,
                            "celdas_intersectadas": len(interseccion),
                        }
                    )

        return solapamientos, interferencias

    def _tipo_interferencia(self, ap_a: APCalculado, ap_b: APCalculado) -> str | None:
        if ap_a.canal is None or ap_b.canal is None:
            return None
        if ap_a.canal == ap_b.canal:
            return "CCI"
        if 1 <= ap_a.canal <= 14 and 1 <= ap_b.canal <= 14:
            if abs(ap_a.canal - ap_b.canal) <= 4:
                return "ACI"
        return None

    def _porcentaje(self, valor: int, total: int) -> float:
        if total == 0:
            return 0.0
        return round((valor / total) * 100, 2)
