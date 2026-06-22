"""Servicio de procesamiento de PDF — Sprint 2 PB-02.

Renderiza la primera página de un PDF a PNG usando PyMuPDF.
"""

from dataclasses import dataclass

import fitz  # PyMuPDF


@dataclass
class PdfRenderResult:
    png_bytes: bytes
    ancho_px: int
    alto_px: int
    multipagina: bool
    cantidad_paginas: int


class PdfService:
    """Conversión PDF→PNG (primera página) para visualización del plano."""

    DEFAULT_DPI = 150

    def render_first_page(self, contenido_pdf: bytes, dpi: int = DEFAULT_DPI) -> PdfRenderResult:
        """Renderiza la primera página del PDF a PNG con la resolución indicada.

        Lanza ``ValueError`` si el PDF está vacío o corrupto.
        """
        try:
            doc = fitz.open(stream=contenido_pdf, filetype="pdf")
        except Exception as exc:  # pragma: no cover - depende de la libería
            raise ValueError("PDF inválido o corrupto") from exc

        try:
            if doc.page_count < 1:
                raise ValueError("El PDF no contiene páginas")

            page = doc.load_page(0)
            zoom = dpi / 72  # PyMuPDF usa 72 DPI por defecto
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            png_bytes = pix.tobytes("png")

            return PdfRenderResult(
                png_bytes=png_bytes,
                ancho_px=pix.width,
                alto_px=pix.height,
                multipagina=doc.page_count > 1,
                cantidad_paginas=doc.page_count,
            )
        finally:
            doc.close()
