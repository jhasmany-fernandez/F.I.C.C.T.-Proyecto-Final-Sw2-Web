"""Tests Sprint 6 — PB-15, PB-16 y PB-17."""

from datetime import UTC, datetime, timedelta

from app.models.escenario import EscenarioOptimizado, Reporte
from app.models.heatmap import AnalisisCobertura, APDetectado, MapaCalor
from app.models.plano import Plano
from app.models.proyecto import Proyecto
from app.models.share import TokenEnlaceCliente


def _crear_proyecto_publicable(db, tecnico):
    proyecto = Proyecto(
        nombre="Portal Cliente Bulldog",
        descripcion="Resultado final para cliente.",
        tecnico_id=tecnico.id,
    )
    db.add(proyecto)
    db.flush()
    plano = Plano(
        proyecto_id=proyecto.id,
        nombre="planta.png",
        formato="png",
        ruta_storage=f"portal/{proyecto.id}/planta.png",
        ancho_px=400,
        alto_px=300,
        tamano_bytes=100,
        calibracion_x1=0,
        calibracion_y1=0,
        calibracion_x2=100,
        calibracion_y2=0,
        distancia_real_m=10,
        escala_m_por_px=0.1,
    )
    db.add(plano)
    db.flush()
    mapa = MapaCalor(
        plano_id=plano.id,
        modo_generacion="CONJUNTO_COMPLETO",
        algoritmo="IDW",
        resolucion=32,
        bssid="aa:bb:cc:dd:ee:01",
        ssid="BulldogCorp",
        ap_pos_x=100,
        ap_pos_y=120,
        aps_interes=[
            {
                "bssid": "aa:bb:cc:dd:ee:01",
                "ssid": "BulldogCorp",
                "canal": 6,
                "frecuencia_mhz": 2437,
                "rssi_promedio": -62,
                "pos_x": 100,
                "pos_y": 120,
                "cantidad_puntos": 5,
            }
        ],
        bssids_generacion=["aa:bb:cc:dd:ee:01"],
        matriz=[[-62.0 for _ in range(32)] for _ in range(32)],
        escala=[{"desde": -70, "hasta": -60, "color": "#2ecc71", "etiqueta": "Buena"}],
        ruta_imagen=f"heatmaps/{plano.id}/portal.png",
        cantidad_puntos=5,
        rssi_min=-70,
        rssi_max=-55,
        firma_mediciones="portal-test",
    )
    db.add(mapa)
    db.flush()
    analisis = AnalisisCobertura(
        mapa_calor_id=mapa.id,
        pct_cobertura=92.5,
        pct_zonas_muertas=0,
        celdas_zonas_muertas=0,
        cantidad_solapamientos=1,
        cantidad_interferencias=0,
        hallazgos={"zonas_muertas": []},
        resumen="Cobertura apta para el cliente.",
    )
    db.add(analisis)
    db.flush()
    db.add(
        APDetectado(
            analisis_id=analisis.id,
            bssid="aa:bb:cc:dd:ee:01",
            ssid="BulldogCorp",
            canal=6,
            frecuencia_mhz=2437,
            rssi_promedio=-62,
            pos_x=100,
            pos_y=120,
            confirmado=True,
        )
    )
    escenario = EscenarioOptimizado(
        proyecto_id=proyecto.id,
        plano_id=plano.id,
        mapa_actual_id=mapa.id,
        mapa_proyectado_id=mapa.id,
        origen="ia",
        estado_gobernanza="publicado_cliente",
        nombre="Alternativa publicada",
        banda="5",
        bandas=["5"],
        modelo_ap="AP propuesto para cobertura",
        pct_cobertura_actual=80,
        pct_cobertura=95,
        costo_estimado=0,
        cantidad_aps=1,
        resumen="Mejora publicada para cliente.",
        restricciones={"max_aps": 1},
        metricas={"mejora_pct": 15},
        mapas_por_banda={},
        mapas_actuales_por_banda={},
    )
    db.add(escenario)
    reporte = Reporte(
        proyecto_id=proyecto.id,
        escenario=escenario,
        estado="LISTO",
        ruta_pdf=f"reportes/proyecto_{proyecto.id}/reporte.pdf",
        sha256="a" * 64,
        tamanio_bytes=120,
    )
    db.add(reporte)
    db.commit()
    db.refresh(proyecto)
    db.refresh(mapa)
    db.refresh(analisis)
    db.refresh(escenario)
    db.refresh(reporte)
    return proyecto, mapa, analisis, escenario, reporte


def test_enlace_cliente_expone_solo_contenido_autorizado(
    client,
    db_session,
    admin_token,
    tecnico_usuario,
):
    proyecto, mapa, analisis, escenario, reporte = _crear_proyecto_publicable(
        db_session,
        tecnico_usuario,
    )

    respuesta = client.post(
        f"/share/proyectos/{proyecto.id}/enlaces",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "expira_en_dias": 7,
            "contenido": {
                "mapa_ids": [mapa.id],
                "analisis_ids": [analisis.id],
                "escenario_ids": [escenario.id],
                "reporte_id": reporte.id,
            },
        },
    )
    assert respuesta.status_code == 201
    enlace = respuesta.json()
    assert enlace["url_publica"].startswith("/portal/")
    assert enlace["contenido"]["mapa_ids"] == [mapa.id]

    token = enlace["url_publica"].removeprefix("/portal/")
    portal = client.get(f"/share/{token}")
    assert portal.status_code == 200
    payload = portal.json()
    assert payload["proyecto"]["nombre"] == "Portal Cliente Bulldog"
    assert payload["proyecto"].get("tecnico") is None
    assert [item["id"] for item in payload["heatmaps"]] == [mapa.id]
    assert [item["id"] for item in payload["analisis"]] == [analisis.id]
    assert [item["id"] for item in payload["escenarios"]] == [escenario.id]
    assert payload["reporte_disponible"] is True

    db_session.expire_all()
    enlace_db = db_session.query(TokenEnlaceCliente).filter_by(id=enlace["id"]).one()
    assert enlace_db.accesos == 1
    assert enlace_db.ultimo_acceso is not None

    reporte_response = client.get(f"/share/{token}/reporte", follow_redirects=False)
    assert reporte_response.status_code == 302
    assert "/reportes/archivo/" in reporte_response.headers["location"]


def test_enlace_cliente_revocado_o_expirado_devuelve_404(
    client,
    db_session,
    admin_token,
    tecnico_usuario,
):
    proyecto, mapa, _, _, _ = _crear_proyecto_publicable(db_session, tecnico_usuario)
    respuesta = client.post(
        f"/share/proyectos/{proyecto.id}/enlaces",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"expira_en_dias": 1, "contenido": {"mapa_ids": [mapa.id]}},
    )
    enlace = respuesta.json()
    token = enlace["url_publica"].removeprefix("/portal/")

    revocado = client.patch(
        f"/share/enlaces/{enlace['id']}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"revocado": True},
    )
    assert revocado.status_code == 200
    assert client.get(f"/share/{token}").status_code == 404

    enlace_db = db_session.query(TokenEnlaceCliente).filter_by(id=enlace["id"]).one()
    enlace_db.revocado = False
    enlace_db.expira_en = datetime.now(UTC) - timedelta(minutes=1)
    db_session.commit()
    assert client.get(f"/share/{token}").status_code == 404


def test_enlace_cliente_rechaza_escenario_no_publicado(
    client,
    db_session,
    admin_token,
    tecnico_usuario,
):
    proyecto, _, _, escenario, _ = _crear_proyecto_publicable(
        db_session,
        tecnico_usuario,
    )
    escenario.estado_gobernanza = "aprobado_interno"
    db_session.commit()

    respuesta = client.post(
        f"/share/proyectos/{proyecto.id}/enlaces",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "expira_en_dias": 7,
            "contenido": {"escenario_ids": [escenario.id]},
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["detail"] == "Escenario no publicado para cliente."


def test_enlace_deja_de_exponer_escenario_si_se_retira_publicacion(
    client,
    db_session,
    admin_token,
    tecnico_usuario,
):
    proyecto, _, _, escenario, _ = _crear_proyecto_publicable(
        db_session, tecnico_usuario
    )
    respuesta = client.post(
        f"/share/proyectos/{proyecto.id}/enlaces",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"contenido": {"escenario_ids": [escenario.id]}},
    )
    assert respuesta.status_code == 201
    token = respuesta.json()["url_publica"].removeprefix("/portal/")

    escenario.estado_gobernanza = "aprobado_interno"
    db_session.commit()

    portal = client.get(f"/share/{token}")
    assert portal.status_code == 200
    assert portal.json()["escenarios"] == []


def test_enlace_con_contenido_explicito_no_agrega_reporte_automaticamente(
    client,
    db_session,
    admin_token,
    tecnico_usuario,
):
    proyecto, mapa, _, _, _ = _crear_proyecto_publicable(db_session, tecnico_usuario)
    respuesta = client.post(
        f"/share/proyectos/{proyecto.id}/enlaces",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"contenido": {"mapa_ids": [mapa.id]}},
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["contenido"]["reporte_id"] is None


def test_enlace_cliente_rechaza_expiracion_mayor_a_365(
    client,
    db_session,
    admin_token,
    tecnico_usuario,
):
    proyecto, *_ = _crear_proyecto_publicable(db_session, tecnico_usuario)
    respuesta = client.post(
        f"/share/proyectos/{proyecto.id}/enlaces",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"expira_en_dias": 366},
    )
    assert respuesta.status_code == 422


def test_enlace_cliente_exige_seleccion_explicita_de_contenido(
    client,
    db_session,
    admin_token,
    tecnico_usuario,
):
    proyecto, *_ = _crear_proyecto_publicable(db_session, tecnico_usuario)
    respuesta = client.post(
        f"/share/proyectos/{proyecto.id}/enlaces",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"expira_en_dias": 7},
    )

    assert respuesta.status_code == 422
