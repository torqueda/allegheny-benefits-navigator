from __future__ import annotations

import time
from typing import Dict, List
from uuid import uuid4

from src.models.common import DecisionStatus, FinalStatus, IntakeStatus
from src.models.eligibility import EligibilityPrioritizationOutput
from src.models.explanation import ChecklistExplanationOutput
from src.models.intake import IntakeOutput
from src.models.session import (
    Audit,
    AuditEvent,
    RunInput,
    SessionMeta,
    SessionState,
)


def create_initial_session_state(
    case_id: str | None = None,
    raw_form_input: Dict[str, any] = None,
) -> SessionState:
    """Create initial session state for a new run."""
    if raw_form_input is None:
        raw_form_input = {}

    session_id = str(uuid4())
    run_id = str(uuid4())
    created_at = "2026-04-12T00:00:00Z"  # Placeholder; in real impl, use datetime

    session_meta = SessionMeta(
        session_id=session_id,
        run_id=run_id,
        case_id=case_id,
        mode="synthetic_test",
        created_at=created_at,
        app_version="1.0.0",
        ruleset_version="2026-04-12",
        template_version="v1",
        program_scope=["SNAP", "Medicaid/CHIP", "LIHEAP", "WIC", "local_referral_pathway"],
        policy_snapshot_version="snapshot-2026-04-12",
        llm_enabled=False,
        llm_model=None,
    )

    input_data = RunInput(raw_form_input=raw_form_input, source="ui_form")

    # Placeholder initial outputs
    intake_output = IntakeOutput(
        household_profile=None,  # Will be set by intake component
        missing_fields=[],
        contradictory_fields=[],
        validation_warnings=[],
        intake_status=IntakeStatus.needs_clarification,  # Placeholder
        clarification_questions=[],
    )

    eligibility_output = EligibilityPrioritizationOutput(
        program_assessments=[],
        eligible_or_likely_programs=[],
        inapplicable_programs=[],
        uncertainty_flags=[],
        priority_order=[],
        priority_rationale=[],
        decision_status=DecisionStatus.insufficient_data,  # Placeholder
    )

    checklist_output = ChecklistExplanationOutput(
        checklist_items_by_program={},
        recommended_programs=[],
        next_steps=[],
        user_explanation="",
        visible_caveats=[],
        referral_notes=[],
        final_status=FinalStatus.needs_human_followup,  # Placeholder
    )

    audit = Audit(events=[], errors=[], timings_ms={})

    return SessionState(
        session_meta=session_meta,
        input=input_data,
        intake=intake_output,
        eligibility_prioritization=eligibility_output,
        checklist_explanation=checklist_output,
        audit=audit,
    )


def update_session_with_intake_output(
    session: SessionState, intake_output: IntakeOutput
) -> SessionState:
    """Update session state with intake component output."""
    session.intake = intake_output
    # Add audit event
    event = AuditEvent(
        component="intake",
        event_type="validation_complete",
        timestamp="2026-04-12T00:00:01Z",  # Placeholder
        details={"status": intake_output.intake_status.value},
    )
    session.audit.events.append(event)
    return session


def update_session_with_eligibility_output(
    session: SessionState, eligibility_output: EligibilityPrioritizationOutput
) -> SessionState:
    """Update session state with eligibility component output."""
    session.eligibility_prioritization = eligibility_output
    # Add audit event
    event = AuditEvent(
        component="eligibility_prioritization",
        event_type="assessment_complete",
        timestamp="2026-04-12T00:00:02Z",  # Placeholder
        details={"decision_status": eligibility_output.decision_status.value},
    )
    session.audit.events.append(event)
    return session


def update_session_with_checklist_output(
    session: SessionState, checklist_output: ChecklistExplanationOutput
) -> SessionState:
    """Update session state with checklist component output."""
    session.checklist_explanation = checklist_output
    # Add audit event
    event = AuditEvent(
        component="checklist_explanation",
        event_type="generation_complete",
        timestamp="2026-04-12T00:00:03Z",  # Placeholder
        details={"final_status": checklist_output.final_status.value},
    )
    session.audit.events.append(event)
    return session


def finalize_session_timings(session: SessionState) -> SessionState:
    """Add placeholder timings to session audit."""
    # Placeholder timings
    session.audit.timings_ms = {
        "intake": 100,
        "eligibility_prioritization": 200,
        "checklist_explanation": 150,
        "total": 450,
    }
    return session