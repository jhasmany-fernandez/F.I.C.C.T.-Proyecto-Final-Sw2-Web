"""Endpoints de planos del edificio.

Sprint 2 — PB-02 (Importar Plano), PB-11 (Calibrar Escala).
"""

import math
import secrets
from io import BytesIO
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from PIL import Image
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.repositories.plano_repository import PlanoRepository
from app.repositories.proyecto_repository import ProyectoRepository
from app.schemas.plano import PlanoCalibracionIn, PlanoOut, UrlFirmadaOut
from app.services.pdf_service import PdfService
from app.storage import LocalFilesystemStorage, generar_url_firmada, verificar_firma

# Routers separados según prefijo lógico
router_proyectos = APIRouter(prefix="/proyectos", tags=["planos"])
router_planos = APIRouter(prefix="/planos", tags=["planos"])

MAX_BYTES = 20 * 1024 * 1024  # 20 MB (CA-2 de PB-02)
FORMATOS_IMAGEN = {"png": "png", "jpg": "jpg", "jpeg": "jpg"}
FORMATOS_VALIDOS = {"png", "jpg", "jpeg", "pdf"}


def _storage() -> LocalFilesystemStorage:
    return LocalFilesystemStorage(root=settings.storage_root)


def _base_url(request: Request) -> str:
    # Devuelve la URL pública del API. En producción nginx expone /api,
    # por lo que ``public_api_url`` se inyecta vía settings. Si está vacío,
    # devolvemos ruta relativa para que el cliente la prefije.
    return settings.public_api_url


def _firmar(ruta: str, request: Request) -> str:
    return generar_url_firmada(
        ruta_relativa=ruta,
        secret=settings.storage_url_secret,
        base_url=_base_url(request),
        ttl_seconds=settings.storage_url_ttl_seconds,
    )


def _verificar_ownership(
    *,
    proyecto_id: int,
    current_user: Usuario,
    db: Session,
):
    repo = ProyectoRepository(db)
    proyecto = (
        repo.obtener_por_id_admin(proyecto_id=proyecto_id)
        if current_user.rol == "admin"
        else repo.obtener_por_id(
            proyecto_id=proyecto_id,
            tecnico_id=current_user.id,
        )
    )
    if proyecto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proyecto no encontrado.",
        )
    return proyecto


def _verificar_ownership_plano(
    *,
    plano_id: int,
    current_user: Usuario,
    db: Session,
):
    plano_repo = PlanoRepository(db)
    plano = plano_repo.obtener_por_id(plano_id=plano_id)
    if plano is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plano no encontrado.",
        )
    _verificar_ownership(
        proyecto_id=plano.proyecto_id,
        current_user=current_user,
        db=db,
    )
    return plano


@router_proyectos.post(
    "/{proyecto_id}/planos",
    response_model=PlanoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Importar plano",
    description=(
        "Sube un plano del edificio (PNG, JPG ≤ 20 MB) o un PDF cuya primera página "
        "se renderiza a PNG en backend. PB-02 — CA-1 a CA-5."
    ),
)
async def importar_plano(
    proyecto_id: int,
    request: Request,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PlanoOut:
    _verificar_ownership(
        proyecto_id=proyecto_id,
        current_user=current_user,
        db=db,
    )

    contenido = await archivo.read()
    if len(contenido) > MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo supera el límite de 20 MB.",
        )

    nombre_orig = archivo.filename or "plano"
    ext = Path(nombre_orig).suffix.lower().lstrip(".")
    if ext not in FORMATOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Formato no soportado: .{ext}. Use PNG, JPG o PDF.",
        )

    storage = _storage()
    warning: str | None = None

    if ext == "pdf":
        try:
            render = PdfService().render_first_page(contenido)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        formato_final = "pdf"
        png_bytes = render.png_bytes
        ancho_px = render.ancho_px
        alto_px = render.alto_px
        tamano_bytes = len(png_bytes)
        if render.multipagina:
            warning = (
                f"El PDF tenía {render.cantidad_paginas} páginas. "
                "Solo se importó la primera."
            )
        ruta = f"{proyecto_id}/{secrets.token_hex(8)}_{Path(nombre_orig).stem}.png"
        storage.save(png_bytes, ruta)
    else:
        formato_final = FORMATOS_IMAGEN[ext]
        try:
            with Image.open(BytesIO(contenido)) as img:
                img.verify()
            with Image.open(BytesIO(contenido)) as img:
                ancho_px, alto_px = img.size
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La imagen está corrupta o no es válida.",
            ) from exc
        tamano_bytes = len(contenido)
        ruta = (
            f"{proyecto_id}/{secrets.token_hex(8)}_{Path(nombre_orig).stem}.{formato_final}"
        )
        storage.save(contenido, ruta)

    plano_repo = PlanoRepository(db)
    plano = plano_repo.crear(
        proyecto_id=proyecto_id,
        nombre=Path(nombre_orig).name,
        formato=formato_final,
        ruta_storage=ruta,
        ancho_px=ancho_px,
        alto_px=alto_px,
        tamano_bytes=tamano_bytes,
    )

    return PlanoOut.from_plano(
        plano,
        url_firmada=_firmar(plano.ruta_storage, request),
        warning=warning,
        cantidad_puntos=0,
    )


@router_proyectos.get(
    "/{proyecto_id}/planos",
    response_model=list[PlanoOut],
    summary="Listar planos del proyecto",
)
def listar_planos(
    proyecto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[PlanoOut]:
    _verificar_ownership(
        proyecto_id=proyecto_id,
        current_user=current_user,
        db=db,
    )
    plano_repo = PlanoRepository(db)
    planos = plano_repo.listar_por_proyecto(proyecto_id=proyecto_id)
    return [
        PlanoOut.from_plano(
            p,
            url_firmada=_firmar(p.ruta_storage, request),
            cantidad_puntos=plano_repo.contar_puntos(plano_id=p.id),
        )
        for p in planos
    ]


@router_planos.get(
    "/{plano_id}",
    response_model=PlanoOut,
    summary="Obtener detalle de un plano",
)
def obtener_plano(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PlanoOut:
    plano = _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )
    plano_repo = PlanoRepository(db)
    return PlanoOut.from_plano(
        plano,
        url_firmada=_firmar(plano.ruta_storage, request),
        cantidad_puntos=plano_repo.contar_puntos(plano_id=plano.id),
    )


@router_planos.get(
    "/{plano_id}/url-firmada",
    response_model=UrlFirmadaOut,
    summary="Renovar URL firmada de descarga",
)
def renovar_url(
    plano_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> UrlFirmadaOut:
    plano = _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )
    url = _firmar(plano.ruta_storage, request)
    return UrlFirmadaOut(
        url_firmada=url,
        expira_en=settings.storage_url_ttl_seconds,
    )


@router_planos.patch(
    "/{plano_id}/calibracion",
    response_model=PlanoOut,
    summary="Calibrar escala del plano",
    description=(
        "Define la escala metros/píxel a partir de dos puntos y una distancia real. "
        "PB-11 — CA-1 a CA-4. Bloquea recalibración si el plano ya tiene puntos."
    ),
)
def calibrar_plano(
    plano_id: int,
    body: PlanoCalibracionIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PlanoOut:
    plano = _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )

    if body.distancia_real_m < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La distancia real debe ser ≥ 1 metro (PB-11 CA-3).",
        )

    plano_repo = PlanoRepository(db)
    if plano.calibrado and plano_repo.contar_puntos(plano_id=plano.id) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede recalibrar un plano con puntos de medición.",
        )

    distancia_px = math.hypot(body.x2 - body.x1, body.y2 - body.y1)
    if distancia_px < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Los puntos están demasiado cerca para calibrar.",
        )
    escala = body.distancia_real_m / distancia_px

    plano = plano_repo.actualizar_calibracion(
        plano=plano,
        x1=body.x1,
        y1=body.y1,
        x2=body.x2,
        y2=body.y2,
        distancia_real_m=body.distancia_real_m,
        escala_m_por_px=escala,
    )
    return PlanoOut.from_plano(
        plano,
        url_firmada=_firmar(plano.ruta_storage, request),
        cantidad_puntos=plano_repo.contar_puntos(plano_id=plano.id),
    )


@router_planos.delete(
    "/{plano_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar plano",
)
def eliminar_plano(
    plano_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    plano = _verificar_ownership_plano(
        plano_id=plano_id,
        current_user=current_user,
        db=db,
    )
    plano_repo = PlanoRepository(db)
    if plano_repo.contar_puntos(plano_id=plano.id) > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar un plano con puntos de medición.",
        )
    storage = _storage()
    storage.delete(plano.ruta_storage)
    plano_repo.eliminar(plano=plano)


_MEDIA_TYPES = {"png": "image/png", "jpg": "image/jpeg"}


@router_planos.get(
    "/archivo/{ruta:path}",
    summary="Descargar archivo de plano (URL firmada)",
    description="Endpoint público que valida la firma HMAC + expiración.",
)
def descargar_archivo(
    ruta: str,
    exp: int = Query(...),
    sig: str = Query(...),
    db: Session = Depends(get_db),
) -> Response:
    if not verificar_firma(
        ruta_relativa=ruta,
        secret=settings.storage_url_secret,
        exp=exp,
        sig=sig,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Firma inválida o URL expirada.",
        )

    plano_repo = PlanoRepository(db)
    plano = plano_repo.obtener_por_ruta(ruta_storage=ruta)
    if plano is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado.",
        )

    storage = _storage()
    if not storage.exists(ruta):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en storage.",
        )

    contenido = storage.read(ruta)
    # Los PDFs se sirven como PNG (renderizados durante la importación).
    ext = Path(ruta).suffix.lower().lstrip(".")
    media_type = _MEDIA_TYPES.get(ext, "application/octet-stream")
    return Response(content=contenido, media_type=media_type)
