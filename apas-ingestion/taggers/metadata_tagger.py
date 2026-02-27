"""Tags chunks with metadata from the document registry."""

import logging

from config.document_registry import get_om_by_id, get_file_info

logger = logging.getLogger(__name__)


def tag_chunk(chunk: dict, filename: str) -> dict:
    """Add metadata to a chunk based on its source file.

    Args:
        chunk: Dict with 'text' and 'section_heading' keys.
        filename: Source PDF filename.

    Returns:
        Dict with full metadata added.
    """
    file_info = get_file_info(filename)
    if not file_info:
        logger.warning(f"File '{filename}' not found in registry, using minimal metadata")
        return {
            "text": chunk["text"],
            "section_heading": chunk.get("section_heading", ""),
            "om_id": "unknown",
            "om_number": "unknown",
            "doc_type": "unknown",
            "nature": "unknown",
            "date": "unknown",
            "applies_to": "",
            "agent_scope": "",
            "source_file": filename,
        }

    om_id = file_info["om_id"]
    doc_type = file_info["doc_type"]
    om = get_om_by_id(om_id)

    if not om:
        logger.error(f"OM '{om_id}' not found in registry for file '{filename}'")
        return {
            "text": chunk["text"],
            "section_heading": chunk.get("section_heading", ""),
            "om_id": om_id,
            "om_number": "unknown",
            "doc_type": doc_type,
            "nature": "unknown",
            "date": "unknown",
            "applies_to": "",
            "agent_scope": "",
            "source_file": filename,
        }

    return {
        "text": chunk["text"],
        "section_heading": chunk.get("section_heading", ""),
        "om_id": om_id,
        "om_number": om["om_number"],
        "doc_type": doc_type,
        "nature": om["nature"],
        "date": om["date"],
        # ChromaDB stores metadata values as strings — join lists
        "applies_to": ",".join(om["applies_to"]),
        "agent_scope": ",".join(om["agent_scope"]),
        "source_file": filename,
    }


def tag_reference_chunk(chunk: dict, doc_type: str, doc_title: str, agent_scope: list[str], source_file: str) -> dict:
    """Tag a reference document chunk with metadata.

    Args:
        chunk: Dict with 'text' and 'section_heading' keys.
        doc_type: e.g. 'gfr', 'fc_report', 'niti', 'budget', 'international'.
        doc_title: Title of the source document.
        agent_scope: List of agent scopes.
        source_file: Source filename.

    Returns:
        Dict with full metadata.
    """
    return {
        "text": chunk["text"],
        "doc_type": doc_type,
        "doc_title": doc_title,
        "section": chunk.get("section_heading", ""),
        "agent_scope": ",".join(agent_scope),
        "source_file": source_file,
    }
