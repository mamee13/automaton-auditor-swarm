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
    repo_url = state.get("repo_url")
    target_path = state.get("target_path")

    # If repo_url is provided but target_path is not, clone it
    if repo_url and not target_path:
        from src.tools.forensics import clone_to_temp_dir

        try:
            target_path = clone_to_temp_dir(repo_url)
            # Update state with target_path for other tools/nodes
        except Exception as e:
            return {
                "evidences": {
                    "forensic_accuracy_code": [
                        Evidence(
                            goal="Clone and analyze repository",
                            found=False,
                            content=str(e),
                            location=repo_url,
                            rationale="Git clone failed.",
                            confidence=1.0,
                        )
                    ]
                }
            }

    path = target_path or "."
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

    return {
        "evidences": {"forensic_accuracy_code": [evidence]},
        "target_path": path,  # Share the cloned path with other nodes
    }


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
    Uses multimodal LLM capabilities.
    """
    pdf_path = state.get("pdf_path")
    if not pdf_path:
        return {"evidences": {}}

    print(f"🕵️ VisionInspector analyzing diagrams in: {pdf_path}")

    from src.tools.forensics import extract_images_from_pdf
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage

    images = extract_images_from_pdf(pdf_path)
    if not images:
        print("⚠️ No images found in PDF.")
        return {"evidences": {}}

    # Initialize Multimodal Model
    vision_model = ChatOpenAI(model="gpt-4o", temperature=0)

    vision_evidences = []
    for i, img in enumerate(images[:3]):  # Limit to 3 images for efficiency
        print(f"👁️ Analyzing Image {i+1} on Page {img['page']}...")

        img_b64 = img["base64"]
        img_mime = img["mime"]
        # Use variable to keep line length short for flake8/black
        image_data_url = f"data:image/{img_mime};base64,{img_b64}"

        prompt = [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "Analyze this architectural diagram. Is it a "
                        "LangGraph State Machine diagram? Does it explicitly "
                        "visualize parallel split (fan-out) for Detectives or "
                        "Judges? Describe the flow structure "
                        "(Linear vs Swarm).",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ]
            )
        ]

        try:
            response = vision_model.invoke(prompt)
            content = response.content

            evidence = Evidence(
                goal="Verify Swarm Visual flow in diagrams",
                found=True,
                content=str(content),
                location=f"{pdf_path} page {img['page']}",
                rationale="Multimodal analysis of extracted diagram.",
                confidence=0.85,
            )
            vision_evidences.append(evidence)
        except Exception as e:
            print(f"⚠️ vision_inspector error on image {i+1}: {str(e)}")

    return {"evidences": {"vision_accuracy": vision_evidences}}
