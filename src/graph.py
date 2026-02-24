from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.detectives import (
    repo_investigator,
    doc_analyst,
    vision_inspector,
)
from src.nodes.judges import prosecutor_node, defense_node, tech_lead_node
from src.nodes.justice import chief_justice_node


def create_auditor_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("repo_investigator", repo_investigator)
    workflow.add_node("doc_analyst", doc_analyst)
    workflow.add_node("vision_inspector", vision_inspector)

    workflow.add_node("prosecutor", prosecutor_node)
    workflow.add_node("defense", defense_node)
    workflow.add_node("tech_lead", tech_lead_node)

    workflow.add_node("chief_justice", chief_justice_node)

    # Add Edges
    # 1. Parallel Detectives (Fan-out)
    workflow.set_entry_point(
        "repo_investigator"
    )  # Starting with one for now, or use a router

    # We want repo, doc, and vision to run in parallel eventually.
    # For initial wiring, let's go linear then convert to parallel.
    workflow.add_edge("repo_investigator", "doc_analyst")
    workflow.add_edge("doc_analyst", "vision_inspector")

    # 2. Transition to Judicial Bench (Fan-out)
    workflow.add_edge("vision_inspector", "prosecutor")
    workflow.add_edge("vision_inspector", "defense")
    workflow.add_edge("vision_inspector", "tech_lead")

    # 3. Aggregation (Fan-in) to Chief Justice
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("tech_lead", "chief_justice")

    workflow.add_edge("chief_justice", END)

    return workflow.compile()
