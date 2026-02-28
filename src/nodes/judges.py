import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState, JudicialOpinion

# Models will be initialized lazily to ensure env vars are loaded
# Models will be initialized lazily to ensure env vars are loaded


def _get_model():
    """Lazy initialization of model for OpenRouter/DeepSeek-V3."""
    return ChatOpenAI(
        model="deepseek/deepseek-chat",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
        max_tokens=500,  # Limit output tokens per judge
    )


PROSECUTOR_PROMPT = """You are the PROSECUTOR - your role is ADVERSARIAL SCRUTINY.

Your mandate:
- Actively search for gaps, security flaws, and lazy implementations
- Question every claim not backed by concrete evidence
- Apply the LOWEST reasonable score when evidence is ambiguous
- Flag any use of dangerous patterns (os.system, shell=True, eval)
- Penalize bulk uploads, stub code, and missing implementations

Criterion: {dimension_name}
Target Artifact: {target_artifact}
Rubric Levels: {levels}
Your Specific Logic: {judicial_logic}

Evidence Available:
{evidences}

Evaluate strictly and return JudicialOpinion JSON with score, argument,
and cited_evidence_ids."""

DEFENSE_PROMPT = """You are the DEFENSE ATTORNEY - your role is to RECOGNIZE EFFORT.

Your mandate:
- Highlight creative workarounds and partial implementations
- Give credit for atomic commits and iterative development
- Apply the HIGHEST reasonable score when evidence shows genuine effort
- Advocate for intent even when execution is incomplete
- Recognize learning and experimentation as valuable

Criterion: {dimension_name}
Target Artifact: {target_artifact}
Rubric Levels: {levels}
Your Specific Logic: {judicial_logic}

Evidence Available:
{evidences}

Evaluate generously and return JudicialOpinion JSON with score, argument,
and cited_evidence_ids."""

TECH_LEAD_PROMPT = """You are the TECH LEAD - your role is PRAGMATIC EVALUATION.

Your mandate:
- Focus on maintainability, scalability, and technical debt
- Evaluate if the architecture is production-viable
- Weight architectural soundness HIGHEST for architecture criteria
- Consider practical trade-offs (time vs perfection)
- Assess if the code can be extended and maintained by a team

Criterion: {dimension_name}
Target Artifact: {target_artifact}
Rubric Levels: {levels}
Your Specific Logic: {judicial_logic}

Evidence Available:
{evidences}

Evaluate pragmatically and return JudicialOpinion JSON with score, argument,
and cited_evidence_ids."""


def _call_judge(
    state: AgentState,
    persona_prompt: str,
    persona_name: str,
    dimension: Dict[str, Any],
) -> JudicialOpinion:
    """Helper to call LLM for a specific persona and rubric dimension."""
    model = _get_model()  # Lazy initialization
    prompt = ChatPromptTemplate.from_template(persona_prompt)

    # Filter and condense evidence
    evidences_text = ""
    target_art = dimension.get("target_artifact", "").lower()
    for category, evs in state.get("evidences", {}).items():
        # Simple heuristic filtering to save tokens
        if target_art == "github_repo" and category not in ["architecture", "vision"]:
            continue
        if target_art == "pdf_report" and category != "pdf_analysis":
            continue

        evidences_text += f"\n[{category}]\n"
        for ev in evs:
            # Minimal evidence: only goal, found status, and location
            evidences_text += (
                f"- {ev.goal[:30]}: {'Y' if ev.found else 'N'} @ {ev.location[:40]}\n"
            )

    # Use structured output for better reliability and rubric compliance
    structured_model = model.with_structured_output(JudicialOpinion)
    chain = prompt | structured_model

    opinion = chain.invoke(
        {
            "dimension_name": dimension["name"],
            "target_artifact": dimension["target_artifact"],
            "levels": dimension.get("levels", ""),
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
