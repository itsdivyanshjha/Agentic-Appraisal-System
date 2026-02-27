"""General-purpose semantic chunker for reference documents."""

import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ~512-768 tokens ≈ 2000-3000 chars for English text
DEFAULT_CHUNK_SIZE = 2500
DEFAULT_CHUNK_OVERLAP = 200


def chunk_general(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP) -> list[dict]:
    """Chunk text using RecursiveCharacterTextSplitter.

    Returns list of dicts with 'text' and 'section_heading' keys.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    splits = splitter.split_text(text)

    chunks = []
    for i, split in enumerate(splits):
        # Use first line as heading hint
        first_line = split.strip().split("\n")[0].strip()
        heading = first_line[:80] if len(first_line) < 100 else f"chunk_{i + 1}"
        chunks.append({"text": split.strip(), "section_heading": heading})

    logger.info(f"General chunker: produced {len(chunks)} chunks")
    return chunks
