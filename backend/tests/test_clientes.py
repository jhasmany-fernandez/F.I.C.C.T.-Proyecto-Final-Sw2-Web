"""Tests de la gestión de clientes (admin web).

Sprint 1 — Sp1-35 — PB-19 (CA-1, CA-2, CA-3, CA-4, CA-5).
"""

import pytest
from fastapi.testclient import TestClient

from app.models.cliente import Cliente


@pytest.fixture
def cliente_existente(db_session) -> Cliente:
    """Crea un cliente de prueba en la BD."""
    c = Cliente(nombre="Bulldog Tech.")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)
    return c


class TestListarClientes:
    """CA-3: técnico y admin pueden listar clientes activos."""

    def test_admin_lista_clientes_activos(
        self,
        client: TestClient,
        admin_token: str,
        cliente_existente: Cliente,
    ):
        resp = client.get(
            "/clientes",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert any(c["nombre"] == "Bulldog Tech." for c in items)

    def test_tecnico_puede_listar_clientes_activos(
        self,
        client: TestClient,
        tecnico_token: str,
        cliente_existente: Cliente,
    ):
        """CA-3: técnico autenticado puede listar clientes (para el selector en la app)."""
        resp = client.get(
            "/clientes",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_sin_token_retorna_401(self, client: TestClient):
        resp = client.get("/clientes")
        assert resp.status_code == 401

    def test_cliente_inactivo_no_aparece_en_lista_activos(
        self,
        client: TestClient,
        admin_token: str,
        db_session,
    ):
        """CA-4: cliente inactivo no aparece en GET /clientes."""
        c = Cliente(nombre="Cliente Inactivo SA", activo=False)
        db_session.add(c)
        db_session.commit()
        resp = client.get(
            "/clientes",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert not any(x["nombre"] == "Cliente Inactivo SA" for x in resp.json())


class TestCrearCliente:
    """CA-1, CA-2, CA-3 de PB-19."""

    def test_admin_crea_cliente(self, client: TestClient, admin_token: str):
        """CA-1: admin crea cliente con nombre válido → 201 con objeto cliente."""
        resp = client.post(
            "/admin/clientes",
            json={"nombre": "Empresa Nueva SRL"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Empresa Nueva SRL"
        assert data["activo"] is True
        assert "id" in data
        assert "created_at" in data

    def test_admin_crea_cliente_nombre_duplicado_retorna_409(
        self,
        client: TestClient,
        admin_token: str,
        cliente_existente: Cliente,
    ):
        """CA-2: nombre duplicado → 409 Conflict."""
        resp = client.post(
            "/admin/clientes",
            json={"nombre": "Bulldog Tech."},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 409
        assert "Bulldog Tech." in resp.json()["detail"]

    def test_tecnico_no_puede_crear_cliente(
        self, client: TestClient, tecnico_token: str
    ):
        """CA-3: técnico recibe 403 al intentar crear cliente."""
        resp = client.post(
            "/admin/clientes",
            json={"nombre": "Empresa No Autorizada"},
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 403

    def test_nombre_vacio_retorna_422(self, client: TestClient, admin_token: str):
        """Validación: nombre vacío → 422."""
        resp = client.post(
            "/admin/clientes",
            json={"nombre": "   "},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_sin_token_retorna_401(self, client: TestClient):
        resp = client.post("/admin/clientes", json={"nombre": "Test"})
        assert resp.status_code == 401


class TestActualizarCliente:
    """Cobertura del endpoint PUT /admin/clientes/{id}."""

    def test_admin_actualiza_nombre(
        self,
        client: TestClient,
        admin_token: str,
        cliente_existente: Cliente,
    ):
        resp = client.put(
            f"/admin/clientes/{cliente_existente.id}",
            json={"nombre": "Bulldog Tech. Actualizado"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Bulldog Tech. Actualizado"

    def test_actualizar_cliente_inexistente_retorna_404(
        self, client: TestClient, admin_token: str
    ):
        resp = client.put(
            "/admin/clientes/999999",
            json={"nombre": "No existe"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    def test_tecnico_no_puede_actualizar_cliente(
        self,
        client: TestClient,
        tecnico_token: str,
        cliente_existente: Cliente,
    ):
        resp = client.put(
            f"/admin/clientes/{cliente_existente.id}",
            json={"nombre": "Intento técnico"},
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 403


class TestDesactivarCliente:
    """CA-4, CA-5 de PB-19."""

    def test_admin_desactiva_cliente(
        self,
        client: TestClient,
        admin_token: str,
        cliente_existente: Cliente,
    ):
        """CA-4: cliente desactivado → activo=False y desaparece del selector."""
        resp = client.patch(
            f"/admin/clientes/{cliente_existente.id}/desactivar",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["activo"] is False

        # Verificar que no aparece en el listado de activos
        resp_lista = client.get(
            "/clientes",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert not any(c["id"] == cliente_existente.id for c in resp_lista.json())

    def test_desactivar_cliente_inexistente_retorna_404(
        self, client: TestClient, admin_token: str
    ):
        resp = client.patch(
            "/admin/clientes/999999/desactivar",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    def test_tecnico_no_puede_desactivar_cliente(
        self,
        client: TestClient,
        tecnico_token: str,
        cliente_existente: Cliente,
    ):
        resp = client.patch(
            f"/admin/clientes/{cliente_existente.id}/desactivar",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 403

    def test_admin_lista_todos_incluye_inactivos(
        self,
        client: TestClient,
        admin_token: str,
        cliente_existente: Cliente,
    ):
        """GET /admin/clientes incluye clientes inactivos."""
        # Desactivar primero
        client.patch(
            f"/admin/clientes/{cliente_existente.id}/desactivar",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get(
            "/admin/clientes",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert any(c["id"] == cliente_existente.id for c in resp.json())
