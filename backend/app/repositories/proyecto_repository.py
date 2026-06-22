"""Repositorio de acceso a datos para la entidad Proyecto.

PB-18 — Sprint 1 (Sp1-23): listado paginado y filtrado para el admin.
PB-09 — Sprint 1: listado de proyectos propios del técnico autenticado.
PB-19 — Sprint 1: joinedload de la relación cliente.
PB-01 — Sprint 1: CRUD completo de proyectos para el técnico autenticado.
"""

from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.proyecto import Proyecto


class ProyectoRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def listar_por_tecnico(
        self,
        *,
        tecnico_id: int,
        estado: str | None = None,
    ) -> list[Proyecto]:
        """Retorna proyectos del técnico indicado.

        Sin filtro de estado devuelve solo los no-archivados.
        El parámetro *estado* se compara en minúsculas para tolerancia.
        PB-09 — CA-1.
        """
        q = (
            self._db.query(Proyecto)
            .options(joinedload(Proyecto.cliente))
            .filter(Proyecto.tecnico_id == tecnico_id)
        )
        if estado is not None:
            q = q.filter(Proyecto.estado == estado.lower())
        else:
            q = q.filter(Proyecto.estado != "archivado")
        return q.order_by(Proyecto.ultima_actividad.desc()).all()

    def listar_paginado(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        tecnico_id: int | None = None,
        estado: str | None = None,
        fecha_desde: date | None = None,
        fecha_hasta: date | None = None,
    ) -> tuple[list[Proyecto], int]:
        """Retorna (proyectos, total) con joins a tecnico y cliente para la vista de admin."""
        q = self._db.query(Proyecto).options(
            joinedload(Proyecto.tecnico), joinedload(Proyecto.cliente)
        )

        if tecnico_id is not None:
            q = q.filter(Proyecto.tecnico_id == tecnico_id)
        if estado is not None:
            q = q.filter(Proyecto.estado == estado)
        if fecha_desde is not None:
            q = q.filter(
                func.date(Proyecto.ultima_actividad) >= fecha_desde.isoformat()
            )
        if fecha_hasta is not None:
            q = q.filter(
                func.date(Proyecto.ultima_actividad) <= fecha_hasta.isoformat()
            )

        total = q.count()
        items = (
            q.order_by(Proyecto.ultima_actividad.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    # ── Operaciones CRUD (PB-01) ───────────────────────────────────────────

    def obtener_por_id(self, *, proyecto_id: int, tecnico_id: int) -> Proyecto | None:
        """Retorna el proyecto si pertenece al técnico, o None si no existe/no es suyo."""
        return (
            self._db.query(Proyecto)
            .options(joinedload(Proyecto.cliente))
            .filter(Proyecto.id == proyecto_id, Proyecto.tecnico_id == tecnico_id)
            .first()
        )

    def crear(
        self,
        *,
        nombre: str,
        tecnico_id: int,
        cliente_id: int | None = None,
        descripcion: str | None = None,
    ) -> Proyecto:
        """Crea un nuevo proyecto y lo persiste. PB-01 — CA-1."""
        proyecto = Proyecto(
            nombre=nombre,
            tecnico_id=tecnico_id,
            cliente_id=cliente_id,
            descripcion=descripcion,
            estado="en_progreso",
        )
        self._db.add(proyecto)
        self._db.commit()
        self._db.refresh(proyecto)
        # Recargar con el join de cliente para la respuesta
        return self.obtener_por_id(proyecto_id=proyecto.id, tecnico_id=tecnico_id)  # type: ignore[return-value]

    def actualizar(
        self,
        *,
        proyecto: Proyecto,
        nombre: str,
        cliente_id: int | None = None,
        descripcion: str | None = None,
    ) -> Proyecto:
        """Actualiza nombre, cliente y descripción. PB-01 — CA-2."""
        proyecto.nombre = nombre
        proyecto.cliente_id = cliente_id
        proyecto.descripcion = descripcion
        self._db.commit()
        self._db.refresh(proyecto)
        return self.obtener_por_id(
            proyecto_id=proyecto.id, tecnico_id=proyecto.tecnico_id
        )  # type: ignore[return-value]

    def obtener_por_id_admin(self, *, proyecto_id: int) -> Proyecto | None:
        """Retorna el proyecto por id sin restricción de técnico. Solo para uso admin. PB-18."""
        return (
            self._db.query(Proyecto)
            .options(joinedload(Proyecto.cliente), joinedload(Proyecto.tecnico))
            .filter(Proyecto.id == proyecto_id)
            .first()
        )

    def archivar(self, *, proyecto: Proyecto) -> Proyecto:
        """Cambia el estado del proyecto a 'archivado'. PB-01 — CA-3 / PB-18 admin."""
        proyecto.estado = "archivado"
        self._db.commit()
        self._db.refresh(proyecto)
        return proyecto

    def reasignar_tecnico(
        self, *, proyecto: Proyecto, nuevo_tecnico_id: int
    ) -> Proyecto:
        """Reasigna el proyecto a otro técnico activo. Solo admin. PB-18."""
        proyecto.tecnico_id = nuevo_tecnico_id
        self._db.commit()
        self._db.refresh(proyecto)
        return self.obtener_por_id_admin(proyecto_id=proyecto.id)  # type: ignore[return-value]

    def eliminar(self, *, proyecto: Proyecto) -> None:
        """Elimina el proyecto de la base de datos. PB-01 — CA-4."""
        self._db.delete(proyecto)
        self._db.commit()
