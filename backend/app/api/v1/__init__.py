"""Router principal v1: agrupa auth, admin/usuarios, admin/proyectos, clientes y proyectos.

Sprint 1 — PB-09, PB-13, PB-18, PB-19.
"""

from fastapi import APIRouter

from app.api.v1 import admin_proyectos, admin_usuarios, auth, clientes, proyectos

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(admin_usuarios.router)
api_router.include_router(admin_proyectos.router)
api_router.include_router(clientes.router)
api_router.include_router(proyectos.router)
