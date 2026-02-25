import os
import git
import base64
import fitz  # PyMuPDF
import tempfile
import shutil
from typing import Dict, Any, List
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


def clone_to_temp_dir(repo_url: str) -> str:
    """
    Clones a remote repository to a temporary directory.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"📥 Cloning {repo_url} to {temp_dir}...")
        git.Repo.clone_from(repo_url, temp_dir, depth=1)
        return temp_dir
    except git.exc.GitCommandError as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        msg = f"Git clone failed (check URL/auth): {e.stderr or str(e)}"
        raise RuntimeError(msg)
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Unexpected error during clone: {str(e)}")


def cleanup_sandboxed_repo(path: str) -> bool:
    """
    Removes a temporary repository directory.
    """
    if os.path.exists(path) and "tmp" in path:
        try:
            shutil.rmtree(path, ignore_errors=True)
            return True
        except Exception:
            return False
    return False


def parse_ast_for_forensics(file_path: str) -> Dict[str, Any]:
    """
    Parses a Python file to find specific forensic patterns.
    """
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    with open(file_path, "rb") as f:
        content = f.read()
        tree = parser.parse(content)

    # Queries for deep forensics
    query = Query(
        PY_LANGUAGE,
        """
        ; Classes and Inheritance (Master Thinker)
        (class_definition
            (identifier) @class_name
            superinterfaces: (argument_list (identifier) @base_class)?
        )

        ; Method Calls (e.g. add_node, add_edge)
        (call
            function: (attribute attribute: (identifier) @method_call)
        )

        ; Decorators
        (decorator (identifier) @decorator_name)
        (decorator (call function: (identifier) @decorator_name))
        """,
    )

    cursor = QueryCursor(query)
    captures = cursor.captures(tree.root_node)

    found_classes: list[str] = []
    found_bases: list[str] = []
    found_calls: list[str] = []
    found_decs: list[str] = []

    for node in captures.get("class_name", []):
        found_classes.append(node.text.decode("utf8"))

    for node in captures.get("base_class", []):
        found_bases.append(node.text.decode("utf8"))

    for node in captures.get("method_call", []):
        found_calls.append(node.text.decode("utf8"))

    for node in captures.get("decorator_name", []):
        found_decs.append(node.text.decode("utf8"))

    # Forensic heuristics
    has_pydantic = "BaseModel" in found_bases
    is_state_machine = any(
        c in found_calls for c in ["add_node", "add_edge", "compile"]
    )

    return {
        "classes": found_classes,
        "base_classes": found_bases,
        "method_calls": found_calls,
        "decorators": found_decs,
        "pydantic_score": 1.0 if has_pydantic else 0.0,
        "state_machine_score": 1.0 if is_state_machine else 0.0,
    }


def extract_images_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts images from a PDF and returns them as base64 strings.
    """
    if not os.path.exists(pdf_path):
        return []

    images = []
    try:
        doc = fitz.open(pdf_path)
        for i in range(len(doc)):
            for img in doc.get_page_images(i):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]

                # Encode to base64
                b64 = base64.b64encode(image_bytes).decode("utf-8")
                images.append(
                    {
                        "page": i + 1,
                        "mime": base_image["ext"],
                        "base64": b64,
                    }
                )
        doc.close()
    except Exception as e:
        print(f"⚠️ Error extracting images: {str(e)}")

    return images


def ingest_pdf_content(pdf_path: str) -> Dict[str, Any]:
    """
    Placeholder for PDF ingestion.
    Actual implementation will use runners/run_doc_analyst.py via subprocess.
    """
    # This will be wired in DocAnalyst node
    return {"status": "pending_subprocess_call"}
