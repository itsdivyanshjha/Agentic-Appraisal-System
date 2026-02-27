"""Routes documents to the correct chunker based on doc_type."""

import logging

from chunkers.om_chunker import chunk_om
from chunkers.guidelines_chunker import chunk_guidelines
from chunkers.general_chunker import chunk_general

logger = logging.getLogger(__name__)


def route_chunker(text: str, doc_type: str) -> list[dict]:
    """Route document text to the appropriate chunker.

    Args:
        text: Parsed document text.
        doc_type: One of 'om', 'guidelines', 'annexure', 'supplementary',
                  'gfr', 'fc_report', 'niti', 'budget', 'international'.

    Returns:
        List of chunk dicts with 'text' and 'section_heading' keys.
    """
    if doc_type == "om":
        logger.info("Routing to OM chunker")
        return chunk_om(text)
    elif doc_type == "guidelines":
        logger.info("Routing to guidelines chunker")
        return chunk_guidelines(text)
    elif doc_type in ("annexure", "supplementary"):
        # Keep annexures as larger chunks — use guidelines chunker
        # which splits at section boundaries but keeps content intact
        logger.info("Routing annexure/supplementary to guidelines chunker")
        return chunk_guidelines(text, min_chunk_size=200)
    else:
        # Reference docs: GFR, FC reports, NITI, budget, international
        logger.info(f"Routing '{doc_type}' to general chunker")
        return chunk_general(text)
