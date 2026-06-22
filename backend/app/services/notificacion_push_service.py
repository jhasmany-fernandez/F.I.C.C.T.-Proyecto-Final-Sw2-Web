"""Envío de notificaciones de asignación mediante Firebase Cloud Messaging."""

import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.dispositivo_push_repository import DispositivoPushRepository

logger = logging.getLogger(__name__)


class NotificacionPushService:
    def notificar_asignacion(
        self,
        *,
        db: Session,
        tecnico_id: int,
        proyecto_id: int,
        proyecto_nombre: str,
    ) -> bool:
        repo = DispositivoPushRepository(db)
        try:
            tokens = repo.listar_tokens_activos(usuario_id=tecnico_id)
            if not tokens:
                return False

            app, messaging = self._firebase()
            mensajes = [
                messaging.Message(
                    token=token,
                    notification=messaging.Notification(
                        title="Nuevo proyecto asignado",
                        body=f'Se te asignó el proyecto "{proyecto_nombre}".',
                    ),
                    data={
                        "tipo": "proyecto_asignado",
                        "proyecto_id": str(proyecto_id),
                        "proyecto_nombre": proyecto_nombre,
                    },
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            channel_id="asignaciones_proyecto",
                        ),
                    ),
                )
                for token in tokens
            ]
            respuesta = messaging.send_each(mensajes, app=app)
            invalidos = [
                tokens[indice]
                for indice, resultado in enumerate(respuesta.responses)
                if not resultado.success and self._token_invalido(resultado.exception)
            ]
            repo.desactivar_tokens(invalidos)
            if respuesta.failure_count:
                logger.warning(
                    "FCM no entregó %s de %s notificaciones para el técnico %s.",
                    respuesta.failure_count,
                    len(tokens),
                    tecnico_id,
                )
            return respuesta.success_count > 0
        except Exception:
            # Una consulta o envío fallido no debe dejar inutilizable la sesión
            # usada por el endpoint que ya persistió la asignación.
            db.rollback()
            logger.exception(
                "No se pudo enviar la notificación FCM al técnico %s.", tecnico_id
            )
            return False

    @staticmethod
    def _token_invalido(error: Exception | None) -> bool:
        codigo = getattr(error, "code", "")
        mensaje = str(error).lower()
        return (
            codigo
            in {
                "NOT_FOUND",
                "INVALID_ARGUMENT",
            }
            or "registration-token-not-registered" in mensaje
        )

    @staticmethod
    def _firebase():
        import firebase_admin
        from firebase_admin import credentials, messaging

        try:
            app = firebase_admin.get_app()
        except ValueError:
            opciones = (
                {"projectId": settings.firebase_project_id}
                if settings.firebase_project_id
                else None
            )
            if settings.firebase_credentials_json:
                credencial = credentials.Certificate(
                    json.loads(settings.firebase_credentials_json)
                )
            elif settings.firebase_credentials_path:
                credencial = credentials.Certificate(
                    str(Path(settings.firebase_credentials_path))
                )
            else:
                credencial = credentials.ApplicationDefault()
            app = firebase_admin.initialize_app(credencial, opciones)
        return app, messaging


notificacion_push_service = NotificacionPushService()


def get_notificacion_push_service() -> NotificacionPushService:
    return notificacion_push_service
