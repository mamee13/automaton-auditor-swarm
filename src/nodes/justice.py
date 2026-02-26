import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.state import AgentState, AuditReport

# Initialize Model
model = ChatOpenAI(model="gpt-4o", temperature=0.1)
parser = PydanticOutputParser(pydantic_object=AuditReport)

CHIEF_JUSTICE_PROMPT = """You are the Chief Justice of the Supreme Court.
Your goal is to synthesize the final verdict using Synthesis protocols.

Synthesis Rules (Protocol B):
1. SECURITY OVERRIDE: If the Prosecutor identifies a confirmed security
   vulnerability (e.g. os.system with unsanitized inputs), the score is
   capped at 3 regardless of other opinions.
2. FACT SUPREMACY: If the Defense claims features that RepoInvestigator
   evidence proves do not exist (Hallucination), the Defense is overruled.
3. TECH LEAD WEIGHT: Tech Lead's judgment carries the highest weight for
   technical architecture and maintainability.
4. DISSENT REQUIREMENT: You MUST summarize why the Prosecutor and
   Defense disagreed.

Evidence Collection:
{evidences_summary}

Opinions to Synthesize:
{opinions}

Provide your final synthesis as JSON matching the AuditReport schema.
"""

RE_EVALUATION_PROMPT = """You are the Supreme Court Mediator.
There is a significant disagreement (variance > 2) between judges on the
criterion: {criterion_id}.

Judges' Opinions:
{opinions}

Forensic Evidence for this Criterion:
{evidence}

Task:
Synthesize a 'Dissent Mitigation' instruction for the judges.
Ask the {judge_a} and {judge_b} to re-examine the specific evidence
provided and find a middle ground or provide a much more detailed
justification for their extreme scores.

Provide a brief mediation note.
"""


def chief_justice_node(state: AgentState) -> Dict[str, Any]:
    """The synthesis engine: Resolves judicial conflict using Protocol B."""
    print("⚖️ SUPREME COURT: Chief Justice issuing final ruling...")

    opinions = state.get("opinions", [])
    evidences = state.get("evidences", {})

    # Build summaries for context
    opinions_text = ""
    for op in opinions:
        msg = f"\nJudge: {op.judge}\nScore: {op.score}\nRate: {op.argument}\n"
        opinions_text += msg

    evidences_summary = ""
    for cat, evs in evidences.items():
        ev_list = [f"- {e.goal}: {'Yes' if e.found else 'No'}" for e in evs]
        evidences_summary += f"\nCategory {cat}:\n" + "\n".join(ev_list)

    print("DEBUG: Creating prompt...")
    prompt = ChatPromptTemplate.from_template(CHIEF_JUSTICE_PROMPT)
    print("DEBUG: Creating chain...")
    chain = prompt | model | parser

    print("DEBUG: Invoking chain...")
    report = chain.invoke(
        {"opinions": opinions_text, "evidences_summary": evidences_summary}
    )
    print("DEBUG: Chain invoked.")

    # ENFORCE DETERMINISTIC PROTOCOL B (Hardcoded override)
    final_scores = report.dimension_scores
    for op in opinions:
        # Rule of Security: os.system or shell=True check
        if op.judge == "Prosecutor" and (
            "os.system" in op.argument or "shell=True" in op.argument
        ):
            if final_scores.get(op.criterion_id, 5) > 3:
                print(f"🚨 SECURITY OVERRIDE: Capping {op.criterion_id}.")
                final_scores[op.criterion_id] = 3
                report.dissent_summary += (
                    f" [Security Override: {op.criterion_id} capped at 3 "
                    "due to vulnerability found by Prosecutor]"
                )

    report.dimension_scores = final_scores
    report.raw_opinions = opinions

    return {"audit_data": report}


def _generate_markdown_report(report: AuditReport, repo_url: str) -> str:
    """Generates a professional Markdown audit report."""
    md = f"# Audit Report: {repo_url}\n\n"
    md += f"## ⚖️ Executive Summary\n\n{report.verdict}\n\n"

    md += "## 📊 Criterion Breakdown\n\n"
    md += "| Criterion | Score | Verdict |\n"
    md += "| :--- | :--- | :--- |\n"
    for crit, score in report.dimension_scores.items():
        v = "✅ PASS" if score >= 4 else "⚠️ WARN" if score == 3 else "❌ FAIL"
        md += f"| {crit} | {score}/5 | {v} |\n"

    res_hdr = f"\n## 🏛️ Judicial Conflict Res\n\n{report.dissent_summary}\n\n"
    md += res_hdr

    md += "## 🛠️ Remediation Plan\n\n"
    md += f"{report.remediation_plan}\n\n"

    md += "## 📂 Raw Evidence (Judicial Opinions)\n\n"
    for op in report.raw_opinions:
        md += f"### {op.judge} - {op.criterion_id}\n"
        md += f"**Score:** {op.score}/5\n\n"
        md += f"{op.argument}\n\n"

    return md


def report_saver(state: AgentState) -> Dict[str, Any]:
    """Saves final report to audit/ folders following challenge structure."""
    report = state.get("audit_data")
    if not report:
        return {}

    url = state.get("repo_url", "unknown")
    repo_name = url.split("/")[-1].replace(".git", "")

    # Determine folder based on target (self vs peer)
    # For now, we default to 'report_onself_generated' if not specified
    target_folder = "report_onself_generated"
    if "peer" in url.lower():
        target_folder = "report_onpeer_generated"

    output_dir = os.path.join("audit", target_folder)
    os.makedirs(output_dir, exist_ok=True)

    # Save JSON
    json_path = os.path.join(output_dir, f"report_{repo_name}.json")
    with open(json_path, "w") as f:
        f.write(report.model_dump_json(indent=2))

    # Save Markdown
    md_content = _generate_markdown_report(report, url)
    md_path = os.path.join(output_dir, f"report_{repo_name}.md")
    with open(md_path, "w") as f:
        f.write(md_content)

    print(f"💾 Report saved to {output_dir}")
    return {"final_report": f"Report saved to {md_path}"}


def evidence_aggregator(state: AgentState) -> Dict[str, Any]:
    """
    Synchronization node that formally crystalizes the evidence collected
    by all detectives before judicial review begins.
    """
    ev_count = sum(len(evs) for evs in state.get("evidences", {}).values())
    print(f"📊 EvidenceAggregator: {ev_count} pieces of evidence crystallized.")
    return {}


def variance_check_node(state: AgentState) -> Dict[str, Any]:
    """Checks if there is high variance in scores for any criterion."""
    print("⚖️ Variance Check: Analyzing judge disagreements...")
    opinions = state.get("opinions", [])
    if not opinions:
        return {"has_variance": False}

    # Group opinions by criterion
    by_crit: Dict[str, List[int]] = {}
    for op in opinions:
        if op.criterion_id not in by_crit:
            by_crit[op.criterion_id] = []
        by_crit[op.criterion_id].append(op.score)

    has_variance = False
    conflicting_criteria = []

    for crit_id, scores in by_crit.items():
        if not scores:
            continue
        max_s = max(scores)
        min_s = min(scores)
        if (max_s - min_s) > 2:
            print(f"⚠️ HIGH VARIANCE detected for {crit_id}: {scores}")
            has_variance = True
            conflicting_criteria.append(crit_id)

    return {
        "has_variance": has_variance,
        "conflicting_criteria": conflicting_criteria,
    }


def re_evaluation_node(state: AgentState) -> Dict[str, Any]:
    """Node to handle re-evaluation of conflicting opinions."""
    print("⚖️ RE-EVALUATION: Attempting to resolve high variance...")
    # In a real system, we'd loop back to judges with mediator notes.
    # For now, we'll append a "Mediation Note" to the state or
    # flag that re-evaluation occurred.
    # To keep the graph loopable without infinite loops,
    # we might only do this once.
    return {"re_evaluated": True}


def variance_router(state: Dict[str, Any]) -> str:
    """Routes to re-evaluation if high variance is detected."""
    # Note: State might be a dict or AgentState depending on how it's called
    if state.get("has_variance") and not state.get("re_evaluated"):
        return "re_evaluate"
    return "synthesize"


def cleanup_node(state: AgentState) -> Dict[str, Any]:
    """Ensures temporary forensic sandboxes are cleaned up."""
    path = state.get("target_path")
    if path:
        from src.tools.forensics import cleanup_sandboxed_repo

        success = cleanup_sandboxed_repo(path)
        if success:
            print(f"🧹 Cleanup: Removed sandboxed repo at {path}")
        else:
            print(f"⚠️ Cleanup: No action needed or failed for {path}")
    return {"target_path": None}
