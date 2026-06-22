"""Tests de gestión de usuarios (panel admin).

Sprint 1 — Sp1-07 — PB-13 (CA-1, CA-2, CA-3, CA-4).
Coverage objetivo: ≥ 80 % en admin/usuarios.
"""

from fastapi.testclient import TestClient

from app.models.usuario import Usuario


class TestCrearUsuario:
    """PB-13 — Sp1-07: creación de cuentas."""

    def test_admin_puede_crear_tecnico(self, client: TestClient, admin_token: str):
        """CA-1: Admin crea técnico → 201 con estado ACTIVO."""
        resp = client.post(
            "/admin/usuarios",
            json={
                "nombre": "Nuevo Técnico",
                "email": "nuevo@test.bo",
                "password": "Pass1234!",
                "rol": "tecnico",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "nuevo@test.bo"
        assert data["activo"] is True
        assert "password_hash" not in data  # CA-5

    def test_email_duplicado_retorna_409(
        self, client: TestClient, admin_token: str, admin_usuario: Usuario
    ):
        """CA-3: Email ya registrado → 409 Conflict."""
        resp = client.post(
            "/admin/usuarios",
            json={
                "nombre": "Duplicado",
                "email": "admin@test.bo",  # Ya existe
                "password": "Pass1234!",
                "rol": "tecnico",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 409

    def test_tecnico_no_puede_crear_usuario(
        self, client: TestClient, tecnico_token: str
    ):
        """CA-4: Rol TECNICO intenta acceder a /admin/usuarios → 403."""
        resp = client.post(
            "/admin/usuarios",
            json={
                "nombre": "Intento",
                "email": "intento@test.bo",
                "password": "Pass1234!",
                "rol": "tecnico",
            },
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 403

    def test_sin_auth_retorna_401(self, client: TestClient):
        """Sin token → 401."""
        resp = client.post(
            "/admin/usuarios",
            json={
                "nombre": "Sin auth",
                "email": "sinauth@test.bo",
                "password": "Pass1234!",
            },
        )
        assert resp.status_code == 401

    def test_contrasena_corta_retorna_422(self, client: TestClient, admin_token: str):
        """Contraseña < 8 caracteres → validación 422."""
        resp = client.post(
            "/admin/usuarios",
            json={
                "nombre": "Corta",
                "email": "corta@test.bo",
                "password": "123",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422


class TestActivarDesactivar:
    """PB-13 — Sp1-07: activar y desactivar cuentas."""

    def test_desactivar_usuario(
        self, client: TestClient, admin_token: str, tecnico_usuario: Usuario
    ):
        """Desactivar técnico → activo=False + tokens revocados."""
        resp = client.patch(
            f"/admin/usuarios/{tecnico_usuario.id}",
            json={"activo": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["activo"] is False

    def test_activar_usuario(
        self, client: TestClient, admin_token: str, tecnico_usuario: Usuario
    ):
        """Reactivar técnico → activo=True."""
        # Primero desactivar
        client.patch(
            f"/admin/usuarios/{tecnico_usuario.id}",
            json={"activo": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # Luego reactivar
        resp = client.patch(
            f"/admin/usuarios/{tecnico_usuario.id}",
            json={"activo": True},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["activo"] is True

    def test_tecnico_inactivo_no_puede_hacer_login(
        self, client: TestClient, admin_token: str, tecnico_usuario: Usuario
    ):
        """CA-2: Técnico desactivado → login devuelve 403."""
        client.patch(
            f"/admin/usuarios/{tecnico_usuario.id}",
            json={"activo": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.post(
            "/auth/login",
            json={"email": "tecnico@test.bo", "password": "Tecnico1234!"},
        )
        assert resp.status_code == 403


class TestListarUsuarios:
    """PB-13: listado de usuarios."""

    def test_admin_lista_todos_los_usuarios(
        self,
        client: TestClient,
        admin_token: str,
        admin_usuario: Usuario,
        tecnico_usuario: Usuario,
    ):
        """Admin puede listar todos los usuarios del sistema."""
        resp = client.get(
            "/admin/usuarios",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        emails = [u["email"] for u in resp.json()]
        assert "admin@test.bo" in emails
        assert "tecnico@test.bo" in emails

    def test_tecnico_no_puede_listar_usuarios(
        self, client: TestClient, tecnico_token: str
    ):
        """CA-4: Técnico no puede acceder a /admin/usuarios GET → 403."""
        resp = client.get(
            "/admin/usuarios",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 403


class TestValidacionesSchema:
    """Cobertura de schemas/usuario.py: ramas de validación no ejercidas."""

    def test_rol_invalido_retorna_422(self, client: TestClient, admin_token: str):
        """rol_valido: valor fuera de ('tecnico','admin') → 422 (línea 25 schemas/usuario.py)."""
        resp = client.post(
            "/admin/usuarios",
            json={
                "nombre": "Supervisor",
                "email": "supervisor@test.bo",
                "password": "Pass1234!",
                "rol": "supervisor",  # rol inválido
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_reset_password_corta_en_patch_retorna_422(
        self, client: TestClient, admin_token: str, tecnico_usuario
    ):
        """UsuarioUpdate.password_min_length: password < 8 en PATCH → 422 (líneas 51-53 schemas/usuario.py)."""
        resp = client.patch(
            f"/admin/usuarios/{tecnico_usuario.id}",
            json={"password": "123"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422


class TestListarSoloActivos:
    """Cobertura de usuario_repository.py línea 42: rama solo_activos=True."""

    def test_listar_solo_activos_excluye_inactivos(
        self,
        client: TestClient,
        admin_token: str,
        admin_usuario,
        tecnico_usuario,
    ):
        """GET /admin/usuarios?solo_activos=true no incluye usuarios inactivos."""
        # Desactivar técnico
        client.patch(
            f"/admin/usuarios/{tecnico_usuario.id}",
            json={"activo": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get(
            "/admin/usuarios?solo_activos=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert "admin@test.bo" in emails
        assert "tecnico@test.bo" not in emails
