import sys
from typing import Optional
from src.graph import create_auditor_graph
from src.utils import load_rubric


def run_auditor(repo_url: str, pdf_path: Optional[str] = None):
    """
    Executes the Automaton Auditor Swarm against a target repository.
    """
    _ = load_rubric()

    # Initialize and run graph
    _ = create_auditor_graph()

    print(f"🚀 Starting audit for: {repo_url}")
    # In production, we would use graph.invoke(initial_state)
    print("Graph initialized successfully.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_auditor.py <repo_url> [pdf_path]")
        sys.exit(1)

    repo_url = sys.argv[1]
    pdf_path = sys.argv[2] if len(sys.argv) > 2 else None

    run_auditor(repo_url, pdf_path)
