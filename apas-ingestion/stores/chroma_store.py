"""ChromaDB collection manager for APAS."""

import logging
from pathlib import Path

import chromadb

from config.settings import (
    CHROMA_PERSIST_DIR,
    STRUCTURED_RULES_COLLECTION,
    OM_CHUNKS_COLLECTION,
    REFERENCE_CORPUS_COLLECTION,
)

logger = logging.getLogger(__name__)

_client = None


def get_client() -> chromadb.PersistentClient:
    """Get or initialize the ChromaDB client (singleton)."""
    global _client
    if _client is None:
        persist_dir = str(CHROMA_PERSIST_DIR)
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing ChromaDB at: {persist_dir}")
        _client = chromadb.PersistentClient(path=persist_dir)
    return _client


def get_or_create_collection(name: str) -> chromadb.Collection:
    """Get or create a ChromaDB collection."""
    client = get_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def clear_collection(name: str):
    """Delete a collection if it exists, then recreate it."""
    client = get_client()
    try:
        client.delete_collection(name)
        logger.info(f"Deleted collection: {name}")
    except Exception:
        pass
    return get_or_create_collection(name)


def clear_all_collections():
    """Clear and recreate all 3 collections."""
    logger.info("Clearing all collections for fresh ingestion")
    structured = clear_collection(STRUCTURED_RULES_COLLECTION)
    om_chunks = clear_collection(OM_CHUNKS_COLLECTION)
    reference = clear_collection(REFERENCE_CORPUS_COLLECTION)
    return structured, om_chunks, reference


def add_to_collection(
    collection: chromadb.Collection,
    ids: list[str],
    embeddings: list[list[float]],
    documents: list[str],
    metadatas: list[dict],
):
    """Add documents to a collection in batches."""
    batch_size = 100
    total = len(ids)

    for i in range(0, total, batch_size):
        end = min(i + batch_size, total)
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )

    logger.info(f"Added {total} entries to collection '{collection.name}'")


def query_collection(
    collection: chromadb.Collection,
    query_embedding: list[float],
    n_results: int = 5,
    where: dict | None = None,
) -> dict:
    """Query a collection with an embedding vector."""
    kwargs = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where
    return collection.query(**kwargs)


def get_collection_stats() -> dict:
    """Get counts for all collections."""
    client = get_client()
    stats = {}
    for name in [STRUCTURED_RULES_COLLECTION, OM_CHUNKS_COLLECTION, REFERENCE_CORPUS_COLLECTION]:
        try:
            coll = client.get_collection(name)
            stats[name] = coll.count()
        except Exception:
            stats[name] = 0
    return stats
