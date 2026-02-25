from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.state import AgentState, JudicialOpinion

# Initialize Models (Assuming API keys are in env)
# Defaulting to GPT-4o for judicial reasoning
model = ChatOpenAI(model="gpt-4o", temperature=0)

parser = PydanticOutputParser(pydantic_object=JudicialOpinion)

PROSECUTOR_PROMPT = """You are the Prosecutor for the Digital Courtroom.
Core Philosophy: "Trust No One. Assume Vibe Coding."
Objective: Scrutinize the evidence for gaps and orchestration fraud.

Specifically:
- Check for "Orchestration Fraud": If the graph is linear, score
  'LangGraph Architecture' as 1.
- Check for "Security Negligence": If os.system is used without
  sandboxing, score is capped.
- Check for "Hallucination Liability": If Judges return free text,
  charge them.

Rubric: {rubric}
Evidences: {evidences}

Provide your opinion as JSON matching the JudicialOpinion schema.
Be harsh, critical, and cite specific evidence IDs.
"""

DEFENSE_PROMPT = """You are the Defense Counsel for the Digital Courtroom.
Core Philosophy: "Reward Effort and Intent. Look for the 'Spirit of the Law'."
Objective: Highlight creative workarounds, deep thought, and effort.

Specifically:
- Argue for higher scores if the implementation process (Git history)
  shows struggle and iteration.
- Highlight sophisticated AST logic even if the graph has minor syntax errors.
- Mitigate 'Hallucination' charges by finding alignment with MAS theories.

Rubric: {rubric}
Evidences: {evidences}

Provide your opinion as JSON matching the JudicialOpinion schema.
Be optimistic, highlight strengths, and cite specific evidence IDs.
"""

TECH_LEAD_PROMPT = """You are the Tech Lead for the Automaton Auditor Swarm.
Core Philosophy: "Does it actually work? Is it maintainable?"
Objective: Evaluate architectural soundness, code cleanliness,
and practical viability.

Specifically:
- Focus on Artifacts: Is Pydantic rigor maintained? Are state reducers
  used correctly?
- Assess Technical Debt: Ruling is 3 if it executes but is
  architecturally brittle.
- You are the tie-breaker for Architecture.

Rubric: {rubric}
Evidences: {evidences}

Provide your opinion as JSON matching the JudicialOpinion schema.
Be pragmatic, focused on technical facts, and cite specific evidence IDs.
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
