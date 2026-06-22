"""Fixtures compartidos para los tests del backend.

Sprint 1 — Usa SQLite en memoria para independencia de PostgreSQL.
"""

import pytest
import anyio
import anyio.to_thread
import fastapi.routing
import httpx
import starlette.concurrency
import starlette.routing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.models.usuario import Usuario


async def _run_in_threadpool_directo(func, *args, **kwargs):
    return func(*args, **kwargs)


async def _anyio_run_sync_directo(func, *args, **kwargs):
    kwargs.pop("abandon_on_cancel", None)
    kwargs.pop("cancellable", None)
    kwargs.pop("limiter", None)
    return func(*args)


fastapi.routing.run_in_threadpool = _run_in_threadpool_directo
starlette.routing.run_in_threadpool = _run_in_threadpool_directo
starlette.concurrency.run_in_threadpool = _run_in_threadpool_directo
anyio.to_thread.run_sync = _anyio_run_sync_directo

from app.main import app

TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class SyncASGIClient:
    """Cliente síncrono para tests sobre httpx.ASGITransport.

    Evita el bloqueo observado en ``fastapi.testclient.TestClient`` con
    Python 3.14 + Starlette 1.0.0, manteniendo la API usada por los tests.
    """

    def __init__(self, app) -> None:
        self._app = app

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        async def _send() -> httpx.Response:
            transport = httpx.ASGITransport(app=self._app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.request(method, url, **kwargs)
                await response.aread()
                return response

        return anyio.run(_send)

    def get(self, url: str, **kwargs) -> httpx.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs) -> httpx.Response:
        return self.request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)

    def close(self) -> None:
        return None


@pytest.fixture(autouse=True)
def crear_tablas():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Sesión de BD con rollback automático al finalizar cada test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """TestClient con la BD de pruebas inyectada."""

    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    c = SyncASGIClient(app)
    try:
        yield c
    finally:
        c.close()
        app.dependency_overrides.clear()


@pytest.fixture
def admin_usuario(db_session) -> Usuario:
    """Usuario administrador de prueba."""
    u = Usuario(
        nombre="Admin Test",
        email="admin@test.bo",
        password_hash=hash_password("Admin1234!"),
        rol="admin",
        activo=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def tecnico_usuario(db_session) -> Usuario:
    """Usuario técnico de prueba."""
    u = Usuario(
        nombre="Técnico Test",
        email="tecnico@test.bo",
        password_hash=hash_password("Tecnico1234!"),
        rol="tecnico",
        activo=True,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def admin_token(client, admin_usuario) -> str:
    """JWT de acceso para el admin de prueba."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.bo", "password": "Admin1234!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def tecnico_token(client, tecnico_usuario) -> str:
    """JWT de acceso para el técnico de prueba."""
    response = client.post(
        "/auth/login",
        json={"email": "tecnico@test.bo", "password": "Tecnico1234!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]
