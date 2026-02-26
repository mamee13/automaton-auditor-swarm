import operator
from typing import Annotated, Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Evidence(BaseModel):
    goal: str = Field(description="The specific rubric criterion or forensic goal")
    found: bool = Field(description="Whether the artifact or evidence exists")
    content: Optional[str] = Field(
        default=None,
        description="The extracted evidence content",
    )
    location: str = Field(description="File path, line number, or commit hash")
    rationale: str = Field(description="Detailed explanation of findings")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class JudicialOpinion(BaseModel):
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str = Field(description="The ID of the rubric dimension being judged")
    score: int = Field(ge=1, le=5, description="The assigned score (1-5)")
    argument: str = Field(description="The judicial reasoning for the score")
    cited_evidence_ids: List[str] = Field(
        default_factory=list,
        description="IDs or descriptions of the evidence used",
    )


class AuditReport(BaseModel):
    verdict: str = Field(description="The overall synthesized verdict")
    dimension_scores: Dict[str, int] = Field(
        description="Final scores per rubric dimension"
    )
    dissent_summary: str = Field(description="Summary of conflicts between judges")
    remediation_plan: str = Field(description="Actionable steps for improvement")
    raw_opinions: List[JudicialOpinion] = Field(
        description="Full list of all judicial opinions"
    )


class AgentState(TypedDict):
    """
    State for the Automaton Auditor Swarm.
    Uses reducers to handle parallel execution synchronization.
    """

    repo_url: str
    target_path: str
    pdf_path: Optional[str]
    rubric: Dict[str, Any]
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    opinions: Annotated[List[JudicialOpinion], operator.add]
    batch_urls: List[str]
    current_url_index: int
    has_variance: bool
    conflicting_criteria: List[str]
    re_evaluated: bool
    mediation_notes: Optional[str]
    audit_data: Optional[AuditReport]
    final_report: Optional[str]
