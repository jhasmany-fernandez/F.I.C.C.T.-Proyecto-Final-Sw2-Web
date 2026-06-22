"""Tests del flujo de autenticación.

Sprint 1 — Sp1-16 — PB-09 (CA-1, CA-2, CA-3, CA-4).
Coverage objetivo: ≥ 80 % en auth.
"""

import pytest
from fastapi.testclient import TestClient

from app.models.usuario import Usuario


class TestLogin:
    """PB-09 — Sp1-16: login OK y KO."""

    def test_login_exitoso_retorna_tokens(self, client: TestClient, admin_usuario: Usuario):
        """CA-1: Login válido retorna access_token, refresh_token y perfil."""
        resp = client.post(
            "/auth/login",
            json={"email": "admin@test.bo", "password": "Admin1234!"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["usuario"]["email"] == "admin@test.bo"
        assert "password_hash" not in data["usuario"]  # CA-5: no exponer hash

    def test_login_contrasena_incorrecta_retorna_401(self, client: TestClient, admin_usuario: Usuario):
        """CA-2: Contraseña incorrecta → 401 con mensaje genérico."""
        resp = client.post(
            "/auth/login",
            json={"email": "admin@test.bo", "password": "incorrecta"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Credenciales inválidas"

    def test_login_email_inexistente_retorna_401(self, client: TestClient):
        """CA-2: Email inexistente → mismo 401 (no revelar si el email existe)."""
        resp = client.post(
            "/auth/login",
            json={"email": "noexiste@test.bo", "password": "cualquiera"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Credenciales inválidas"

    def test_login_cuenta_inactiva_retorna_403(self, client: TestClient, db_session):
        """CA-3: Cuenta desactivada → 403."""
        u = Usuario(
            nombre="Inactivo",
            email="inactivo@test.bo",
            password_hash="$2b$12$dummy_not_real",
            rol="tecnico",
            activo=False,
        )
        from app.core.security import hash_password
        u.password_hash = hash_password("Pass1234!")
        db_session.add(u)
        db_session.commit()

        resp = client.post(
            "/auth/login",
            json={"email": "inactivo@test.bo", "password": "Pass1234!"},
        )
        assert resp.status_code == 403
        assert resp.json()["detail"] == "Cuenta desactivada"


class TestRefresh:
    """PB-09 — Sp1-16: renovación de access_token."""

    def test_refresh_exitoso(self, client: TestClient, admin_usuario: Usuario):
        """Refresh token válido → nuevo access_token."""
        login_resp = client.post(
            "/auth/login",
            json={"email": "admin@test.bo", "password": "Admin1234!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_refresh_token_invalido_retorna_401(self, client: TestClient):
        """Refresh token inexistente → 401."""
        resp = client.post(
            "/auth/refresh",
            json={"refresh_token": "uuid-no-existe"},
        )
        assert resp.status_code == 401


class TestLogout:
    """PB-09 — Sp1-16: cierre de sesión (CA-4)."""

    def test_logout_revoca_refresh_token(self, client: TestClient, admin_usuario: Usuario):
        """CA-4: Logout elimina refresh_token; refresh posterior debe fallar."""
        login_resp = client.post(
            "/auth/login",
            json={"email": "admin@test.bo", "password": "Admin1234!"},
        )
        data = login_resp.json()
        refresh_token = data["refresh_token"]
        access_token = data["access_token"]

        # Logout
        resp = client.post(
            "/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 204

        # Verificar que el refresh_token ya no funciona
        refresh_resp = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_resp.status_code == 401

    def test_logout_idempotente(self, client: TestClient, admin_usuario: Usuario):
        """Logout con token ya revocado no lanza error."""
        resp = client.post(
            "/auth/logout",
            json={"refresh_token": "uuid-inexistente"},
        )
        assert resp.status_code == 204


class TestGetCurrentUser:
    """Cobertura de security.py: ramas de error en get_current_user."""

    def test_token_invalido_retorna_401(self, client: TestClient, admin_usuario):
        """JWTError: token con firma inválida → 401 (líneas 71-72 security.py)."""
        resp = client.get(
            "/admin/usuarios",
            headers={"Authorization": "Bearer token.completamente.invalido"},
        )
        assert resp.status_code == 401

    def test_token_sin_sub_retorna_401(self, client: TestClient, admin_usuario):
        """sub ausente en payload JWT → 401 (línea 70 security.py)."""
        from app.core.security import create_access_token

        token_sin_sub = create_access_token(data={})  # sin campo 'sub'
        resp = client.get(
            "/admin/usuarios",
            headers={"Authorization": f"Bearer {token_sin_sub}"},
        )
        assert resp.status_code == 401

    def test_usuario_inexistente_retorna_401(self, client: TestClient):
        """ID de usuario inexistente en token válido → 401 (línea 79 security.py)."""
        from app.core.security import create_access_token

        token = create_access_token(data={"sub": "999999"})
        resp = client.get(
            "/admin/usuarios",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    def test_usuario_inactivo_con_token_valido_retorna_403(
        self, client: TestClient, admin_token: str, tecnico_usuario: Usuario
    ):
        """Técnico obtiene token, admin lo desactiva, técnico usa token → 403 (línea 81 security.py)."""
        # Técnico obtiene su propio token
        login = client.post(
            "/auth/login",
            json={"email": "tecnico@test.bo", "password": "Tecnico1234!"},
        )
        assert login.status_code == 200
        tecnico_access = login.json()["access_token"]

        # Admin desactiva al técnico
        client.patch(
            f"/admin/usuarios/{tecnico_usuario.id}",
            json={"activo": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        # Técnico intenta usar su token (válido, pero cuenta inactiva)
        resp = client.get(
            "/proyectos",
            headers={"Authorization": f"Bearer {tecnico_access}"},
        )
        assert resp.status_code == 403
