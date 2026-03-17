"""APAS Document Ingestion Pipeline — main orchestrator.

Pipeline steps:
1. Parse & chunk source OM PDFs
2. Extract structured rules via LLM (GPT-4o-mini via OpenRouter)
3. Ingest extracted rules into structured_rules collection
4. Ingest enriched OM chunks into om_document_chunks collection
5. Ingest reference documents (optional)
"""

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import (
    SOURCE_DOCS_DIR,
    REFERENCE_DOCS_DIR,
    OPENROUTER_API_KEY,
    STRUCTURED_RULES_COLLECTION,
    OM_CHUNKS_COLLECTION,
    REFERENCE_CORPUS_COLLECTION,
    LOG_LEVEL,
)
from config.document_registry import OM_REGISTRY, FILE_TO_OM_MAP
from embeddings.embedder import embed_texts
from stores.chroma_store import (
    clear_all_collections,
    get_or_create_collection,
    add_to_collection,
    get_collection_stats,
)
from parsers.pdf_parser import parse_pdf
from chunkers.chunk_router import route_chunker
from taggers.metadata_tagger import tag_chunk, tag_reference_chunk
from extractors.rule_extractor import extract_rules_batch
from enrichers.context_prepender import prepend_context, prepend_reference_context

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
console = Console()


def parse_and_chunk_source_pdfs() -> list[dict]:
    """Step 1: Parse and chunk all source OM PDFs. Returns tagged chunks in memory."""
    console.print("\n[bold cyan]═══ Step 1: Parsing & Chunking Source OM PDFs ═══[/bold cyan]")

    source_dir = Path(SOURCE_DOCS_DIR)
    if not source_dir.exists():
        console.print(f"  [yellow]⚠ Source directory not found: {source_dir}[/yellow]")
        return []

    # Find PDFs that are in our registry
    pdf_files = list(source_dir.glob("*.pdf")) + list(source_dir.glob("*.PDF"))
    registered_pdfs = [f for f in pdf_files if f.name in FILE_TO_OM_MAP]
    unregistered_pdfs = [f for f in pdf_files if f.name not in FILE_TO_OM_MAP]

    if unregistered_pdfs:
        console.print(f"  [yellow]⚠ {len(unregistered_pdfs)} PDFs not in registry (skipped):[/yellow]")
        for f in unregistered_pdfs:
            console.print(f"    - {f.name}")

    if not registered_pdfs:
        console.print("  [yellow]⚠ No registered PDFs found in source directory[/yellow]")
        return []

    console.print(f"  Found {len(registered_pdfs)} registered PDFs to process")

    all_tagged_chunks = []

    for pdf_path in registered_pdfs:
        filename = pdf_path.name
        file_info = FILE_TO_OM_MAP[filename]
        doc_type = file_info["doc_type"]

        console.print(f"\n  Processing: [bold]{filename}[/bold]")
        console.print(f"    OM: {file_info['om_id']} | Type: {doc_type}")

        # Parse
        text, parser_used = parse_pdf(pdf_path)
        if not text:
            console.print(f"    [red]✗ Failed to parse[/red]")
            continue
        console.print(f"    Parser: {parser_used} | Extracted: {len(text)} chars")

        # Chunk
        chunks = route_chunker(text, doc_type)
        console.print(f"    Chunks: {len(chunks)}")

        # Tag with metadata
        for chunk in chunks:
            tagged = tag_chunk(chunk, filename)
            all_tagged_chunks.append(tagged)

    console.print(f"\n  [green]✓[/green] Total tagged chunks: {len(all_tagged_chunks)}")
    return all_tagged_chunks


def extract_structured_rules(tagged_chunks: list[dict]) -> list[dict]:
    """Step 2: Extract structured rules from chunks using LLM."""
    console.print("\n[bold cyan]═══ Step 2: Extracting Structured Rules via LLM ═══[/bold cyan]")

    if not OPENROUTER_API_KEY:
        console.print("  [red]✗ OPENROUTER_API_KEY not set — cannot extract rules[/red]")
        console.print("  [yellow]  Add OPENROUTER_API_KEY to .env and re-run.[/yellow]")
        return []

    console.print(f"  Processing {len(tagged_chunks)} chunks through LLM extraction...")

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Extracting rules...", total=None)
        extracted_rules = extract_rules_batch(tagged_chunks)
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


def ingest_structured_rules(extracted_rules: list[dict]):
    """Step 3: Embed and store extracted rules into structured_rules collection."""
    console.print("\n[bold cyan]═══ Step 3: Ingesting Structured Rules ═══[/bold cyan]")

    if not extracted_rules:
        console.print("  [yellow]⚠ No rules to ingest[/yellow]")
        return

    collection = get_or_create_collection(STRUCTURED_RULES_COLLECTION)

    ids = []
    documents = []
    metadatas = []

    for rule in extracted_rules:
        rule_id = f"{rule['om_id']}_clause_{rule['clause_ref']}"

        # Compose rich text for embedding (same format as old hand-crafted rules)
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

    # Embed
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Embedding structured rules...", total=None)
        embeddings = embed_texts(documents)

    # Store
    add_to_collection(collection, ids, embeddings, documents, metadatas)
    console.print(f"  [green]✓[/green] Loaded {len(ids)} rules into '{STRUCTURED_RULES_COLLECTION}'")


def ingest_om_chunks(tagged_chunks: list[dict]):
    """Step 4: Embed and store enriched OM chunks into om_document_chunks collection."""
    console.print("\n[bold cyan]═══ Step 4: Ingesting OM Document Chunks ═══[/bold cyan]")

    if not tagged_chunks:
        console.print("  [yellow]⚠ No chunks to ingest[/yellow]")
        return

    collection = get_or_create_collection(OM_CHUNKS_COLLECTION)

    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(tagged_chunks):
        file_info = FILE_TO_OM_MAP.get(chunk.get("source_file", ""), {})
        om_id = chunk.get("om_id", "unknown")
        doc_type = chunk.get("doc_type", "unknown")
        filename = chunk.get("source_file", "unknown")

        chunk_id = f"{om_id}_{doc_type}_{filename}_{i}"

        # Prepend document context for better embedding
        enriched_text = prepend_context(chunk["text"], chunk)

        # Store enriched text as the document
        ids.append(chunk_id)
        documents.append(enriched_text)

        # Metadata excludes the text field
        meta = {k: v for k, v in chunk.items() if k != "text"}
        metadatas.append(meta)

    # Embed all chunks
    console.print(f"  Embedding {len(documents)} enriched chunks...")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Embedding document chunks...", total=None)
        embeddings = embed_texts(documents)

    # Store
    add_to_collection(collection, ids, embeddings, documents, metadatas)
    console.print(f"  [green]✓[/green] Loaded {len(ids)} chunks into '{OM_CHUNKS_COLLECTION}'")


def ingest_reference_docs():
    """Step 5: Parse and embed reference documents (GFR, FC reports, etc.)."""
    console.print("\n[bold cyan]═══ Step 5: Ingesting Reference Documents ═══[/bold cyan]")

    ref_dir = Path(REFERENCE_DOCS_DIR)
    if not ref_dir.exists():
        console.print(f"  [yellow]⚠ Reference directory not found: {ref_dir}[/yellow]")
        console.print("  [yellow]  This is optional — create it later to add GFR, FC reports, etc.[/yellow]")
        return

    pdf_files = list(ref_dir.glob("*.pdf")) + list(ref_dir.glob("*.PDF"))
    if not pdf_files:
        console.print("  [yellow]⚠ No reference PDFs found[/yellow]")
        return

    collection = get_or_create_collection(REFERENCE_CORPUS_COLLECTION)

    # Reference doc type inference from filename
    def infer_doc_type(name: str) -> tuple[str, list[str]]:
        name_lower = name.lower()
        if "gfr" in name_lower or "general financial" in name_lower:
            return "gfr", ["compliance", "fiscal"]
        elif "finance commission" in name_lower or "fc_report" in name_lower:
            return "fc_report", ["fiscal"]
        elif "niti" in name_lower:
            return "niti", ["sector"]
        elif "budget" in name_lower:
            return "budget", ["fiscal"]
        else:
            return "international", ["sector"]

    all_ids = []
    all_documents = []
    all_metadatas = []

    for pdf_path in pdf_files:
        filename = pdf_path.name
        doc_type, agent_scope = infer_doc_type(filename)
        doc_title = filename.replace(".pdf", "").replace(".PDF", "").replace("_", " ")

        console.print(f"\n  Processing reference: [bold]{filename}[/bold]")
        console.print(f"    Type: {doc_type} | Scope: {agent_scope}")

        text, parser_used = parse_pdf(pdf_path)
        if not text:
            console.print(f"    [red]✗ Failed to parse[/red]")
            continue
        console.print(f"    Parser: {parser_used} | Extracted: {len(text)} chars")

        chunks = route_chunker(text, doc_type)
        console.print(f"    Chunks: {len(chunks)}")

        for i, chunk in enumerate(chunks):
            tagged = tag_reference_chunk(chunk, doc_type, doc_title, agent_scope, filename)
            chunk_id = f"ref_{doc_type}_{filename}_{i}"

            # Prepend context for reference docs too
            enriched_text = prepend_reference_context(tagged["text"], tagged)

            all_ids.append(chunk_id)
            all_documents.append(enriched_text)
            meta = {k: v for k, v in tagged.items() if k != "text"}
            all_metadatas.append(meta)

    if not all_documents:
        console.print("  [yellow]⚠ No reference chunks to embed[/yellow]")
        return

    console.print(f"\n  Embedding {len(all_documents)} reference chunks...")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Embedding reference chunks...", total=None)
        embeddings = embed_texts(all_documents)

    add_to_collection(collection, all_ids, embeddings, all_documents, all_metadatas)
    console.print(f"  [green]✓[/green] Loaded {len(all_ids)} chunks into '{REFERENCE_CORPUS_COLLECTION}'")


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


def main():
    console.print("[bold green]╔══════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║   APAS Document Ingestion Pipeline v2   ║[/bold green]")
    console.print("[bold green]╚══════════════════════════════════════════╝[/bold green]")

    # Clear all collections for idempotent re-run
    clear_all_collections()

    # Step 1: Parse & chunk source PDFs (kept in memory)
    tagged_chunks = parse_and_chunk_source_pdfs()

    # Step 2: Extract structured rules via LLM
    extracted_rules = extract_structured_rules(tagged_chunks)

    # Step 3: Ingest extracted rules into structured_rules collection
    ingest_structured_rules(extracted_rules)

    # Step 4: Ingest enriched OM chunks into om_document_chunks
    ingest_om_chunks(tagged_chunks)

    # Step 5: Reference documents (optional)
    ingest_reference_docs()

    # Final stats
    print_stats()

    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print("Run [bold]python validate.py[/bold] to test retrieval quality.\n")


if __name__ == "__main__":
    main()
