import pytest

from src.loaders.rules import load_eligibility_rules, load_priority_heuristics
from src.models.common import ProgramStatus
from src.models.intake import HouseholdProfile
from src.pipeline.components import _evaluate_program, _prioritize_programs


def test_load_eligibility_rules() -> None:
    rules = load_eligibility_rules("data/rules_source")
    assert len(rules) > 0
    assert rules[0].program_id == "snap"


def test_load_priority_heuristics() -> None:
    heuristics = load_priority_heuristics("data/rules_source")
    assert len(heuristics) > 0
    assert heuristics[0].program_id == "snap"


def test_evaluate_program_snap_eligible() -> None:
    rules = load_eligibility_rules("data/rules_source")
    profile = HouseholdProfile(
        county="Allegheny", num_adults=1, num_children=0, household_income_total=1000
    )
    assessment = _evaluate_program("SNAP", profile, 1, rules)
    assert assessment.status == ProgramStatus.likely_applicable
    assert "SNAP_R_01_INCOME" in assessment.matched_conditions


def test_evaluate_program_snap_ineligible() -> None:
    rules = load_eligibility_rules("data/rules_source")
    profile = HouseholdProfile(
        county="Allegheny", num_adults=1, num_children=0, household_income_total=3000
    )
    assessment = _evaluate_program("SNAP", profile, 1, rules)
    assert assessment.status == ProgramStatus.likely_inapplicable


def test_evaluate_program_uncertain_missing_income() -> None:
    rules = load_eligibility_rules("data/rules_source")
    profile = HouseholdProfile(
        county="Allegheny", num_adults=1, num_children=0, household_income_total=None
    )
    assessment = _evaluate_program("SNAP", profile, 1, rules)
    assert assessment.status == ProgramStatus.uncertain
    assert "household_income_total" in assessment.missing_evidence


def test_prioritize_programs() -> None:
    heuristics = load_priority_heuristics("data/rules_source")
    profile = HouseholdProfile(
        county="Allegheny", num_adults=1, num_children=1, food_insecurity_signal="clear"
    )
    eligible = ["SNAP", "LIHEAP"]
    order, rationale = _prioritize_programs(eligible, profile, heuristics)
    assert "LIHEAP" in order  # Higher priority for heating need, but since not set, SNAP first
    assert len(rationale) == 2