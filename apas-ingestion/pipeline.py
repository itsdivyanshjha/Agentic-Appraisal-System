"""APAS Document Ingestion Pipeline — main orchestrator."""

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from config.settings import (
    SOURCE_DOCS_DIR,
    REFERENCE_DOCS_DIR,
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

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
console = Console()


def ingest_structured_rules():
    """Step 1: Flatten OM_REGISTRY key_rules into structured_rules collection."""
    console.print("\n[bold cyan]═══ Step 1: Ingesting Structured Rules ═══[/bold cyan]")

    collection = get_or_create_collection(STRUCTURED_RULES_COLLECTION)

    ids = []
    documents = []
    metadatas = []

    for om in OM_REGISTRY:
        om_id = om["id"]
        om_number = om["om_number"]
        nature = om["nature"]
        applies_to = ",".join(om["applies_to"])
        agent_scope = ",".join(om["agent_scope"])

        for rule in om["key_rules"]:
            rule_id = f"{om_id}_clause_{rule['clause']}"

            # Compose a rich text representation for embedding
            rule_text = (
                f"OM {om_number} ({om['date']}) - {nature}\n"
                f"Clause {rule['clause']}: {rule['rule']}\n"
                f"Direction: {rule['direction']}\n"
                f"Ministry must show: {rule['ministry_must_show']}"
            )

            metadata = {
                "om_id": om_id,
                "om_number": om_number,
                "clause_ref": rule["clause"],
                "nature": nature,
                "direction": rule["direction"],
                "ministry_requirement": rule["ministry_must_show"],
                "applies_to": applies_to,
                "agent_scope": agent_scope,
            }

            ids.append(rule_id)
            documents.append(rule_text)
            metadatas.append(metadata)

    console.print(f"  Prepared {len(ids)} structured rule entries from {len(OM_REGISTRY)} OMs")

    # Embed all rules
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Embedding structured rules...", total=None)
        embeddings = embed_texts(documents)

    # Store in ChromaDB
    add_to_collection(collection, ids, embeddings, documents, metadatas)
    console.print(f"  [green]✓[/green] Loaded {len(ids)} rules into '{STRUCTURED_RULES_COLLECTION}'")


def ingest_source_pdfs():
    """Step 2: Parse, chunk, tag, and embed source OM PDFs."""
    console.print("\n[bold cyan]═══ Step 2: Ingesting Source OM PDFs ═══[/bold cyan]")

    source_dir = Path(SOURCE_DOCS_DIR)
    if not source_dir.exists():
        console.print(f"  [yellow]⚠ Source directory not found: {source_dir}[/yellow]")
        console.print("  [yellow]  Create it and add PDFs, then re-run.[/yellow]")
        return

    collection = get_or_create_collection(OM_CHUNKS_COLLECTION)

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
        return

    console.print(f"  Found {len(registered_pdfs)} registered PDFs to process")

    all_ids = []
    all_documents = []
    all_metadatas = []
    all_embeddings = []

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

        # Tag
        tagged_chunks = [tag_chunk(c, filename) for c in chunks]

        # Prepare for embedding
        for i, tc in enumerate(tagged_chunks):
            chunk_id = f"{file_info['om_id']}_{doc_type}_{filename}_{i}"
            all_ids.append(chunk_id)
            all_documents.append(tc["text"])
            # Remove 'text' from metadata (stored as document)
            meta = {k: v for k, v in tc.items() if k != "text"}
            all_metadatas.append(meta)

    if not all_documents:
        console.print("  [yellow]⚠ No chunks to embed[/yellow]")
        return

    # Embed all chunks
    console.print(f"\n  Embedding {len(all_documents)} chunks...")
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("Embedding document chunks...", total=None)
        all_embeddings = embed_texts(all_documents)

    # Store
    add_to_collection(collection, all_ids, all_embeddings, all_documents, all_metadatas)
    console.print(f"  [green]✓[/green] Loaded {len(all_ids)} chunks into '{OM_CHUNKS_COLLECTION}'")


def ingest_reference_docs():
    """Step 3: Parse and embed reference documents (GFR, FC reports, etc.)."""
    console.print("\n[bold cyan]═══ Step 3: Ingesting Reference Documents ═══[/bold cyan]")

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
            all_ids.append(chunk_id)
            all_documents.append(tagged["text"])
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
    console.print("[bold green]║   APAS Document Ingestion Pipeline      ║[/bold green]")
    console.print("[bold green]╚══════════════════════════════════════════╝[/bold green]")

    # Clear all collections for idempotent re-run
    clear_all_collections()

    # Step 1: Structured rules (always runs — no PDFs needed)
    ingest_structured_rules()

    # Step 2: Source OM PDFs
    ingest_source_pdfs()

    # Step 3: Reference documents
    ingest_reference_docs()

    # Final stats
    print_stats()

    console.print("\n[bold green]Pipeline complete![/bold green]")
    console.print("Run [bold]python validate.py[/bold] to test retrieval quality.\n")


if __name__ == "__main__":
    main()
