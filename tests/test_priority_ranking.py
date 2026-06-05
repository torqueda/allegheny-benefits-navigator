from __future__ import annotations

from src.rgnavigator.pipeline import run_navigator


def test_pregnancy_case_prioritizes_medicaid_chip(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = run_navigator(
        {
            "user_description": (
                "I live in Pittsburgh with my husband and I am pregnant with twins. We make about 2800 per month. "
                "We are insured through his job but the plan is expensive and I want to know if I might qualify "
                "for health coverage while pregnant."
            )
        }
    )

    assert session.eligibility.priority_order[0] == "Medicaid/CHIP"
    medicaid = next(match for match in session.eligibility.program_matches if match.program_name == "Medicaid/CHIP")
    assert medicaid.priority_boost_reason is not None
    assert "pregnancy" in session.explanation.plain_language_explanation.lower()


def test_uninsured_children_case_prioritizes_medicaid_chip(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = run_navigator(
        {
            "user_description": (
                "I live in Pittsburgh with three children ages 2, 7, and 15. We make about 2500 a month. "
                "The kids do not have health insurance right now."
            )
        }
    )

    assert session.eligibility.priority_order[0] == "Medicaid/CHIP"
    medicaid = next(match for match in session.eligibility.program_matches if match.program_name == "Medicaid/CHIP")
    assert medicaid.priority_boost_reason is not None
    assert "children" in medicaid.priority_boost_reason.lower()


def test_suppressed_programs_are_not_reintroduced_by_priority_boosts(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    session = run_navigator(
        {
            "user_description": (
                "I am a single adult in Pittsburgh with no children, staying with relatives after an eviction. "
                "I work full time and make about 3200 a month. I have insurance and my biggest need is help with "
                "housing and legal support, not food or heating."
            )
        }
    )

    assert session.eligibility.priority_order == []
    assert all(match.decision_state != "likely_eligible" for match in session.eligibility.program_matches)
