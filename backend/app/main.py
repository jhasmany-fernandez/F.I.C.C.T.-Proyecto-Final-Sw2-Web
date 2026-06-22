from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import SessionLocal

app = FastAPI(
    title="Wireless HeatMapper API",
    description="Backend REST + IA para el sistema de análisis de cobertura WiFi. Bulldog Tech.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers Sprint 1: auth, admin/usuarios, admin/proyectos, clientes, proyectos
app.include_router(api_router)


@app.get("/health", tags=["infraestructura"])
def health_check():
    """Verifica que el backend y la base de datos estén operativos."""
    db_status = "error"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_status = "ok"
    except OperationalError:
        pass

    return {"status": "ok", "version": "0.1.0", "db": db_status}
