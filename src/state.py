import operator
from typing import Annotated, Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

class Evidence(BaseModel):
    goal: str = Field(description="The specific rubric criterion or forensic goal being investigated")
    found: bool = Field(description="Whether the artifact or evidence exists")
    content: Optional[str] = Field(default=None, description="The extracted evidence content (code snippet, text, etc.)")
    location: str = Field(description="File path, line number, or commit hash where evidence was found")
    rationale: str = Field(description="Detailed explanation of why this evidence confirms or refutes the goal")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score in the findings (0.0 to 1.0)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context (e.g., AST node type, timestamp)")

class JudicialOpinion(BaseModel):
    judge: Literal["Prosecutor", "Defense", "TechLead"]
    criterion_id: str = Field(description="The ID of the rubric dimension being judged")
    score: int = Field(ge=1, le=5, description="The assigned score (1-5)")
    argument: str = Field(description="The judicial reasoning for the score, citing specific evidence")
    cited_evidence_ids: List[str] = Field(default_factory=list, description="IDs or descriptions of the evidence used for this judgment")

class AuditReport(BaseModel):
    verdict: str = Field(description="The overall synthesized verdict")
    dimension_scores: Dict[str, int] = Field(description="Final scores per rubric dimension")
    dissent_summary: str = Field(description="Summary of conflicts between judges and how they were resolved")
    remediation_plan: str = Field(description="Actionable steps for improvement")
    raw_opinions: List[JudicialOpinion] = Field(description="Full list of all judicial opinions")

class AgentState(TypedDict):
    """
    State for the Automaton Auditor Swarm.
    Uses reducers to handle parallel execution synchronization.
    """
    repo_url: str
    target_path: str  # Local path where repo is cloned
    pdf_path: Optional[str]
    rubric: Dict[str, Any]
    
    # Evidence collection: Dict mapping criterion_id to list of Evidence
    # Using ior (|=) for merging dicts, but we need to handle list merging
    evidences: Annotated[Dict[str, List[Evidence]], operator.ior]
    
    # Judicial opinions: List of all opinions from all judges
    opinions: Annotated[List[JudicialOpinion], operator.add]
    
    # Final output
    final_report: Optional[str]
    audit_data: Optional[AuditReport]
    
    # Batch processing support
    batch_urls: List[str]
    current_url_index: int
