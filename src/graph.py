from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END, START
from src.state import AgentState
from src.nodes.detectives import (
    repo_investigator,
    doc_analyst,
    vision_inspector,
)
from src.nodes.judges import prosecutor_node, defense_node, tech_lead_node
from src.nodes.justice import chief_justice_node, report_saver
from src.nodes.batch import prepare_audit, batch_router


def create_auditor_graph():
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("prepare_audit", prepare_audit)

    workflow.add_node("repo_investigator", repo_investigator)
    workflow.add_node("doc_analyst", doc_analyst)
    workflow.add_node("vision_inspector", vision_inspector)

    workflow.add_node("prosecutor", prosecutor_node)
    workflow.add_node("defense", defense_node)
    workflow.add_node("tech_lead", tech_lead_node)

    workflow.add_node("chief_justice", chief_justice_node)
    workflow.add_node("save_report", report_saver)

    # Add Edges
    # 0. Entry and Batch Setup
    workflow.add_edge(START, "prepare_audit")

    # 1. Parallel Detectives (Fan-out)
    workflow.add_edge("prepare_audit", "repo_investigator")
    workflow.add_edge("prepare_audit", "doc_analyst")
    workflow.add_edge("prepare_audit", "vision_inspector")

    # 2. Transition to Judicial Bench (Fan-in/Fan-out)
    # Fan-in from all detectives to all judges
    for detective in ["repo_investigator", "doc_analyst", "vision_inspector"]:
        for judge in ["prosecutor", "defense", "tech_lead"]:
            workflow.add_edge(detective, judge)

    # 3. Aggregation (Fan-in) to Chief Justice
    workflow.add_edge("prosecutor", "chief_justice")
    workflow.add_edge("defense", "chief_justice")
    workflow.add_edge("tech_lead", "chief_justice")

    # 4. Save and Loop/End
    workflow.add_edge("chief_justice", "save_report")

    # Conditional edge for Batch Processing
    workflow.add_conditional_edges(
        "save_report", batch_router, {"continue": "prepare_audit", "end": END}
    )

    # 5. Checkpointing
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
