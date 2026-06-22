"""Optimizador de APs Sprint 5 — PB-07."""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.ai.modelo_propagacion import ModeloPropagacion
from app.services.interpolacion_service import PuntoRSSI


@dataclass(frozen=True)
class AlternativaOptimizada:
    nombre: str
    banda: str
    modelo_ap: str
    pct_cobertura_actual: float
    pct_cobertura: float
    costo_estimado: float
    cantidad_aps: int
    resumen: str
    metricas: dict
    recomendaciones: list[dict]
    matriz: list[list[float]]
    mapas_por_banda: dict[str, list[list[float]]]
    valores_proyectados: list[dict]
    supuestos: list[str]
    confianza: str


class OptimizadorAPService:
    """Greedy + búsqueda local sobre una grilla del plano."""

    def __init__(self, modelo: ModeloPropagacion | None = None) -> None:
        self._modelo = modelo or ModeloPropagacion()

    def optimizar(
        self,
        *,
        puntos_actuales: list[PuntoRSSI],
        matriz_actual: list[list[float]],
        ancho_px: int,
        alto_px: int,
        metros_por_pixel: float,
        max_aps: int,
        banda: str,
        resolucion: int,
        umbral_objetivo_dbm: int = -70,
        bandas: list[str] | None = None,
        aps_existentes: list[dict] | None = None,
    ) -> list[AlternativaOptimizada]:
        if not puntos_actuales:
            raise ValueError("Se requieren puntos de medición para optimizar.")

        bandas_objetivo = list(dict.fromkeys(bandas or [banda]))
        if banda not in bandas_objetivo:
            banda = "5" if "5" in bandas_objetivo else bandas_objetivo[0]
        cantidad_max = max(1, max_aps)

        pct_actual = self._pct_cobertura(
            matriz_actual,
            umbral_objetivo_dbm=umbral_objetivo_dbm,
        )
        candidatos = self._candidatos(
            puntos=puntos_actuales,
            ancho_px=ancho_px,
            alto_px=alto_px,
        )
        alternativas: list[AlternativaOptimizada] = []
        for cantidad in range(1, cantidad_max + 1):
            seleccionados = self._greedy(
                candidatos=candidatos,
                cantidad=cantidad,
                ancho_px=ancho_px,
                alto_px=alto_px,
                metros_por_pixel=metros_por_pixel,
                banda=banda,
                resolucion=resolucion,
                umbral_objetivo_dbm=umbral_objetivo_dbm,
            )
            seleccionados = self._busqueda_local(
                seleccionados=seleccionados,
                ancho_px=ancho_px,
                alto_px=alto_px,
                metros_por_pixel=metros_por_pixel,
                banda=banda,
                resolucion=resolucion,
                umbral_objetivo_dbm=umbral_objetivo_dbm,
            )
            for indice, ap in enumerate((aps_existentes or [])[: len(seleccionados)]):
                if ap.get("restriccion_movimiento") == "FIJO":
                    seleccionados[indice] = (float(ap["coord_x"]), float(ap["coord_y"]))
            mapas_por_banda = {
                banda_actual: self._matriz_desde_aps(
                    aps=seleccionados,
                    ancho_px=ancho_px,
                    alto_px=alto_px,
                    metros_por_pixel=metros_por_pixel,
                    banda=banda_actual,
                    resolucion=resolucion,
                )
                for banda_actual in bandas_objetivo
            }
            matriz_proyectada = mapas_por_banda[banda]
            pct = self._pct_cobertura(
                matriz_proyectada,
                umbral_objetivo_dbm=umbral_objetivo_dbm,
            )
            recomendaciones = [
                self._recomendacion(
                    orden=idx,
                    x=x,
                    y=y,
                    banda=banda,
                    puntos=puntos_actuales,
                    metros_por_pixel=metros_por_pixel,
                    bandas=bandas_objetivo,
                    umbral_objetivo_dbm=umbral_objetivo_dbm,
                    ap_existente=(aps_existentes or [None] * cantidad)[idx - 1]
                    if idx <= len(aps_existentes or [])
                    else None,
                )
                for idx, (x, y) in enumerate(seleccionados, start=1)
            ]
            alternativas.append(
                AlternativaOptimizada(
                    nombre=f"Alternativa {cantidad}",
                    banda=banda,
                    modelo_ap="AP propuesto para cobertura",
                    pct_cobertura_actual=pct_actual,
                    pct_cobertura=pct,
                    costo_estimado=0,
                    cantidad_aps=cantidad,
                    resumen=(
                        f"Con {cantidad} AP(s) de potencia ajustable en banda "
                        f"{banda} GHz se proyecta {pct:.1f}% de cobertura "
                        f">= {umbral_objetivo_dbm} dBm."
                    ),
                    metricas={
                        "pct_cobertura_actual": pct_actual,
                        "pct_cobertura_proyectada": pct,
                        "mejora_pct": round(pct - pct_actual, 2),
                        "zonas_muertas_proyectadas": self._zonas_muertas(
                            matriz_proyectada
                        ),
                        "pct_cobertura_por_banda": {
                            key: self._pct_cobertura(
                                value,
                                umbral_objetivo_dbm=umbral_objetivo_dbm,
                            )
                            for key, value in mapas_por_banda.items()
                        },
                        "umbral_objetivo_dbm": umbral_objetivo_dbm,
                    },
                    recomendaciones=recomendaciones,
                    matriz=matriz_proyectada,
                    mapas_por_banda=mapas_por_banda,
                    valores_proyectados=self._valores_proyectados(
                        puntos=puntos_actuales,
                        aps=seleccionados,
                        bandas=bandas_objetivo,
                        metros_por_pixel=metros_por_pixel,
                    ),
                    supuestos=[
                        "Antena omnidireccional de 2,14 dBi cuando no existe "
                        "inventario verificado.",
                        "Ancho de canal inicial de 20 MHz para favorecer "
                        "reutilización.",
                    ],
                    confianza="ALTA"
                    if aps_existentes
                    and all(ap.get("verificado") for ap in aps_existentes)
                    else "MEDIA",
                )
            )
        return sorted(
            alternativas,
            key=lambda item: (-item.pct_cobertura, item.cantidad_aps),
        )[:3]

    def _candidatos(
        self,
        *,
        puntos: list[PuntoRSSI],
        ancho_px: int,
        alto_px: int,
    ) -> list[tuple[float, float]]:
        criticos = sorted(puntos, key=lambda p: p.rssi)[: max(6, len(puntos) // 3)]
        candidatos = [(p.x, p.y) for p in criticos]
        for x_frac in (0.2, 0.5, 0.8):
            for y_frac in (0.2, 0.5, 0.8):
                candidatos.append((ancho_px * x_frac, alto_px * y_frac))
        unicos: list[tuple[float, float]] = []
        for x, y in candidatos:
            coord = (
                round(max(0, min(ancho_px, x)), 2),
                round(max(0, min(alto_px, y)), 2),
            )
            if coord not in unicos:
                unicos.append(coord)
        return unicos

    def _greedy(
        self,
        *,
        candidatos: list[tuple[float, float]],
        cantidad: int,
        ancho_px: int,
        alto_px: int,
        metros_por_pixel: float,
        banda: str,
        resolucion: int,
        umbral_objetivo_dbm: int,
    ) -> list[tuple[float, float]]:
        seleccionados: list[tuple[float, float]] = []
        restantes = candidatos[:]
        while len(seleccionados) < cantidad and restantes:
            mejor = max(
                restantes,
                key=lambda c: self._pct_cobertura(
                    self._matriz_desde_aps(
                        aps=[*seleccionados, c],
                        ancho_px=ancho_px,
                        alto_px=alto_px,
                        metros_por_pixel=metros_por_pixel,
                        banda=banda,
                        resolucion=resolucion,
                    ),
                    umbral_objetivo_dbm=umbral_objetivo_dbm,
                ),
            )
            seleccionados.append(mejor)
            restantes.remove(mejor)
        return seleccionados

    def _busqueda_local(
        self,
        *,
        seleccionados: list[tuple[float, float]],
        ancho_px: int,
        alto_px: int,
        metros_por_pixel: float,
        banda: str,
        resolucion: int,
        umbral_objetivo_dbm: int,
    ) -> list[tuple[float, float]]:
        paso = max(20.0, min(ancho_px, alto_px) * 0.08)
        actuales = seleccionados[:]
        for idx, (x, y) in enumerate(actuales):
            vecinos = [
                (x, y),
                (x - paso, y),
                (x + paso, y),
                (x, y - paso),
                (x, y + paso),
            ]
            vecinos = [
                (
                    round(max(0, min(ancho_px, vx)), 2),
                    round(max(0, min(alto_px, vy)), 2),
                )
                for vx, vy in vecinos
            ]
            actuales[idx] = max(
                vecinos,
                key=lambda c: self._pct_cobertura(
                    self._matriz_desde_aps(
                        aps=[*actuales[:idx], c, *actuales[idx + 1 :]],
                        ancho_px=ancho_px,
                        alto_px=alto_px,
                        metros_por_pixel=metros_por_pixel,
                        banda=banda,
                        resolucion=resolucion,
                    ),
                    umbral_objetivo_dbm=umbral_objetivo_dbm,
                ),
            )
        return actuales

    def _matriz_desde_aps(
        self,
        *,
        aps: list[tuple[float, float]],
        ancho_px: int,
        alto_px: int,
        metros_por_pixel: float,
        banda: str,
        resolucion: int,
    ) -> list[list[float]]:
        matriz: list[list[float]] = []
        for fila in range(resolucion):
            y = ((fila + 0.5) / resolucion) * alto_px
            valores_fila: list[float] = []
            for col in range(resolucion):
                x = ((col + 0.5) / resolucion) * ancho_px
                mejor = max(
                    self._modelo.predecir_rssi(
                        distancia_px=math.hypot(x - ap_x, y - ap_y),
                        metros_por_pixel=metros_por_pixel,
                        banda=banda,
                    )
                    for ap_x, ap_y in aps
                )
                valores_fila.append(mejor)
            matriz.append(valores_fila)
        return matriz

    def _recomendacion(
        self,
        *,
        orden: int,
        x: float,
        y: float,
        banda: str,
        puntos: list[PuntoRSSI],
        metros_por_pixel: float,
        bandas: list[str],
        umbral_objetivo_dbm: int,
        ap_existente: dict | None,
    ) -> dict:
        if (
            ap_existente
            and ap_existente.get("restriccion_movimiento") == "FIJO"
        ):
            x = float(ap_existente["coord_x"])
            y = float(ap_existente["coord_y"])
        punto_critico = min(puntos, key=lambda p: math.hypot(p.x - x, p.y - y))
        distancia_m = (
            math.hypot(punto_critico.x - x, punto_critico.y - y) * metros_por_pixel
        )
        rssi = self._modelo.predecir_rssi(
            distancia_px=math.hypot(punto_critico.x - x, punto_critico.y - y),
            metros_por_pixel=metros_por_pixel,
            banda=banda,
        )
        radios = [
            self._configuracion_radio(banda_actual, orden) for banda_actual in bandas
        ]
        accion = "AGREGAR"
        ap_fisico_id = None
        if ap_existente:
            ap_fisico_id = ap_existente.get("id")
            accion = (
                "RECONFIGURAR"
                if ap_existente.get("restriccion_movimiento") == "FIJO"
                else "MOVER"
            )
        return {
            "ap_fisico_id": ap_fisico_id,
            "accion": accion,
            "coord_x": round(x, 2),
            "coord_y": round(y, 2),
            "banda": banda,
            "altura_m": float(ap_existente.get("altura_m", 2.5))
            if ap_existente
            else 2.5,
            "tipo_montaje": str(ap_existente.get("tipo_montaje", "TECHO"))
            if ap_existente
            else "TECHO",
            "modelo_ap": "AP propuesto para cobertura",
            "costo_estimado": 0,
            "rssi_proyectado": rssi,
            "radios": radios,
            "justificacion": (
                f"AP {orden}: ubicar un equipo con potencia TX ajustable y "
                f"capacidad para mantener RSSI proyectado {rssi:.1f} dBm "
                f"en una zona crítica a {distancia_m:.1f} m. Debe permitir "
                f"regular potencia para evitar solapamiento excesivo, operar "
                f"en banda {banda} GHz, usar antenas adecuadas al área y "
                f"soportar gestión centralizada. Objetivo de diseño: "
                f">= {umbral_objetivo_dbm} dBm."
            ),
        }

    def _configuracion_radio(self, banda: str, orden: int) -> dict:
        if banda == "2.4":
            canales = [1, 6, 11]
            potencia = 8.0
        else:
            canales = [36, 44, 149, 157]
            potencia = 14.0
        return {
            "banda": banda,
            "habilitada": True,
            "canal": canales[(orden - 1) % len(canales)],
            "ancho_canal_mhz": 20,
            "potencia_dbm": potencia,
            "ganancia_dbi": 2.14,
            "eirp_dbm": round(potencia + 2.14, 2),
            "tipo_antena": "OMNIDIRECCIONAL",
            "dfs": False,
        }

    def _valores_proyectados(
        self,
        *,
        puntos: list[PuntoRSSI],
        aps: list[tuple[float, float]],
        bandas: list[str],
        metros_por_pixel: float,
    ) -> list[dict]:
        valores: list[dict] = []
        for punto in puntos:
            for banda in bandas:
                predicciones = sorted(
                    (
                        self._modelo.predecir_rssi(
                            distancia_px=math.hypot(punto.x - x, punto.y - y),
                            metros_por_pixel=metros_por_pixel,
                            banda=banda,
                            potencia_dbm=8.0 if banda == "2.4" else 14.0,
                        ),
                        indice,
                    )
                    for indice, (x, y) in enumerate(aps, start=1)
                )
                mejor, primaria = predicciones[-1]
                secundaria = predicciones[-2] if len(predicciones) > 1 else None
                observado = punto.rssi if banda == "5" else None
                valores.append(
                    {
                        "punto_medicion_id": punto.punto_id,
                        "banda": banda,
                        "rssi_observado_dbm": observado,
                        "rssi_proyectado_dbm": mejor,
                        "diferencia_db": round(mejor - observado, 2)
                        if observado is not None
                        else None,
                        "radio_primaria": f"AP-{primaria}:{banda}",
                        "radio_secundaria": f"AP-{secundaria[1]}:{banda}"
                        if secundaria
                        else None,
                        "rssi_secundario_dbm": secundaria[0] if secundaria else None,
                        "snr_proyectado_db": None,
                        "incertidumbre_db": 6.0,
                    }
                )
        return valores

    def _pct_cobertura(
        self,
        matriz: list[list[float]],
        *,
        umbral_objetivo_dbm: int = -70,
    ) -> float:
        valores = [valor for fila in matriz for valor in fila]
        if not valores:
            return 0.0
        cubiertas = sum(1 for valor in valores if valor >= umbral_objetivo_dbm)
        return round(cubiertas * 100 / len(valores), 2)

    def _zonas_muertas(self, matriz: list[list[float]]) -> int:
        return sum(1 for fila in matriz for valor in fila if valor < -90)
