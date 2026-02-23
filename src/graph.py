from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.nodes.detectives import repo_investigator, doc_analyst, vision_inspector
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
    # Parallel Detectives
    workflow.set_entry_point("repo_investigator")
    # Note: Need fan-in/fan-out logic here
    
    return workflow.compile()
