import os
import git
from typing import Dict, Any
from tree_sitter import Language, Parser, Query, QueryCursor
import tree_sitter_python as tspython

# Initialize Tree-Sitter
PY_LANGUAGE = Language(tspython.language())
parser = Parser(PY_LANGUAGE)


def analyze_git_history(repo_path: str) -> Dict[str, Any]:
    """
    Analyzes the git history of a local repository.
    """
    try:
        repo = git.Repo(repo_path)
        commits = list(repo.iter_commits())
        authors = {c.author.name for c in commits}

        latest = commits[0].authored_datetime if commits else None
        return {
            "commit_count": len(commits),
            "author_count": len(authors),
            "latest_commit": str(latest),
            "is_dirty": repo.is_dirty(),
        }
    except Exception as e:
        return {"error": f"Git analysis failed: {str(e)}"}


def parse_ast_for_forensics(file_path: str) -> Dict[str, Any]:
    """
    Parses a Python file using tree-sitter to find Pydantic models
    and interesting patterns.
    """
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    with open(file_path, "rb") as f:
        content = f.read()
        tree = parser.parse(content)

    # Basic forensic check: count class and function definitions
    query = Query(
        PY_LANGUAGE,
        """
    (class_definition (identifier) @class_name)
    (function_definition (identifier) @func_name)
    """,
    )

    # Execute query using QueryCursor for 0.22+
    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)

    # In tree-sitter 0.25+, captures() returns a Dict[str, List[Node]]
    found_classes = []
    found_funcs = []

    for node in captures.get("class_name", []):
        found_classes.append(node.text.decode("utf8"))

    for node in captures.get("func_name", []):
        found_funcs.append(node.text.decode("utf8"))

    # Pydantic score: check if any class inherits from BaseModel
    has_pydantic = "BaseModel" in content.decode("utf8")

    return {
        "classes": found_classes,
        "functions": found_funcs,
        "pydantic_score": 1.0 if has_pydantic else 0.0,
    }


def ingest_pdf_content(pdf_path: str) -> Dict[str, Any]:
    """
    Placeholder for PDF ingestion.
    Actual implementation will use runners/run_doc_analyst.py via subprocess.
    """
    # This will be wired in DocAnalyst node
    return {"status": "pending_subprocess_call"}
