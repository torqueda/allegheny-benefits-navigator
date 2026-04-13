from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from src.components.eligibility import run_eligibility_and_prioritization
from src.components.explanation import run_checklist_and_explanation
from src.components.intake import run_intake
from src.models.session import (
    AuditEvent,
    AuditTrail,
    ChecklistExplanationOutput,
    EligibilityPrioritizationOutput,
    SessionMeta,
    SessionState,
)


def run_case(case: dict[str, object]) -> SessionState:
    timings: dict[str, int] = {}
    audit = AuditTrail()
    session_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    started = time.perf_counter()
    intake_started = time.perf_counter()
    intake = run_intake(case)
    timings["intake"] = int((time.perf_counter() - intake_started) * 1000)
    audit.events.append(
        AuditEvent(
            component="intake",
            event_type="validation_complete",
            timestamp=created_at,
            details={"status": intake.intake_status.value},
        )
    )

    decision_started = time.perf_counter()
    eligibility = run_eligibility_and_prioritization(intake)
    timings["eligibility_prioritization"] = int((time.perf_counter() - decision_started) * 1000)
    audit.events.append(
        AuditEvent(
            component="eligibility_prioritization",
            event_type="decision_complete",
            timestamp=created_at,
            details={"status": eligibility.decision_status.value},
        )
    )

    explanation_started = time.perf_counter()
    checklist = run_checklist_and_explanation(intake, eligibility)
    timings["checklist_explanation"] = int((time.perf_counter() - explanation_started) * 1000)
    audit.events.append(
        AuditEvent(
            component="checklist_explanation",
            event_type="delivery_complete",
            timestamp=created_at,
            details={"status": checklist.final_status.value},
        )
    )
    timings["total"] = int((time.perf_counter() - started) * 1000)
    audit.timings_ms = timings

    return SessionState(
        session_meta=SessionMeta(
            session_id=session_id,
            run_id=run_id,
            case_id=str(case["case_id"]),
            created_at=created_at,
        ),
        input={"raw_form_input": case, "source": "csv_loader"},
        intake=intake,
        eligibility_prioritization=eligibility,
        checklist_explanation=checklist,
        audit=audit,
    )


def summarize_case(
    state: SessionState,
) -> tuple[dict[str, str], EligibilityPrioritizationOutput, ChecklistExplanationOutput]:
    statuses = {
        assessment.program_name: assessment.status.value
        for assessment in state.eligibility_prioritization.program_assessments
    }
    return statuses, state.eligibility_prioritization, state.checklist_explanation
