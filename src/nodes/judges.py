from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.state import AgentState, JudicialOpinion

# Initialize Models (Assuming API keys are in env)
# Defaulting to GPT-4o for judicial reasoning
model = ChatOpenAI(model="gpt-4o", temperature=0)

parser = PydanticOutputParser(pydantic_object=JudicialOpinion)

PROSECUTOR_PROMPT = """You are the Prosecutor.
Your goal is to find flaws, security gaps, and missing requirements.
Be critical, skeptical, and focused on potential failures.

Rubric: {rubric}
Evidences: {evidences}

Provide your opinion as JSON matching the JudicialOpinion schema.
"""

DEFENSE_PROMPT = """You are the Defense Counsel.
Your goal is to find highlights, clever implementations, and clear intent.
Be optimistic, focused on achievements.

Rubric: {rubric}
Evidences: {evidences}

Provide your opinion as JSON matching the JudicialOpinion schema.
"""

TECH_LEAD_PROMPT = """You are the Tech Lead for the Automaton Auditor Swarm.
Your goal is to evaluate technical debt and maintainability.
Be pragmatic, focused on long-term sustainability.

Rubric: {rubric}
Evidences: {evidences}

Provide your opinion as JSON matching the JudicialOpinion schema.
"""


def _call_judge(
    state: AgentState, persona_prompt: str, persona_name: str
) -> JudicialOpinion:
    """Helper to call LLM for a specific persona."""
    prompt = ChatPromptTemplate.from_template(persona_prompt)

    # Simple aggregation of evidences for the prompt
    evidences_text = ""
    for category, evs in state.get("evidences", {}).items():
        evidences_text += f"\nCategory: {category}\n"
        for ev in evs:
            evidences_text += f"- {ev.dict()}\n"

    chain = prompt | model | parser

    opinion = chain.invoke(
        {"rubric": str(state.get("rubric")), "evidences": evidences_text}
    )

    # Ensure judge is set correctly (map persona name if needed)
    opinion.judge = persona_name  # type: ignore
    return opinion


def prosecutor_node(state: AgentState) -> Dict[str, Any]:
    """The critical lens: Scrutinizes for gaps and security flaws."""
    print("⚖️ Prosecutor evaluating evidence...")
    opinion = _call_judge(state, PROSECUTOR_PROMPT, "Prosecutor")
    return {"opinions": [opinion]}


def defense_node(state: AgentState) -> Dict[str, Any]:
    """The optimistic lens: Highlights effort and intent."""
    print("⚖️ Defense evaluating evidence...")
    opinion = _call_judge(state, DEFENSE_PROMPT, "Defense")
    return {"opinions": [opinion]}


def tech_lead_node(state: AgentState) -> Dict[str, Any]:
    """The pragmatic lens: Evaluates technical debt and maintainability."""
    print("⚖️ Tech Lead evaluating evidence...")
    opinion = _call_judge(state, TECH_LEAD_PROMPT, "Tech Lead")
    return {"opinions": [opinion]}
