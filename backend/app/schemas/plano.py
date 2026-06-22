"""DTOs de Plano (Sprint 2 — PB-02, PB-11)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from app.models.plano import Plano


class PlanoOut(BaseModel):
    """DTO de salida de un plano."""

    id: int
    proyecto_id: int
    nombre: str
    formato: Literal["png", "jpg", "pdf"]
    ancho_px: int
    alto_px: int
    tamano_bytes: int
    url_firmada: str
    calibrado: bool
    escala_m_por_px: float | None = None
    distancia_real_m: float | None = None
    calibracion_x1: float | None = None
    calibracion_y1: float | None = None
    calibracion_x2: float | None = None
    calibracion_y2: float | None = None
    warning: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_plano(
        cls,
        p: Plano,
        *,
        url_firmada: str,
        warning: str | None = None,
    ) -> PlanoOut:
        return cls(
            id=p.id,
            proyecto_id=p.proyecto_id,
            nombre=p.nombre,
            formato=p.formato,
            ancho_px=p.ancho_px,
            alto_px=p.alto_px,
            tamano_bytes=p.tamano_bytes,
            url_firmada=url_firmada,
            calibrado=p.calibrado,
            escala_m_por_px=p.escala_m_por_px,
            distancia_real_m=p.distancia_real_m,
            calibracion_x1=p.calibracion_x1,
            calibracion_y1=p.calibracion_y1,
            calibracion_x2=p.calibracion_x2,
            calibracion_y2=p.calibracion_y2,
            warning=warning,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )


class PlanoCalibracionIn(BaseModel):
    """Entrada para PATCH /api/planos/{id}/calibracion. PB-11 CA-2."""

    x1: float = Field(..., ge=0)
    y1: float = Field(..., ge=0)
    x2: float = Field(..., ge=0)
    y2: float = Field(..., ge=0)
    distancia_real_m: float = Field(..., gt=0, description="Debe ser ≥ 1 metro.")

    @model_validator(mode="after")
    def _validar_puntos_distintos(self) -> PlanoCalibracionIn:
        if (self.x1, self.y1) == (self.x2, self.y2):
            raise ValueError("Los puntos de calibración deben ser distintos.")
        return self


class UrlFirmadaOut(BaseModel):
    """Respuesta de renovación de URL firmada."""

    url_firmada: str
    expira_en: int
