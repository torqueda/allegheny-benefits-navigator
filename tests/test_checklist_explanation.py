from pathlib import Path

import pytest

from src.loaders.expected_results import load_expected_results
from src.loaders.rules import load_checklist_requirements
from src.loaders.test_cases import load_test_cases
from src.models.common import DecisionStatus, FinalStatus, IntakeStatus, ProgramStatus
from src.models.eligibility import EligibilityPrioritizationOutput, ProgramAssessment
from src.models.intake import HouseholdProfile, IntakeOutput
from src.pipeline.components import _generate_program_checklist, checklist_and_explanation
from src.pipeline.session_state import (
    create_initial_session_state,
    update_session_with_eligibility_output,
    update_session_with_intake_output,
)


def _make_assessment(
    program_name: str,
    status: ProgramStatus,
    *,
    missing_evidence: list[str] | None = None,
    caveats: list[str] | None = None,
) -> ProgramAssessment:
    return ProgramAssessment(
        program_name=program_name,
        status=status,
        matched_conditions=[],
        failed_conditions=[],
        missing_evidence=missing_evidence or [],
        caveats=caveats or [],
        source_refs=[],
    )


def _build_session(
    profile: HouseholdProfile,
    *,
    missing_fields: list[str] | None = None,
    contradictory_fields: list[str] | None = None,
    intake_status: IntakeStatus = IntakeStatus.complete,
    assessments: list[ProgramAssessment] | None = None,
    eligible_programs: list[str] | None = None,
    inapplicable_programs: list[str] | None = None,
    uncertainty_flags: list[str] | None = None,
    priority_order: list[str] | None = None,
    priority_rationale: list[str] | None = None,
    decision_status: DecisionStatus = DecisionStatus.ready_for_explanation,
):
    session = create_initial_session_state()
    session = update_session_with_intake_output(
        session,
        IntakeOutput(
            household_profile=profile,
            missing_fields=missing_fields or [],
            contradictory_fields=contradictory_fields or [],
            validation_warnings=[],
            intake_status=intake_status,
            clarification_questions=[],
        ),
    )
    session = update_session_with_eligibility_output(
        session,
        EligibilityPrioritizationOutput(
            program_assessments=assessments or [],
            eligible_or_likely_programs=eligible_programs or [],
            inapplicable_programs=inapplicable_programs or [],
            uncertainty_flags=uncertainty_flags or [],
            priority_order=priority_order or [],
            priority_rationale=priority_rationale or [],
            decision_status=decision_status,
        ),
    )
    return session


def test_load_checklist_requirements_success() -> None:
    requirements = load_checklist_requirements("data/rules_source")
    assert len(requirements) > 0
    assert requirements[0].program_id == "snap"
    assert requirements[0].item_id == "SNAP_DOC_01"


def test_load_checklist_requirements_fails_on_missing_required_columns(tmp_path: Path) -> None:
    checklist_csv = tmp_path / "checklist_requirements.csv"
    checklist_csv.write_text(
        "program_id,pathway_id,document_name\nsnap,all,Proof of income\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        load_checklist_requirements(tmp_path)


def test_generate_program_checklist_for_snap() -> None:
    requirements = load_checklist_requirements("data/rules_source")
    items, caveats, mapping_found = _generate_program_checklist(
        "SNAP",
        HouseholdProfile(food_insecurity_signal="clear"),
        requirements,
    )

    assert mapping_found is True
    assert any("Proof of household income for the last 30 days" in item for item in items)
    assert any(item.startswith("Required:") for item in items)
    assert caveats == []


def test_generate_program_checklist_for_medicaid_chip() -> None:
    requirements = load_checklist_requirements("data/rules_source")
    items, caveats, mapping_found = _generate_program_checklist(
        "Medicaid/CHIP",
        HouseholdProfile(elderly_or_disabled_member=True),
        requirements,
    )

    assert mapping_found is True
    assert any("Employer and income information" in item for item in items)
    assert any("Resource / asset information" in item for item in items)
    assert caveats == []


def test_generate_program_checklist_for_liheap() -> None:
    requirements = load_checklist_requirements("data/rules_source")
    items, caveats, mapping_found = _generate_program_checklist(
        "LIHEAP",
        HouseholdProfile(heating_assistance_need=True, utility_burden="high"),
        requirements,
    )

    assert mapping_found is True
    assert any("Recent bill from the main heating source" in item for item in items)
    assert any("Proof of household income for each household member" in item for item in items)
    assert any("heating costs are included in rent" in caveat for caveat in caveats)


def test_generate_program_checklist_handles_missing_mapping_gracefully() -> None:
    requirements = load_checklist_requirements("data/rules_source")
    items, caveats, mapping_found = _generate_program_checklist(
        "Unsupported Program",
        HouseholdProfile(),
        requirements,
    )

    assert mapping_found is False
    assert items == []
    assert any("not available" in caveat for caveat in caveats)


def test_checklist_and_explanation_reflects_priority_and_expected_fixture_programs() -> None:
    case = next(row for row in load_test_cases("data/test_cases.csv") if row.case_id == "TC01")
    expected = next(row for row in load_expected_results("data/expected_results.csv") if row.case_id == "TC01")
    profile = HouseholdProfile(**case.model_dump(exclude={"case_id", "case_type", "scenario_summary", "missing_fields", "contradictory_fields"}))
    session = _build_session(
        profile,
        assessments=[
            _make_assessment("SNAP", ProgramStatus.likely_applicable),
            _make_assessment("Medicaid/CHIP", ProgramStatus.likely_applicable),
            _make_assessment("LIHEAP", ProgramStatus.likely_applicable),
        ],
        eligible_programs=["SNAP", "Medicaid/CHIP", "LIHEAP"],
        priority_order=["LIHEAP", "SNAP", "Medicaid/CHIP"],
        priority_rationale=["LIHEAP first", "SNAP second", "Medicaid/CHIP third"],
        decision_status=DecisionStatus.ready_for_explanation,
    )

    output = checklist_and_explanation(session)

    assert output.recommended_programs == expected.expected_priority_order
    assert set(output.recommended_programs) == set(expected.expected_checklist_programs or [])
    assert "prescreen only" in output.user_explanation.lower()
    assert "LIHEAP, SNAP, and Medicaid/CHIP" in output.user_explanation
    assert "not an official determination" in output.user_explanation.lower()
    assert output.final_status == FinalStatus.delivered


def test_checklist_and_explanation_preserves_uncertainty() -> None:
    session = _build_session(
        HouseholdProfile(
            county="Allegheny",
            num_adults=2,
            num_children=1,
            food_insecurity_signal="possible",
            heating_assistance_need=True,
            utility_burden="high",
        ),
        missing_fields=["household_income_total"],
        intake_status=IntakeStatus.needs_clarification,
        assessments=[
            _make_assessment(
                "SNAP",
                ProgramStatus.likely_applicable,
                missing_evidence=["household_income_total"],
            ),
            _make_assessment(
                "Medicaid/CHIP",
                ProgramStatus.uncertain,
                missing_evidence=["citizenship_status"],
            ),
        ],
        eligible_programs=["SNAP"],
        uncertainty_flags=["SNAP: more information may change this prescreen (household_income_total)."],
        decision_status=DecisionStatus.ambiguous,
    )

    output = checklist_and_explanation(session)

    assert output.recommended_programs == ["SNAP"]
    assert output.final_status == FinalStatus.delivered_with_uncertainty
    assert any("still missing" in caveat for caveat in output.visible_caveats)
    assert "important caveat" in output.user_explanation.lower()


def test_checklist_and_explanation_handles_no_clear_match_without_denial_language() -> None:
    session = _build_session(
        HouseholdProfile(
            county="Allegheny",
            num_adults=2,
            num_children=0,
            household_income_total=7200,
            employment_status="full_time",
            insurance_status="insured",
        ),
        assessments=[
            _make_assessment("SNAP", ProgramStatus.likely_inapplicable),
            _make_assessment("Medicaid/CHIP", ProgramStatus.likely_inapplicable),
            _make_assessment("LIHEAP", ProgramStatus.likely_inapplicable),
        ],
        inapplicable_programs=["SNAP", "Medicaid/CHIP", "LIHEAP"],
        decision_status=DecisionStatus.ready_for_explanation,
    )

    output = checklist_and_explanation(session)

    assert output.recommended_programs == []
    assert "no clear match" in output.user_explanation.lower()
    assert "not a denial" in output.user_explanation.lower()
    assert output.final_status == FinalStatus.delivered


def test_checklist_and_explanation_sets_needs_human_followup_for_conflicting_intake() -> None:
    session = _build_session(
        HouseholdProfile(
            county="Allegheny",
            num_adults=1,
            num_children=1,
            household_income_total=0,
            employment_status="full_time",
            food_insecurity_signal="clear",
            heating_assistance_need=True,
        ),
        contradictory_fields=["employment_status vs monthly_earned_income"],
        assessments=[_make_assessment("SNAP", ProgramStatus.likely_applicable)],
        eligible_programs=["SNAP"],
        priority_order=["SNAP"],
        decision_status=DecisionStatus.ready_for_explanation,
    )

    output = checklist_and_explanation(session)

    assert output.final_status == FinalStatus.needs_human_followup
    assert any("caseworker" in note.lower() for note in output.referral_notes)
