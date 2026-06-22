"""Repositorio de acceso a datos para la entidad Plano.

Sprint 2 — PB-02 (Importar Plano), PB-11 (Calibrar Escala).
"""

from sqlalchemy.orm import Session

from app.models.plano import Plano


class PlanoRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def listar_por_proyecto(self, *, proyecto_id: int) -> list[Plano]:
        return (
            self._db.query(Plano)
            .filter(Plano.proyecto_id == proyecto_id)
            .order_by(Plano.created_at.desc())
            .all()
        )

    def obtener_por_id(self, *, plano_id: int) -> Plano | None:
        return self._db.query(Plano).filter(Plano.id == plano_id).first()

    def obtener_por_ruta(self, *, ruta_storage: str) -> Plano | None:
        return self._db.query(Plano).filter(Plano.ruta_storage == ruta_storage).first()

    def crear(
        self,
        *,
        proyecto_id: int,
        nombre: str,
        formato: str,
        ruta_storage: str,
        ancho_px: int,
        alto_px: int,
        tamano_bytes: int,
    ) -> Plano:
        plano = Plano(
            proyecto_id=proyecto_id,
            nombre=nombre,
            formato=formato,
            ruta_storage=ruta_storage,
            ancho_px=ancho_px,
            alto_px=alto_px,
            tamano_bytes=tamano_bytes,
        )
        self._db.add(plano)
        self._db.commit()
        self._db.refresh(plano)
        return plano

    def actualizar_calibracion(
        self,
        *,
        plano: Plano,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        distancia_real_m: float,
        escala_m_por_px: float,
    ) -> Plano:
        plano.calibracion_x1 = x1
        plano.calibracion_y1 = y1
        plano.calibracion_x2 = x2
        plano.calibracion_y2 = y2
        plano.distancia_real_m = distancia_real_m
        plano.escala_m_por_px = escala_m_por_px
        self._db.commit()
        self._db.refresh(plano)
        return plano

    def eliminar(self, *, plano: Plano) -> None:
        self._db.delete(plano)
        self._db.commit()

    def contar_puntos(self, *, plano_id: int) -> int:
        """Placeholder hasta el Sprint 3 (tabla 'punto_medicion' aún no existe)."""
        return 0
