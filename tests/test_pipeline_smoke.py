from src.rgnavigator.ingestion_agent import ingest_policy_text
from src.rgnavigator.pipeline import run_navigator


def test_run_navigator_returns_recommended_programs_for_clear_food_case_from_natural_language() -> None:
    session = run_navigator(
        {
            "user_description": (
                "I live in Pittsburgh by myself. I make about $900 a month, "
                "I do not have health insurance, I am struggling to afford groceries, "
                "and I am behind on my gas bill."
            )
        }
    )

    assert "SNAP" in session.explanation.recommended_programs
    assert "LIHEAP" in session.explanation.recommended_programs
    assert session.eligibility.priority_order


def test_run_navigator_hard_stops_out_of_county_case() -> None:
    session = run_navigator(
        {
            "user_description": (
                "I live in Philadelphia with my daughter. I have no insurance, "
                "my income is about $900 a month, and I am behind on my gas bill."
            )
        }
    )

    assert session.intake.intake_status == "insufficient_data"
    assert session.eligibility.recommended_programs == []
    assert session.eligibility.priority_order == []
    assert session.explanation.final_status == "needs_human_followup"
    assert "Allegheny County" in session.explanation.plain_language_explanation


def test_run_navigator_suppresses_actionable_recommendations_for_core_contradictions() -> None:
    session = run_navigator(
        {
            "user_description": (
                "I live in Pittsburgh with my son. I work full time, "
                "but I have zero earned income this month. We are struggling with food "
                "and our gas bill is overdue."
            )
        }
    )

    assert session.intake.contradictory_fields == ["employment_status vs monthly_earned_income"]
    assert session.eligibility.recommended_programs == []
    assert session.eligibility.priority_order == []
    assert session.explanation.final_status == "needs_human_followup"
    assert "resolve the contradiction" in session.explanation.plain_language_explanation.lower()


def test_run_navigator_adds_useful_fallback_guidance_for_incomplete_intake() -> None:
    session = run_navigator(
        {
            "user_description": (
                "I live in Pittsburgh and I have been having trouble buying groceries."
            )
        }
    )

    assert session.intake.intake_status in {"needs_clarification", "insufficient_data"}
    assert session.eligibility.recommended_programs == []
    assert any("missing" in step.lower() or "gather" in step.lower() for step in session.explanation.next_steps)
    assert any(field in session.explanation.plain_language_explanation for field in session.intake.missing_fields)


def test_ingested_policy_becomes_available_to_session(monkeypatch) -> None:
    monkeypatch.setenv("POLICY_ALLOW_LOCAL_EMBEDDING_FALLBACK", "true")
    ingest_policy_text(
        "Transit Relief Pilot",
        """
        This policy supports households with transportation hardship.
        Applicants should bring proof of address and proof of reduced work hours.
        """,
    )

    session = run_navigator(
        {
            "user_description": (
                "I live in Pittsburgh alone, I make about $1200 a month, "
                "and transportation problems are making it hard to keep working."
            )
        }
    )

    assert any("Transit Relief Pilot" in title for title in session.uploaded_documents_available)
