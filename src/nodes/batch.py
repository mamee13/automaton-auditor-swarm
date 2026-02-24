from typing import Dict, Any, Literal
from src.state import AgentState


def prepare_audit(state: AgentState) -> Dict[str, Any]:
    """
    Sets the next URL from the batch and prepares the state
    for a fresh iteration.
    """
    urls = state.get("batch_urls", [])
    index = state.get("current_url_index", 0)

    if index < len(urls):
        url = urls[index]
        print(f"📦 Batch: Preparing audit for {url} ({index+1}/{len(urls)})")
        return {
            "repo_url": url,
            "current_url_index": index + 1,
            "evidences": {},  # Reset for new run
            "opinions": [],  # Reset for new run
            "audit_data": None,
            "final_report": None,
        }
    return {}


def batch_router(state: AgentState) -> Literal["continue", "end"]:
    """
    Determines if more URLs need to be processed.
    """
    urls = state.get("batch_urls", [])
    index = state.get("current_url_index", 0)

    if index < len(urls):
        return "continue"
    return "end"
