"""Unified PDF parser — tries LlamaParse first, falls back to PyMuPDF."""

import logging
from pathlib import Path

from parsers.llamaparse_client import parse_with_llamaparse
from parsers.pymupdf_fallback import parse_with_pymupdf

logger = logging.getLogger(__name__)


def parse_pdf(file_path: Path) -> tuple[str | None, str]:
    """Parse a PDF file. Returns (text, parser_used) tuple.

    Tries LlamaParse first, falls back to PyMuPDF.
    parser_used is one of: 'llamaparse', 'pymupdf', 'failed'
    """
    # Try LlamaParse first
    text = parse_with_llamaparse(file_path)
    if text:
        return text, "llamaparse"

    # Fallback to PyMuPDF
    logger.info(f"Falling back to PyMuPDF for {file_path.name}")
    text = parse_with_pymupdf(file_path)
    if text:
        return text, "pymupdf"

    logger.error(f"All parsers failed for {file_path.name}")
    return None, "failed"
