import pytest

from src.models.common import DecisionStatus, FinalStatus, IntakeStatus
from src.models.session import SessionState
from src.pipeline.controller import run_pipeline


def test_run_pipeline_creates_session_state() -> None:
    session = run_pipeline(case_id="TC01", raw_form_input={"num_adults": 1})
    assert isinstance(session, SessionState)
    assert session.session_meta.case_id == "TC01"
    assert session.input.raw_form_input == {"num_adults": 1}


def test_run_pipeline_executes_components_in_order() -> None:
    session = run_pipeline()
    # Check that intake was called (status set)
    assert session.intake.intake_status == IntakeStatus.complete
    # Check that eligibility was called
    assert session.eligibility_prioritization.decision_status == DecisionStatus.ready_for_explanation
    # Check that checklist was called
    assert session.checklist_explanation.final_status == FinalStatus.delivered


def test_run_pipeline_adds_audit_events() -> None:
    session = run_pipeline()
    events = session.audit.events
    assert len(events) == 3  # intake, eligibility, checklist
    assert events[0].component == "intake"
    assert events[1].component == "eligibility_prioritization"
    assert events[2].component == "checklist_explanation"


def test_run_pipeline_adds_timings() -> None:
    session = run_pipeline()
    timings = session.audit.timings_ms
    assert "total" in timings
    assert timings["total"] > 0