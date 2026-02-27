# APAS — AI-based Project & Scheme Appraisal System

## Project Overview

An agentic query assistant for the Department of Expenditure, Government of India. Helps Section Officers get instant, citation-backed answers about government appraisal rules and procedures.

## Current State (Completed)

### Ingestion Pipeline (`apas-ingestion/`)

Fully working pipeline that:
- Ingests 52 structured rules from 7 OMs into ChromaDB `structured_rules` collection
- Parses 13+ source OM PDFs (LlamaParse primary, PyMuPDF fallback) into `om_document_chunks` collection
- Optional `reference_corpus` collection for GFR, FC reports, NITI papers
- Validation: 9/10 test queries pass (structured rules retrieval is strong)

**Key files:**
- `apas-ingestion/pipeline.py` — main entry point, run with `python pipeline.py`
- `apas-ingestion/validate.py` — retrieval quality tests
- `apas-ingestion/config/document_registry.py` — all 7 OMs, 52 rules, file-to-OM mappings (filenames updated to match actual PDFs)
- `apas-ingestion/config/settings.py` — env vars, paths, model config

**Tech stack:** ChromaDB (embedded), sentence-transformers (BAAI/bge-base-en-v1.5), LlamaParse + PyMuPDF

**Known issues:**
- ChromaDB `$contains` filter doesn't work on comma-separated string metadata — validate.py queries without filter and post-filters in Python
- Query 10 (sector agent, risk flags from OM-3) fails because sector agent routes to `om_document_chunks` where PDF text is noisier; consider also querying `structured_rules` as secondary

## Architecture: 4 LangGraph Agents

```
User Query
    |
    v
Orchestrator Agent (routes query to 1+ specialist agents)
    |
    ├── Compliance & Rules Agent  → structured_rules + om_document_chunks (scope: compliance)
    ├── Fiscal & Financial Agent  → structured_rules + reference_corpus (scope: fiscal)
    └── Sector & Evaluation Agent → om_document_chunks + reference_corpus (scope: sector)
    |
    v
Synthesized answer with citations (OM number, clause ref, date)
```

## Next Steps (Priority Order)

### Phase 2: LangGraph Agent Layer
1. **Build base retrieval tool** — a LangGraph tool that queries ChromaDB collections with agent-scoped filtering, returns top-k results with metadata for citation
2. **Compliance Agent** — LangGraph ReAct agent with retrieval tool scoped to compliance collections; system prompt covering OM rules, appraisal process, IPA requirements
3. **Fiscal Agent** — same pattern, scoped to fiscal; handles cost thresholds, Centre-State ratios, outlay calculations
4. **Sector Agent** — scoped to sector; handles NITI rationalisation, OOMF performance assessment, evaluation
5. **Orchestrator Agent** — routes user queries to 1+ specialist agents, synthesizes responses, handles ambiguous queries
6. **Citation formatting** — every answer must cite OM number, clause reference, and date

### Phase 3: Reference Corpus Expansion
- Add GFR (General Financial Rules) PDFs to `reference_documents/`
- Add Finance Commission reports (XV FC, XVI FC)
- Add NITI Aayog evaluation reports
- Add budget circulars and cost norm documents
- Re-run `python pipeline.py` after adding docs

### Phase 4: UI / Interface
- Streamlit or Gradio web interface for Section Officers
- Query input with suggested questions
- Response display with expandable citations
- Agent routing visualization (which agent answered what)

### Phase 5: Improvements
- Fix sector agent to also query `structured_rules` as secondary collection
- Add hybrid search (BM25 + vector) for better keyword matching on clause numbers
- Add re-ranking step (cross-encoder) for better precision
- Consider switching to `text-embedding-3-small` if OpenAI API is available for better multilingual support (some OMs have Hindi)

## Development Commands

```bash
cd apas-ingestion/

# First time setup
cp .env.example .env   # add LLAMA_CLOUD_API_KEY
pip install -r requirements.txt

# Run pipeline (idempotent — clears and rebuilds all collections)
python pipeline.py

# Test retrieval quality
python validate.py
```

## File Naming Convention

Source PDFs go in `apas-ingestion/source_documents/` with exact filenames matching `FILE_TO_OM_MAP` in `config/document_registry.py`. The filenames have spaces and special characters — this is intentional to match the actual government document names.

## Dependencies

- Python 3.11+
- sentence-transformers, chromadb, llama-parse, pymupdf
- python-dotenv, pydantic, rich, langchain-text-splitters
- For Phase 2: langgraph, langchain-core, langchain-anthropic (Claude API)
