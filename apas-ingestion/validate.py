"""Post-ingestion validation — test queries per agent scope."""

import logging
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config.settings import (
    STRUCTURED_RULES_COLLECTION,
    OM_CHUNKS_COLLECTION,
    REFERENCE_CORPUS_COLLECTION,
    LOG_LEVEL,
)
from config.document_registry import AGENT_RETRIEVAL_CONFIG
from embeddings.embedder import embed_single
from stores.chroma_store import get_or_create_collection, query_collection, get_collection_stats

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)
console = Console()

TEST_QUERIES = [
    # Compliance Agent scope
    {"query": "Is in-principle approval mandatory for new schemes?", "expected_scope": "compliance", "expected_om": "OM-1"},
    {"query": "What is the 5.5x eligible outlay rule?", "expected_scope": "compliance", "expected_om": "OM-5"},
    {"query": "What happens if a ministry exceeds 20% cost escalation?", "expected_scope": "compliance", "expected_om": "OM-1"},
    {"query": "What are the approval thresholds based on cost?", "expected_scope": "compliance", "expected_om": "OM-1"},
    {"query": "Is OOMF submission required for continuation schemes?", "expected_scope": "compliance", "expected_om": "OM-3"},
    {"query": "What is the EFC threshold for scheme appraisal?", "expected_scope": "compliance", "expected_om": "OM-6"},
    # Fiscal Agent scope
    {"query": "What is the approval authority for a 600 crore scheme?", "expected_scope": "fiscal", "expected_om": "OM-1"},
    {"query": "How is Centre-State funding ratio determined for CSS?", "expected_scope": "fiscal", "expected_om": "OM-5"},
    # Cross-agent queries
    {"query": "What must a ministry submit for scheme continuation into XVI FC?", "expected_scope": "compliance", "expected_om": "OM-5"},
    {"query": "What are the risk flags for scheme performance assessment?", "expected_scope": "sector", "expected_om": "OM-3"},
]


def run_query(query_info: dict) -> dict:
    """Run a single test query and return results."""
    query = query_info["query"]
    scope = query_info["expected_scope"]
    expected_om = query_info["expected_om"]

    # Get agent config
    agent_config = AGENT_RETRIEVAL_CONFIG.get(scope, AGENT_RETRIEVAL_CONFIG["compliance"])
    primary_collection_name = agent_config["primary_collection"]
    top_k = min(agent_config["top_k"], 5)

    # Embed query
    query_embedding = embed_single(query)

    # Query primary collection
    primary_collection = get_or_create_collection(primary_collection_name)

    # Query without metadata filter first, then filter results in Python
    # (ChromaDB $contains doesn't work reliably on comma-separated strings)
    results = query_collection(
        primary_collection,
        query_embedding,
        n_results=top_k * 2,  # fetch extra to compensate for post-filtering
    )

    # Check if expected OM appears in results
    found_expected = False
    top_results = []

    if results and results["ids"] and results["ids"][0]:
        for i, (doc_id, doc, meta, dist) in enumerate(zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )):
            om_id = meta.get("om_id", "unknown")
            similarity = 1 - dist  # ChromaDB cosine distance -> similarity
            if om_id == expected_om:
                found_expected = True
            top_results.append({
                "rank": i + 1,
                "om_id": om_id,
                "clause_ref": meta.get("clause_ref", meta.get("section_heading", "")),
                "similarity": similarity,
                "text_preview": doc[:120] + "..." if len(doc) > 120 else doc,
            })

    return {
        "query": query,
        "scope": scope,
        "expected_om": expected_om,
        "collection": primary_collection_name,
        "found_expected": found_expected,
        "results": top_results[:3],
    }


def main():
    console.print("[bold green]╔══════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║   APAS Retrieval Validation             ║[/bold green]")
    console.print("[bold green]╚══════════════════════════════════════════╝[/bold green]")

    # Print collection stats
    stats = get_collection_stats()
    console.print("\n[bold]Collection counts:[/bold]")
    for name, count in stats.items():
        console.print(f"  {name}: {count}")

    if all(c == 0 for c in stats.values()):
        console.print("\n[red]No data in collections! Run pipeline.py first.[/red]")
        sys.exit(1)

    # Run queries
    console.print(f"\n[bold cyan]Running {len(TEST_QUERIES)} test queries...[/bold cyan]\n")

    passed = 0
    failed = 0

    for i, query_info in enumerate(TEST_QUERIES, 1):
        result = run_query(query_info)

        status = "[green]PASS[/green]" if result["found_expected"] else "[red]FAIL[/red]"
        if result["found_expected"]:
            passed += 1
        else:
            failed += 1

        console.print(f"{'─' * 80}")
        console.print(f"[bold]Query {i}:[/bold] {result['query']}")
        console.print(f"  Scope: {result['scope']} | Expected: {result['expected_om']} | Collection: {result['collection']} | {status}")

        if result["results"]:
            table = Table(show_header=True, header_style="dim", box=None, pad_edge=False)
            table.add_column("#", width=3)
            table.add_column("OM", width=6)
            table.add_column("Clause", width=15)
            table.add_column("Score", width=6)
            table.add_column("Preview", max_width=50)

            for r in result["results"]:
                score_str = f"{r['similarity']:.3f}"
                match_marker = " ✓" if r["om_id"] == result["expected_om"] else ""
                table.add_row(
                    str(r["rank"]),
                    r["om_id"] + match_marker,
                    str(r["clause_ref"])[:15],
                    score_str,
                    r["text_preview"][:50],
                )
            console.print(table)
        else:
            console.print("  [yellow]No results returned[/yellow]")

    # Summary
    console.print(f"\n{'═' * 80}")
    console.print(f"[bold]Results: {passed}/{passed + failed} passed[/bold]")
    if failed:
        console.print(f"[red]{failed} queries did not find expected OM in top results[/red]")
    else:
        console.print("[green]All queries matched expected OMs![/green]")


if __name__ == "__main__":
    main()
