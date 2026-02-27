"""OM-specific chunker — splits at Para/Clause boundaries."""

import re
import logging

logger = logging.getLogger(__name__)

# Patterns for government OM paragraph/clause boundaries
BOUNDARY_PATTERNS = [
    # "Para 1.", "Para 2.", "Para. 1", etc.
    r"(?=\n\s*Para\.?\s*\d+)",
    # "1.", "2.", "3." at start of line (numbered paragraphs)
    r"(?=\n\s*\d+\.\s+[A-Z])",
    # "Clause 4(i)", "Clause 4(ii)", etc.
    r"(?=\n\s*Clause\s+\d+)",
    # "(i)", "(ii)", "(iii)" at start of line (sub-clauses)
    r"(?=\n\s*\([ivxlc]+\)\s+)",
    # "4(i)", "4(ii)" style references
    r"(?=\n\s*\d+\([ivxlc]+\))",
]

# Combined pattern
SPLIT_PATTERN = re.compile("|".join(BOUNDARY_PATTERNS), re.IGNORECASE)

# Pattern to extract clause/para reference from chunk start
REF_PATTERN = re.compile(
    r"^\s*(?:Para\.?\s*(\d+)|(\d+)\.\s|Clause\s+(\d+(?:\([ivxlc]+\))?)|(\d+\([ivxlc]+\))|\(([ivxlc]+)\))",
    re.IGNORECASE,
)


def _extract_section_ref(text: str) -> str:
    """Extract the clause/para reference from the start of a chunk."""
    match = REF_PATTERN.match(text.strip())
    if match:
        groups = match.groups()
        for g in groups:
            if g:
                return g.strip()
    return ""


def chunk_om(text: str, min_chunk_size: int = 100) -> list[dict]:
    """Chunk an OM document at Para/Clause boundaries.

    Returns list of dicts with 'text' and 'section_heading' keys.
    """
    # Split at boundary patterns
    chunks_raw = SPLIT_PATTERN.split(text)

    chunks = []
    buffer = ""

    for piece in chunks_raw:
        piece = piece.strip()
        if not piece:
            continue

        # If piece is too small, merge with buffer
        if len(piece) < min_chunk_size and buffer:
            buffer += "\n\n" + piece
            continue

        # If buffer exists and current piece is substantial, flush buffer
        if buffer:
            if len(buffer) >= min_chunk_size:
                ref = _extract_section_ref(buffer)
                chunks.append({"text": buffer.strip(), "section_heading": ref})
            else:
                # Merge small buffer with current piece
                piece = buffer + "\n\n" + piece
            buffer = ""

        if len(piece) >= min_chunk_size:
            ref = _extract_section_ref(piece)
            chunks.append({"text": piece.strip(), "section_heading": ref})
        else:
            buffer = piece

    # Flush remaining buffer
    if buffer.strip():
        ref = _extract_section_ref(buffer)
        chunks.append({"text": buffer.strip(), "section_heading": ref})

    # If no boundaries found, return whole text as single chunk
    if not chunks and text.strip():
        chunks = [{"text": text.strip(), "section_heading": ""}]

    logger.info(f"OM chunker: produced {len(chunks)} chunks")
    return chunks
