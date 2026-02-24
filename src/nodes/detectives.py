import subprocess
import json
import os
from typing import Dict, Any
from src.state import AgentState, Evidence
from src.tools.forensics import analyze_git_history, parse_ast_for_forensics


def repo_investigator(state: AgentState) -> Dict[str, Any]:
    """
    Detective node that analyzes local repository structure,
    AST for forensic patterns, and Git history.
    """
    path = state.get("target_path", ".")
    print(f"🕵️ RepoInvestigator scanning: {path}")

    # Analyze Git
    git_data = analyze_git_history(path)

    # Analyze core files (heuristic)
    ast_data = {}
    core_files = ["src/state.py", "src/graph.py", "src/utils.py"]
    for f in core_files:
        full_path = os.path.join(path, f)
        if os.path.exists(full_path):
            ast_data[f] = parse_ast_for_forensics(full_path)

    content_dict = {
        "git": git_data,
        "ast": ast_data,
    }

    evidence = Evidence(
        goal="Verify production-grade engineering (State models, Sandboxing)",
        found=True if ast_data else False,
        content=str(content_dict),
        location="repository root",
        rationale="Analyzing Git history and AST patterns.",
        confidence=0.9,
    )

    # Aggregate into evidences dict
    return {"evidences": {"forensic_accuracy_code": [evidence]}}


def doc_analyst(state: AgentState) -> Dict[str, Any]:
    """
    Detective node that parses PDFs by invoking the isolated docling
    environment via subprocess.
    """
    pdf_path = state.get("pdf_path")
    if not pdf_path:
        return {"evidences": {}}

    print(f"🕵️ DocAnalyst parsing PDF: {pdf_path}")

    # Run the isolated docling runner
    try:
        runner = "runners/run_doc_analyst.py"
        result = subprocess.run(
            ["envs/docling/bin/python", runner, pdf_path],
            capture_output=True,
            check=True,
            text=True,
        )
        doc_data = json.loads(result.stdout)
    except Exception as e:
        doc_data = {"error": f"DocAnalyst subprocess failed: {str(e)}"}

    evidence = Evidence(
        goal="Ingest PDF for forensic verification",
        found="error" not in doc_data,
        content=str(doc_data),
        location=pdf_path,
        rationale="Invoking isolated docling environment for PDF parsing.",
        confidence=0.8,
    )

    return {"evidences": {"forensic_accuracy_docs": [evidence]}}


def vision_inspector(state: AgentState) -> Dict[str, Any]:
    """
    Detective node that extracts and analyzes images/diagrams from PDFs.
    """
    print("🕵️ VisionInspector: Logic pending implementation")
    return {"evidences": {}}
