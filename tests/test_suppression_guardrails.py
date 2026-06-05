from __future__ import annotations

from src.rgnavigator.eligibility_agent import _cross_check, _finalize_program_match
from src.rgnavigator.models import MatchReason, ProgramMatch, UserIntake
from src.rgnavigator.pipeline import run_navigator


def test_high_income_household_does_not_receive_normal_recommendations(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = run_navigator(
        {
            "user_description": (
                "I am a single adult in Pittsburgh with no children, staying with relatives after an eviction. "
                "I work full time and make about $3200 a month. I have insurance and my biggest need is help "
                "with housing and legal support, not food or heating."
            )
        }
    )

    assert session.explanation.recommended_programs == []
    assert any(match.decision_state == "suppressed_high_income" for match in session.eligibility.program_matches)
    assert "did not identify a likely benefit match" in session.explanation.plain_language_explanation.lower()


def test_missing_income_case_stays_in_clarification_mode(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = run_navigator(
        {
            "user_description": "I live in Pittsburgh and I have been having trouble buying groceries."
        }
    )

    assert session.intake.intake_status == "needs_clarification"
    assert "household_income_total" in session.intake.missing_fields
    assert session.explanation.recommended_programs == []
    assert "income" in session.explanation.plain_language_explanation.lower()


def test_out_of_scope_household_is_suppressed(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = run_navigator(
        {
            "user_description": (
                "I live in Philadelphia with my daughter. I have no insurance, my income is about $900 a month, "
                "and I am behind on my gas bill."
            )
        }
    )

    assert session.intake.geography_status == "out_of_scope_geography"
    assert session.eligibility.recommended_programs == []
    assert session.explanation.final_status == "needs_human_followup"


def test_llm_positive_rule_negative_conflict_is_withheld() -> None:
    llm_match = ProgramMatch(
        program_name="SNAP",
        status="strong_match",
        decision_state="unsupported_or_unknown",
        match_score=8.0,
        priority_score=9.0,
        rationale=[MatchReason(reason="LLM said yes.", score=8.0)],
        caveats=[],
        retrieved_evidence=[],
        checklist_items=[],
        llm_match_score=8.0,
        cross_check_status="live_llm_cross_check_used",
    )
    rule_match = ProgramMatch(
        program_name="SNAP",
        status="no_clear_match",
        decision_state="unsupported_or_unknown",
        match_score=-2.0,
        priority_score=0.0,
        rationale=[MatchReason(reason="Income appears above the screening band.", score=-2.0)],
        caveats=[],
        retrieved_evidence=[],
        checklist_items=[],
        suppression_reason="high_income",
        rule_match_score=-2.0,
        cross_check_status="rule_only_fallback",
        cross_check_summary="Rule result only.",
    )
    crossed = _cross_check(llm_match, rule_match)
    finalized = _finalize_program_match(
        crossed,
        UserIntake(county="Allegheny", num_adults=1, num_children=0, household_income_total=4000),
        "complete",
        [],
        [],
    )

    assert crossed.cross_check_status == "suppressed_rule_conflict"
    assert finalized.decision_state == "suppressed_high_income"
    assert finalized.status == "no_clear_match"
