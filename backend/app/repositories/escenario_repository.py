"""Repositorios de Sprint 5: escenarios IA y reportes."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.escenario import (
    EscenarioOptimizado,
    RecomendacionAP,
    Reporte,
    ValorProyectadoPunto,
)


class EscenarioRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def obtener_por_id(self, *, escenario_id: int) -> EscenarioOptimizado | None:
        return (
            self._db.query(EscenarioOptimizado)
            .filter(EscenarioOptimizado.id == escenario_id)
            .first()
        )

    def listar_por_proyecto(self, *, proyecto_id: int) -> list[EscenarioOptimizado]:
        return (
            self._db.query(EscenarioOptimizado)
            .filter(EscenarioOptimizado.proyecto_id == proyecto_id)
            .order_by(
                EscenarioOptimizado.pct_cobertura.desc(),
                EscenarioOptimizado.costo_estimado.asc(),
                EscenarioOptimizado.created_at.desc(),
            )
            .all()
        )

    def crear(
        self,
        *,
        proyecto_id: int,
        plano_id: int,
        mapa_actual_id: int | None,
        mapa_proyectado_id: int | None,
        conjunto_base_id: int | None = None,
        nombre: str,
        banda: str,
        modelo_ap: str,
        pct_cobertura_actual: float,
        pct_cobertura: float,
        costo_estimado: float,
        cantidad_aps: int,
        resumen: str,
        restricciones: dict,
        metricas: dict,
        recomendaciones: list[dict],
        tipo_negocio: str = "INSTALACION_NUEVA",
        perfil: str = "COBERTURA_EQUILIBRADA",
        politica_combinacion: str = "PREFERIR_5_GHZ_SI_CUMPLE_UMBRAL",
        bandas: list[str] | None = None,
        mapas_por_banda: dict | None = None,
        mapas_actuales_por_banda: dict | None = None,
        supuestos: list[str] | None = None,
        confianza: str = "MEDIA",
        version_motor: str = "rf-hibrido-1.0",
        valores_proyectados: list[dict] | None = None,
        origen: str = "ia",
        estado_gobernanza: str = "pendiente_revision",
        generado_por_id: int | None = None,
    ) -> EscenarioOptimizado:
        escenario = EscenarioOptimizado(
            proyecto_id=proyecto_id,
            plano_id=plano_id,
            mapa_actual_id=mapa_actual_id,
            mapa_proyectado_id=mapa_proyectado_id,
            conjunto_base_id=conjunto_base_id,
            origen=origen,
            estado_gobernanza=estado_gobernanza,
            generado_por_id=generado_por_id,
            nombre=nombre,
            tipo_negocio=tipo_negocio,
            perfil=perfil,
            politica_combinacion=politica_combinacion,
            banda=banda,
            bandas=bandas or [banda],
            modelo_ap=modelo_ap,
            pct_cobertura_actual=pct_cobertura_actual,
            pct_cobertura=pct_cobertura,
            costo_estimado=costo_estimado,
            cantidad_aps=cantidad_aps,
            resumen=resumen,
            restricciones=restricciones,
            metricas=metricas,
            mapas_por_banda=mapas_por_banda or {},
            mapas_actuales_por_banda=mapas_actuales_por_banda or {},
            supuestos=supuestos or [],
            confianza=confianza,
            version_motor=version_motor,
        )
        self._db.add(escenario)
        self._db.flush()
        for idx, data in enumerate(recomendaciones, start=1):
            self._db.add(
                RecomendacionAP(
                    escenario_id=escenario.id,
                    orden=idx,
                    **data,
                )
            )
        for data in valores_proyectados or []:
            self._db.add(ValorProyectadoPunto(escenario_id=escenario.id, **data))
        self._db.commit()
        self._db.refresh(escenario)
        return escenario

    def cambiar_estado(
        self,
        *,
        escenario: EscenarioOptimizado,
        estado_gobernanza: str,
        usuario_id: int,
    ) -> EscenarioOptimizado:
        escenario.estado_gobernanza = estado_gobernanza
        ahora = datetime.now(UTC)
        if estado_gobernanza == "aprobado_interno":
            escenario.aprobado_por_id = usuario_id
            escenario.aprobado_at = ahora
        elif estado_gobernanza == "publicado_cliente":
            escenario.publicado_por_id = usuario_id
            escenario.publicado_at = ahora
            if escenario.aprobado_por_id is None:
                escenario.aprobado_por_id = usuario_id
                escenario.aprobado_at = ahora
        self._db.commit()
        self._db.refresh(escenario)
        return escenario

    def eliminar(self, *, escenario: EscenarioOptimizado) -> None:
        (
            self._db.query(Reporte)
            .filter(Reporte.escenario_id == escenario.id)
            .update({Reporte.escenario_id: None}, synchronize_session=False)
        )
        self._db.delete(escenario)
        self._db.commit()

    def eliminar_por_proyecto(self, *, proyecto_id: int) -> int:
        escenarios = self.listar_por_proyecto(proyecto_id=proyecto_id)
        cantidad = len(escenarios)
        if cantidad == 0:
            return 0
        escenario_ids = [escenario.id for escenario in escenarios]
        (
            self._db.query(Reporte)
            .filter(Reporte.escenario_id.in_(escenario_ids))
            .update({Reporte.escenario_id: None}, synchronize_session=False)
        )
        for escenario in escenarios:
            self._db.delete(escenario)
        self._db.commit()
        return cantidad


class ReporteRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def obtener_por_id(self, *, reporte_id: int) -> Reporte | None:
        return self._db.query(Reporte).filter(Reporte.id == reporte_id).first()

    def listar_por_proyecto(self, *, proyecto_id: int) -> list[Reporte]:
        return (
            self._db.query(Reporte)
            .filter(Reporte.proyecto_id == proyecto_id)
            .order_by(Reporte.created_at.desc(), Reporte.id.desc())
            .all()
        )

    def existe_para_proyecto(self, *, proyecto_id: int) -> bool:
        return (
            self._db.query(Reporte.id)
            .filter(Reporte.proyecto_id == proyecto_id)
            .first()
            is not None
        )

    def crear_procesando(
        self,
        *,
        proyecto_id: int,
        escenario_id: int | None,
    ) -> Reporte:
        reporte = Reporte(
            proyecto_id=proyecto_id,
            escenario_id=escenario_id,
            estado="PROCESANDO",
        )
        self._db.add(reporte)
        self._db.commit()
        self._db.refresh(reporte)
        return reporte

    def marcar_listo(
        self,
        *,
        reporte: Reporte,
        ruta_pdf: str,
        sha256: str,
        tamanio_bytes: int,
    ) -> Reporte:
        reporte.estado = "LISTO"
        reporte.ruta_pdf = ruta_pdf
        reporte.sha256 = sha256
        reporte.tamanio_bytes = tamanio_bytes
        reporte.error = None
        self._db.commit()
        self._db.refresh(reporte)
        return reporte

    def marcar_error(self, *, reporte: Reporte, error: str) -> Reporte:
        reporte.estado = "ERROR"
        reporte.error = error
        self._db.commit()
        self._db.refresh(reporte)
        return reporte
