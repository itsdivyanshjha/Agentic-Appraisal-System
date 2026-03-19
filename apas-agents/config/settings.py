"""Configuration for APAS agent layer."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the ingestion folder (shared credentials)
INGESTION_DIR = Path(__file__).parent.parent.parent / "apas-ingestion"
load_dotenv(INGESTION_DIR / ".env")

# Add ingestion folder to path so we can import shared modules
sys.path.insert(0, str(INGESTION_DIR))

# ─── Paths ───
CHROMA_PERSIST_DIR = INGESTION_DIR / "chroma_db"

# ─── Models (all via OpenRouter) ───
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "openai/gpt-4o-mini")
AGENT_MODEL = os.getenv("AGENT_MODEL", "openai/gpt-4o-mini")

# ─── Embedding (same model as ingestion — must match!) ───
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

# ─── Collection names (must match ingestion pipeline) ───
STRUCTURED_RULES_COLLECTION = "structured_rules"
OM_CHUNKS_COLLECTION = "om_document_chunks"
REFERENCE_CORPUS_COLLECTION = "reference_corpus"

# ─── Retrieval config per agent scope ───
AGENT_RETRIEVAL_CONFIG = {
    "compliance": {
        "primary_collection": STRUCTURED_RULES_COLLECTION,
        "secondary_collection": OM_CHUNKS_COLLECTION,
        "scope": "compliance",
        "top_k": 8,
    },
    "fiscal": {
        "primary_collection": STRUCTURED_RULES_COLLECTION,
        "secondary_collection": REFERENCE_CORPUS_COLLECTION,
        "scope": "fiscal",
        "top_k": 6,
    },
    "sector": {
        "primary_collection": OM_CHUNKS_COLLECTION,
        "secondary_collection": REFERENCE_CORPUS_COLLECTION,
        "scope": "sector",
        "top_k": 8,
    },
}

# ─── Logging ───
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
