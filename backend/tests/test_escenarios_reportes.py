"""Tests Sprint 5 — PB-07, PB-12 y PB-08."""

import fitz
import pytest

from app.ai.modelo_propagacion import ModeloPropagacion
from app.ai.optimizador_ap_service import OptimizadorAPService
from app.models.escenario import EscenarioOptimizado, RecomendacionAP
from app.models.proyecto import Proyecto
from app.services.interpolacion_service import PuntoRSSI
from app.services.reporte_service import ReporteService


def test_fspl_pierde_seis_db_por_duplicar_distancia():
    modelo = ModeloPropagacion()
    rssi_1m = modelo.fspl(distancia_m=1)
    rssi_2m = modelo.fspl(distancia_m=2)
    rssi_4m = modelo.fspl(distancia_m=4)
    assert rssi_2m == pytest.approx(rssi_1m - 6, abs=0.1)
    assert rssi_4m == pytest.approx(rssi_2m - 6, abs=0.1)


def test_optimizador_edificio_en_u_propone_aps_en_extremos():
    puntos = [
        PuntoRSSI(punto_id=1, x=20, y=20, rssi=-91),
        PuntoRSSI(punto_id=2, x=380, y=20, rssi=-92),
        PuntoRSSI(punto_id=3, x=20, y=280, rssi=-88),
        PuntoRSSI(punto_id=4, x=380, y=280, rssi=-89),
        PuntoRSSI(punto_id=5, x=200, y=150, rssi=-76),
        PuntoRSSI(punto_id=6, x=200, y=40, rssi=-80),
    ]
    matriz_actual = [[-85.0 for _ in range(32)] for _ in range(32)]

    escenarios = OptimizadorAPService().optimizar(
        puntos_actuales=puntos,
        matriz_actual=matriz_actual,
        ancho_px=400,
        alto_px=300,
        metros_por_pixel=0.1,
        max_aps=2,
        banda="5",
        resolucion=32,
        umbral_objetivo_dbm=-70,
    )

    assert escenarios
    mejor = escenarios[0]
    assert mejor.cantidad_aps <= 2
    assert mejor.pct_cobertura >= mejor.pct_cobertura_actual
    xs = [rec["coord_x"] for rec in mejor.recomendaciones]
    assert min(xs) < 120 or max(xs) > 280
    assert "RSSI proyectado" in mejor.recomendaciones[0]["justificacion"]
    assert "potencia TX ajustable" in mejor.recomendaciones[0]["justificacion"]


def test_reporte_pdf_contiene_hash_y_bytes_pdf():
    proyecto = Proyecto(
        id=1, nombre="Survey Bulldog", estado="en_progreso", tecnico_id=1
    )
    escenario = EscenarioOptimizado(
        id=1,
        proyecto_id=1,
        plano_id=1,
        nombre="Alternativa 1",
        banda="5",
        modelo_ap="AP empresarial de potencia ajustable",
        pct_cobertura_actual=42.0,
        pct_cobertura=88.0,
        costo_estimado=240.0,
        cantidad_aps=2,
        resumen="Cobertura proyectada con dos APs.",
        restricciones={"max_aps": 2},
        metricas={"mejora_pct": 46.0},
    )
    escenario.recomendaciones = [
        RecomendacionAP(
            orden=1,
            accion="AGREGAR",
            coord_x=40,
            coord_y=30,
            banda="5",
            modelo_ap="AP empresarial de potencia ajustable",
            costo_estimado=120,
            rssi_proyectado=-62,
            justificacion="RSSI proyectado -62 dBm en zona critica.",
        )
    ]

    reporte = ReporteService().generar(
        proyecto=proyecto,
        escenarios=[escenario],
        escenario_seleccionado=escenario,
        cantidad_mediciones=12,
    )

    assert reporte.contenido.startswith(b"%PDF")
    assert len(reporte.sha256) == 64
    assert reporte.tamanio_bytes == len(reporte.contenido)


def test_reporte_pdf_deduplica_y_omite_costos_modelos():
    proyecto = Proyecto(
        id=1, nombre="Survey Bulldog", estado="en_progreso", tecnico_id=1
    )
    escenario = EscenarioOptimizado(
        id=8,
        proyecto_id=1,
        plano_id=1,
        nombre="Alternativa 3",
        banda="5",
        modelo_ap="AP WiFi 6 Bulldog BT-AX1800",
        pct_cobertura_actual=75.4,
        pct_cobertura=99.4,
        costo_estimado=360.0,
        cantidad_aps=3,
        resumen="Texto historico con modelo AP WiFi 6 Bulldog BT-AX1800.",
        restricciones={"max_aps": 3},
        metricas={"mejora_pct": 24.0},
    )
    escenario.recomendaciones = [
        RecomendacionAP(
            orden=1,
            accion="AGREGAR",
            coord_x=262,
            coord_y=258,
            banda="5",
            modelo_ap="AP WiFi 6 Bulldog BT-AX1800",
            costo_estimado=120,
            rssi_proyectado=-52.6,
            justificacion="Texto historico con modelo AP WiFi 6 Bulldog BT-AX1800.",
        )
    ]

    reporte = ReporteService().generar(
        proyecto=proyecto,
        escenarios=[escenario, escenario, escenario],
        escenario_seleccionado=escenario,
        cantidad_mediciones=233,
    )

    doc = fitz.open(stream=reporte.contenido, filetype="pdf")
    texto = "\n".join(page.get_text() for page in doc)
    doc.close()

    assert "Informe tecnico de cobertura WiFi" in texto
    assert texto.count("Ubicaciones sugeridas") == 1
    assert "AP WiFi 6 Bulldog" not in texto
    assert "costo" not in texto.lower()
