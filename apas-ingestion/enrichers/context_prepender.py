"""Contextual chunk enrichment — prepends document-level context to chunks.

Implements the "contextual retrieval" pattern: each chunk gets a prefix
with document metadata so the embedding model has broader context.
No LLM call — pure string transformation.
"""

import logging

logger = logging.getLogger(__name__)


def prepend_context(chunk_text: str, metadata: dict) -> str:
    """Prepend document-level context to a chunk for better embedding quality.

    Args:
        chunk_text: The raw chunk text.
        metadata: Tagged chunk metadata (om_number, date, nature, section_heading, etc.).

    Returns:
        Context-prefixed chunk text.
    """
    om_number = metadata.get("om_number", "unknown")
    date = metadata.get("date", "unknown")
    nature = metadata.get("nature", "unknown")
    section = metadata.get("section_heading", "")
    doc_type = metadata.get("doc_type", "")

    parts = [f"Document: OM {om_number} dated {date}."]
    parts.append(f"Subject: {nature}.")

    if doc_type:
        parts.append(f"Type: {doc_type}.")

    if section:
        parts.append(f"Section: {section}.")

    prefix = " ".join(parts)
    return f"{prefix}\n\n{chunk_text}"


def prepend_reference_context(chunk_text: str, metadata: dict) -> str:
    """Prepend context to a reference document chunk.

    Args:
        chunk_text: The raw chunk text.
        metadata: Reference chunk metadata (doc_title, doc_type, section, etc.).

    Returns:
        Context-prefixed chunk text.
    """
    doc_title = metadata.get("doc_title", "unknown")
    doc_type = metadata.get("doc_type", "")
    section = metadata.get("section", "")

    parts = [f"Document: {doc_title}."]

    if doc_type:
        parts.append(f"Type: {doc_type}.")

    if section:
        parts.append(f"Section: {section}.")

    prefix = " ".join(parts)
    return f"{prefix}\n\n{chunk_text}"
