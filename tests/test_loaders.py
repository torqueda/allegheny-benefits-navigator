import pytest

from src.loaders.expected_results import ExpectedResultRow, load_expected_results
from src.loaders.test_cases import TestCaseRow, load_test_cases


def test_load_test_cases_returns_expected_count() -> None:
    rows = load_test_cases("data/test_cases.csv")
    assert len(rows) == 10
    assert rows[0].case_id == "TC01"
    assert rows[0].scenario_summary.startswith("Single adult in Pittsburgh")


def test_test_case_list_fields_parse_json_arrays() -> None:
    row = load_test_cases("data/test_cases.csv")[3]
    assert row.case_id == "TC04"
    assert row.missing_fields == ["monthly_earned_income", "household_income_total"]
    assert row.contradictory_fields == []


def test_test_case_blank_text_fields_normalize_to_none() -> None:
    row = load_test_cases("data/test_cases.csv")[1]
    assert row.language_or_stress_notes is None


def test_load_expected_results_returns_expected_count() -> None:
    rows = load_expected_results("data/expected_results.csv")
    assert len(rows) == 10
    assert rows[0].case_id == "TC01"
    assert rows[0].expected_snap is not None
    assert rows[0].expected_snap.name == "likely_applicable"


def test_expected_results_blank_fields_are_none() -> None:
    row = load_expected_results("data/expected_results.csv")[1]
    assert row.expected_priority_order == []
    assert row.expected_checklist_programs is None
    assert row.expected_explanation_notes is not None


def test_expected_priority_order_parses_to_list() -> None:
    row = load_expected_results("data/expected_results.csv")[0]
    assert row.expected_priority_order == ["LIHEAP", "SNAP", "Medicaid/CHIP"]


def test_expected_uncertainty_flag_parses_boolean() -> None:
    row = load_expected_results("data/expected_results.csv")[3]
    assert row.expected_uncertainty_flag is True


def test_missing_case_id_raises_value_error_for_test_cases() -> None:
    with pytest.raises(ValueError):
        TestCaseRow(
            case_id="",
            case_type="clear_eligible",
            scenario_summary="Summary",
            county="Allegheny",
            zip_code="15219",
            employment_status="part_time",
            utility_burden="high",
            insurance_status="uninsured",
            missing_fields="[]",
            contradictory_fields="[]",
        )


def test_missing_case_id_raises_value_error_for_expected_results() -> None:
    with pytest.raises(ValueError):
        ExpectedResultRow(
            case_id="",
            expected_snap="likely_applicable",
        )
