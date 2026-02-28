import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.state import AgentState, AuditReport

# Models will be initialized lazily to ensure env vars are loaded


def _get_model():
    """Lazy initialization of model for OpenRouter/DeepSeek-V3."""
    return ChatOpenAI(
        model="deepseek/deepseek-chat",
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.1,
        max_tokens=2000,  # Chief Justice needs more for structured JSON output
    )


CHIEF_JUSTICE_PROMPT = """Chief Justice: Synthesize verdict.

Rules: 1) Security flaws cap at 3. 2) Facts > Claims.
3) Tech Lead weighted for arch. 4) Summarize dissent.
5) Remediation MUST be file-level specific (e.g., "In src/utils.py, line 45...").

Opinions: {opinions}
Evidence: {evidences_summary}

Return AuditReport JSON."""

RE_EVALUATION_PROMPT = """Mediator: Resolve variance for {criterion_id}.

{judge_a} vs {judge_b}:
{opinions}

Synthesize mediation note (max 100 words)."""


def chief_justice_node(state: AgentState) -> Dict[str, Any]:
    """The synthesis engine: Resolves judicial conflict using Protocol B."""
    print("⚖️ SUPREME COURT: Chief Justice issuing final ruling...")

    opinions = state.get("opinions", [])
    evidences = state.get("evidences", {})

    # Build condensed summaries - only scores and criterion IDs
    opinions_text = ""
    for op in opinions:
        opinions_text += f"{op.judge}: {op.criterion_id}={op.score}\n"

    detailed_ev_summary = ""
    for cat, ev_list in evidences.items():
        detailed_ev_summary += f"\n[{cat}]\n"
        for ev in ev_list:
            status = "FOUND" if ev.found else "MISSING"
            detailed_ev_summary += f"- {ev.goal} ({status}) @ {ev.location}\n"

    prompt = ChatPromptTemplate.from_template(CHIEF_JUSTICE_PROMPT)
    model = _get_model()  # Lazy initialization
    structured_model = model.with_structured_output(AuditReport)
    chain = prompt | structured_model

    report = chain.invoke(
        {"opinions": opinions_text, "evidences_summary": detailed_ev_summary}
    )

    # ENFORCE DETERMINISTIC PROTOCOL B (Hardcoded override)
    final_scores = report.dimension_scores
    rubric = state.get("rubric", {})

    # RULE 1: Security Override
    for op in opinions:
        if op.judge == "Prosecutor" and (
            "os.system" in op.argument or "shell=True" in op.argument
        ):
            dim = next(
                (d for d in rubric.get("dimensions", []) if d["id"] == op.criterion_id),
                None,
            )
            max_val = dim.get("max_score", 5) if dim else 5
            cap_val = int(max_val * 0.6)  # Cap at 60%
            if final_scores.get(op.criterion_id, max_val) > cap_val:
                print(f"🚨 SECURITY OVERRIDE: Capping {op.criterion_id}.")
                final_scores[op.criterion_id] = cap_val
                report.dissent_summary += (
                    f" [Security Override: {op.criterion_id} capped at {cap_val} "
                    "due to vulnerability]"
                )

    # RULE 2: Fact Supremacy - Evidence overrules unsupported claims
    evidences_flat = []
    for ev_list in state.get("evidences", {}).values():
        evidences_flat.extend(ev_list)

    for op in opinions:
        dim = next(
            (d for d in rubric.get("dimensions", []) if d["id"] == op.criterion_id),
            None,
        )
        max_val = dim.get("max_score", 5) if dim else 5

        # Check if judge claims contradict evidence
        for ev in evidences_flat:
            goal_match = ev.goal.lower() in op.argument.lower()
            # Evidence says NOT found but judge scored high
            if goal_match and not ev.found and op.score > (max_val * 0.5):
                reduced = int(op.score * 0.7)
                print(
                    f"⚖️ FACT SUPREMACY: Evidence contradicts "
                    f"{op.judge} on {op.criterion_id}"
                )
                final_scores[op.criterion_id] = min(
                    final_scores.get(op.criterion_id, op.score), reduced
                )
                report.dissent_summary += (
                    f" [Fact Override: {op.criterion_id} reduced - "
                    "evidence contradicts claim]"
                )
                break

    # RULE 3: Tech Lead Weight - Architecture criteria get higher weight
    criterion_opinions: Dict[str, List[Any]] = {}
    for op in opinions:
        if op.criterion_id not in criterion_opinions:
            criterion_opinions[op.criterion_id] = []
        criterion_opinions[op.criterion_id].append(op)

    for crit_id, crit_ops in criterion_opinions.items():
        # Check if this is an architecture-related criterion
        is_arch = any(
            keyword in crit_id.lower()
            for keyword in ["architecture", "orchestration", "dev_progress"]
        )

        if is_arch and len(crit_ops) >= 3:
            tech_lead_op = next((o for o in crit_ops if o.judge == "TechLead"), None)
            if tech_lead_op:
                other_scores = [o.score for o in crit_ops if o.judge != "TechLead"]
                if other_scores:
                    avg_others = sum(other_scores) / len(other_scores)
                    # Weighted average: TechLead 60%, Others 40%
                    weighted = int(tech_lead_op.score * 0.6 + avg_others * 0.4)
                    final_scores[crit_id] = weighted
                    print(f"⚖️ TECH LEAD WEIGHT: {crit_id} weighted to {weighted}")

    report.dimension_scores = final_scores
    report.raw_opinions = opinions

    return {"audit_data": report}


def _generate_markdown_report(
    report: AuditReport, repo_url: str, rubric: Dict[str, Any]
) -> str:
    """Generates a professional Markdown audit report."""
    md = f"# Audit Report: {repo_url}\n\n"
    md += f"## ⚖️ Executive Summary\n\n{report.verdict}\n\n"

    md += "## 📊 Criterion Breakdown\n\n"
    md += "| Criterion | Score | Verdict |\n"
    md += "| :--- | :--- | :--- |\n"
    for crit, score in report.dimension_scores.items():
        # Get max score from rubric for reporting
        dim = next((d for d in rubric.get("dimensions", []) if d["id"] == crit), None)
        max_val = dim.get("max_score", 5) if dim else 5

        # Calculate verdict based on percentage
        ratio = score / max_val
        v = "✅ PASS" if ratio >= 0.8 else "⚠️ WARN" if ratio >= 0.6 else "❌ FAIL"
        md += f"| {crit} | {score}/{max_val} | {v} |\n"

    res_hdr = f"\n## 🏛️ Judicial Conflict Res\n\n{report.dissent_summary}\n\n"
    md += res_hdr

    md += "## 🛠️ Remediation Plan\n\n"
    md += f"{report.remediation_plan}\n\n"

    md += "## 📂 Raw Evidence (Judicial Opinions)\n\n"
    for op in report.raw_opinions:
        dim = next(
            (d for d in rubric.get("dimensions", []) if d["id"] == op.criterion_id),
            None,
        )
        max_val = dim.get("max_score", 5) if dim else 5
        md += f"### {op.judge} - {op.criterion_id}\n"
        md += f"**Score:** {op.score}/{max_val}\n\n"
        md += f"{op.argument}\n\n"

    return md


def report_saver(state: AgentState) -> Dict[str, Any]:
    """Saves final report to audit/ folders following challenge structure."""
    report = state.get("audit_data")
    if not report:
        return {}

    url = state.get("repo_url", "unknown")
    repo_name = url.split("/")[-1].replace(".git", "")

    # Determine folder based on explicit is_self_audit flag
    is_self = state.get("is_self_audit", False)
    target_folder = "report_onself_generated" if is_self else "report_onpeer_generated"

    output_dir = os.path.join("audit", target_folder)
    os.makedirs(output_dir, exist_ok=True)

    # Save JSON
    json_path = os.path.join(output_dir, f"report_{repo_name}.json")
    with open(json_path, "w") as f:
        f.write(report.model_dump_json(indent=2))

    # Save Markdown
    md_content = _generate_markdown_report(report, url, state.get("rubric", {}))
    md_path = os.path.join(output_dir, f"report_{repo_name}.md")
    with open(md_path, "w") as f:
        f.write(md_content)

    print("💾 Report saved successfully to audit/ directory.")
    return {"final_report": f"Report saved to {md_path}"}


def evidence_aggregator(state: AgentState) -> Dict[str, Any]:
    """
    Synchronization node that formally crystalizes the evidence collected
    by all detectives before judicial review begins.
    """
    evs = state.get("evidences", {})
    ev_count = sum(len(e_list) for e_list in evs.values())
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

        # Get max value for this dimension
        rubric = state.get("rubric", {})
        dim = next(
            (d for d in rubric.get("dimensions", []) if d["id"] == crit_id), None
        )
        max_val = dim.get("max_score", 5) if dim else 5

        # High variance if difference is > 20% of max score
        if (max_s - min_s) > (max_val * 0.2):
            print(f"⚠️ HIGH VARIANCE detected for {crit_id}: {scores}")
            has_variance = True
            conflicting_criteria.append(crit_id)

    return {
        "has_variance": has_variance,
        "conflicting_criteria": conflicting_criteria,
    }


def re_evaluation_node(state: AgentState) -> Dict[str, Any]:
    """
    Node to handle re-evaluation of conflicting opinions via LLM mediation.
    Invokes the Mediator model for each criterion with high variance,
    producing a dissent note that is appended to the audit context.
    """
    print("⚖️ RE-EVALUATION: Mediator resolving high variance...")

    conflicting = state.get("conflicting_criteria", [])
    if not isinstance(conflicting, list) or not conflicting:
        return {"re_evaluated": True}

    opinions = state.get("opinions", [])

    mediation_notes: List[str] = []

    for crit_id in conflicting:
        crit_ops = [op for op in opinions if op.criterion_id == crit_id]
        if len(crit_ops) < 2:
            continue

        # Identify the two most extreme judges by score
        crit_ops.sort(key=lambda x: x.score)
        judge_low = crit_ops[0]
        judge_high = crit_ops[-1]

        # Format their arguments for the mediator
        opinions_text = (
            f"Judge: {judge_low.judge}\n"
            f"Score: {judge_low.score}\n"
            f"Argument: {judge_low.argument}\n\n"
            f"Judge: {judge_high.judge}\n"
            f"Score: {judge_high.score}\n"
            f"Argument: {judge_high.argument}\n"
        )

        # Invoke the mediator LLM
        try:
            print(
                f"⚖️ Mediator: Resolving {crit_id} "
                f"({judge_low.judge} vs {judge_high.judge})..."
            )
            prompt = ChatPromptTemplate.from_template(RE_EVALUATION_PROMPT)
            model = ChatOpenAI(
                model="deepseek/deepseek-chat",
                openai_api_key=os.getenv("OPENROUTER_API_KEY"),
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.1,
                max_tokens=200,  # Mediator only needs brief notes
            )
            chain = prompt | model
            response = chain.invoke(
                {
                    "criterion_id": crit_id,
                    "opinions": opinions_text,
                    "judge_a": judge_low.judge,
                    "judge_b": judge_high.judge,
                }
            )
            note = getattr(response, "content", str(response))
            mediation_notes.append(f"[Mediation: {crit_id}]\n{note}\n")
            print(f"✅ Mediation complete for {crit_id}.")
        except Exception as e:
            print(f"❌ Mediator failed for {crit_id}: {e}")
            mediation_notes.append(f"[Mediation: {crit_id}] Mediator failed: {e}\n")

    # Return the dissent notes so chief justice can incorporate them
    dissent_text = "\n".join(mediation_notes)
    return {"re_evaluated": True, "mediation_notes": dissent_text}


def variance_router(state: Dict[str, Any]) -> str:
    """Routes to re-evaluation if high variance is detected."""
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
