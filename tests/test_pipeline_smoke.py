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


def test_ingested_policy_becomes_available_to_session() -> None:
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
