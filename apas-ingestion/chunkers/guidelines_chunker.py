"""Guidelines document chunker — splits at section heading boundaries."""

import re
import logging

logger = logging.getLogger(__name__)

# Section heading patterns for guidelines documents
HEADING_PATTERNS = [
    # "1. Title", "2. Title", "10. Title"
    r"(?=\n\s*\d+\.\s+[A-Z][A-Za-z\s]+)",
    # "Section 1", "Section 2"
    r"(?=\n\s*Section\s+\d+)",
    # "Chapter 1", "Chapter 2"
    r"(?=\n\s*Chapter\s+\d+)",
    # "ANNEXURE I", "Annexure II", "ANNEX-I"
    r"(?=\n\s*(?:ANNEXURE|Annexure|ANNEX)[\s\-]*[IVXLC\d]+)",
    # "Part A", "Part B"
    r"(?=\n\s*Part\s+[A-Z])",
    # Bold/caps headings (all-caps lines > 5 chars)
    r"(?=\n\s*[A-Z][A-Z\s&,]{5,}\n)",
]

SPLIT_PATTERN = re.compile("|".join(HEADING_PATTERNS))

HEADING_REF = re.compile(
    r"^\s*(?:(\d+)\.\s+(.+?)$|Section\s+(\d+).*?$|Chapter\s+(\d+).*?$|(?:ANNEXURE|Annexure|ANNEX)[\s\-]*([IVXLC\d]+).*?$|Part\s+([A-Z]).*?$|([A-Z][A-Z\s&,]{5,})$)",
    re.MULTILINE,
)


def _extract_heading(text: str) -> str:
    """Extract section heading from start of chunk."""
    match = HEADING_REF.match(text.strip())
    if match:
        groups = match.groups()
        for g in groups:
            if g:
                return g.strip()[:80]
    # Return first line as heading if short enough
    first_line = text.strip().split("\n")[0].strip()
    if len(first_line) < 100:
        return first_line
    return ""


def chunk_guidelines(text: str, min_chunk_size: int = 150) -> list[dict]:
    """Chunk a guidelines document at section heading boundaries.

    Returns list of dicts with 'text' and 'section_heading' keys.
    """
    chunks_raw = SPLIT_PATTERN.split(text)

    chunks = []
    buffer = ""

    for piece in chunks_raw:
        piece = piece.strip()
        if not piece:
            continue

        if len(piece) < min_chunk_size and buffer:
            buffer += "\n\n" + piece
            continue

        if buffer:
            if len(buffer) >= min_chunk_size:
                heading = _extract_heading(buffer)
                chunks.append({"text": buffer.strip(), "section_heading": heading})
            else:
                piece = buffer + "\n\n" + piece
            buffer = ""

        if len(piece) >= min_chunk_size:
            heading = _extract_heading(piece)
            chunks.append({"text": piece.strip(), "section_heading": heading})
        else:
            buffer = piece

    if buffer.strip():
        heading = _extract_heading(buffer)
        chunks.append({"text": buffer.strip(), "section_heading": heading})

    if not chunks and text.strip():
        chunks = [{"text": text.strip(), "section_heading": ""}]

    logger.info(f"Guidelines chunker: produced {len(chunks)} chunks")
    return chunks
