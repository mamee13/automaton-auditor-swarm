from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.state import AgentState, JudicialOpinion

# Models will be initialized lazily to ensure env vars are loaded
parser = PydanticOutputParser(pydantic_object=JudicialOpinion)


def _get_model():
    """Lazy initialization of model to ensure env vars are loaded."""
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", temperature=0)


PROSECUTOR_PROMPT = """You are the Prosecutor for the Digital Courtroom.
Core Philosophy: "Trust No One. Assume Vibe Coding."
Objective: Scrutinize the evidence for gaps and orchestration fraud.

Criterion to Judge: {dimension_name}
Target Artifact: {target_artifact}
Prosecutor's Specific Logic: {judicial_logic}

Forensic Evidences:
{evidences}

Instructions:
1. Examine if the implementation matches the claims.
2. Identify any "Orchestration Fraud" (linear vs parallel).
3. Look for "Hallucination Liability" (missing structured output).
4. Be harsh and critical. Cite specific evidence items.

Provide your opinion as JSON matching the JudicialOpinion schema.
"""

DEFENSE_PROMPT = """You are the Defense Counsel for the Digital Courtroom.
Core Philosophy: "Reward Effort and Intent. Look for the 'Spirit of the Law'."
Objective: Highlight creative workarounds, deep thought, and engineering
effort.

Criterion to Judge: {dimension_name}
Target Artifact: {target_artifact}
Defense's Specific Logic: {judicial_logic}

Forensic Evidences:
{evidences}

Instructions:
1. Look for signs of "Engineering Struggle" and iterative
   improvement in git history.
2. Highlight where the student attempted sophisticated patterns
   (e.g., AST parsing, reducers).
3. Argue for the "Spirit of the Law" if the syntax is slightly off
   but the intent is clear.
4. Be optimistic and highlight strengths. Cite specific evidence items.

Provide your opinion as JSON matching the JudicialOpinion schema.
"""

TECH_LEAD_PROMPT = """You are the Tech Lead for the Automaton Auditor Swarm.
Core Philosophy: "Does it actually work? Is it maintainable?"
Objective: Evaluate architectural soundness, code cleanliness, and
pragmatic viability.

Criterion to Judge: {dimension_name}
Target Artifact: {target_artifact}
Tech Lead's Specific Logic: {judicial_logic}

Forensic Evidences:
{evidences}

Instructions:
1. Evaluate if state management (Pydantic models, reducers) is
   strictly implemented.
2. Check for "Technical Debt" (hardcoded paths, lack of error handling).
3. Be pragmatic and focused on technical facts. Ignore the "Vibe".
4. Cite specific evidence items and provide technical remediation advice.

Provide your opinion as JSON matching the JudicialOpinion schema.
"""


def _call_judge(
    state: AgentState,
    persona_prompt: str,
    persona_name: str,
    dimension: Dict[str, Any],
) -> JudicialOpinion:
    """Helper to call LLM for a specific persona and rubric dimension."""
    model = _get_model()  # Lazy initialization
    prompt = ChatPromptTemplate.from_template(persona_prompt)

    # Filter evidences relevant to this criterion
    # If detectives set Evidence.goal to dimension.id, we can filter here.
    # For now, we'll provide all evidences but label them by category.
    evidences_text = ""
    for category, evs in state.get("evidences", {}).items():
        evidences_text += f"\nCategory: {category}\n"
        for ev in evs:
            # Pydantic dict() is v1, model_dump() is v2.
            # Using dict() as per original code.
            evidences_text += f"- {ev.dict()}\n"

    chain = prompt | model | parser

    opinion = chain.invoke(
        {
            "dimension_name": dimension["name"],
            "target_artifact": dimension["target_artifact"],
            "judicial_logic": dimension["judicial_logic"].get(
                persona_name.lower().replace(" ", "_"), "Judge reasonably."
            ),
            "evidences": evidences_text,
        }
    )

    # Ensure metadata is set correctly
    opinion.judge = persona_name  # type: ignore
    opinion.criterion_id = dimension["id"]
    return opinion


def prosecutor_node(state: AgentState) -> Dict[str, Any]:
    """The critical lens: Scrutinizes for gaps and security flaws."""
    print("⚖️ Prosecutor evaluating evidence per criterion...")
    rubric = state.get("rubric", {})
    dimensions = rubric.get("dimensions", [])
    opinions = []
    for dim in dimensions:
        opinion = _call_judge(state, PROSECUTOR_PROMPT, "Prosecutor", dim)
        opinions.append(opinion)
    return {"opinions": opinions}


def defense_node(state: AgentState) -> Dict[str, Any]:
    """The optimistic lens: Highlights effort and intent."""
    print("⚖️ Defense evaluating evidence per criterion...")
    rubric = state.get("rubric", {})
    dimensions = rubric.get("dimensions", [])
    opinions = []
    for dim in dimensions:
        opinion = _call_judge(state, DEFENSE_PROMPT, "Defense", dim)
        opinions.append(opinion)
    return {"opinions": opinions}


def tech_lead_node(state: AgentState) -> Dict[str, Any]:
    """The pragmatic lens: Evaluates technical debt and maintainability."""
    print("⚖️ Tech Lead evaluating evidence per criterion...")
    rubric = state.get("rubric", {})
    dimensions = rubric.get("dimensions", [])
    opinions = []
    for dim in dimensions:
        opinion = _call_judge(state, TECH_LEAD_PROMPT, "TechLead", dim)
        opinions.append(opinion)
    return {"opinions": opinions}
