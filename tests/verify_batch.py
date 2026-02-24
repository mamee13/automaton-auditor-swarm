import os
from unittest.mock import patch

# Set dummy key FIRST
os.environ["OPENAI_API_KEY"] = "mock-key"


# We must patch the nodes IN THE GRAPH MODULE
def test_batch_flow():
    print("🧪 Verifying Batch processing and Graph flow (Offline)...")
    from src.state import JudicialOpinion, AuditReport

    mock_op_obj = JudicialOpinion(
        judge="Prosecutor",
        criterion_id="code",
        score=3,
        argument="Mock argument",
        cited_evidence_ids=[],
    )

    mock_report_obj = AuditReport(
        verdict="Mock Verdict",
        dimension_scores={"code": 3},
        dissent_summary="None",
        remediation_plan="None",
        raw_opinions=[],
    )

    with patch("src.graph.prosecutor_node") as mock_pros, patch(
        "src.graph.defense_node"
    ) as mock_def, patch("src.graph.tech_lead_node") as mock_tl, patch(
        "src.graph.chief_justice_node"
    ) as mock_cj, patch(
        "src.graph.doc_analyst"
    ) as mock_doc, patch(
        "src.graph.repo_investigator"
    ) as mock_repo, patch(
        "src.nodes.justice.os.makedirs"
    ):
        mock_pros.return_value = {"opinions": [mock_op_obj]}
        mock_def.return_value = {"opinions": [mock_op_obj]}
        mock_tl.return_value = {"opinions": [mock_op_obj]}
        mock_cj.return_value = {"audit_data": mock_report_obj}
        mock_repo.return_value = {"evidences": {"code": []}}
        mock_doc.return_value = {"evidences": {"docs": []}}

        from src.graph import create_auditor_graph

        graph = create_auditor_graph()

        initial_state = {
            "batch_urls": [
                "https://github.com/u/r1",
                "https://github.com/u/r2",
            ],
            "current_url_index": 0,
            "rubric": {"dimensions": []},
            "evidences": {},
            "opinions": [],
        }

        config = {"configurable": {"thread_id": "batch_test_final_v2"}}
        result = graph.invoke(initial_state, config=config)

        print("\n✅ Graph completed batch run successfully.")
        assert result.get("current_url_index") == 2
        assert "Report saved" in result.get("final_report")


if __name__ == "__main__":
    test_batch_flow()
