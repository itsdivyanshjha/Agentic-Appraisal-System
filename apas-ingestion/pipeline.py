"""APAS Document Ingestion Pipeline — main orchestrator.

Pipeline steps:
1. Parse & chunk all source PDFs (split into OM chunks + reference chunks)
2. Extract structured rules via LLM (OM chunks only)
3. Ingest extracted rules into structured_rules collection
4. Ingest enriched OM chunks into om_document_chunks collection
5. Ingest reference chunks into reference_corpus collection
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import (
    SOURCE_DOCS_DIR,
    OPENROUTER_API_KEY,
    STRUCTURED_RULES_COLLECTION,
    OM_CHUNKS_COLLECTION,
    REFERENCE_CORPUS_COLLECTION,
    EXTRACTION_CACHE_DIR,
    LOG_LEVEL,
)
from config.document_registry import OM_REGISTRY, FILE_TO_OM_MAP
from embeddings.embedder import embed_texts
from stores.chroma_store import (
    clear_all_collections,
    clear_collection,
    get_or_create_collection,
    add_to_collection,
    get_collection_stats,
)
from parsers.pdf_parser import parse_pdf
from chunkers.chunk_router import route_chunker
from taggers.metadata_tagger import tag_chunk_with_metadata
from extractors.rule_extractor import extract_rules_batch
from enrichers.context_prepender import prepend_context, prepend_reference_context
from extractors.document_classifier import classify_document

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
console = Console()


# ─── Cache paths ───

OM_CHUNKS_CACHE = Path(EXTRACTION_CACHE_DIR) / "om_chunks.json"
REF_CHUNKS_CACHE = Path(EXTRACTION_CACHE_DIR) / "reference_chunks.json"
RULES_CACHE_FILE = Path(EXTRACTION_CACHE_DIR) / "extracted_rules.json"


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def _load_json(path: Path):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


# ─── Step 1 ───

def parse_and_chunk_source_pdfs() -> tuple[list[dict], list[dict]]:
    """Step 1: Parse and chunk all source PDFs.

    Returns two lists:
      - om_chunks: chunks from registered OM PDFs (→ om_document_chunks + structured_rules)
      - reference_chunks: chunks from auto-discovered PDFs (→ reference_corpus)
    """
    console.print("\n[bold cyan]═══ Step 1: Parsing & Chunking Source PDFs ═══[/bold cyan]")

    source_dir = Path(SOURCE_DOCS_DIR)
    if not source_dir.exists():
        console.print(f"  [yellow]⚠ Source directory not found: {source_dir}[/yellow]")
        return [], []

    # Deduplicate (Windows case-insensitive glob)
    pdf_files = list({f.name: f for f in list(source_dir.glob("*.pdf")) + list(source_dir.glob("*.PDF"))}.values())
    if not pdf_files:
        console.print("  [yellow]⚠ No PDFs found in source directory[/yellow]")
        return [], []

    registered_count = sum(1 for f in pdf_files if f.name in FILE_TO_OM_MAP)
    new_count = len(pdf_files) - registered_count
    console.print(f"  Found {len(pdf_files)} PDFs ({registered_count} registered OMs, {new_count} reference/auto-discovered)")

    om_chunks = []
    reference_chunks = []

    for pdf_path in pdf_files:
        filename = pdf_path.name

        # Classify document (registry fast path or auto-discovery)
        metadata = classify_document(pdf_path)
        doc_type = metadata.get("doc_type", "om")
        source = metadata.get("source", "unknown")

        if source == "registry":
            source_label = "registry → om_document_chunks"
        else:
            source_label = "[yellow]auto-discovered → reference_corpus[/yellow]"

        console.print(f"\n  Processing: [bold]{filename}[/bold]")
        console.print(f"    {source_label} | Type: {doc_type}")

        # Parse
        text, parser_used = parse_pdf(pdf_path)
        if not text:
            console.print(f"    [red]✗ Failed to parse[/red]")
            continue
        console.print(f"    Parser: {parser_used} | Extracted: {len(text)} chars")

        # Chunk
        chunks = route_chunker(text, doc_type)
        console.print(f"    Chunks: {len(chunks)}")

        # Tag and route to correct stream
        for chunk in chunks:
            tagged = tag_chunk_with_metadata(chunk, filename, metadata)
            if source == "registry":
                om_chunks.append(tagged)
            else:
                reference_chunks.append(tagged)

    console.print(f"\n  [green]✓[/green] OM chunks: {len(om_chunks)} | Reference chunks: {len(reference_chunks)}")
    return om_chunks, reference_chunks


# ─── Step 2 ───

def extract_structured_rules(om_chunks: list[dict]) -> list[dict]:
    """Step 2: Extract structured rules from OM chunks using LLM."""
    console.print("\n[bold cyan]═══ Step 2: Extracting Structured Rules via LLM ═══[/bold cyan]")

    if not OPENROUTER_API_KEY:
        console.print("  [red]✗ OPENROUTER_API_KEY not set — cannot extract rules[/red]")
        console.print("  [yellow]  Add OPENROUTER_API_KEY to .env and re-run.[/yellow]")
        return []

    console.print(f"  Processing {len(om_chunks)} OM chunks through LLM extraction...")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Extracting rules...", total=None)
        extracted_rules = extract_rules_batch(om_chunks)
        progress.update(task, completed=True)

    console.print(f"  [green]✓[/green] Extracted {len(extracted_rules)} structured rules")

    # Deduplicate rules with same om_id + clause_ref (keep first occurrence)
    seen = set()
    unique_rules = []
    for rule in extracted_rules:
        key = f"{rule['om_id']}_{rule['clause_ref']}"
        if key not in seen:
            seen.add(key)
            unique_rules.append(rule)
        else:
            logger.debug(f"Dedup: skipping duplicate {key}")

    if len(unique_rules) < len(extracted_rules):
        console.print(f"  Deduplicated: {len(extracted_rules)} → {len(unique_rules)} unique rules")

    return unique_rules


# ─── Step 3 ───

def ingest_structured_rules(extracted_rules: list[dict]):
    """Step 3: Embed and store extracted rules into structured_rules collection."""
    console.print("\n[bold cyan]═══ Step 3: Ingesting Structured Rules ═══[/bold cyan]")

    if not extracted_rules:
        console.print("  [yellow]⚠ No rules to ingest[/yellow]")
        return

    # Always clear before re-ingesting to avoid stale/polluted data
    console.print("  Clearing old structured_rules collection...")
    collection = clear_collection(STRUCTURED_RULES_COLLECTION)

    ids = []
    documents = []
    metadatas = []

    for rule in extracted_rules:
        rule_id = f"{rule['om_id']}_clause_{rule['clause_ref']}"

        rule_text = (
            f"OM {rule['om_number']} ({rule['date']}) - {rule['nature']}\n"
            f"Clause {rule['clause_ref']}: {rule['rule_statement']}\n"
            f"Direction: {rule['direction']}\n"
            f"Ministry must show: {rule['ministry_must_show']}"
        )

        metadata = {
            "om_id": rule["om_id"],
            "om_number": rule["om_number"],
            "clause_ref": rule["clause_ref"],
            "nature": rule["nature"],
            "direction": rule["direction"],
            "ministry_requirement": rule["ministry_must_show"],
            "applies_to": rule.get("applies_to", ""),
            "agent_scope": rule.get("agent_scope", ""),
        }

        ids.append(rule_id)
        documents.append(rule_text)
        metadatas.append(metadata)

    console.print(f"  Prepared {len(ids)} structured rule entries")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Embedding structured rules...", total=None)
        embeddings = embed_texts(documents)

    add_to_collection(collection, ids, embeddings, documents, metadatas)
    console.print(f"  [green]✓[/green] Loaded {len(ids)} rules into '{STRUCTURED_RULES_COLLECTION}'")


# ─── Step 4 ───

def ingest_om_chunks(om_chunks: list[dict]):
    """Step 4: Embed and store enriched OM chunks into om_document_chunks collection."""
    console.print("\n[bold cyan]═══ Step 4: Ingesting OM Document Chunks ═══[/bold cyan]")

    if not om_chunks:
        console.print("  [yellow]⚠ No OM chunks to ingest[/yellow]")
        return

    # Clear to avoid duplicates from previous runs
    console.print("  Clearing old om_document_chunks collection...")
    collection = clear_collection(OM_CHUNKS_COLLECTION)

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(om_chunks):
        om_id = chunk.get("om_id", "unknown")
        doc_type = chunk.get("doc_type", "unknown")
        filename = chunk.get("source_file", "unknown")

        chunk_id = f"{om_id}_{doc_type}_{filename}_{i}"
        enriched_text = prepend_context(chunk["text"], chunk)

        ids.append(chunk_id)
        documents.append(enriched_text)

        meta = {k: v for k, v in chunk.items() if k != "text"}
        metadatas.append(meta)

    console.print(f"  Embedding {len(documents)} enriched OM chunks...")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Embedding OM chunks...", total=None)
        embeddings = embed_texts(documents)

    add_to_collection(collection, ids, embeddings, documents, metadatas)
    console.print(f"  [green]✓[/green] Loaded {len(ids)} chunks into '{OM_CHUNKS_COLLECTION}'")


# ─── Step 5 ───

def ingest_reference_chunks(reference_chunks: list[dict]):
    """Step 5: Embed and store reference document chunks into reference_corpus."""
    console.print("\n[bold cyan]═══ Step 5: Ingesting Reference Documents ═══[/bold cyan]")

    if not reference_chunks:
        console.print("  [yellow]⚠ No reference chunks to ingest[/yellow]")
        return

    console.print("  Clearing old reference_corpus collection...")
    collection = clear_collection(REFERENCE_CORPUS_COLLECTION)

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(reference_chunks):
        doc_type = chunk.get("doc_type", "unknown")
        filename = chunk.get("source_file", "unknown")
        doc_title = filename.replace(".pdf", "").replace(".PDF", "").replace("_", " ")

        chunk_id = f"ref_{doc_type}_{filename}_{i}"

        # Build reference metadata for context prepending
        ref_meta = {
            "doc_title": doc_title,
            "doc_type": doc_type,
            "section": chunk.get("section_heading", ""),
        }
        enriched_text = prepend_reference_context(chunk["text"], ref_meta)

        ids.append(chunk_id)
        documents.append(enriched_text)

        # Store full metadata for retrieval filtering
        meta = {k: v for k, v in chunk.items() if k != "text"}
        meta["doc_title"] = doc_title
        metadatas.append(meta)

    console.print(f"  Embedding {len(documents)} reference chunks...")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Embedding reference chunks...", total=None)
        embeddings = embed_texts(documents)

    add_to_collection(collection, ids, embeddings, documents, metadatas)
    console.print(f"  [green]✓[/green] Loaded {len(ids)} chunks into '{REFERENCE_CORPUS_COLLECTION}'")


# ─── Stats ───

def print_stats():
    """Print final collection statistics."""
    console.print("\n[bold cyan]═══ Collection Statistics ═══[/bold cyan]")
    stats = get_collection_stats()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Collection", style="cyan")
    table.add_column("Entries", justify="right")

    for name, count in stats.items():
        table.add_row(name, str(count))

    table.add_row("[bold]Total[/bold]", f"[bold]{sum(stats.values())}[/bold]")
    console.print(table)


# ─── Main ───

def main():
    parser = argparse.ArgumentParser(description="APAS Document Ingestion Pipeline")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last run — skip clearing collections, use all caches")
    parser.add_argument("--from-step", type=int, default=1, choices=[1, 2, 3, 4, 5],
                        help="Start from this step (uses cached data for prior steps)")
    args = parser.parse_args()

    console.print("[bold green]╔══════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║   APAS Document Ingestion Pipeline v2   ║[/bold green]")
    console.print("[bold green]╚══════════════════════════════════════════╝[/bold green]")

    if args.resume:
        console.print("[yellow]  ► Resume mode — keeping existing collections[/yellow]")

    if not args.resume and args.from_step == 1:
        clear_all_collections()

    om_chunks = None
    reference_chunks = None
    extracted_rules = None

    # Step 1: Parse & chunk (split into OM + reference streams)
    if args.from_step <= 1:
        om_chunks, reference_chunks = parse_and_chunk_source_pdfs()
        _save_json(OM_CHUNKS_CACHE, om_chunks)
        _save_json(REF_CHUNKS_CACHE, reference_chunks)
        console.print(f"  [dim]Saved chunks to cache[/dim]")
    else:
        console.print(f"\n[yellow]  ► Skipping to step {args.from_step} — loading cached data[/yellow]")
        om_chunks = _load_json(OM_CHUNKS_CACHE)
        reference_chunks = _load_json(REF_CHUNKS_CACHE)
        if not om_chunks:
            console.print("  [red]✗ No cached OM chunks found. Run without --from-step first.[/red]")
            sys.exit(1)
        console.print(f"  [green]✓[/green] Loaded {len(om_chunks)} OM chunks + {len(reference_chunks or [])} reference chunks from cache")

    # Step 2: Extract structured rules (OM chunks only, uses extraction cache)
    if args.from_step <= 2:
        extracted_rules = extract_structured_rules(om_chunks)
        _save_json(RULES_CACHE_FILE, extracted_rules)

    # Step 3: Ingest structured rules
    if args.from_step <= 3:
        if not extracted_rules:
            extracted_rules = _load_json(RULES_CACHE_FILE)
        if extracted_rules:
            ingest_structured_rules(extracted_rules)
        else:
            console.print("  [yellow]⚠ No rules to ingest (no cache found)[/yellow]")

    # Step 4: Ingest OM chunks
    if args.from_step <= 4:
        ingest_om_chunks(om_chunks)

    # Step 5: Ingest reference chunks
    if args.from_step <= 5:
        if reference_chunks is None:
            reference_chunks = _load_json(REF_CHUNKS_CACHE) or []
        ingest_reference_chunks(reference_chunks)

    # Final stats
    print_stats()

    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print("Run [bold]python validate.py[/bold] to test retrieval quality.\n")


if __name__ == "__main__":
    main()
