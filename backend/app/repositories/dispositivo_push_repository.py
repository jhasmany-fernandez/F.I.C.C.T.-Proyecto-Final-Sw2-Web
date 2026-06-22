"""Persistencia de tokens FCM asociados a usuarios."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.dispositivo_push import DispositivoPush


class DispositivoPushRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def registrar(
        self, *, usuario_id: int, token: str, plataforma: str
    ) -> DispositivoPush:
        dispositivo = (
            self._db.query(DispositivoPush)
            .filter(DispositivoPush.token == token)
            .first()
        )
        if dispositivo is None:
            dispositivo = DispositivoPush(
                usuario_id=usuario_id,
                token=token,
                plataforma=plataforma,
            )
            self._db.add(dispositivo)
        else:
            dispositivo.usuario_id = usuario_id
            dispositivo.plataforma = plataforma
            dispositivo.activo = True
            dispositivo.ultimo_registro = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(dispositivo)
        return dispositivo

    def desactivar(self, *, usuario_id: int, token: str) -> bool:
        actualizados = (
            self._db.query(DispositivoPush)
            .filter(
                DispositivoPush.usuario_id == usuario_id,
                DispositivoPush.token == token,
            )
            .update(
                {DispositivoPush.activo: False},
                synchronize_session=False,
            )
        )
        self._db.commit()
        return actualizados > 0

    def listar_tokens_activos(self, *, usuario_id: int) -> list[str]:
        filas = (
            self._db.query(DispositivoPush.token)
            .filter(
                DispositivoPush.usuario_id == usuario_id,
                DispositivoPush.activo.is_(True),
            )
            .all()
        )
        return [fila[0] for fila in filas]

    def desactivar_tokens(self, tokens: list[str]) -> None:
        if not tokens:
            return
        (
            self._db.query(DispositivoPush)
            .filter(DispositivoPush.token.in_(tokens))
            .update({DispositivoPush.activo: False}, synchronize_session=False)
        )
        self._db.commit()
