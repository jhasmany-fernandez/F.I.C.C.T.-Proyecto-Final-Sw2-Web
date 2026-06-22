"""Modelo físico de propagación RF con configuración por radio."""

from __future__ import annotations

import math


class ModeloPropagacion:
    """Predicción RSSI determinística con degradación controlada a FSPL."""

    def fspl(self, *, rssi_referencia: float = -42.0, distancia_m: float) -> float:
        distancia = max(distancia_m, 1.0)
        perdida = 6.0 * math.log2(distancia)
        return round(max(-120.0, min(0.0, rssi_referencia - perdida)), 2)

    def predecir_rssi(
        self,
        *,
        distancia_px: float,
        metros_por_pixel: float,
        banda: str,
        penalizacion_material_db: float = 0.0,
        potencia_dbm: float | None = None,
        ganancia_dbi: float = 2.14,
        perdida_cable_db: float = 0.0,
    ) -> float:
        distancia_m = max(1.0, distancia_px * max(metros_por_pixel, 0.01))
        penalizacion_banda = {"2.4": 0.0, "5": 6.4}.get(banda, 6.4)
        if potencia_dbm is None:
            base = self.fspl(distancia_m=distancia_m)
        else:
            # Aproximación indoor: EIRP - FSPL(1 m) - pérdidas de sistema.
            eirp = potencia_dbm + ganancia_dbi - perdida_cable_db
            referencia_1m = eirp - 40.0 - 12.0
            base = self.fspl(rssi_referencia=referencia_1m, distancia_m=distancia_m)
        return round(
            max(-120.0, base - penalizacion_banda - penalizacion_material_db), 2
        )


def generar_dataset_sintetico(seed: int = 24) -> list[dict]:
    """Dataset paramétrico reproducible para pruebas y reentrenamiento futuro."""
    filas: list[dict] = []
    bandas = ["2.4", "5"]
    materiales = [0.0, 3.0, 7.0, 12.0]
    modelo = ModeloPropagacion()
    for banda in bandas:
        for material in materiales:
            for distancia in range(1, 61):
                ruido = ((distancia * seed) % 7 - 3) * 0.35
                rssi = modelo.predecir_rssi(
                    distancia_px=float(distancia),
                    metros_por_pixel=1.0,
                    banda=banda,
                    penalizacion_material_db=material,
                )
                filas.append(
                    {
                        "distancia_m": distancia,
                        "banda": banda,
                        "perdida_material_db": material,
                        "rssi": round(rssi + ruido, 2),
                    }
                )
    return filas
