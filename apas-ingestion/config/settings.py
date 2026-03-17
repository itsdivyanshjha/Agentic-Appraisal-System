"""Environment configuration for APAS ingestion pipeline."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).parent.parent
SOURCE_DOCS_DIR = Path(os.getenv("SOURCE_DOCS_DIR", "./source_documents/"))
REFERENCE_DOCS_DIR = Path(os.getenv("REFERENCE_DOCS_DIR", "./reference_documents/"))
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "./chroma_db/"))

# LlamaParse
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY", "")

# Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
EMBEDDING_DEVICE = os.getenv("EMBEDDING_DEVICE", "cpu")

# LLM Extraction (OpenRouter)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
EXTRACTION_MODEL = os.getenv("EXTRACTION_MODEL", "openai/gpt-4o-mini")
EXTRACTION_CACHE_DIR = Path(os.getenv("EXTRACTION_CACHE_DIR", "./cache/"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Collection names
STRUCTURED_RULES_COLLECTION = "structured_rules"
OM_CHUNKS_COLLECTION = "om_document_chunks"
REFERENCE_CORPUS_COLLECTION = "reference_corpus"
