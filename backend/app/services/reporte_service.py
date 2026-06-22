"""Generacion de reportes PDF Sprint 5 - PB-08."""

from __future__ import annotations

import hashlib
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

import fitz

from app.models.escenario import EscenarioOptimizado
from app.models.proyecto import Proyecto


@dataclass(frozen=True)
class ReporteGenerado:
    contenido: bytes
    sha256: str
    tamanio_bytes: int


class ReporteService:
    """Construye un informe tecnico formal de cobertura WiFi."""

    ANCHO = 595
    ALTO = 842
    MARGEN_X = 56
    COLOR_PRIMARIO = (0.08, 0.18, 0.28)
    COLOR_ACENTO = (0.16, 0.45, 0.72)
    COLOR_TEXTO = (0.10, 0.12, 0.16)
    COLOR_MUTED = (0.36, 0.40, 0.45)
    COLOR_FONDO = (0.94, 0.97, 0.99)
    COLOR_LINEA = (0.78, 0.84, 0.90)
    OBJETIVO_COBERTURA = -70
    UMBRAL_ZONA_MUERTA = -90

    def generar(
        self,
        *,
        proyecto: Proyecto,
        escenarios: list[EscenarioOptimizado],
        escenario_seleccionado: EscenarioOptimizado | None = None,
        cantidad_mediciones: int = 0,
    ) -> ReporteGenerado:
        escenarios_relevantes = self._escenarios_relevantes(
            escenarios=escenarios,
            escenario_seleccionado=escenario_seleccionado,
        )
        escenario_recomendado = escenario_seleccionado or (
            escenarios_relevantes[0] if escenarios_relevantes else None
        )

        doc = fitz.open()
        self._portada(doc, proyecto=proyecto, escenario=escenario_recomendado)
        self._resumen(
            doc,
            proyecto=proyecto,
            escenarios=escenarios_relevantes,
            escenario=escenario_recomendado,
            cantidad_mediciones=cantidad_mediciones,
        )
        self._comparativa(doc, escenarios=escenarios_relevantes)
        if escenario_recomendado is not None:
            self._escenario_recomendado(doc, escenario=escenario_recomendado)
            self._plan_accion(doc, escenario=escenario_recomendado)
        self._anexo(
            doc,
            proyecto=proyecto,
            escenario=escenario_recomendado,
            cantidad_mediciones=cantidad_mediciones,
            cantidad_escenarios=len(escenarios_relevantes),
        )
        self._pie_paginas(doc)

        contenido = doc.tobytes(deflate=True)
        doc.close()
        sha = hashlib.sha256(contenido).hexdigest()
        return ReporteGenerado(
            contenido=contenido,
            sha256=sha,
            tamanio_bytes=len(contenido),
        )

    def _escenarios_relevantes(
        self,
        *,
        escenarios: list[EscenarioOptimizado],
        escenario_seleccionado: EscenarioOptimizado | None,
    ) -> list[EscenarioOptimizado]:
        unicos: list[EscenarioOptimizado] = []
        vistos: set[tuple[object, ...]] = set()
        candidatos = (
            [escenario_seleccionado, *escenarios]
            if escenario_seleccionado
            else escenarios
        )

        for escenario in candidatos:
            if escenario is None:
                continue
            clave = self._clave_escenario(escenario)
            if clave in vistos:
                continue
            vistos.add(clave)
            unicos.append(escenario)

        unicos.sort(
            key=lambda e: (
                e.id != getattr(escenario_seleccionado, "id", None),
                -float(e.pct_cobertura or 0),
                int(e.cantidad_aps or 0),
            )
        )
        return unicos[:3]

    def _clave_escenario(self, escenario: EscenarioOptimizado) -> tuple[object, ...]:
        recomendaciones = tuple(
            (
                round(float(rec.coord_x), 1),
                round(float(rec.coord_y), 1),
                round(float(rec.rssi_proyectado), 1),
                str(rec.banda),
            )
            for rec in escenario.recomendaciones
        )
        return (
            str(escenario.nombre),
            int(escenario.cantidad_aps or 0),
            round(float(escenario.pct_cobertura_actual or 0), 1),
            round(float(escenario.pct_cobertura or 0), 1),
            str(escenario.banda),
            recomendaciones,
        )

    def _portada(
        self,
        doc: fitz.Document,
        *,
        proyecto: Proyecto,
        escenario: EscenarioOptimizado | None,
    ) -> None:
        page = self._nueva_pagina(doc)
        page.draw_rect(
            fitz.Rect(0, 0, self.ANCHO, 150),
            color=self.COLOR_PRIMARIO,
            fill=self.COLOR_PRIMARIO,
        )
        page.draw_rect(
            fitz.Rect(0, 150, self.ANCHO, 154),
            color=self.COLOR_ACENTO,
            fill=self.COLOR_ACENTO,
        )

        self._texto(page, 56, 64, "Bulldog Tech.", 24, color=(1, 1, 1), bold=True)
        self._texto(
            page,
            56,
            100,
            "Informe tecnico de cobertura WiFi",
            18,
            color=(1, 1, 1),
            bold=True,
        )
        self._texto(
            page,
            56,
            128,
            "Wireless HeatMapper - Modalidad 100% en linea",
            10,
            color=(0.86, 0.92, 0.98),
        )

        cliente = (
            proyecto.cliente.nombre if proyecto.cliente else "Sin cliente asignado"
        )
        tecnico = proyecto.tecnico.nombre if proyecto.tecnico else "Tecnico asignado"
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        cobertura = (
            f"{escenario.pct_cobertura:.1f}%"
            if escenario
            else "Sin escenario recomendado"
        )

        self._seccion(page, "Datos del proyecto", 56, 210)
        self._tabla(
            page,
            56,
            245,
            [
                ("Proyecto", proyecto.nombre),
                ("Cliente", cliente),
                ("Tecnico responsable", tecnico),
                ("Fecha de emision", fecha),
                ("Cobertura proyectada", cobertura),
            ],
            ancho_etiqueta=150,
        )

        self._caja_texto(
            page,
            56,
            520,
            483,
            112,
            "Alcance del informe",
            (
                "Este documento resume el diagnostico de cobertura WiFi, "
                "la alternativa tecnica recomendada y el plan de accion "
                "propuesto para mejorar la disponibilidad de senal "
                "en las zonas evaluadas del proyecto."
            ),
        )

    def _resumen(
        self,
        doc: fitz.Document,
        *,
        proyecto: Proyecto,
        escenarios: list[EscenarioOptimizado],
        escenario: EscenarioOptimizado | None,
        cantidad_mediciones: int,
    ) -> None:
        page = self._nueva_pagina(doc)
        self._titulo(page, "1. Resumen ejecutivo")

        if escenario is None:
            self._parrafo(
                page,
                self.MARGEN_X,
                120,
                "No existe un escenario optimizado seleccionado para este proyecto.",
            )
            return

        mejora = escenario.pct_cobertura - escenario.pct_cobertura_actual
        ap_plural = self._nombre_aps(escenario.cantidad_aps)
        bandas = getattr(escenario, "bandas", None) or [escenario.banda]
        conclusion = (
            f"Para el proyecto {proyecto.nombre} se recomienda implementar "
            f"{escenario.cantidad_aps} {ap_plural} empresariales "
            "con potencia TX ajustable, operando en las bandas "
            f"{' y '.join(bandas)} GHz. La cobertura proyectada alcanza "
            f"{escenario.pct_cobertura:.1f}% de area con RSSI >= "
            f"{self.OBJETIVO_COBERTURA} dBm, equivalente a una mejora de "
            f"{mejora:.1f} puntos porcentuales frente a la condicion actual."
        )
        y = self._parrafo(page, self.MARGEN_X, 118, conclusion, ancho=92)

        self._metricas(
            page,
            y + 18,
            [
                ("Cobertura actual", f"{escenario.pct_cobertura_actual:.1f}%"),
                ("Cobertura proyectada", f"{escenario.pct_cobertura:.1f}%"),
                ("Mejora estimada", f"{mejora:.1f} pp"),
                ("APs propuestos", str(escenario.cantidad_aps)),
            ],
        )

        y = 365
        self._seccion(page, "Criterios tecnicos utilizados", self.MARGEN_X, y)
        criterios = [
            "Objetivo de diseno: "
            f"RSSI >= {self.OBJETIVO_COBERTURA} dBm en areas operativas.",
            f"Zona muerta: RSSI < {self.UMBRAL_ZONA_MUERTA} dBm.",
            "La recomendacion es orientativa y debe verificarse con "
            "medicion posterior a la instalacion.",
            "Confianza del escenario: "
            f"{getattr(escenario, 'confianza', None) or 'MEDIA'}.",
            f"Mediciones consideradas para el reporte: {cantidad_mediciones}.",
            f"Alternativas tecnicas evaluadas en el informe: {len(escenarios)}.",
        ]
        self._bullets(page, self.MARGEN_X, y + 34, criterios)

    def _comparativa(
        self, doc: fitz.Document, *, escenarios: list[EscenarioOptimizado]
    ) -> None:
        page = self._nueva_pagina(doc)
        self._titulo(page, "2. Comparativa de alternativas")
        self._parrafo(
            page,
            self.MARGEN_X,
            116,
            (
                "La tabla presenta las alternativas tecnicas no duplicadas "
                "consideradas para la decision. Se prioriza cobertura "
                "proyectada, cantidad de APs requeridos y mejora frente "
                "al estado actual."
            ),
            ancho=92,
        )
        y = 190
        columnas = [180, 82, 92, 82, 82]
        encabezados = ["Alternativa", "Actual", "Proyectada", "Mejora", "APs"]
        filas = []
        for escenario in escenarios:
            mejora = escenario.pct_cobertura - escenario.pct_cobertura_actual
            filas.append(
                [
                    escenario.nombre,
                    f"{escenario.pct_cobertura_actual:.1f}%",
                    f"{escenario.pct_cobertura:.1f}%",
                    f"{mejora:.1f} pp",
                    str(escenario.cantidad_aps),
                ]
            )
        self._tabla_grid(page, self.MARGEN_X, y, encabezados, filas, columnas)

        if not escenarios:
            self._parrafo(
                page,
                self.MARGEN_X,
                y,
                "No existen alternativas optimizadas registradas.",
            )

    def _escenario_recomendado(
        self, doc: fitz.Document, *, escenario: EscenarioOptimizado
    ) -> None:
        page = self._nueva_pagina(doc)
        self._titulo(page, "3. Escenario recomendado")

        y = 116
        ap_plural = self._nombre_aps(escenario.cantidad_aps)
        bandas = getattr(escenario, "bandas", None) or [escenario.banda]
        self._caja_texto(
            page,
            self.MARGEN_X,
            y,
            483,
            112,
            "Descripcion tecnica",
            (
                f"La alternativa seleccionada incorpora {escenario.cantidad_aps} "
                f"{ap_plural} con potencia TX ajustable, capacidad de operacion "
                f"en bandas {' y '.join(bandas)} GHz, antenas adecuadas al area "
                "de cobertura y soporte de administracion centralizada. "
                f"Esta configuracion busca alcanzar RSSI >= "
                f"{self.OBJETIVO_COBERTURA} dBm en las zonas criticas detectadas."
            ),
        )

        y = 265
        self._seccion(page, "Ubicaciones sugeridas", self.MARGEN_X, y)
        filas = []
        for rec in escenario.recomendaciones:
            radios = getattr(rec, "radios", None) or []
            configuracion = (
                "; ".join(
                    f"{radio['banda']}G C{radio['canal']} "
                    f"{radio['ancho_canal_mhz']}MHz {radio['potencia_dbm']:.0f}dBm"
                    for radio in radios
                )
                or "Potencia TX ajustable"
            )
            filas.append(
                [
                    f"AP {rec.orden}",
                    f"({rec.coord_x:.1f}, {rec.coord_y:.1f})",
                    "/".join(radio["banda"] for radio in radios) or f"{rec.banda}",
                    f"{rec.rssi_proyectado:.1f} dBm",
                    configuracion,
                ]
            )
        self._tabla_grid(
            page,
            self.MARGEN_X,
            y + 34,
            ["Punto", "Coordenada", "Banda", "RSSI esperado", "Caracteristica clave"],
            filas,
            [55, 105, 70, 95, 158],
            size=8,
        )

    def _plan_accion(
        self, doc: fitz.Document, *, escenario: EscenarioOptimizado
    ) -> None:
        page = self._nueva_pagina(doc)
        self._titulo(page, "4. Plan de accion recomendado")
        y = 116
        acciones = []
        for rec in escenario.recomendaciones:
            radios = getattr(rec, "radios", None) or []
            detalle_radios = "; ".join(
                f"{radio['banda']} GHz canal {radio['canal']}, "
                f"{radio['ancho_canal_mhz']} MHz, {radio['potencia_dbm']:.0f} dBm"
                for radio in radios
            )
            acciones.append(
                (
                    f"{rec.accion.title()} AP {rec.orden}",
                    (
                        "Ubicar un punto de acceso en la coordenada "
                        f"({rec.coord_x:.1f}, {rec.coord_y:.1f}), operando "
                        f"con configuracion {detalle_radios or rec.banda + ' GHz'}. "
                        "El equipo debe permitir "
                        "ajuste de potencia TX, control de solapamiento, "
                        "antenas acordes al ambiente y gestion centralizada."
                    ),
                )
            )

        for titulo, detalle in acciones:
            self._texto(
                page, self.MARGEN_X, y, titulo, 11, bold=True, color=self.COLOR_PRIMARIO
            )
            y = (
                self._parrafo(
                    page, self.MARGEN_X + 16, y + 22, detalle, size=10, ancho=86
                )
                + 8
            )

        self._seccion(page, "Validacion posterior", self.MARGEN_X, y + 18)
        self._bullets(
            page,
            self.MARGEN_X,
            y + 52,
            [
                "Realizar una nueva captura de mediciones y confirmar "
                f"cobertura RSSI >= {self.OBJETIVO_COBERTURA} dBm.",
                "Verificar ausencia de zonas muertas con "
                f"RSSI < {self.UMBRAL_ZONA_MUERTA} dBm en areas operativas.",
                "Ajustar potencia por AP para evitar solapamiento excesivo "
                "y degradacion por interferencia.",
                "Registrar el resultado final en Wireless HeatMapper para "
                "trazabilidad del proyecto.",
            ],
        )

    def _anexo(
        self,
        doc: fitz.Document,
        *,
        proyecto: Proyecto,
        escenario: EscenarioOptimizado | None,
        cantidad_mediciones: int,
        cantidad_escenarios: int,
    ) -> None:
        page = self._nueva_pagina(doc)
        self._titulo(page, "5. Anexo tecnico")
        self._tabla(
            page,
            self.MARGEN_X,
            120,
            [
                ("Proyecto ID", str(proyecto.id)),
                ("Estado del proyecto", str(proyecto.estado)),
                ("Puntos registrados", str(proyecto.cantidad_puntos or 0)),
                ("Mediciones incluidas", str(cantidad_mediciones)),
                (
                    "Escenario recomendado",
                    escenario.nombre if escenario else "No especificado",
                ),
                ("Alternativas incluidas", str(cantidad_escenarios)),
                ("Integridad", "El PDF se registra con hash SHA-256 en el backend."),
            ],
            ancho_etiqueta=155,
        )

        self._caja_texto(
            page,
            self.MARGEN_X,
            420,
            483,
            120,
            "Nota de alcance",
            (
                "Las proyecciones se basan en las mediciones disponibles "
                "y en el modelo de propagacion del sistema. El informe no "
                "reemplaza una certificacion de sitio posterior a la "
                "instalacion; su proposito es respaldar la decision tecnica "
                "y orientar la implementacion."
            ),
        )

    def _nueva_pagina(self, doc: fitz.Document) -> fitz.Page:
        return doc.new_page(width=self.ANCHO, height=self.ALTO)

    @staticmethod
    def _nombre_aps(cantidad: int) -> str:
        return "punto de acceso" if cantidad == 1 else "puntos de acceso"

    def _titulo(self, page: fitz.Page, texto: str) -> None:
        self._texto(
            page, self.MARGEN_X, 74, texto, 18, bold=True, color=self.COLOR_PRIMARIO
        )
        page.draw_line(
            (self.MARGEN_X, 92),
            (self.ANCHO - self.MARGEN_X, 92),
            color=self.COLOR_ACENTO,
            width=1.2,
        )

    def _seccion(self, page: fitz.Page, texto: str, x: float, y: float) -> None:
        self._texto(page, x, y, texto, 12, bold=True, color=self.COLOR_PRIMARIO)

    def _metricas(
        self, page: fitz.Page, y: float, metricas: list[tuple[str, str]]
    ) -> None:
        ancho = 112
        alto = 78
        espacio = 12
        for idx, (etiqueta, valor) in enumerate(metricas):
            x = self.MARGEN_X + idx * (ancho + espacio)
            page.draw_rect(
                fitz.Rect(x, y, x + ancho, y + alto),
                color=self.COLOR_LINEA,
                fill=self.COLOR_FONDO,
            )
            self._texto(page, x + 10, y + 24, etiqueta, 8, color=self.COLOR_MUTED)
            self._texto(
                page, x + 10, y + 55, valor, 15, bold=True, color=self.COLOR_PRIMARIO
            )

    def _tabla(
        self,
        page: fitz.Page,
        x: float,
        y: float,
        filas: list[tuple[str, str]],
        *,
        ancho_etiqueta: float,
    ) -> float:
        actual = y
        for etiqueta, valor in filas:
            self._texto(
                page, x, actual, etiqueta, 10, bold=True, color=self.COLOR_MUTED
            )
            self._texto(
                page, x + ancho_etiqueta, actual, valor, 10, color=self.COLOR_TEXTO
            )
            page.draw_line(
                (x, actual + 9),
                (self.ANCHO - self.MARGEN_X, actual + 9),
                color=self.COLOR_LINEA,
                width=0.4,
            )
            actual += 30
        return actual

    def _tabla_grid(
        self,
        page: fitz.Page,
        x: float,
        y: float,
        encabezados: list[str],
        filas: list[list[str]],
        columnas: list[int],
        *,
        size: int = 9,
    ) -> float:
        alto_header = 28
        alto_fila = 34
        ancho_total = sum(columnas)
        page.draw_rect(
            fitz.Rect(x, y, x + ancho_total, y + alto_header),
            color=self.COLOR_PRIMARIO,
            fill=self.COLOR_PRIMARIO,
        )
        actual_x = x
        for idx, encabezado in enumerate(encabezados):
            self._texto(
                page, actual_x + 6, y + 18, encabezado, size, bold=True, color=(1, 1, 1)
            )
            actual_x += columnas[idx]

        actual_y = y + alto_header
        for fila_idx, fila in enumerate(filas):
            fill = (0.98, 0.99, 1.0) if fila_idx % 2 == 0 else (1, 1, 1)
            page.draw_rect(
                fitz.Rect(x, actual_y, x + ancho_total, actual_y + alto_fila),
                color=self.COLOR_LINEA,
                fill=fill,
                width=0.4,
            )
            actual_x = x
            for col_idx, valor in enumerate(fila):
                self._texto(
                    page,
                    actual_x + 6,
                    actual_y + 20,
                    valor,
                    size,
                    color=self.COLOR_TEXTO,
                )
                actual_x += columnas[col_idx]
            actual_y += alto_fila
        return actual_y

    def _caja_texto(
        self,
        page: fitz.Page,
        x: float,
        y: float,
        ancho: float,
        alto: float,
        titulo: str,
        texto: str,
    ) -> None:
        page.draw_rect(
            fitz.Rect(x, y, x + ancho, y + alto),
            color=self.COLOR_LINEA,
            fill=self.COLOR_FONDO,
        )
        self._texto(
            page, x + 18, y + 28, titulo, 11, bold=True, color=self.COLOR_PRIMARIO
        )
        self._parrafo(page, x + 18, y + 54, texto, size=10, ancho=74)

    def _bullets(
        self, page: fitz.Page, x: float, y: float, items: Iterable[str]
    ) -> float:
        actual = y
        for item in items:
            self._texto(page, x, actual, "-", 10, bold=True, color=self.COLOR_ACENTO)
            actual = self._parrafo(page, x + 14, actual, item, size=10, ancho=86) + 4
        return actual

    def _parrafo(
        self,
        page: fitz.Page,
        x: float,
        y: float,
        texto: str,
        *,
        size: int = 10,
        ancho: int = 88,
    ) -> float:
        actual = y
        for linea in texto.splitlines():
            for parte in textwrap.wrap(linea, width=ancho) or [""]:
                self._texto(page, x, actual, parte, size)
                actual += size + 6
        return actual

    def _texto(
        self,
        page: fitz.Page,
        x: float,
        y: float,
        texto: str,
        size: int,
        *,
        bold: bool = False,
        color: tuple[float, float, float] | None = None,
    ) -> None:
        fontname = "hebo" if bold else "helv"
        page.insert_text(
            (x, y),
            str(texto),
            fontsize=size,
            fontname=fontname,
            fill=color or self.COLOR_TEXTO,
        )

    def _pie_paginas(self, doc: fitz.Document) -> None:
        total = doc.page_count
        for indice, page in enumerate(doc, start=1):
            page.draw_line(
                (self.MARGEN_X, 790),
                (self.ANCHO - self.MARGEN_X, 790),
                color=self.COLOR_LINEA,
                width=0.5,
            )
            self._texto(
                page,
                self.MARGEN_X,
                812,
                "Wireless HeatMapper | Bulldog Tech.",
                8,
                color=self.COLOR_MUTED,
            )
            self._texto(
                page,
                self.ANCHO - 108,
                812,
                f"Pagina {indice} de {total}",
                8,
                color=self.COLOR_MUTED,
            )
