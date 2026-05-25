"""Document ingestion: text in, normalised text out.

Two paths:
  * ``ingest_text`` — for digital PDFs the web client extracted via pdf.js.
  * ``ingest_pdf_bytes`` — for raw PDF uploads. Tries PyMuPDF's text layer
    first; if the result is below a density threshold (i.e. likely scanned),
    renders each page to an image and runs Tesseract OCR.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.schemas import IngestionMethod

logger = logging.getLogger(__name__)

# Below this many text-layer characters per page, assume the PDF is scanned
# and we need OCR. Matches the threshold used in apps/web/lib/pdf-extract.ts.
_SCANNED_TEXT_DENSITY = 30


@dataclass
class IngestionResult:
    text: str
    page_count: int
    method: IngestionMethod


def normalise_text(text: str) -> str:
    """Cheap rules-only cleanup. Safe to apply to both pdf.js text and OCR output."""
    text = text.replace("﻿", "").replace("​", "")
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return text.strip()


def ingest_text(text: str) -> IngestionResult:
    """Text-direct ingestion (Next.js extracted text client-side via pdf.js)."""
    cleaned = normalise_text(text)
    return IngestionResult(text=cleaned, page_count=0, method="text-direct")


def ingest_pdf_bytes(pdf_bytes: bytes) -> IngestionResult:
    """Extract text from a PDF byte stream.

    Strategy:
      1. PyMuPDF (fitz) — tries to read the text layer.
      2. If the text layer is sparse (likely scanned), render each page to a
         300 DPI image and run pytesseract OCR.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF (pymupdf) is required for PDF ingestion but is not installed"
        ) from exc

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_count = doc.page_count

    # Phase 1: text layer
    pages_text: list[str] = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    text_layer = "\n\n".join(pages_text)
    text_layer_normalised = normalise_text(text_layer)

    is_scanned = page_count > 0 and len(text_layer_normalised) < _SCANNED_TEXT_DENSITY * page_count

    if not is_scanned:
        doc.close()
        return IngestionResult(
            text=text_layer_normalised,
            page_count=page_count,
            method="pymupdf",
        )

    # Phase 2: OCR
    logger.info("PDF appears scanned (text density too low) — falling back to OCR")
    try:
        import io

        import pytesseract
        from PIL import Image
    except ImportError as exc:
        doc.close()
        raise RuntimeError(
            "pytesseract and Pillow are required for OCR on scanned PDFs"
        ) from exc

    ocr_text: list[str] = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        ocr_text.append(pytesseract.image_to_string(img))
    doc.close()

    full = "\n\n".join(ocr_text)
    return IngestionResult(
        text=normalise_text(full),
        page_count=page_count,
        method="tesseract-ocr",
    )
