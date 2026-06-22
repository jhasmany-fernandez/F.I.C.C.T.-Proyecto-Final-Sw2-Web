from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, Field

from app.schemas.cliente import ClienteBasicoOut

if TYPE_CHECKING:
    from app.models.proyecto import Proyecto


class ProyectoIn(BaseModel):
    """DTO de entrada para crear o actualizar un proyecto. PB-01 — CA-1/CA-2."""

    nombre: str = Field(..., min_length=1, max_length=200)
    cliente_id: int | None = None
    descripcion: str | None = Field(default=None, max_length=500)


class ProyectoAdminCreate(ProyectoIn):
    """Alta de proyecto desde el panel web con técnico responsable."""

    tecnico_id: int
    estado: Literal["nuevo", "en_progreso", "completado", "archivado"] = "nuevo"


class ProyectoAdminUpdate(BaseModel):
    """Cambios parciales permitidos al administrador."""

    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    cliente_id: int | None = None
    descripcion: str | None = Field(default=None, max_length=500)
    tecnico_id: int | None = None
    estado: Literal["nuevo", "en_progreso", "completado", "archivado"] | None = None


class ProyectoTecnicoOut(BaseModel):
    """DTO de salida para el listado de proyectos del técnico autenticado.

    Normaliza ``ultima_actividad`` → ``updated_at`` y ``estado`` a mayúsculas
    para compatibilidad con la app móvil. PB-09 — CA-1.
    """

    id: int
    nombre: str
    cliente: ClienteBasicoOut | None
    descripcion: str | None = None
    estado: Literal["NUEVO", "EN_PROGRESO", "COMPLETADO", "ARCHIVADO"]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_proyecto(cls, p: Proyecto) -> ProyectoTecnicoOut:
        return cls(
            id=p.id,
            nombre=p.nombre,
            cliente=ClienteBasicoOut.model_validate(p.cliente) if p.cliente else None,
            descripcion=p.descripcion,
            estado=p.estado.upper(),
            created_at=p.created_at,
            updated_at=p.ultima_actividad,
        )


class TecnicoBasicoOut(BaseModel):
    """Datos mínimos del técnico asignado a un proyecto. PB-18."""

    id: int
    nombre: str
    email: str

    model_config = {"from_attributes": True}


class ProyectoListOut(BaseModel):
    """DTO de salida para el listado de proyectos del admin. PB-18 (CA-2)."""

    id: int
    nombre: str
    descripcion: str | None = None
    cliente: ClienteBasicoOut | None
    estado: Literal["nuevo", "en_progreso", "completado", "archivado"]
    ultima_actividad: datetime
    cantidad_puntos: int
    tecnico: TecnicoBasicoOut
    created_at: datetime

    model_config = {"from_attributes": True}


class ProyectosPageOut(BaseModel):
    """Respuesta paginada del listado de proyectos de la organización."""

    items: list[ProyectoListOut]
    total: int
    page: int
    page_size: int
