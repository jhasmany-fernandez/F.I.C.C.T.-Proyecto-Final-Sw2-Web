"""DTOs del módulo de heatmap y análisis.

Sprint 4 — PB-05, PB-06.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AlgoritmoHeatmap = Literal["IDW", "KRIGING"]
ResolucionHeatmap = Literal[64, 128, 256]
ModoGeneracionHeatmap = Literal["INDIVIDUAL", "SUBCONJUNTO", "CONJUNTO_COMPLETO"]
EstadoGobernanzaConjunto = Literal[
    "borrador_tecnico",
    "preliminar",
    "pendiente_revision",
    "aprobado_interno",
    "publicado_cliente",
    "descartado",
]


class EscalaHeatmapItem(BaseModel):
    desde: int
    hasta: int
    color: str
    etiqueta: str


class PuntoLecturaHeatmapOut(BaseModel):
    punto_id: int
    pos_x: float
    pos_y: float
    rssi: float


class APDisponibleOut(BaseModel):
    bssid: str
    ssid: str
    canal: int | None
    frecuencia_mhz: int | None
    rssi_promedio: float
    pos_x: float
    pos_y: float
    cantidad_puntos: int
    seleccionado: bool = False


class MapaCalorOut(BaseModel):
    id: int
    plano_id: int
    conjunto_ap_id: int | None = None
    analisis_id: int | None = None
    modo_generacion: str = "SUBCONJUNTO"
    algoritmo: str
    resolucion: int
    bssid: str
    ssid: str
    ap_pos_x: float
    ap_pos_y: float
    aps_interes: list[APDisponibleOut]
    bssids_generacion: list[str]
    url_imagen: str
    matriz: list[list[float]]
    escala: list[EscalaHeatmapItem]
    cantidad_puntos: int
    rssi_min: float
    rssi_max: float
    rssi_promedio: float
    puntos_lectura: list[PuntoLecturaHeatmapOut]
    advertencias: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class APDetectadoOut(BaseModel):
    id: int
    bssid: str
    ssid: str
    canal: int | None
    frecuencia_mhz: int | None
    rssi_promedio: float
    pos_x: float
    pos_y: float
    confirmado: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ConjuntoAPItemOut(BaseModel):
    bssid: str
    ssid: str
    canal: int | None
    frecuencia_mhz: int | None = None
    rssi_promedio: float | None = None
    pos_x: float | None = None
    pos_y: float | None = None
    cantidad_puntos: int | None = None


class ConjuntoAPBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    proposito: str = Field(..., min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=1000)
    es_principal: bool = False
    bssids: list[str] = Field(..., min_length=1)


class ConjuntoAPCrearIn(ConjuntoAPBase):
    pass


class ConjuntoAPActualizarIn(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=100)
    proposito: str | None = Field(default=None, min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=1000)
    es_principal: bool | None = None
    bssids: list[str] | None = Field(default=None, min_length=1)
    estado_gobernanza: EstadoGobernanzaConjunto | None = None


class ConjuntoAPOut(BaseModel):
    id: int
    plano_id: int
    nombre: str
    proposito: str
    descripcion: str | None
    es_principal: bool
    origen: str
    estado_gobernanza: str
    creado_por_id: int | None
    cantidad_aps: int
    items: list[ConjuntoAPItemOut]
    created_at: datetime
    updated_at: datetime


class GenerarHeatmapConjuntoIn(BaseModel):
    modo: ModoGeneracionHeatmap = "CONJUNTO_COMPLETO"
    bssids: list[str] | None = None
    ap_pos_x: list[float] | None = None
    ap_pos_y: list[float] | None = None
    algoritmo: AlgoritmoHeatmap = "IDW"
    resolucion: ResolucionHeatmap = 128


class ActualizarUbicacionAPConjuntoIn(BaseModel):
    bssid: str = Field(..., min_length=17, max_length=17)
    pos_x: float = Field(..., ge=0)
    pos_y: float = Field(..., ge=0)


class AnalisisCoberturaOut(BaseModel):
    id: int
    mapa_calor_id: int
    pct_cobertura: float
    pct_zonas_muertas: float
    celdas_zonas_muertas: int
    cantidad_solapamientos: int
    cantidad_interferencias: int
    hallazgos: dict
    resumen: str
    aps_detectados: list[APDetectadoOut]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfirmarAPIn(BaseModel):
    pos_x: float = Field(..., ge=0)
    pos_y: float = Field(..., ge=0)
    confirmado: bool = True
