from __future__ import annotations

from src.rgnavigator.intake_agent import run_intake


def test_missing_income_records_validation_reason(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    intake = run_intake({"user_description": "I live in Pittsburgh and need help buying groceries."})

    assert intake.intake_status == "needs_clarification"
    assert "household_income_total" in intake.missing_fields
    assert any("income" in reason.lower() for reason in intake.validation_reasons)


def test_out_of_county_input_is_marked_out_of_scope(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    intake = run_intake({"user_description": "I live in Philadelphia and need help with my gas bill."})

    assert intake.geography_status == "out_of_scope_geography"
    assert intake.intake_status == "insufficient_data"


def test_ambiguous_geography_prompts_for_clarification(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    intake = run_intake(
        {
            "user_description": (
                "I split time between Pittsburgh and Philadelphia and I need help with groceries."
            )
        }
    )

    assert intake.geography_status == "unknown_or_ambiguous_geography"
    assert "county" in intake.missing_fields
    assert any("county" in question.lower() for question in intake.clarification_questions)


def test_mixed_household_insurance_story_is_flagged(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    intake = run_intake(
        {
            "user_description": (
                "I live in Pittsburgh with two children. I am insured through work, but the kids do not have "
                "health insurance right now."
            )
        }
    )

    assert "insured_household_vs_uninsured_children" in intake.contradictory_fields
    assert intake.intake_status == "needs_clarification"
