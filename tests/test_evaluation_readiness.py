from src.loaders.expected_results import ExpectedResultRow, load_expected_results
from src.loaders.test_cases import TestCaseRow, load_test_cases
from src.models.common import DecisionStatus, FinalStatus, IntakeStatus, ProgramStatus
from src.models.session import SessionState
from src.pipeline.controller import run_pipeline

SUPPORTED_PROGRAMS = ["SNAP", "Medicaid/CHIP", "LIHEAP"]
EXPECTED_STATUS_FIELDS = {
    "SNAP": "expected_snap",
    "Medicaid/CHIP": "expected_medicaid_chip",
    "LIHEAP": "expected_liheap",
}


def _case_to_raw_input(case: TestCaseRow) -> dict:
    return case.model_dump(
        exclude={"case_id", "case_type", "scenario_summary", "missing_fields", "contradictory_fields"}
    )


def _program_statuses(session: SessionState) -> dict[str, ProgramStatus]:
    return {
        assessment.program_name: assessment.status
        for assessment in session.eligibility_prioritization.program_assessments
    }


def _filter_supported(values: list[str] | None) -> list[str] | None:
    if values is None:
        return None
    return [value for value in values if value in SUPPORTED_PROGRAMS]


def test_fixture_driven_evaluation_readiness() -> None:
    test_cases = load_test_cases("data/test_cases.csv")
    expected_rows = {row.case_id: row for row in load_expected_results("data/expected_results.csv")}

    for case in test_cases:
        raw_form_input = _case_to_raw_input(case)
        session = run_pipeline(case_id=case.case_id, raw_form_input=raw_form_input, ambiguity_mode=True)
        repeated_session = run_pipeline(case_id=case.case_id, raw_form_input=raw_form_input, ambiguity_mode=True)
        expected = expected_rows[case.case_id]

        serialized = session.model_dump_json()
        parsed = SessionState.model_validate_json(serialized)

        assert parsed.session_meta.case_id == case.case_id
        assert parsed.session_meta.program_scope == SUPPORTED_PROGRAMS
        assert parsed.intake.intake_status in {
            IntakeStatus.complete,
            IntakeStatus.needs_clarification,
            IntakeStatus.insufficient_data,
        }
        assert parsed.eligibility_prioritization.decision_status in {
            DecisionStatus.ready_for_explanation,
            DecisionStatus.ambiguous,
            DecisionStatus.insufficient_data,
        }
        assert parsed.checklist_explanation.final_status in {
            FinalStatus.delivered,
            FinalStatus.delivered_with_uncertainty,
            FinalStatus.needs_human_followup,
        }

        assert session.eligibility_prioritization.model_dump() == repeated_session.eligibility_prioritization.model_dump()
        assert session.checklist_explanation.model_dump() == repeated_session.checklist_explanation.model_dump()

        statuses = _program_statuses(session)
        assert set(statuses) == set(SUPPORTED_PROGRAMS)
        for program in SUPPORTED_PROGRAMS:
            expected_status = getattr(expected, EXPECTED_STATUS_FIELDS[program])
            if expected_status is not None:
                assert statuses[program] == expected_status

        if expected.expected_uncertainty_flag is not None:
            assert bool(session.eligibility_prioritization.uncertainty_flags) == expected.expected_uncertainty_flag

        expected_priority = _filter_supported(expected.expected_priority_order) or []
        if expected_priority:
            assert set(session.eligibility_prioritization.priority_order) == set(expected_priority)

        expected_checklist = _filter_supported(expected.expected_checklist_programs)
        if expected_checklist is not None:
            assert set(session.checklist_explanation.recommended_programs) == set(expected_checklist)

        if expected_checklist:
            assert "prescreen" in session.checklist_explanation.user_explanation.lower()
            assert "official determination" in session.checklist_explanation.user_explanation.lower()
        else:
            assert "no clear match" in session.checklist_explanation.user_explanation.lower()


def test_priority_order_matches_expected_for_stable_current_scope_cases() -> None:
    expected_rows = {row.case_id: row for row in load_expected_results("data/expected_results.csv")}

    for case_id in ["TC04", "TC09", "TC10"]:
        case = next(row for row in load_test_cases("data/test_cases.csv") if row.case_id == case_id)
        session = run_pipeline(
            case_id=case.case_id,
            raw_form_input=_case_to_raw_input(case),
            ambiguity_mode=True,
        )
        expected = expected_rows[case.case_id]

        assert session.eligibility_prioritization.priority_order == _filter_supported(expected.expected_priority_order)
