"""Router principal v1.

Agrupa auth, admin/usuarios, admin/proyectos, clientes y proyectos.

Sprint 1 — PB-09, PB-13, PB-18, PB-19.
Sprint 3 — PB-03, PB-04.
Sprint 4 — PB-05, PB-06.
Sprint 5 — PB-07, PB-12, PB-08.
"""

from fastapi import APIRouter

from app.api.v1 import (
    admin_proyectos,
    admin_usuarios,
    auth,
    clientes,
    escenarios,
    heatmaps,
    inventario_rf,
    mediciones,
    notificaciones,
    planos,
    proyectos,
    share,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin_usuarios.router)
api_router.include_router(admin_proyectos.router)
api_router.include_router(clientes.router)
api_router.include_router(proyectos.router)
api_router.include_router(notificaciones.router)
api_router.include_router(planos.router_proyectos)
api_router.include_router(planos.router_planos)
api_router.include_router(mediciones.router_mediciones)
api_router.include_router(mediciones.router_puntos)
api_router.include_router(mediciones.router_planos_puntos)
api_router.include_router(heatmaps.router_planos_heatmap)
api_router.include_router(heatmaps.router_conjuntos_ap)
api_router.include_router(heatmaps.router_mapas)
api_router.include_router(heatmaps.router_aps)
api_router.include_router(inventario_rf.router)
api_router.include_router(escenarios.router_proyectos_escenarios)
api_router.include_router(escenarios.router_escenarios)
api_router.include_router(escenarios.router_reportes)
api_router.include_router(share.router)
