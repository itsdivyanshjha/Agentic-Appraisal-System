"""PyMuPDF fallback parser for PDF extraction."""

import logging
from pathlib import Path

import pymupdf

logger = logging.getLogger(__name__)


def parse_with_pymupdf(file_path: Path) -> str | None:
    """Parse a PDF using PyMuPDF. Returns extracted text or None on failure."""
    try:
        doc = pymupdf.open(str(file_path))
        pages = []
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                pages.append(text)
        doc.close()

        if pages:
            text = "\n\n".join(pages)
            logger.info(f"PyMuPDF: extracted {len(text)} chars from {file_path.name} ({len(pages)} pages)")
            return text
        logger.warning(f"PyMuPDF: no text extracted from {file_path.name}")
        return None
    except Exception as e:
        logger.error(f"PyMuPDF failed for {file_path.name}: {e}")
        return None
