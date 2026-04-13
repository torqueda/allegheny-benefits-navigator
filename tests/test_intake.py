import pytest

from src.models.common import IntakeStatus
from src.models.intake import HouseholdProfile, IntakeOutput
from src.models.session import SessionState
from src.pipeline.components import intake
from src.pipeline.session_state import create_initial_session_state


def test_intake_normalizes_whitespace_and_empty_strings() -> None:
    session = create_initial_session_state()
    raw = {"county": " Allegheny ", "zip_code": "", "num_adults": " 1 ", "language_or_stress_notes": " test "}
    output = intake(session, raw)
    assert output.household_profile.county == "Allegheny"
    assert output.household_profile.zip_code is None
    assert output.household_profile.num_adults == 1
    assert output.household_profile.language_or_stress_notes == "test"


def test_intake_parses_booleans() -> None:
    session = create_initial_session_state()
    raw = {"child_under_5": "true", "pregnant_household_member": "false", "heating_assistance_need": "True"}
    output = intake(session, raw)
    assert output.household_profile.child_under_5 is True
    assert output.household_profile.pregnant_household_member is False
    assert output.household_profile.heating_assistance_need is True


def test_intake_validates_numeric_fields() -> None:
    session = create_initial_session_state()
    raw = {"num_adults": "2", "monthly_earned_income": "1500.5", "housing_cost": "-100"}
    output = intake(session, raw)
    assert output.household_profile.num_adults == 2
    assert output.household_profile.monthly_earned_income == 1500.5
    assert output.household_profile.housing_cost is None  # Negative invalid


def test_intake_detects_missing_required_fields() -> None:
    session = create_initial_session_state()
    raw = {"county": "Allegheny"}  # Missing num_adults, num_children, income
    output = intake(session, raw)
    assert "num_adults" in output.missing_fields
    assert "num_children" in output.missing_fields
    assert "monthly_earned_income" in output.missing_fields


def test_intake_detects_contradictions() -> None:
    session = create_initial_session_state()
    raw = {
        "county": "Allegheny", "num_adults": 1, "num_children": 0,
        "child_under_5": "true",  # Contradiction
        "monthly_earned_income": 1000, "monthly_unearned_income": 0, "household_income_total": 1200  # Income mismatch
    }
    output = intake(session, raw)
    assert "num_children vs child_under_5" in output.contradictory_fields
    assert "income components vs total" in output.contradictory_fields


def test_intake_sets_complete_status_for_valid_input() -> None:
    session = create_initial_session_state()
    raw = {
        "county": "Allegheny", "num_adults": 1, "num_children": 0,
        "monthly_earned_income": 1000, "housing_cost": 800
    }
    output = intake(session, raw)
    assert output.intake_status == IntakeStatus.complete
    assert not output.missing_fields
    assert not output.contradictory_fields


def test_intake_sets_needs_clarification_for_minor_issues() -> None:
    session = create_initial_session_state()
    raw = {
        "county": "Allegheny", "num_adults": 1, "num_children": 0,
        "monthly_earned_income": 1000  # Missing housing_cost, but not required
    }
    output = intake(session, raw)
    assert output.intake_status == IntakeStatus.complete  # Since housing_cost not required


def test_intake_sets_insufficient_data_for_major_issues() -> None:
    session = create_initial_session_state()
    raw = {
        "county": "Allegheny", "num_children": 0,  # Missing num_adults, income
        "child_under_5": "true"  # Contradiction
    }
    output = intake(session, raw)
    assert output.intake_status == IntakeStatus.insufficient_data


def test_intake_handles_out_of_scope_geography() -> None:
    session = create_initial_session_state()
    raw = {"county": "Philadelphia", "num_adults": 1, "num_children": 0, "monthly_earned_income": 1000}
    output = intake(session, raw)
    assert output.intake_status == IntakeStatus.insufficient_data
    assert "Geography out of scope" in output.validation_warnings


def test_intake_generates_clarification_questions() -> None:
    session = create_initial_session_state()
    raw = {"county": "Allegheny", "num_adults": 1}  # Missing num_children, income
    output = intake(session, raw)
    assert len(output.clarification_questions) > 0
    assert any("num_children" in q for q in output.clarification_questions)