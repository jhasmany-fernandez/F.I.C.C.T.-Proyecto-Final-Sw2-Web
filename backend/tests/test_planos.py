"""Tests Sprint 2 — PB-02 (Importar Plano) y PB-11 (Calibrar Escala)."""

import io
import tempfile
import time

import fitz  # PyMuPDF
import pytest
from PIL import Image

from app.core.config import settings
from app.storage.signing import generar_url_firmada, verificar_firma


@pytest.fixture(autouse=True)
def storage_temporal(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        monkeypatch.setattr(settings, "storage_root", tmp)
        monkeypatch.setattr(
            settings, "storage_url_secret", "test_secret_32chars_minimo_xxxxxx"
        )
        monkeypatch.setattr(settings, "storage_url_ttl_seconds", 60)
        monkeypatch.setattr(settings, "public_api_url", "")
        yield tmp


def _crear_proyecto(client, token, nombre="Proyecto Plano"):
    r = client.post(
        "/proyectos",
        json={"nombre": nombre},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _png_bytes(ancho=200, alto=100) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (ancho, alto), color=(255, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


def _jpg_bytes(ancho=120, alto=80) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (ancho, alto), color=(0, 0, 255)).save(buf, format="JPEG")
    return buf.getvalue()


def _pdf_bytes(paginas=1) -> bytes:
    doc = fitz.open()
    for _ in range(paginas):
        doc.new_page(width=200, height=100)
    data = doc.tobytes()
    doc.close()
    return data


# ---------- PB-02: importar plano ----------


def test_importar_plano_png(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    files = {"archivo": ("piso1.png", _png_bytes(), "image/png")}
    r = client.post(
        f"/proyectos/{pid}/planos",
        files=files,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["formato"] == "png"
    assert body["ancho_px"] == 200 and body["alto_px"] == 100
    assert body["calibrado"] is False
    assert body["warning"] is None
    assert "/planos/archivo/" in body["url_firmada"]


def test_importar_plano_jpg(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    files = {"archivo": ("piso.jpg", _jpg_bytes(), "image/jpeg")}
    r = client.post(
        f"/proyectos/{pid}/planos",
        files=files,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201
    assert r.json()["formato"] == "jpg"


def test_importar_pdf_una_pagina(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    files = {"archivo": ("plan.pdf", _pdf_bytes(1), "application/pdf")}
    r = client.post(
        f"/proyectos/{pid}/planos",
        files=files,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["formato"] == "pdf"
    assert body["warning"] is None
    assert body["ancho_px"] > 0


def test_importar_pdf_multipagina_genera_warning(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    files = {"archivo": ("plan.pdf", _pdf_bytes(3), "application/pdf")}
    r = client.post(
        f"/proyectos/{pid}/planos",
        files=files,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["warning"] is not None
    assert "3" in body["warning"]


def test_importar_formato_no_soportado(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    files = {"archivo": ("plano.tiff", b"\x00\x00", "image/tiff")}
    r = client.post(
        f"/proyectos/{pid}/planos",
        files=files,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 415


def test_importar_tamano_excedido(client, tecnico_token, monkeypatch):
    from app.api.v1 import planos as planos_mod

    monkeypatch.setattr(planos_mod, "MAX_BYTES", 100)
    pid = _crear_proyecto(client, tecnico_token)
    files = {"archivo": ("piso.png", _png_bytes(300, 300), "image/png")}
    r = client.post(
        f"/proyectos/{pid}/planos",
        files=files,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 413


def test_importar_proyecto_ajeno_devuelve_404(
    client,
    tecnico_token,
    admin_token,
    admin_usuario,
):
    # Crear proyecto como admin (otro técnico/usuario)
    r = client.post(
        "/proyectos",
        json={"nombre": "Ajeno"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert r.status_code == 201
    pid_ajeno = r.json()["id"]

    files = {"archivo": ("p.png", _png_bytes(), "image/png")}
    r = client.post(
        f"/proyectos/{pid_ajeno}/planos",
        files=files,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 404


def test_listar_planos(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    client.post(
        f"/proyectos/{pid}/planos",
        files={"archivo": ("p1.png", _png_bytes(), "image/png")},
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    client.post(
        f"/proyectos/{pid}/planos",
        files={"archivo": ("p2.png", _png_bytes(), "image/png")},
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    r = client.get(
        f"/proyectos/{pid}/planos",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 200
    assert len(r.json()) == 2


# ---------- PB-11: calibrar escala ----------


def _subir_plano(client, token, pid) -> dict:
    r = client.post(
        f"/proyectos/{pid}/planos",
        files={"archivo": ("p.png", _png_bytes(1000, 500), "image/png")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_calibrar_plano_valido(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    plano = _subir_plano(client, tecnico_token, pid)
    body = {
        "x1": 100,
        "y1": 100,
        "x2": 200,
        "y2": 100,
        "distancia_real_m": 10,
    }
    r = client.patch(
        f"/planos/{plano['id']}/calibracion",
        json=body,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 200, r.text
    out = r.json()
    assert out["calibrado"] is True
    assert out["escala_m_por_px"] == pytest.approx(10 / 100, rel=1e-3)


def test_calibrar_distancia_menor_a_1m_falla(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    plano = _subir_plano(client, tecnico_token, pid)
    r = client.patch(
        f"/planos/{plano['id']}/calibracion",
        json={"x1": 0, "y1": 0, "x2": 100, "y2": 0, "distancia_real_m": 0.5},
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 422


def test_calibrar_puntos_iguales_falla(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    plano = _subir_plano(client, tecnico_token, pid)
    r = client.patch(
        f"/planos/{plano['id']}/calibracion",
        json={"x1": 50, "y1": 50, "x2": 50, "y2": 50, "distancia_real_m": 5},
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 422


def test_recalibrar_sin_puntos_permitido(client, tecnico_token):
    """Sin puntos de medición (placeholder Sprint 2), recalibrar es válido."""
    pid = _crear_proyecto(client, tecnico_token)
    plano = _subir_plano(client, tecnico_token, pid)
    body = {"x1": 0, "y1": 0, "x2": 100, "y2": 0, "distancia_real_m": 5}
    r1 = client.patch(
        f"/planos/{plano['id']}/calibracion",
        json=body,
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r1.status_code == 200
    r2 = client.patch(
        f"/planos/{plano['id']}/calibracion",
        json={**body, "distancia_real_m": 10},
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["distancia_real_m"] == 10


def test_eliminar_plano(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    plano = _subir_plano(client, tecnico_token, pid)
    r = client.delete(
        f"/planos/{plano['id']}",
        headers={"Authorization": f"Bearer {tecnico_token}"},
    )
    assert r.status_code == 204


# ---------- URLs firmadas ----------


def test_url_firmada_valida_sirve_archivo(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    plano = _subir_plano(client, tecnico_token, pid)
    url = plano["url_firmada"]
    r = client.get(url)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
    assert len(r.content) > 0


def test_url_firmada_expirada(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    plano = _subir_plano(client, tecnico_token, pid)
    url = generar_url_firmada(
        ruta_relativa=plano["url_firmada"].split("/planos/archivo/")[1].split("?")[0],
        secret=settings.storage_url_secret,
        base_url="",
        ttl_seconds=-10,
    )
    r = client.get(url)
    assert r.status_code == 403


def test_url_firmada_manipulada(client, tecnico_token):
    pid = _crear_proyecto(client, tecnico_token)
    plano = _subir_plano(client, tecnico_token, pid)
    url = plano["url_firmada"].replace("sig=", "sig=ffff")
    r = client.get(url)
    assert r.status_code == 403


def test_verificar_firma_unit():
    assert (
        verificar_firma(
            ruta_relativa="x.png",
            secret="s",
            exp=int(time.time()) + 60,
            sig="bad",
        )
        is False
    )
