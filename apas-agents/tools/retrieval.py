"""Retrieval tools for APAS agents — search ChromaDB collections.

Each agent gets scoped versions of these tools that only search
collections relevant to its domain (compliance/fiscal/sector).
"""

import logging
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from config.settings import (
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL,
    EMBEDDING_DEVICE,
    AGENT_RETRIEVAL_CONFIG,
)

logger = logging.getLogger(__name__)

# ─── Singletons ───

_chroma_client = None
_embed_model = None


def _get_chroma() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        persist_dir = str(CHROMA_PERSIST_DIR)
        logger.info(f"Connecting to ChromaDB at: {persist_dir}")
        _chroma_client = chromadb.PersistentClient(path=persist_dir)
    return _chroma_client


def _get_embedder() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embed_model = SentenceTransformer(EMBEDDING_MODEL, device=EMBEDDING_DEVICE)
    return _embed_model


def _embed_query(query: str) -> list[float]:
    model = _get_embedder()
    embedding = model.encode([query], normalize_embeddings=True)
    return embedding[0].tolist()


def _query_collection(collection_name: str, query: str, scope: str, top_k: int) -> list[dict]:
    """Query a ChromaDB collection with scope-based post-filtering.

    Uses post-filtering instead of ChromaDB $contains (known bug with
    comma-separated string metadata).
    """
    client = _get_chroma()

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        logger.warning(f"Collection '{collection_name}' not found")
        return []

    query_embedding = _embed_query(query)

    # Fetch more results than needed, then post-filter by scope
    fetch_k = top_k * 3
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(fetch_k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    if not results["ids"][0]:
        return []

    # Post-filter: check if scope is in the agent_scope string
    filtered = []
    for i, doc_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        agent_scope = meta.get("agent_scope", "")

        if scope in agent_scope:
            distance = results["distances"][0][i]
            score = round(1 - distance, 3)  # cosine distance → similarity

            filtered.append({
                "id": doc_id,
                "text": results["documents"][0][i],
                "score": score,
                "om_id": meta.get("om_id", ""),
                "om_number": meta.get("om_number", ""),
                "clause_ref": meta.get("clause_ref", ""),
                "nature": meta.get("nature", ""),
                "date": meta.get("date", ""),
                "doc_type": meta.get("doc_type", ""),
                "source_file": meta.get("source_file", ""),
                "doc_title": meta.get("doc_title", ""),
            })

            if len(filtered) >= top_k:
                break

    return filtered


def _format_results(results: list[dict]) -> str:
    """Format retrieval results as readable text for the LLM."""
    if not results:
        return "No relevant documents found."

    parts = []
    for i, r in enumerate(results, 1):
        header_parts = []
        if r.get("om_number"):
            header_parts.append(f"OM {r['om_number']}")
        if r.get("doc_title"):
            header_parts.append(r["doc_title"])
        if r.get("date"):
            header_parts.append(f"dated {r['date']}")
        if r.get("clause_ref"):
            header_parts.append(f"Clause {r['clause_ref']}")

        header = " | ".join(header_parts) if header_parts else "Document"
        parts.append(f"[Result {i}] ({header}) [Score: {r['score']}]\n{r['text']}")

    return "\n\n---\n\n".join(parts)


# ─── Tool factories (create scoped tools for each agent) ───

def create_search_rules_tool(scope: str):
    """Create a search_rules tool scoped to a specific agent."""
    config = AGENT_RETRIEVAL_CONFIG[scope]

    def search_rules(query: str) -> str:
        """Search structured appraisal rules from Office Memoranda.

        Use this to find specific rules, clauses, compliance requirements,
        cost thresholds, approval procedures, and mandatory formats.

        Args:
            query: Natural language search query about government appraisal rules.

        Returns:
            Formatted search results with OM citations.
        """
        results = _query_collection(
            config["primary_collection"], query, scope, config["top_k"]
        )
        return _format_results(results)

    search_rules.__name__ = "search_rules"
    return search_rules


def create_search_documents_tool(scope: str):
    """Create a search_documents tool scoped to a specific agent."""
    config = AGENT_RETRIEVAL_CONFIG[scope]

    def search_documents(query: str) -> str:
        """Search full document text from OMs, GFR, DFPR, budget docs, and reports.

        Use this to find detailed context, annexure content, specific wordings,
        checklists, or reference material beyond structured rules.

        Args:
            query: Natural language search query about government documents.

        Returns:
            Formatted search results with document citations.
        """
        results = _query_collection(
            config["secondary_collection"], query, scope, config["top_k"]
        )
        return _format_results(results)

    search_documents.__name__ = "search_documents"
    return search_documents
