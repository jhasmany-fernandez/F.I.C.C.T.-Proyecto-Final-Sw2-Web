"""DTOs de Sprint 5: escenarios IA, comparación y reportes."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.heatmap import MapaCalorOut

BandaWifi = Literal["2.4", "5"]
AccionRecomendacion = Literal[
    "MANTENER", "AGREGAR", "MOVER", "RECONFIGURAR", "CAMBIAR_MODELO", "RETIRAR"
]


class FuenteEntradaEscenarioIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tipo: Literal[
        "SELECCION_APS_MAPA",
        "INVENTARIO_RF",
        "BASELINE_OBSERVADO",
        "CONJUNTO_EXISTENTE",
    ] = "SELECCION_APS_MAPA"
    nombre: str | None = Field(default=None, max_length=100)
    proposito: str | None = Field(default=None, max_length=255)
    ap_ids: list[int] = Field(default_factory=list)
    bssids: list[str] = Field(default_factory=list)
    conjunto_id: int | None = Field(default=None, gt=0)

    @field_validator("bssids")
    @classmethod
    def normalizar_bssids(cls, value: list[str]) -> list[str]:
        return [item.strip().lower() for item in value if item.strip()]


class RestriccionesEscenarioIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plano_id: int | None = Field(default=None, gt=0)
    fuente_entrada: FuenteEntradaEscenarioIn | None = None
    max_aps: int = Field(default=3, ge=1, le=5)
    bandas: list[BandaWifi] = Field(default_factory=lambda: ["2.4", "5"], min_length=1)
    umbral_objetivo_dbm: int = Field(default=-70, ge=-90, le=-50)
    resolucion: int = Field(default=64, ge=32, le=128)


class RecomendacionAPOut(BaseModel):
    id: int
    orden: int
    accion: str
    coord_x: float
    coord_y: float
    altura_m: float
    tipo_montaje: str
    banda: str
    modelo_ap: str
    costo_estimado: float
    rssi_proyectado: float
    radios: list[dict]
    justificacion: str

    model_config = {"from_attributes": True}


class EscenarioOptimizadoOut(BaseModel):
    id: int
    proyecto_id: int
    plano_id: int
    mapa_actual_id: int | None
    mapa_proyectado_id: int | None
    conjunto_base_id: int | None
    origen: str
    estado_gobernanza: str
    generado_por_id: int | None
    aprobado_por_id: int | None
    publicado_por_id: int | None
    aprobado_at: datetime | None
    publicado_at: datetime | None
    nombre: str
    tipo_negocio: str
    perfil: str
    politica_combinacion: str
    banda: str
    bandas: list[str]
    modelo_ap: str
    pct_cobertura_actual: float
    pct_cobertura: float
    costo_estimado: float
    cantidad_aps: int
    resumen: str
    restricciones: dict
    metricas: dict
    mapas_por_banda: dict
    mapas_actuales_por_banda: dict
    supuestos: list[str]
    confianza: str
    version_motor: str
    recomendaciones: list[RecomendacionAPOut]
    created_at: datetime

    model_config = {"from_attributes": True}


class EscenariosGeneradosOut(BaseModel):
    escenarios: list[EscenarioOptimizadoOut]


class CambiarEstadoEscenarioIn(BaseModel):
    estado_gobernanza: Literal[
        "pendiente_revision",
        "aprobado_interno",
        "publicado_cliente",
        "descartado",
    ]


class ResumenComparacionOut(BaseModel):
    delta_pct_cobertura: float
    delta_zonas_muertas: int
    costo_estimado: float
    cantidad_cambios: int
    lectura: str


class ComparacionEscenarioOut(BaseModel):
    escenario: EscenarioOptimizadoOut
    heatmap_actual: MapaCalorOut
    heatmap_proyectado: MapaCalorOut
    matriz_diferencia: list[list[float]]
    comparacion_por_banda: dict = Field(default_factory=dict)
    resumen: ResumenComparacionOut


class ValorProyectadoPuntoOut(BaseModel):
    id: int
    escenario_id: int
    punto_medicion_id: int
    banda: str
    rssi_observado_dbm: float | None
    rssi_proyectado_dbm: float
    diferencia_db: float | None
    radio_primaria: str
    radio_secundaria: str | None
    rssi_secundario_dbm: float | None
    snr_proyectado_db: float | None
    incertidumbre_db: float

    model_config = {"from_attributes": True}


class ReporteCrearIn(BaseModel):
    escenario_id: int | None = None
    incluir_csv: bool = False


class ReporteOut(BaseModel):
    id: int
    proyecto_id: int
    escenario_id: int | None
    estado: str
    url_descarga: str | None
    sha256: str | None
    tamanio_bytes: int
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
