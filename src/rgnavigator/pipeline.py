from __future__ import annotations

from .eligibility_agent import run_eligibility_and_prioritization
from .explanation_agent import run_checklist_and_explanation
from .intake_agent import run_intake
from .models import NavigatorSession
from .policy_store import load_policy_documents


def run_navigator(raw_input: dict, *, selected_programs: list[str] | None = None) -> NavigatorSession:
    intake = run_intake(raw_input)
    eligibility = run_eligibility_and_prioritization(
        intake.normalized_profile,
        intake.intake_status,
        missing_fields=intake.missing_fields,
        contradictory_fields=intake.contradictory_fields,
        selected_programs=selected_programs,
    )
    explanation = run_checklist_and_explanation(intake, eligibility)
    uploaded_documents = [document.title for document in load_policy_documents() if document.uploaded]

    return NavigatorSession(
        intake=intake,
        eligibility=eligibility,
        explanation=explanation,
        uploaded_documents_available=uploaded_documents,
    )
