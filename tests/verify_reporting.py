import os
from unittest.mock import MagicMock, patch

# Set dummy key FIRST
os.environ["OPENAI_API_KEY"] = "mock-key"


def test_synthesis_and_reporting():
    print("🧪 Verifying Protocol B and Reporting (Offline)...")
    from src.state import JudicialOpinion, AuditReport, Evidence

    # Evidence for context
    mock_ev = Evidence(
        goal="Check security",
        found=True,
        content="Found os.system call",
        location="src/tools.py",
        rationale="Detective found dangerous call",
        confidence=1.0,
    )

    # Prosecutor finding a security flaw
    mock_op_sec = JudicialOpinion(
        judge="Prosecutor",
        criterion_id="security",
        score=1,
        argument="Found raw os.system call without sanitization.",
        cited_evidence_ids=["ev1"],
    )

    mock_op_other = JudicialOpinion(
        judge="Defense",
        criterion_id="security",
        score=5,
        argument="The dev tried their best.",
        cited_evidence_ids=[],
    )

    # Mock report returned by LLM (will be overridden by deterministic logic)
    mock_report_obj = AuditReport(
        verdict="Mixed results",
        dimension_scores={"security": 5},  # LLM initially gives 5
        dissent_summary="Conflicts found.",
        remediation_plan="Fix the security flaw.",
        raw_opinions=[],
    )

    p1 = patch("src.nodes.justice._get_model")
    p2 = patch("src.nodes.justice.os.makedirs")
    with p1, p2:
        from src.nodes.justice import chief_justice_node, report_saver

        # We patch ChatPromptTemplate.from_template to return our mock chain
        # Avoid complex pipe mocking, just return a mock that has 'invoke'
        with patch(
            "src.nodes.justice.ChatPromptTemplate.from_template"
        ) as mock_from_template:
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_report_obj
            # Match the prompt | model | parser structure
            pipe = mock_from_template.return_value.__or__
            pipe.return_value.__or__.return_value = mock_chain

            # Prepare state
            state = {
                "repo_url": "https://github.com/user/test-repo",
                "is_self_audit": True,
                "evidences": {"security": [mock_ev]},
                "opinions": [mock_op_sec, mock_op_other],
                "rubric": {"dimensions": []},
            }

            # 1. Test Synthesis Logic
            result = chief_justice_node(state)
            report = result["audit_data"]

            print(f"📊 Score: {report.dimension_scores['security']}")
            assert report.dimension_scores["security"] == 3  # Rule B
            assert "Security Override" in report.dissent_summary

            # 2. Test Reporting logic
            state["audit_data"] = report
            save_result = report_saver(state)

            print(f"✅ Save Result: {save_result['final_report']}")
            assert (
                "audit/report_onself_generated/report_test-repo.md"
                in save_result["final_report"]
            )

            # Verify file paths exist (Cleanup handled in real tests)
            # but open() will still work in local dir if we don't mock it.
            # However, for a true unit test, we can mock 'open' as well.

    print("\n✨ Verification PASSED without API calls.")


if __name__ == "__main__":
    test_synthesis_and_reporting()
