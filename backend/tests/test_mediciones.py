"""Tests Sprint 3 — PB-03 (Captura WiFi en línea) y PB-04 (Marcar puntos)."""

import io
import tempfile

import pytest
from PIL import Image

from app.core.config import settings
from app.models.cliente import Cliente
from app.models.plano import Plano
from app.models.proyecto import Proyecto


# ---------------------------------------------------------------------------
# Fixtures de apoyo
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def storage_temporal(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(settings, "storage_root", tmp)
        monkeypatch.setattr(settings, "storage_url_secret", "test_secret_32chars_minimo_xxxxxx")
        monkeypatch.setattr(settings, "storage_url_ttl_seconds", 60)
        monkeypatch.setattr(settings, "public_api_url", "")
        yield tmp


def _png_bytes(ancho: int = 400, alto: int = 300) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (ancho, alto), color=(200, 200, 200)).save(buf, format="PNG")
    return buf.getvalue()


def _crear_proyecto(client, token: str) -> int:
    r = client.post(
        "/proyectos",
        json={"nombre": "Proyecto Medicion"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _subir_plano_calibrado(client, token: str, proyecto_id: int) -> int:
    """Sube un plano PNG y lo calibra; devuelve el plano_id."""
    files = {"archivo": ("piso.png", _png_bytes(), "image/png")}
    r = client.post(
        f"/proyectos/{proyecto_id}/planos",
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    plano_id = r.json()["id"]

    # Calibrar — dos puntos separados + distancia real
    r2 = client.patch(
        f"/planos/{plano_id}/calibracion",
        json={"x1": 0.0, "y1": 0.0, "x2": 100.0, "y2": 0.0, "distancia_real_m": 10.0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["calibrado"] is True
    return plano_id


def _lote_valido(plano_id: int, pos_x: float = 50.0, pos_y: float = 75.0) -> dict:
    return {
        "plano_id": plano_id,
        "pos_x": pos_x,
        "pos_y": pos_y,
        "mediciones": [
            {
                "ssid": "RedOficina",
                "bssid": "aa:bb:cc:dd:ee:01",
                "rssi": -65,
                "canal": 6,
                "frecuencia_mhz": 2437,
            },
            {
                "ssid": "RedVecino",
                "bssid": "aa:bb:cc:dd:ee:02",
                "rssi": -80,
                "canal": 11,
                "frecuencia_mhz": 2462,
            },
        ],
    }


# ---------------------------------------------------------------------------
# PB-03 — Ingesta de lote (POST /api/mediciones)
# ---------------------------------------------------------------------------


def test_lote_valido_retorna_201(client, tecnico_token):
    """CA-1 / CA-2: lote válido → 201 con punto_id y mediciones."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.post(
        "/mediciones",
        json=_lote_valido(plano_id),
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert "punto_id" in body
    assert body["nivel"] in ("verde", "amarillo", "naranja", "rojo", "negro")
    assert len(body["mediciones"]) == 2


def test_clasificacion_nivel_punto_es_el_peor(client, tecnico_token):
    """El nivel del punto debe ser el peor nivel de todas las mediciones."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    lote = {
        "plano_id": plano_id,
        "pos_x": 10.0,
        "pos_y": 10.0,
        "mediciones": [
            {"ssid": "A", "bssid": "aa:bb:cc:dd:ee:01", "rssi": -65},  # verde
            {"ssid": "B", "bssid": "aa:bb:cc:dd:ee:02", "rssi": -91},  # negro
        ],
    }
    r = client.post(
        "/mediciones",
        json=lote,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201
    assert r.json()["nivel"] == "negro"


def test_rssi_fuera_de_rango_retorna_422(client, tecnico_token):
    """CA-6: RSSI fuera de [-120, 0] → 422."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    lote = {
        "plano_id": plano_id,
        "pos_x": 0.0,
        "pos_y": 0.0,
        "mediciones": [
            {"ssid": "X", "bssid": "aa:bb:cc:dd:ee:ff", "rssi": 5},
        ],
    }
    r = client.post(
        "/mediciones",
        json=lote,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 422


def test_rssi_minimo_fuera_de_rango_retorna_422(client, tecnico_token):
    """CA-6: RSSI < -120 → 422."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    lote = {
        "plano_id": plano_id,
        "pos_x": 0.0,
        "pos_y": 0.0,
        "mediciones": [
            {"ssid": "X", "bssid": "aa:bb:cc:dd:ee:ff", "rssi": -121},
        ],
    }
    r = client.post(
        "/mediciones",
        json=lote,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 422


def test_bssid_invalido_retorna_422(client, tecnico_token):
    """CA-6: BSSID con formato incorrecto → 422."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    lote = {
        "plano_id": plano_id,
        "pos_x": 0.0,
        "pos_y": 0.0,
        "mediciones": [
            {"ssid": "X", "bssid": "no-es-mac", "rssi": -70},
        ],
    }
    r = client.post(
        "/mediciones",
        json=lote,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 422


def test_lote_sin_mediciones_retorna_422(client, tecnico_token):
    """Lista de mediciones vacía → 422."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.post(
        "/mediciones",
        json={"plano_id": plano_id, "pos_x": 0.0, "pos_y": 0.0, "mediciones": []},
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 422


def test_ownership_plano_ajeno_retorna_404(client, tecnico_token, admin_token):
    """CA-5 (ownership): técnico no puede insertar en plano ajeno."""
    # El admin crea un proyecto (no tiene proyectos técnicos, pero puede ser otro técnico)
    # Simulamos creando un proyecto con el técnico y luego intentando con admin token
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.post(
        "/mediciones",
        json=_lote_valido(plano_id),
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404


def test_plano_no_calibrado_retorna_422(client, tecnico_token):
    """Plano sin calibrar → 422 con mensaje claro."""
    pid = _crear_proyecto(client, tecnico_token)
    # Subir plano sin calibrar
    files = {"archivo": ("piso.png", _png_bytes(), "image/png")}
    r = client.post(
        f"/proyectos/{pid}/planos",
        files=files,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201
    plano_id = r.json()["id"]

    r2 = client.post(
        "/mediciones",
        json=_lote_valido(plano_id),
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r2.status_code == 422
    assert "calibrado" in r2.json()["detail"].lower()


def test_sin_autenticacion_retorna_401(client, tecnico_token):
    """Sin JWT → 401."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.post("/mediciones", json=_lote_valido(plano_id))
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Clasificación CWNA-107 — umbrales
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rssi, nivel_esperado",
    [
        (-60, "verde"),
        (-70, "verde"),
        (-71, "amarillo"),
        (-80, "amarillo"),
        (-81, "naranja"),
        (-85, "naranja"),
        (-86, "rojo"),
        (-90, "rojo"),
        (-91, "negro"),
        (-120, "negro"),
    ],
)
def test_clasificacion_cwna107(client, tecnico_token, rssi, nivel_esperado):
    """Verifica cada umbral CWNA-107 de clasificación de nivel."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    lote = {
        "plano_id": plano_id,
        "pos_x": float(abs(rssi)),
        "pos_y": 0.0,
        "mediciones": [{"ssid": "Test", "bssid": "aa:bb:cc:dd:ee:ff", "rssi": rssi}],
    }
    r = client.post(
        "/mediciones",
        json=lote,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["nivel"] == nivel_esperado
    assert body["mediciones"][0]["nivel"] == nivel_esperado


# ---------------------------------------------------------------------------
# PB-04 — Listado, detalle y eliminación de puntos
# ---------------------------------------------------------------------------


def test_listar_puntos_plano_vacio(client, tecnico_token):
    """Plano sin puntos → lista vacía."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.get(
        f"/planos/{plano_id}/puntos",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_listar_puntos_retorna_los_creados(client, tecnico_token):
    """Dos puntos insertados → lista de dos."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    for pos in [(10.0, 20.0), (30.0, 40.0)]:
        lote = {
            "plano_id": plano_id,
            "pos_x": pos[0],
            "pos_y": pos[1],
            "mediciones": [{"ssid": "A", "bssid": "aa:bb:cc:dd:ee:01", "rssi": -70}],
        }
        r = client.post(
            "/mediciones",
            json=lote,
            headers={"Authorization": f"Bearer {tecnico_token}"},
        )
        assert r.status_code == 201

    r2 = client.get(
        f"/planos/{plano_id}/puntos",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r2.status_code == 200
    assert len(r2.json()) == 2


def test_detalle_punto_incluye_mediciones(client, tecnico_token):
    """CA-4: detalle incluye todas las mediciones del lote ordenadas por RSSI."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    lote = _lote_valido(plano_id)
    r = client.post(
        "/mediciones",
        json=lote,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201
    punto_id = r.json()["punto_id"]

    r2 = client.get(
        f"/puntos/{punto_id}",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert body["id"] == punto_id
    assert len(body["mediciones"]) == 2
    # Primero el de mayor RSSI (menos negativo)
    assert body["mediciones"][0]["rssi"] >= body["mediciones"][1]["rssi"]


def test_mover_punto_actualiza_posicion_y_preserva_mediciones(client, tecnico_token):
    """Mover punto → nuevas coordenadas y mismas mediciones."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.post(
        "/mediciones",
        json=_lote_valido(plano_id),
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201
    punto_id = r.json()["punto_id"]

    r2 = client.patch(
        f"/puntos/{punto_id}",
        json={"pos_x": 123.5, "pos_y": 456.25},
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )

    assert r2.status_code == 200
    body = r2.json()
    assert body["id"] == punto_id
    assert body["pos_x"] == 123.5
    assert body["pos_y"] == 456.25
    assert len(body["mediciones"]) == 2

    r3 = client.get(
        f"/planos/{plano_id}/puntos",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    punto = next(item for item in r3.json() if item["id"] == punto_id)
    assert punto["pos_x"] == 123.5
    assert punto["pos_y"] == 456.25


def test_mover_punto_ajeno_retorna_404(client, tecnico_token, admin_token):
    """Ownership: intentar mover punto ajeno → 404."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.post(
        "/mediciones",
        json=_lote_valido(plano_id),
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    punto_id = r.json()["punto_id"]

    r2 = client.patch(
        f"/puntos/{punto_id}",
        json={"pos_x": 10, "pos_y": 20},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r2.status_code == 404


def test_eliminar_punto_retorna_204(client, tecnico_token):
    """CA-5: eliminar punto → 204 y ya no aparece en listado."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.post(
        "/mediciones",
        json=_lote_valido(plano_id),
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201
    punto_id = r.json()["punto_id"]

    r2 = client.delete(
        f"/puntos/{punto_id}",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r2.status_code == 204

    # Verificar que el punto ya no existe
    r3 = client.get(
        f"/puntos/{punto_id}",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r3.status_code == 404


def test_eliminar_punto_ajeno_retorna_404(client, tecnico_token, admin_token):
    """Ownership: intentar eliminar punto ajeno → 404."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.post(
        "/mediciones",
        json=_lote_valido(plano_id),
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    punto_id = r.json()["punto_id"]

    r2 = client.delete(
        f"/puntos/{punto_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r2.status_code == 404


def test_detalle_punto_inexistente_retorna_404(client, tecnico_token):
    """Punto que no existe → 404."""
    r = client.get(
        "/puntos/999999",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 404


def test_listar_puntos_plano_ajeno_retorna_404(client, tecnico_token, admin_token):
    """Listar puntos de plano ajeno → 404."""
    pid = _crear_proyecto(client, tecnico_token)
    plano_id = _subir_plano_calibrado(client, tecnico_token, pid)

    r = client.get(
        f"/planos/{plano_id}/puntos",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 404
