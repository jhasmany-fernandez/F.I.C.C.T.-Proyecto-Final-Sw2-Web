"""DTOs del portal público de cliente.

Sprint 6 — PB-15/PB-16/PB-17.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.escenario import EscenarioOptimizadoOut
from app.schemas.heatmap import AnalisisCoberturaOut, ConjuntoAPOut, MapaCalorOut
from app.schemas.plano import PlanoOut


class ContenidoEnlaceIn(BaseModel):
    conjunto_ids: list[int] = Field(default_factory=list)
    mapa_ids: list[int] = Field(default_factory=list)
    analisis_ids: list[int] = Field(default_factory=list)
    escenario_ids: list[int] = Field(default_factory=list)
    reporte_id: int | None = None


class EnlaceClienteCrearIn(BaseModel):
    expira_en_dias: int = Field(default=7, ge=1, le=365)
    contenido: ContenidoEnlaceIn


class EnlaceClienteActualizarIn(BaseModel):
    revocado: bool


class EnlaceClienteOut(BaseModel):
    id: int
    proyecto_id: int
    url_publica: str
    expira_en: datetime
    revocado: bool
    accesos: int
    ultimo_acceso: datetime | None
    ip_ultimo_acceso: str | None
    contenido: ContenidoEnlaceIn
    created_at: datetime


class ProyectoPortalOut(BaseModel):
    id: int
    nombre: str
    cliente: str | None
    descripcion: str | None


class PortalClienteOut(BaseModel):
    proyecto: ProyectoPortalOut
    planos: list[PlanoOut]
    conjuntos: list[ConjuntoAPOut]
    heatmaps: list[MapaCalorOut]
    analisis: list[AnalisisCoberturaOut]
    escenarios: list[EscenarioOptimizadoOut]
    reporte_disponible: bool
