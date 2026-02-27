"""LlamaParse API wrapper for PDF parsing."""

import logging
from pathlib import Path

from config.settings import LLAMA_CLOUD_API_KEY

logger = logging.getLogger(__name__)


def parse_with_llamaparse(file_path: Path) -> str | None:
    """Parse a PDF using LlamaParse API. Returns markdown text or None on failure."""
    if not LLAMA_CLOUD_API_KEY:
        logger.warning("LLAMA_CLOUD_API_KEY not set, skipping LlamaParse")
        return None

    try:
        from llama_parse import LlamaParse

        parser = LlamaParse(
            api_key=LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            verbose=False,
        )
        documents = parser.load_data(str(file_path))
        if documents:
            text = "\n\n".join(doc.text for doc in documents)
            logger.info(f"LlamaParse: extracted {len(text)} chars from {file_path.name}")
            return text
        logger.warning(f"LlamaParse returned empty result for {file_path.name}")
        return None
    except Exception as e:
        logger.warning(f"LlamaParse failed for {file_path.name}: {e}")
        return None
