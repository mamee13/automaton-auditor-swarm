import pytest
from src.state import Evidence, JudicialOpinion

def test_evidence_model():
    evidence = Evidence(
        goal="Verify Pydantic models",
        found=True,
        content="class AgentState(TypedDict)",
        location="src/state.py",
        rationale="Found the TypedDict definition inheriting from Pydantic",
        confidence=1.0
    )
    assert evidence.found is True
    assert evidence.confidence == 1.0

def test_judicial_opinion_model():
    opinion = JudicialOpinion(
        judge="Prosecutor",
        criterion_id="forensic_accuracy_code",
        score=2,
        argument="Missing deep AST parsing",
        cited_evidence_ids=["ev1"]
    )
    assert opinion.judge == "Prosecutor"
    assert opinion.score == 2
