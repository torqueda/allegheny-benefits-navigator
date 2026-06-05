from __future__ import annotations

from src.rgnavigator.pipeline import run_navigator
from src.rgnavigator.traceability import build_reviewer_trace


def test_reviewer_trace_contains_expected_sections(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = run_navigator(
        {
            "user_description": (
                "I live in Pittsburgh with my daughter. We got a shutoff notice but I did not say how much income "
                "we have yet."
            )
        }
    )

    trace = build_reviewer_trace(session, case_id="TEST_CASE")

    assert trace["case_id"] == "TEST_CASE"
    assert "raw_input" in trace
    assert "intake_object" in trace
    assert "retrieved_chunks" in trace
    assert "program_scores" in trace
    assert "final_decision" in trace


def test_offline_runs_are_labeled_honestly(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = run_navigator(
        {
            "user_description": (
                "I live in Pittsburgh with three children ages 2, 7, and 15. We make about 2500 a month. "
                "The kids do not have health insurance right now."
            )
        }
    )

    trace = build_reviewer_trace(session, case_id="AGENT_07")

    assert trace["llm_mode"] == "offline_or_rule_only_fallback"
    assert all(row["cross_check_status"] != "live_llm_cross_check_used" for row in trace["cross_check_result"])
