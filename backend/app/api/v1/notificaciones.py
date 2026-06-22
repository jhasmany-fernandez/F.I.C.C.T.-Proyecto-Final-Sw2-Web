"""Registro de dispositivos del técnico para recibir notificaciones FCM."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.repositories.dispositivo_push_repository import DispositivoPushRepository
from app.schemas.notificacion import DispositivoPushIn, DispositivoPushOut

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])


@router.post(
    "/dispositivos",
    response_model=DispositivoPushOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar dispositivo para notificaciones",
)
def registrar_dispositivo(
    body: DispositivoPushIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> DispositivoPushOut:
    DispositivoPushRepository(db).registrar(
        usuario_id=current_user.id,
        token=body.token,
        plataforma=body.plataforma,
    )
    return DispositivoPushOut(registrado=True)


@router.delete(
    "/dispositivos",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desregistrar dispositivo",
)
def desregistrar_dispositivo(
    body: DispositivoPushIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    DispositivoPushRepository(db).desactivar(
        usuario_id=current_user.id,
        token=body.token,
    )
