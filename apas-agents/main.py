"""APAS Agent CLI — interactive query interface.

Usage:
    python main.py                  # Interactive REPL
    python main.py --query "..."    # Single query mode
"""

import argparse
import logging
import sys

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config.settings import OPENROUTER_API_KEY, AGENT_MODEL, ORCHESTRATOR_MODEL
from graph import ask

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
# Quiet down noisy loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)

console = Console()


def check_prerequisites():
    """Verify all required services are available."""
    if not OPENROUTER_API_KEY:
        console.print("[red]Error: OPENROUTER_API_KEY not set in .env[/red]")
        console.print("Add it to apas-ingestion/.env")
        sys.exit(1)

    # Check ChromaDB has data
    from tools.retrieval import _get_chroma
    client = _get_chroma()
    try:
        rules = client.get_collection("structured_rules")
        chunks = client.get_collection("om_document_chunks")
        refs = client.get_collection("reference_corpus")
        console.print(f"  Collections: rules={rules.count()}, om_chunks={chunks.count()}, reference={refs.count()}")
    except Exception as e:
        console.print(f"[red]Error: ChromaDB collections not found. Run the ingestion pipeline first.[/red]")
        console.print(f"  cd ../apas-ingestion && python pipeline.py")
        sys.exit(1)


def run_single_query(query: str):
    """Run a single query and print the response."""
    console.print(f"\n[bold cyan]Query:[/bold cyan] {query}\n")
    console.print("[dim]Routing query to specialist agents...[/dim]\n")

    try:
        response = ask(query)
        console.print(Panel(Markdown(response), title="APAS Response", border_style="green"))
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def run_interactive():
    """Interactive REPL mode."""
    console.print(Panel(
        "[bold]Welcome to APAS — AI-based Project & Scheme Appraisal System[/bold]\n\n"
        "Ask questions about government scheme appraisal rules and procedures.\n"
        f"Models: Orchestrator={ORCHESTRATOR_MODEL}, Agents={AGENT_MODEL}\n\n"
        "Type [bold]quit[/bold] or [bold]exit[/bold] to stop.",
        title="APAS Query Assistant",
        border_style="cyan",
    ))

    while True:
        try:
            query = console.input("\n[bold cyan]Your question:[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Goodbye![/dim]")
            break

        if not query:
            continue
        if query.lower() in ("quit", "exit", "q"):
            console.print("[dim]Goodbye![/dim]")
            break

        console.print("[dim]Processing...[/dim]")

        try:
            response = ask(query)
            console.print()
            console.print(Panel(Markdown(response), title="APAS Response", border_style="green"))
        except KeyboardInterrupt:
            console.print("\n[yellow]Query interrupted.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")


def main():
    parser = argparse.ArgumentParser(description="APAS Agent CLI")
    parser.add_argument("--query", "-q", type=str, help="Single query mode")
    args = parser.parse_args()

    console.print("[bold green]╔══════════════════════════════════════════╗[/bold green]")
    console.print("[bold green]║    APAS Agent System v1                  ║[/bold green]")
    console.print("[bold green]╚══════════════════════════════════════════╝[/bold green]")

    check_prerequisites()

    if args.query:
        run_single_query(args.query)
    else:
        run_interactive()


if __name__ == "__main__":
    main()
