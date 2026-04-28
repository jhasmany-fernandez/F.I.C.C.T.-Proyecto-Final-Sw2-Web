"""Fixtures compartidos para los tests del backend.

Sprint 1 — Usa SQLite en memoria para independencia de PostgreSQL.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models.usuario import Usuario

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def crear_tablas():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Sesión de BD con rollback automático al finalizar cada test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    """TestClient con la BD de pruebas inyectada."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
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
