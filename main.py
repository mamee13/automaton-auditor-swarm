import argparse
import os
import sys
import uuid
import warnings
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from src.graph import create_auditor_graph
from src.utils import load_rubric

# Silence Pydantic serialization warnings (internal LangChain/OpenRouter conflict)
warnings.filterwarnings("ignore", message="Pydantic serialization warnings")

# Initialize Rich console
console = Console()


def parse_args():
    parser = argparse.ArgumentParser(
        description="⚖️ Automaton Auditor Swarm - AI-Powered Forensic Auditing"
    )
    parser.add_argument("--repo", help="URL of the GitHub repository to audit")
    parser.add_argument("--report", help="Path to the PDF report to audit")
    parser.add_argument(
        "--batch",
        help="Path to a JSON file for batch processing multiple URLs",
    )
    parser.add_argument(
        "--onself",
        action="store_true",
        help="Run audit on this repository itself",
    )
    return parser.parse_args()


def main():
    # 1. Load Environment Variables
    load_dotenv()
    if not os.getenv("OPENROUTER_API_KEY"):
        console.print(
            "[red]Error: OPENROUTER_API_KEY not found in environment.[/red]",
        )
        sys.exit(1)

    # 2. Parse CLI Arguments
    args = parse_args()

    # 3. Handle Batch vs Single Mode
    batch_urls = []
    pdf_path = None

    if args.onself:
        batch_urls = ["https://github.com/mamee13/automaton-auditor-swarm"]
        is_self_audit = True
    elif args.batch:
        import json

        is_self_audit = False

        try:
            with open(args.batch, "r") as f:
                batch_data = json.load(f)
                batch_urls = (
                    batch_data
                    if isinstance(batch_data, list)
                    else batch_data.get("urls", [])
                )
        except Exception as e:
            console.print(f"[red]Error loading batch file: {str(e)}[/red]")
            sys.exit(1)
    elif args.repo:
        batch_urls = [args.repo]
        pdf_path = args.report
        is_self_audit = False
    else:
        console.print(
            "[yellow]Usage: uv run main.py --repo <URL> "
            "[--report <PDF_PATH>] or --batch <FILE> or --onself[/yellow]"
        )
        sys.exit(0)

    # 4. Initialize State
    console.print(Panel("[bold green]⚖️ Initializing Swarm[/bold green]"))

    try:
        rubric = load_rubric()
    except Exception as e:
        console.print(f"[red]Error loading rubric: {str(e)}[/red]")
        sys.exit(1)

    initial_state = {
        "batch_urls": batch_urls,
        "current_url_index": 0,
        "rubric": rubric,
        "pdf_path": pdf_path,
        "is_self_audit": is_self_audit,
        "evidences": {},
        "opinions": [],
        "audit_data": None,
        "final_report": None,
    }

    # 5. Build and Run Graph
    try:
        graph = create_auditor_graph()
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        console.print(
            f"🚀 Starting audit swarm for {len(batch_urls)} "
            "target(s)...",  # noqa: E501
        )

        # Invoke the graph (batch mode handles the loop via conditional edges)
        result = graph.invoke(initial_state, config=config)

        console.print("\n[bold green]✅ Audit Swarm Complete![/bold green]")
        if result.get("final_report"):
            console.print(
                f"\n[bold]Final Report Summary:[/bold]\n"
                f"{result['final_report'][:500]}..."
            )
            console.print(
                "\n[blue]Full report saved in 'audit/' directory.[/blue]",  # noqa: E501
            )

    except Exception as e:
        console.print(f"[red]Execution failed: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
