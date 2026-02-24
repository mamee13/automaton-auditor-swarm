import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from src.state import AgentState, AuditReport

# Initialize Model
model = ChatOpenAI(model="gpt-4o", temperature=0.1)
parser = PydanticOutputParser(pydantic_object=AuditReport)

CHIEF_JUSTICE_PROMPT = """You are the Chief Justice of the Supreme Court.
Your goal is to resolve conflicts between the following judicial opinions.
Construct a Remediation Plan and provide final scores.

Opinions:
{opinions}

Provide your opinion as JSON matching schema.
"""


def chief_justice_node(state: AgentState) -> Dict[str, Any]:
    """The synthesis engine: Resolves judicial conflict."""
    print("⚖️ SUPREME COURT: Chief Justice issuing final ruling...")

    opinions = state.get("opinions", [])
    opinions_text = ""
    for op in opinions:
        raw_op = (
            f"\nJudge: {op.judge}\n"
            f"Score: {op.score}\n"
            f"Rationale: {op.argument}\n"
        )
        opinions_text += raw_op

    prompt = ChatPromptTemplate.from_template(CHIEF_JUSTICE_PROMPT)
    chain = prompt | model | parser

    report = chain.invoke({"opinions": opinions_text})

    # Store raw opinions in report for transparency
    report.raw_opinions = opinions

    return {"audit_data": report}


def report_saver(state: AgentState) -> Dict[str, Any]:
    """Saves the final report to the audit/ directory."""
    report = state.get("audit_data")
    if not report:
        return {}

    url = state.get("repo_url", "unknown")
    repo_name = url.split("/")[-1].replace(".git", "")
    os.makedirs("audit", exist_ok=True)

    filename = f"audit/report_{repo_name}.json"
    print(f"💾 Saving report to {filename}")

    with open(filename, "w") as f:
        f.write(report.model_dump_json(indent=2))

    return {"final_report": f"Report saved to {filename}"}
