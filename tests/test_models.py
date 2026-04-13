import pytest
from pydantic import ValidationError

from src.models.common import DecisionStatus, FinalStatus, IntakeStatus, ProgramStatus
from src.models.eligibility import EligibilityPrioritizationOutput, ProgramAssessment
from src.models.explanation import ChecklistExplanationOutput
from src.models.intake import HouseholdProfile, IntakeOutput
from src.models.session import Audit, AuditError, AuditEvent, RunInput, SessionMeta, SessionState


def test_household_profile_constructs_with_optional_fields() -> None:
    profile = HouseholdProfile(
        county="Allegheny",
        zip_code="15213",
        num_adults=2,
        num_children=1,
        child_under_5=True,
        pregnant_household_member=False,
        elderly_or_disabled_member=False,
        employment_status="employed",
        monthly_earned_income=1800.0,
        monthly_unearned_income=0.0,
        household_income_total=1800.0,
        housing_cost=900.0,
        utility_burden="high",
        heating_assistance_need=True,
        insurance_status="uninsured",
        recent_job_loss=False,
        food_insecurity_signal="clear",
        language_or_stress_notes="Needs English support",
    )

    assert profile.county == "Allegheny"
    assert profile.monthly_earned_income == 1800.0


def test_intake_output_requires_household_profile() -> None:
    with pytest.raises(ValidationError):
        IntakeOutput(
            missing_fields=[],
            contradictory_fields=[],
            validation_warnings=[],
            intake_status=IntakeStatus.complete,
            clarification_questions=[],
        )


def test_program_assessment_enum_validation() -> None:
    assessment = ProgramAssessment(
        program_name="SNAP",
        status=ProgramStatus.likely_applicable,
        matched_conditions=["income_threshold"],
        failed_conditions=[],
        missing_evidence=[],
        caveats=["pending verification"],
        source_refs=["rulebook_section_1"],
    )

    assert assessment.status == ProgramStatus.likely_applicable
    assert assessment.program_name == "SNAP"


def test_checklist_explanation_requires_final_status() -> None:
    with pytest.raises(ValidationError):
        ChecklistExplanationOutput(
            checklist_items_by_program={"SNAP": ["Bring ID"]},
            recommended_programs=["SNAP"],
            next_steps=["Complete application"],
            user_explanation="You may qualify.",
            visible_caveats=["Not an official determination."],
            referral_notes=["Contact the local office."],
        )


def test_session_state_json_round_trip() -> None:
    session = SessionState(
        session_meta=SessionMeta(
            session_id="uuid",
            run_id="uuid",
            case_id="case-1",
            mode="synthetic_test",
            created_at="2026-04-12T00:00:00Z",
            app_version="1.0.0",
            ruleset_version="2026-04-12",
            template_version="v1",
            program_scope=["SNAP", "Medicaid/CHIP"],
            policy_snapshot_version="snapshot-2026-04-12",
            llm_enabled=False,
            llm_model=None,
        ),
        input=RunInput(raw_form_input={"num_adults": 2}, source="ui_form"),
        intake=IntakeOutput(
            household_profile=HouseholdProfile(),
            missing_fields=[],
            contradictory_fields=[],
            validation_warnings=[],
            intake_status=IntakeStatus.complete,
            clarification_questions=[],
        ),
        eligibility_prioritization=EligibilityPrioritizationOutput(
            program_assessments=[
                ProgramAssessment(
                    program_name="SNAP",
                    status=ProgramStatus.likely_applicable,
                    matched_conditions=[],
                    failed_conditions=[],
                    missing_evidence=[],
                    caveats=[],
                    source_refs=[],
                )
            ],
            eligible_or_likely_programs=["SNAP"],
            inapplicable_programs=[],
            uncertainty_flags=[],
            priority_order=["SNAP"],
            priority_rationale=["Highest need"],
            decision_status=DecisionStatus.ready_for_explanation,
        ),
        checklist_explanation=ChecklistExplanationOutput(
            checklist_items_by_program={"SNAP": ["Bring proof of income"]},
            recommended_programs=["SNAP"],
            next_steps=["Apply online"],
            user_explanation="Your household may qualify for SNAP.",
            visible_caveats=["This is not an official determination."],
            referral_notes=["Call the local office."],
            final_status=FinalStatus.delivered,
        ),
        audit=Audit(
            events=[
                AuditEvent(
                    component="intake",
                    event_type="validation_complete",
                    timestamp="2026-04-12T00:00:01Z",
                    details={"result": "ok"},
                )
            ],
            errors=[],
            timings_ms={"intake": 0, "eligibility_prioritization": 0, "checklist_explanation": 0, "total": 0},
        ),
    )

    payload = session.model_dump_json()
    parsed = SessionState.model_validate_json(payload)

    assert parsed.session_meta.session_id == "uuid"
    assert parsed.checklist_explanation.final_status == FinalStatus.delivered
    assert parsed.intake.intake_status == IntakeStatus.complete
