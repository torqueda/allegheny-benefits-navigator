from __future__ import annotations

from typing import Dict, Any

from src.models.common import DecisionStatus, IntakeStatus
from src.models.session import SessionState
from src.pipeline.components import (
    checklist_and_explanation,
    eligibility_and_prioritization,
    intake,
)
from src.pipeline.session_state import (
    create_initial_session_state,
    finalize_session_timings,
    update_session_with_checklist_output,
    update_session_with_eligibility_output,
    update_session_with_intake_output,
)


def run_pipeline(
    case_id: str | None = None,
    raw_form_input: Dict[str, Any] | None = None,
) -> SessionState:
    """
    Orchestrate the 3-component pipeline: intake -> eligibility_and_prioritization -> checklist_and_explanation.

    Returns the final session state after all components have run.
    """
    if raw_form_input is None:
        raw_form_input = {}

    # Create initial session state
    session = create_initial_session_state(case_id, raw_form_input)

    # Component 1: Intake
    intake_output = intake(session, raw_form_input)
    session = update_session_with_intake_output(session, intake_output)

    # Handoff check: Intake -> Eligibility + Prioritization
    if intake_output.intake_status not in [IntakeStatus.complete, IntakeStatus.needs_clarification]:
        # Early stop if not complete or needs_clarification (for ambiguity testing)
        # For now, assume we continue
        pass

    # Component 2: Eligibility + Prioritization
    eligibility_output = eligibility_and_prioritization(session)
    session = update_session_with_eligibility_output(session, eligibility_output)

    # Handoff check: Eligibility + Prioritization -> Checklist + Explanation
    if eligibility_output.decision_status not in [DecisionStatus.ready_for_explanation, DecisionStatus.ambiguous]:
        # Early stop if not ready or ambiguous
        # For now, assume we continue
        pass

    # Component 3: Checklist + Explanation
    checklist_output = checklist_and_explanation(session)
    session = update_session_with_checklist_output(session, checklist_output)

    # Finalize timings
    session = finalize_session_timings(session)

    return session