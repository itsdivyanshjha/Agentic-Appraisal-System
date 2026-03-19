"""Unified PDF parser — tries LlamaParse first, falls back to PyMuPDF.

Includes a disk cache to avoid re-calling LlamaParse for already-parsed PDFs.
"""

import hashlib
import json
import logging
from pathlib import Path

from config.settings import EXTRACTION_CACHE_DIR
from parsers.llamaparse_client import parse_with_llamaparse
from parsers.pymupdf_fallback import parse_with_pymupdf

logger = logging.getLogger(__name__)

PARSE_CACHE_DIR = Path(EXTRACTION_CACHE_DIR) / "parsed_texts"


def _get_file_hash(file_path: Path) -> str:
    """SHA-256 hash of file contents for cache key."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()[:16]


def _load_cached_parse(file_path: Path) -> tuple[str | None, str | None]:
    """Try to load a cached parse result. Returns (text, parser_used) or (None, None)."""
    PARSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = PARSE_CACHE_DIR / f"{_get_file_hash(file_path)}.json"
    if cache_file.exists():
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            logger.info(f"Cache hit for {file_path.name}")
            return data["text"], data["parser_used"]
        except (json.JSONDecodeError, KeyError):
            pass
    return None, None


def _save_to_cache(file_path: Path, text: str, parser_used: str):
    """Save parse result to disk cache."""
    PARSE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = PARSE_CACHE_DIR / f"{_get_file_hash(file_path)}.json"
    cache_file.write_text(
        json.dumps({"filename": file_path.name, "text": text, "parser_used": parser_used}),
        encoding="utf-8",
    )


def parse_pdf(file_path: Path) -> tuple[str | None, str]:
    """Parse a PDF file. Returns (text, parser_used) tuple.

    Checks disk cache first. Tries LlamaParse, falls back to PyMuPDF.
    parser_used is one of: 'llamaparse', 'pymupdf', 'cached', 'failed'
    """
    # Check cache first
    cached_text, cached_parser = _load_cached_parse(file_path)
    if cached_text:
        return cached_text, f"cached ({cached_parser})"

    # Try LlamaParse first
    text = parse_with_llamaparse(file_path)
    if text:
        _save_to_cache(file_path, text, "llamaparse")
        return text, "llamaparse"

    # Fallback to PyMuPDF
    logger.info(f"Falling back to PyMuPDF for {file_path.name}")
    text = parse_with_pymupdf(file_path)
    if text:
        _save_to_cache(file_path, text, "pymupdf")
        return text, "pymupdf"

    logger.error(f"All parsers failed for {file_path.name}")
    return None, "failed"
