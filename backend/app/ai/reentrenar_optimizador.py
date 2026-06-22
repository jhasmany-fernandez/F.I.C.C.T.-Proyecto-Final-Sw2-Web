"""Genera artefacto reproducible del modelo IA Sprint 5.

El proyecto académico permite degradación controlada a FSPL cuando no hay
dataset real suficiente. Este script persiste el dataset sintético usado para
regresión en lugar de depender de paquetes externos no fijados en el stack base.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.ai.modelo_propagacion import generar_dataset_sintetico


def main() -> None:
    destino = Path(__file__).resolve().parent / "models" / "optimizador_ap.joblib"
    destino.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tipo": "baseline_fspl",
        "descripcion": "FSPL CWNA-107 con dataset sintético reproducible.",
        "dataset": generar_dataset_sintetico(),
    }
    destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(destino)


if __name__ == "__main__":
    main()
