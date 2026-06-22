"""DTOs del inventario físico AP -> radio -> BSSID."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

BandaRF = Literal["2.4", "5"]


class BSSIDRadioIn(BaseModel):
    bssid: str = Field(pattern=r"^[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}$")
    ssid: str = Field(min_length=1, max_length=255)
    observado: bool = True
    procedencia: str = "DETECTADA_ANDROID"

    @field_validator("bssid")
    @classmethod
    def normalizar_bssid(cls, value: str) -> str:
        return value.lower()


class RadioAPIn(BaseModel):
    banda: BandaRF
    habilitada: bool = True
    canal: int = Field(ge=1, le=196)
    ancho_canal_mhz: Literal[20, 40, 80] = 20
    potencia_original: float = Field(ge=0)
    unidad_potencia_original: Literal["DBM", "MW", "PORCENTAJE"] = "DBM"
    referencia_potencia: Literal["IR", "EIRP", "DESCONOCIDA"] = "IR"
    potencia_dbm: float = Field(ge=-10, le=36)
    potencia_max_dbm: float = Field(ge=0, le=36)
    modo_gestion_rf: Literal["ESTATICO", "RRM", "TPC"] = "ESTATICO"
    dfs_permitido: bool = False
    dominio_regulatorio: str = Field(default="BO", min_length=2, max_length=10)
    tipo_antena: str = "OMNIDIRECCIONAL"
    modelo_antena: str | None = None
    ganancia_dbi: float = Field(default=2.14, ge=0, le=30)
    beamwidth_horizontal: float = Field(default=360, gt=0, le=360)
    beamwidth_vertical: float = Field(default=60, gt=0, le=360)
    azimut_grados: float = Field(default=0, ge=0, lt=360)
    inclinacion_grados: float = Field(default=0, ge=-90, le=90)
    perdida_cable_db: float = Field(default=0, ge=0, le=30)
    procedencia: str = "INGRESADA_TECNICO"
    bssids: list[BSSIDRadioIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_radio(self):
        if self.potencia_dbm > self.potencia_max_dbm:
            raise ValueError("La potencia configurada supera la potencia máxima.")
        if self.banda == "2.4" and self.canal > 14:
            raise ValueError("El canal no pertenece a 2,4 GHz.")
        if self.banda == "2.4" and self.ancho_canal_mhz == 80:
            raise ValueError("2,4 GHz no admite 80 MHz en este alcance.")
        return self


class APFisicoCrearIn(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    fabricante: str = Field(min_length=1, max_length=100)
    modelo: str = Field(min_length=1, max_length=120)
    rol: Literal["TEMPORAL", "EXISTENTE", "CANDIDATO"] = "EXISTENTE"
    restriccion_movimiento: Literal["MOVIBLE", "FIJO", "RETIRABLE"] = "MOVIBLE"
    coord_x: float = Field(ge=0)
    coord_y: float = Field(ge=0)
    altura_m: float = Field(default=2.5, gt=0, le=30)
    tipo_montaje: str = "TECHO"
    costo_referencial: float | None = Field(default=None, ge=0)
    procedencia: str = "INGRESADA_TECNICO"
    verificado: bool = False
    radios: list[RadioAPIn] = Field(min_length=1)


class BSSIDRadioOut(BSSIDRadioIn):
    id: int
    model_config = {"from_attributes": True}


class RadioAPOut(RadioAPIn):
    id: int
    eirp_dbm: float
    bssids: list[BSSIDRadioOut]
    model_config = {"from_attributes": True}


class APFisicoOut(APFisicoCrearIn):
    id: int
    plano_id: int
    created_at: datetime
    radios: list[RadioAPOut]
    model_config = {"from_attributes": True}


class InventarioRFOut(BaseModel):
    plano_id: int
    aps: list[APFisicoOut]
    porcentaje_completitud: float
    nivel_completitud: Literal["ALTO", "MEDIO", "BAJO"]
    bloqueos: list[str]
    advertencias: list[str]
