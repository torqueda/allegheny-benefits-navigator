import pytest

from src.models.common import DecisionStatus, FinalStatus, IntakeStatus, ProgramStatus
from src.models.eligibility import EligibilityPrioritizationOutput, ProgramAssessment
from src.models.explanation import ChecklistExplanationOutput
from src.models.intake import HouseholdProfile, IntakeOutput
from src.models.session import SessionState
from src.pipeline.controller import run_pipeline


def _make_assessment(program_name: str, status: ProgramStatus) -> ProgramAssessment:
    return ProgramAssessment(
        program_name=program_name,
        status=status,
        matched_conditions=[],
        failed_conditions=[],
        missing_evidence=[],
        caveats=[],
        source_refs=[],
    )


def _make_intake_output(status: IntakeStatus = IntakeStatus.complete) -> IntakeOutput:
    return IntakeOutput(
        household_profile=HouseholdProfile(
            county="Allegheny",
            num_adults=1,
            num_children=0,
            monthly_earned_income=900,
            household_income_total=900,
            employment_status="part_time",
            insurance_status="uninsured",
            food_insecurity_signal="clear",
            heating_assistance_need=True,
            utility_burden="high",
        ),
        missing_fields=[],
        contradictory_fields=[],
        validation_warnings=[],
        intake_status=status,
        clarification_questions=[],
    )


def _make_eligibility_output(decision_status: DecisionStatus) -> EligibilityPrioritizationOutput:
    return EligibilityPrioritizationOutput(
        program_assessments=[
            _make_assessment("SNAP", ProgramStatus.likely_applicable),
            _make_assessment("Medicaid/CHIP", ProgramStatus.likely_applicable),
            _make_assessment("LIHEAP", ProgramStatus.likely_applicable),
        ],
        eligible_or_likely_programs=["SNAP", "Medicaid/CHIP", "LIHEAP"],
        inapplicable_programs=[],
        uncertainty_flags=(
            ["Medicaid/CHIP: more information may change this prescreen (citizenship_status)."]
            if decision_status == DecisionStatus.ambiguous
            else []
        ),
        priority_order=["LIHEAP", "SNAP", "Medicaid/CHIP"],
        priority_rationale=["LIHEAP first", "SNAP second", "Medicaid/CHIP third"],
        decision_status=decision_status,
    )


def _make_checklist_output(final_status: FinalStatus = FinalStatus.delivered) -> ChecklistExplanationOutput:
    return ChecklistExplanationOutput(
        checklist_items_by_program={"SNAP": ["Required: Proof of household income for the last 30 days"]},
        recommended_programs=["SNAP"],
        next_steps=["Gather the listed documents for any program you want to pursue."],
        user_explanation="This is a prescreen only, not an official determination.",
        visible_caveats=["This is prescreening only."],
        referral_notes=["Use official Pennsylvania source materials to confirm the latest requirements for SNAP."],
        final_status=final_status,
    )


def test_run_pipeline_creates_session_state() -> None:
    session = run_pipeline(case_id="TC01", raw_form_input={"num_adults": 1})
    assert isinstance(session, SessionState)
    assert session.session_meta.case_id == "TC01"
    assert session.input.raw_form_input == {"num_adults": 1}


def test_run_pipeline_stops_at_intake_if_handoff_is_not_allowed() -> None:
    session = run_pipeline(raw_form_input={"county": "Allegheny", "num_adults": 1})
    assert session.intake.intake_status == IntakeStatus.needs_clarification
    assert session.eligibility_prioritization.decision_status == DecisionStatus.insufficient_data


@pytest.mark.parametrize(
    "decision_status",
    [DecisionStatus.ready_for_explanation, DecisionStatus.ambiguous],
)
def test_run_pipeline_reaches_checklist_for_allowed_eligibility_handoffs(
    monkeypatch: pytest.MonkeyPatch,
    decision_status: DecisionStatus,
) -> None:
    monkeypatch.setattr("src.pipeline.controller.intake", lambda session, raw: _make_intake_output())
    monkeypatch.setattr(
        "src.pipeline.controller.eligibility_and_prioritization",
        lambda session: _make_eligibility_output(decision_status),
    )
    monkeypatch.setattr(
        "src.pipeline.controller.checklist_and_explanation",
        lambda session: _make_checklist_output(
            FinalStatus.delivered_with_uncertainty
            if decision_status == DecisionStatus.ambiguous
            else FinalStatus.delivered
        ),
    )

    session = run_pipeline(raw_form_input={"county": "Allegheny"})

    assert session.checklist_explanation.user_explanation
    assert len(session.audit.events) == 3
    assert session.audit.events[2].component == "checklist_explanation"


def test_run_pipeline_allows_ambiguity_mode_handoff() -> None:
    session = run_pipeline(
        raw_form_input={"county": "Allegheny", "num_adults": 1, "num_children": 0},
        ambiguity_mode=True,
    )
    assert session.intake.intake_status == IntakeStatus.needs_clarification
    assert session.eligibility_prioritization.decision_status == DecisionStatus.ambiguous
    assert session.checklist_explanation.final_status == FinalStatus.delivered_with_uncertainty


def test_run_pipeline_updates_session_with_checklist_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    checklist_output = ChecklistExplanationOutput(
        checklist_items_by_program={
            "SNAP": ["Required: Proof of household income for the last 30 days"]
        },
        recommended_programs=["SNAP"],
        next_steps=[
            "Gather the listed documents for any program you want to pursue.",
            "Review the likely application requirements for SNAP using official Pennsylvania program materials.",
        ],
        user_explanation="This is a prescreen only, not an official determination.",
        visible_caveats=["This is prescreening only.", "This is not an official determination."],
        referral_notes=["Use official Pennsylvania source materials to confirm the latest requirements for SNAP."],
        final_status=FinalStatus.delivered,
    )

    monkeypatch.setattr("src.pipeline.controller.intake", lambda session, raw: _make_intake_output())
    monkeypatch.setattr(
        "src.pipeline.controller.eligibility_and_prioritization",
        lambda session: _make_eligibility_output(DecisionStatus.ready_for_explanation),
    )
    monkeypatch.setattr(
        "src.pipeline.controller.checklist_and_explanation",
        lambda session: checklist_output,
    )

    session = run_pipeline(raw_form_input={"county": "Allegheny"})

    assert session.checklist_explanation.checklist_items_by_program == checklist_output.checklist_items_by_program
    assert session.checklist_explanation.recommended_programs == ["SNAP"]
    assert session.checklist_explanation.visible_caveats == checklist_output.visible_caveats
    assert session.checklist_explanation.user_explanation == checklist_output.user_explanation
    assert session.checklist_explanation.final_status == FinalStatus.delivered
    assert session.audit.timings_ms["total"] > 0
