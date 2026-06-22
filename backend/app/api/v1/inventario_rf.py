"""Endpoints para inventario físico y configuración RF."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.inventario_rf import APFisico, BSSIDRadio, RadioAP
from app.models.plano import Plano
from app.models.proyecto import Proyecto
from app.models.usuario import Usuario
from app.schemas.inventario_rf import APFisicoCrearIn, APFisicoOut, InventarioRFOut

router = APIRouter(tags=["inventario-rf"])


def _plano_tecnico(plano_id: int, usuario: Usuario, db: Session) -> Plano:
    plano = db.query(Plano).filter(Plano.id == plano_id).first()
    if plano is None or (
        usuario.rol != "admin" and plano.proyecto.tecnico_id != usuario.id
    ):
        raise HTTPException(status_code=404, detail="Plano no encontrado.")
    return plano


def _plano_proyecto(proyecto_id: int, usuario: Usuario, db: Session) -> Plano:
    query = db.query(Proyecto).filter(Proyecto.id == proyecto_id)
    if usuario.rol != "admin":
        query = query.filter(Proyecto.tecnico_id == usuario.id)
    proyecto = query.first()
    if proyecto is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    plano = next(
        (
            item
            for item in sorted(proyecto.planos, key=lambda p: p.id, reverse=True)
            if item.calibrado
        ),
        None,
    )
    if plano is None:
        raise HTTPException(
            status_code=422, detail="El proyecto requiere un plano calibrado."
        )
    return plano


def _evaluar_inventario(plano: Plano) -> InventarioRFOut:
    aps = list(plano.aps_fisicos)
    bloqueos: list[str] = []
    advertencias: list[str] = []
    if not plano.calibrado:
        bloqueos.append("El plano no tiene escala calibrada.")
    if not aps:
        bloqueos.append("No existe inventario de APs físicos.")
    total_campos = max(1, len(aps) * 4)
    completos = 0
    for ap in aps:
        completos += int(bool(ap.fabricante and ap.modelo))
        completos += int(ap.altura_m > 0)
        completos += int(bool(ap.radios))
        radios_completas = bool(ap.radios) and all(
            radio.potencia_max_dbm >= radio.potencia_dbm
            and radio.ganancia_dbi >= 0
            and radio.banda in {"2.4", "5"}
            for radio in ap.radios
        )
        completos += int(radios_completas)
        if not ap.verificado:
            advertencias.append(f"{ap.nombre}: ubicación/configuración no verificada.")
        for radio in ap.radios:
            if radio.referencia_potencia == "DESCONOCIDA":
                advertencias.append(
                    f"{ap.nombre} {radio.banda} GHz: referencia de potencia "
                    "desconocida."
                )
            if not radio.bssids and ap.rol != "CANDIDATO":
                advertencias.append(
                    f"{ap.nombre} {radio.banda} GHz: sin BSSID asociado."
                )
    porcentaje = round(completos * 100 / total_campos, 2) if aps else 0.0
    nivel = (
        "BAJO"
        if bloqueos or porcentaje < 60
        else "MEDIO"
        if porcentaje < 90 or advertencias
        else "ALTO"
    )
    return InventarioRFOut(
        plano_id=plano.id,
        aps=[APFisicoOut.model_validate(ap) for ap in aps],
        porcentaje_completitud=porcentaje,
        nivel_completitud=nivel,
        bloqueos=bloqueos,
        advertencias=advertencias,
    )


@router.get("/planos/{plano_id}/inventario-rf", response_model=InventarioRFOut)
def obtener_inventario(
    plano_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> InventarioRFOut:
    return _evaluar_inventario(_plano_tecnico(plano_id, current_user, db))


@router.get("/proyectos/{proyecto_id}/inventario-rf", response_model=InventarioRFOut)
def obtener_inventario_proyecto(
    proyecto_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> InventarioRFOut:
    return _evaluar_inventario(_plano_proyecto(proyecto_id, current_user, db))


@router.post(
    "/planos/{plano_id}/aps",
    response_model=APFisicoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_ap(
    plano_id: int,
    body: APFisicoCrearIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> APFisicoOut:
    plano = _plano_tecnico(plano_id, current_user, db)
    if body.coord_x > plano.ancho_px or body.coord_y > plano.alto_px:
        raise HTTPException(status_code=422, detail="La posición está fuera del plano.")
    ap_data = body.model_dump(exclude={"radios"})
    ap = APFisico(plano_id=plano.id, **ap_data)
    db.add(ap)
    db.flush()
    try:
        for radio_data in body.radios:
            bssids = radio_data.bssids
            radio = RadioAP(
                ap_fisico_id=ap.id, **radio_data.model_dump(exclude={"bssids"})
            )
            db.add(radio)
            db.flush()
            for item in bssids:
                db.add(BSSIDRadio(radio_id=radio.id, **item.model_dump()))
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="BSSID duplicado o inventario inconsistente."
        )
    db.refresh(ap)
    return APFisicoOut.model_validate(ap)


@router.post(
    "/proyectos/{proyecto_id}/inventario-rf/aps",
    response_model=APFisicoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear_ap_proyecto(
    proyecto_id: int,
    body: APFisicoCrearIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> APFisicoOut:
    plano = _plano_proyecto(proyecto_id, current_user, db)
    return crear_ap(
        plano_id=plano.id,
        body=body,
        db=db,
        current_user=current_user,
    )


@router.put("/aps/{ap_id}", response_model=APFisicoOut)
def reemplazar_ap(
    ap_id: int,
    body: APFisicoCrearIn,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> APFisicoOut:
    ap = db.query(APFisico).filter(APFisico.id == ap_id).first()
    if ap is None:
        raise HTTPException(status_code=404, detail="AP físico no encontrado.")
    _plano_tecnico(ap.plano_id, current_user, db)
    for key, value in body.model_dump(exclude={"radios"}).items():
        setattr(ap, key, value)
    ap.radios.clear()
    db.flush()
    for radio_data in body.radios:
        radio = RadioAP(ap_fisico_id=ap.id, **radio_data.model_dump(exclude={"bssids"}))
        db.add(radio)
        db.flush()
        for item in radio_data.bssids:
            db.add(BSSIDRadio(radio_id=radio.id, **item.model_dump()))
    db.commit()
    db.refresh(ap)
    return APFisicoOut.model_validate(ap)


@router.delete("/aps/{ap_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_ap(
    ap_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    ap = db.query(APFisico).filter(APFisico.id == ap_id).first()
    if ap is None:
        raise HTTPException(status_code=404, detail="AP físico no encontrado.")
    _plano_tecnico(ap.plano_id, current_user, db)
    db.delete(ap)
    db.commit()
