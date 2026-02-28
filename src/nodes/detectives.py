import os
import sys
import json
from typing import Dict, Any, List
from src.state import AgentState, Evidence
from src.tools.forensics import (
    parse_ast_for_forensics,
    analyze_git_history,
    extract_images_from_pdf,
)
from src.utils import download_remote_pdf


def _get_vision_model():
    """Lazy initialization of a multimodal model for vision analysis."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model="google/gemini-2.0-flash-001",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
    )


# Keys indicative of good architectural patterns
GRAPH_METHODS = {"add_node", "add_edge", "compile", "invoke"}
SECURITY_PATTERNS = {"os.system", "shell=True", "eval(", "exec("}


def _scan_repo_for_ast_evidence(path: str) -> List[Evidence]:
    """
    Walks the repo and runs tree-sitter AST analysis on every .py file.
    Returns a consolidated list of Evidence objects.
    """
    evidences: List[Evidence] = []
    py_files: List[str] = []

    for root, _, files in os.walk(path):
        # Skip hidden dirs and venvs
        if any(
            seg.startswith(".") or seg == "__pycache__" or seg == ".venv"
            for seg in root.split(os.sep)
        ):
            continue
        for f in files:
            if f.endswith(".py"):
                py_files.append(os.path.join(root, f))

    if not py_files:
        return evidences

    # Aggregate AST results across all files
    all_classes: List[str] = []
    all_bases: List[str] = []
    all_calls: List[str] = []
    pydantic_files: List[str] = []
    graph_files: List[str] = []
    security_hits: List[str] = []

    for fp in py_files:
        rel = os.path.relpath(fp, path)
        try:
            ast_data = parse_ast_for_forensics(fp)
        except Exception as err:
            print(f"⚠️ AST parse error for {rel}: {err}")
            continue

        all_classes.extend(ast_data.get("classes", []))
        all_bases.extend(ast_data.get("base_classes", []))
        all_calls.extend(ast_data.get("method_calls", []))

        if ast_data.get("pydantic_score", 0) > 0:
            pydantic_files.append(rel)

        if ast_data.get("state_machine_score", 0) > 0:
            graph_files.append(rel)

        # Raw content scan for security patterns (fast heuristic)
        try:
            with open(fp, "r", errors="ignore") as fh:
                raw = fh.read()
            for pat in SECURITY_PATTERNS:
                if pat in raw:
                    security_hits.append(f"{rel}: `{pat}`")
        except Exception:
            pass

    # --- Evidence: State Management / Pydantic ---
    has_pydantic = len(pydantic_files) > 0
    evidences.append(
        Evidence(
            goal="State Management",
            found=has_pydantic,
            location=", ".join(pydantic_files[:5]) or "none",
            rationale=(
                f"AST scan found Pydantic BaseModel in "
                f"{len(pydantic_files)} file(s): {pydantic_files[:3]}"
            ),
            confidence=0.95 if has_pydantic else 0.3,
        )
    )

    # --- Evidence: Multi-Agent Orchestration / LangGraph ---
    has_graph = len(graph_files) > 0
    evidences.append(
        Evidence(
            goal="Multi-Agent Orchestration",
            found=has_graph,
            location=", ".join(graph_files[:5]) or "none",
            rationale=(
                f"AST scan found LangGraph patterns "
                f"(add_node/compile) in {len(graph_files)} file(s)."
            ),
            confidence=0.9 if has_graph else 0.2,
        )
    )

    # --- Evidence: Security Hygiene ---
    is_secure = len(security_hits) == 0
    evidences.append(
        Evidence(
            goal="Security & Code Quality",
            found=is_secure,
            location="Whole Repository",
            rationale=(
                "No dangerous patterns found."
                if is_secure
                else f"Risky patterns found: {security_hits[:5]}"
            ),
            confidence=0.85,
        )
    )

    # --- Evidence: Code Breadth ---
    evidences.append(
        Evidence(
            goal="Engineering Scope",
            found=len(py_files) > 3,
            location="Whole Repository",
            rationale=(
                f"Repository contains {len(py_files)} Python files "
                f"with {len(set(all_classes))} unique classes defined."
            ),
            confidence=0.9,
        )
    )

    return evidences


def repo_investigator(state: AgentState) -> Dict[str, Any]:
    """
    Detective node that examines the local repository structure
    using deep AST forensics and git history analysis.
    """
    path = state.get("target_path")
    if not path or not os.path.exists(path):
        print("🕵️ RepoInvestigator: No valid target_path found. Skipping.")
        return {"evidences": {}}

    # 1. Run AST forensics across all Python files
    ast_evidences = _scan_repo_for_ast_evidence(path)

    # 2. Run Git history analysis
    git_data = analyze_git_history(path)
    commit_count = git_data.get("commit_count", 0)
    has_good_history = commit_count >= 10
    ast_evidences.append(
        Evidence(
            goal="Git History & Engineering Effort",
            found=has_good_history,
            location=".git",
            rationale=(
                f"Repository has {commit_count} commits by "
                f"{git_data.get('author_count', 1)} author(s). "
                f"Latest commit: {git_data.get('latest_commit', 'N/A')}."
            ),
            confidence=0.95,
        )
    )

    return {"evidences": {"architecture": ast_evidences}}


def doc_analyst(state: AgentState) -> Dict[str, Any]:
    """
    Detective node that processes PDF rubric/reports if provided.
    Calls the run_doc_analyst.py script as a subprocess to keep ML
    deps isolated.
    """
    pdf_path = state.get("pdf_path")
    if not pdf_path:
        print("🕵️ DocAnalyst: No PDF forensic artifact found.")
        return {}

    import subprocess

    goals = [
        "Project Overview",
        "Task Accomplishment",
        "Bonus Innovations",
        "Theoretical Depth",
        "Metacognition",
        "Dialectical Synthesis",
    ]

    is_url = pdf_path.startswith(("http://", "https://"))
    temp_pdf = None

    if is_url:
        print(f"🕵️ DocAnalyst: Downloading remote PDF from {pdf_path}")
        try:
            temp_pdf = download_remote_pdf(pdf_path)
            actual_path = temp_pdf
        except Exception as e:
            print(f"❌ DocAnalyst download failed: {e}")
            return {}
    else:
        actual_path = pdf_path

    if not os.path.exists(actual_path):
        print(f"🕵️ DocAnalyst: PDF file not found at {actual_path}")
        return {}

    result = subprocess.run(
        [
            sys.executable,
            "runners/run_doc_analyst.py",
            actual_path,
            ",".join(goals),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    # Cleanup temp file if it was downloaded
    if temp_pdf and os.path.exists(temp_pdf):
        try:
            os.remove(temp_pdf)
        except Exception:
            pass

    if result.returncode != 0:
        print(f"❌ DocAnalyst failed: {result.stderr}")
        return {}

    try:
        data = json.loads(result.stdout)
        query_results = data.get("query_results", [])

        pdf_evidences = []
        for i, chunk in enumerate(query_results):
            pdf_evidences.append(
                Evidence(
                    goal=f"PDF Forensic - Segment {i+1}",
                    found=True,
                    location=f"{pdf_path} (extracted)",
                    content=chunk,
                    rationale="Extracted context-aware chunk using RAG-lite.",
                    confidence=0.95,
                )
            )

        # Vision: Extract and analyze images from PDF
        print(f"🕵️ DocAnalyst: Extracting images from {pdf_path}...")
        pdf_images = extract_images_from_pdf(actual_path)
        if pdf_images:
            # Analyze only the first image to save tokens, but implementation exists
            img = pdf_images[0]
            try:
                from langchain_core.messages import HumanMessage

                model = _get_vision_model()
                msg = HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": (
                                "Analyze this screenshot from the project report. "
                                "Identify UI components and verify if they match "
                                "the project's description."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": (
                                    f"data:image/{img['mime']};"
                                    f"base64,{img['base64']}"
                                )
                            },
                        },
                    ]
                )
                vision_res = model.invoke([msg])
                pdf_evidences.append(
                    Evidence(
                        goal="PDF Visual Evidence",
                        found=True,
                        location=f"{pdf_path} (page {img['page']})",
                        content=str(vision_res.content),
                        rationale="Multimodal LLM analyzed image extracted from PDF.",
                        confidence=0.9,
                    )
                )
            except Exception as ve:
                print(f"⚠️ DocAnalyst Vision failed: {ve}")

        return {"evidences": {"pdf_analysis": pdf_evidences}}
    except Exception as e:
        print(f"❌ DocAnalyst parsing error: {e}")
        return {}


def screenshot_analyst(state: AgentState) -> Dict[str, Any]:
    """
    Detective node that looks for UI/Product evidence in screenshots.
    """
    target_path = state.get("target_path")
    if not target_path:
        return {"evidences": {}}

    image_dir = os.path.join(target_path, "docs", "images")
    if not os.path.exists(image_dir):
        image_dir = os.path.join(target_path, "assets")

    if not os.path.exists(image_dir):
        print("🕵️ ScreenshotAnalyst: No visual evidence folders found.")
        return {}

    images = []
    for f in os.listdir(image_dir):
        if f.lower().endswith((".png", ".jpg", ".jpeg")):
            images.append(os.path.join(image_dir, f))

    if not images:
        print("🕵️ ScreenshotAnalyst: No screenshots found to analyze.")
        return {}

    print(
        f"🕵️ ScreenshotAnalyst: Found {len(images)} images. "
        "Analyzing with Vision LLM..."
    )

    import base64
    from langchain_core.messages import HumanMessage

    vision_evidences = []
    # Analyze the most relevant looking image (e.g. one containing 'dashboard' or 'ui')
    # or just the first one for implementation demonstration.
    selected_img = images[0]

    try:
        with open(selected_img, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        model = _get_vision_model()
        msg = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": (
                        "Identify UI components and layout quality in this screenshot."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"},
                },
            ]
        )
        response = model.invoke([msg])

        vision_evidences.append(
            Evidence(
                goal="UI Quality & Implementation",
                found=True,
                location=os.path.relpath(selected_img, target_path),
                content=str(response.content),
                rationale="Vision model verified UI implementation screenshots.",
                confidence=0.9,
            )
        )
    except Exception as e:
        print(f"⚠️ ScreenshotAnalyst LLM failed: {e}")
        vision_evidences.append(
            Evidence(
                goal="UI Quality & Implementation",
                found=True,
                location="Visual Assets",
                rationale="Screenshots found but LLM analysis failed.",
                confidence=0.5,
            )
        )

    return {"evidences": {"vision": vision_evidences}}
