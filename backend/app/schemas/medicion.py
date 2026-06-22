"""DTOs de mediciones WiFi.

Sprint 3 — PB-03 (Captura WiFi en línea), PB-04 (Marcar puntos de medición).
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------

NivelSenal = Literal["verde", "amarillo", "naranja", "rojo", "negro"]

_BSSID_RE = re.compile(
    r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Entrada (ingesta de lote — POST /api/mediciones)
# ---------------------------------------------------------------------------


class MedicionItemIn(BaseModel):
    """Un resultado de escaneo WiFi (un BSSID)."""

    ssid: str = Field(..., max_length=255)
    bssid: str = Field(..., description="MAC AA:BB:CC:DD:EE:FF")
    rssi: int = Field(..., ge=-120, le=0, description="dBm entre -120 y 0 (CA-6 PB-03)")
    canal: int | None = Field(default=None, ge=1, le=196)
    frecuencia_mhz: int | None = Field(default=None, ge=2400, le=6000)

    @field_validator("bssid", mode="before")
    @classmethod
    def _normalizar_bssid(cls, v: str) -> str:
        v = v.strip().lower()
        if not _BSSID_RE.match(v):
            raise ValueError(
                "El campo bssid debe tener formato AA:BB:CC:DD:EE:FF."
            )
        return v


class LoteMedicionIn(BaseModel):
    """Cuerpo del lote de medición enviado desde la app (POST /api/mediciones).

    Un lote = un toque del técnico sobre el plano (modo Puntual) o un
    intervalo en modo Continuo. Debe contener al menos una medición.
    """

    plano_id: int = Field(..., gt=0)
    pos_x: float = Field(..., ge=0, description="Posición X en píxeles del plano")
    pos_y: float = Field(..., ge=0, description="Posición Y en píxeles del plano")
    mediciones: list[MedicionItemIn] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------


class MedicionWifiOut(BaseModel):
    """DTO de salida para una medición WiFi individual."""

    id: int
    punto_id: int
    ssid: str
    bssid: str
    rssi: int
    canal: int | None
    frecuencia_mhz: int | None
    nivel: NivelSenal
    numero_lectura: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PuntoMedicionOut(BaseModel):
    """DTO de salida para un punto de medición (sin mediciones detalladas)."""

    id: int
    plano_id: int
    pos_x: float
    pos_y: float
    nivel: NivelSenal
    created_at: datetime

    model_config = {"from_attributes": True}


class PuntoMedicionDetalleOut(BaseModel):
    """DTO de salida completo: punto + lista de mediciones ordenadas por RSSI."""

    id: int
    plano_id: int
    pos_x: float
    pos_y: float
    nivel: NivelSenal
    created_at: datetime
    mediciones: list[MedicionWifiOut]

    model_config = {"from_attributes": True}


class PuntoMedicionUpdateIn(BaseModel):
    """Cuerpo para mover un punto de medición existente sobre el plano."""

    pos_x: float = Field(..., ge=0, description="Posición X en píxeles del plano")
    pos_y: float = Field(..., ge=0, description="Posición Y en píxeles del plano")


class LoteMedicionOut(BaseModel):
    """Respuesta 201 del POST /api/mediciones."""

    punto_id: int
    nivel: NivelSenal
    mediciones: list[MedicionWifiOut]


class AgregarMedicionesIn(BaseModel):
    """Cuerpo para agregar mediciones a un punto existente (modo continuo).

    El backend recalcula el nivel del punto con el peor RSSI acumulado.
    """

    mediciones: list[MedicionItemIn] = Field(..., min_length=1)
