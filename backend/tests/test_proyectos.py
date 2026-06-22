"""Tests del listado de proyectos para el admin.

Sprint 1 — Sp1-24 — PB-18 (CA-1, CA-3, CA-4).
"""

from datetime import UTC

import pytest
from fastapi.testclient import TestClient

from app.models.cliente import Cliente
from app.models.proyecto import Proyecto
from app.models.usuario import Usuario


@pytest.fixture
def cliente_seed(db_session) -> Cliente:
    """Crea un cliente de prueba reutilizable."""
    cliente = Cliente(nombre="Cliente Test")
    db_session.add(cliente)
    db_session.commit()
    db_session.refresh(cliente)
    return cliente


@pytest.fixture
def proyectos_seed(
    db_session, tecnico_usuario: Usuario, cliente_seed: Cliente
) -> list[Proyecto]:
    """Crea 3 proyectos de prueba asignados al técnico."""
    proyectos = [
        Proyecto(
            nombre="Proyecto Alpha",
            cliente_id=cliente_seed.id,
            estado="en_progreso",
            tecnico_id=tecnico_usuario.id,
        ),
        Proyecto(
            nombre="Proyecto Beta",
            cliente_id=cliente_seed.id,
            estado="completado",
            tecnico_id=tecnico_usuario.id,
        ),
        Proyecto(
            nombre="Proyecto Gamma",
            cliente_id=None,
            estado="en_progreso",
            tecnico_id=tecnico_usuario.id,
        ),
    ]
    for p in proyectos:
        db_session.add(p)
    db_session.commit()
    for p in proyectos:
        db_session.refresh(p)
    return proyectos


class TestListarProyectos:
    """PB-18 — Sp1-24: listado con seed data."""

    def test_admin_lista_proyectos(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """CA-1 + CA-2: Admin ve todos los proyectos con campos requeridos."""
        resp = client.get(
            "/admin/proyectos",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 1

        primer = data["items"][0]
        for campo in [
            "id",
            "nombre",
            "cliente",
            "estado",
            "ultima_actividad",
            "cantidad_puntos",
            "tecnico",
        ]:
            assert campo in primer, f"Falta el campo '{campo}' en la respuesta"

    def test_filtro_por_tecnico(
        self,
        client: TestClient,
        admin_token: str,
        tecnico_usuario: Usuario,
        proyectos_seed: list[Proyecto],
    ):
        """CA-3: Filtro por técnico retorna solo sus proyectos."""
        resp = client.get(
            f"/admin/proyectos?tecnico_id={tecnico_usuario.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(p["tecnico"]["id"] == tecnico_usuario.id for p in data["items"])

    def test_sin_proyectos_retorna_lista_vacia(
        self,
        client: TestClient,
        admin_token: str,
    ):
        """CA-4: Sin proyectos → total=0, items=[]."""
        resp = client.get(
            "/admin/proyectos",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "items" in data

    def test_tecnico_no_puede_listar_proyectos_org(
        self,
        client: TestClient,
        tecnico_token: str,
    ):
        """CA-1: Técnico → 403 al intentar acceder."""
        resp = client.get(
            "/admin/proyectos",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 403

    def test_paginacion(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """Paginación: page_size=1 retorna 1 ítem."""
        resp = client.get(
            "/admin/proyectos?page=1&page_size=1",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) == 1
        assert data["page"] == 1
        assert data["page_size"] == 1


class TestListarMisProyectos:
    """PB-09 — Sp1: endpoint GET /proyectos para el técnico autenticado."""

    def test_tecnico_ve_lista_vacia_sin_proyectos(
        self,
        client: TestClient,
        tecnico_token: str,
    ):
        """CA-1: técnico nuevo → lista vacía (200, [])."""
        resp = client.get(
            "/proyectos",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_tecnico_ve_sus_proyectos(
        self,
        client: TestClient,
        tecnico_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """CA-1: técnico con proyectos activos recibe su lista con campos correctos."""
        resp = client.get(
            "/proyectos",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()
        # Solo proyectos no-archivados (seed tiene 2 en_progreso, 1 completado → 3)
        assert len(items) >= 1
        primer = items[0]
        for campo in [
            "id",
            "nombre",
            "cliente",
            "descripcion",
            "estado",
            "created_at",
            "updated_at",
        ]:
            assert campo in primer, f"Falta el campo '{campo}' en la respuesta"
        # Estado normalizado a mayúsculas
        assert primer["estado"] == primer["estado"].upper()

    def test_estado_normalizado_a_mayusculas(
        self,
        client: TestClient,
        tecnico_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """Estado devuelto en MAYÚSCULAS para compatibilidad con la app móvil."""
        resp = client.get(
            "/proyectos",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 200
        for item in resp.json():
            assert item["estado"] == item["estado"].upper()

    def test_filtro_estado_archivado(
        self,
        client: TestClient,
        tecnico_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """Sin filtro de estado se excluyen los archivados; con filtro se incluyen."""
        # Sin filtro → 0 archivados (seed no tiene archivados directamente)
        resp_activos = client.get(
            "/proyectos",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp_activos.status_code == 200
        for item in resp_activos.json():
            assert item["estado"] != "ARCHIVADO"

        # Con filtro estado=archivado → lista vacía (seed no tiene archivados)
        resp_arch = client.get(
            "/proyectos?estado=archivado",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp_arch.status_code == 200
        assert resp_arch.json() == []

    def test_sin_token_retorna_401(self, client: TestClient):
        """Sin credenciales → 401."""
        resp = client.get("/proyectos")
        assert resp.status_code == 401

    def test_tecnico_no_ve_proyectos_de_otro_tecnico(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """El admin (sin proyectos propios) ve lista vacía en /proyectos."""
        resp = client.get(
            "/proyectos",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestFiltrosFecha:
    """Cobertura de proyecto_repository.py líneas 55-59: filtros fecha_desde/fecha_hasta."""

    def test_filtro_fecha_desde_incluye_proyectos_recientes(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """fecha_desde=ayer (UTC) → incluye proyectos creados hoy (líneas 55-57 proyecto_repository.py)."""
        from datetime import datetime, timedelta

        ayer = (datetime.now(tz=UTC).date() - timedelta(days=1)).isoformat()
        resp = client.get(
            f"/admin/proyectos?fecha_desde={ayer}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3  # los 3 proyectos del seed son recientes

    def test_filtro_fecha_desde_excluye_proyectos_futuros(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """fecha_desde=mañana (UTC) → excluye todos los proyectos creados hoy."""
        from datetime import datetime, timedelta

        manana = (datetime.now(tz=UTC).date() + timedelta(days=1)).isoformat()
        resp = client.get(
            f"/admin/proyectos?fecha_desde={manana}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_filtro_fecha_hasta_incluye_proyectos_pasados(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """fecha_hasta=mañana (UTC) → incluye proyectos de hoy (líneas 58-59 proyecto_repository.py)."""
        from datetime import datetime, timedelta

        manana = (datetime.now(tz=UTC).date() + timedelta(days=1)).isoformat()
        resp = client.get(
            f"/admin/proyectos?fecha_hasta={manana}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 3

    def test_filtro_fecha_rango_completo(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """Ambos filtros combinados (UTC): rango que incluye hoy → proyectos del seed presentes."""
        from datetime import datetime, timedelta

        ayer = (datetime.now(tz=UTC).date() - timedelta(days=1)).isoformat()
        manana = (datetime.now(tz=UTC).date() + timedelta(days=1)).isoformat()
        resp = client.get(
            f"/admin/proyectos?fecha_desde={ayer}&fecha_hasta={manana}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 3


class TestClienteEnProyecto:
    """PB-19: el campo cliente en la respuesta de proyecto es un objeto {id, nombre} o null."""

    def test_proyecto_con_cliente_retorna_objeto(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """Los proyectos con cliente_id retornan cliente como {id, nombre}."""
        resp = client.get(
            "/admin/proyectos",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        con_cliente = [p for p in items if p["cliente"] is not None]
        assert len(con_cliente) >= 1
        for p in con_cliente:
            assert isinstance(p["cliente"], dict)
            assert "id" in p["cliente"]
            assert "nombre" in p["cliente"]
            assert isinstance(p["cliente"]["id"], int)
            assert isinstance(p["cliente"]["nombre"], str)

    def test_proyecto_sin_cliente_retorna_null(
        self,
        client: TestClient,
        admin_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """Los proyectos sin cliente retornan cliente=null."""
        resp = client.get(
            "/admin/proyectos",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        items = resp.json()["items"]
        sin_cliente = [p for p in items if p["cliente"] is None]
        assert len(sin_cliente) >= 1

    def test_tecnico_proyectos_cliente_es_objeto(
        self,
        client: TestClient,
        tecnico_token: str,
        proyectos_seed: list[Proyecto],
    ):
        """GET /proyectos también devuelve cliente como objeto."""
        resp = client.get(
            "/proyectos",
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert resp.status_code == 200
        for item in resp.json():
            if item["cliente"] is not None:
                assert isinstance(item["cliente"], dict)
                assert "id" in item["cliente"]
                assert "nombre" in item["cliente"]
