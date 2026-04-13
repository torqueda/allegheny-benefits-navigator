import pytest

from src.loaders.rules import (
    load_checklist_requirements,
    load_eligibility_rules,
    load_priority_heuristics,
    load_program_sources,
)


def test_load_eligibility_rules_returns_list() -> None:
    rules = load_eligibility_rules("data/rules_source")
    assert isinstance(rules, list)
    assert len(rules) > 0


def test_load_priority_heuristics_returns_list() -> None:
    heuristics = load_priority_heuristics("data/rules_source")
    assert isinstance(heuristics, list)
    assert len(heuristics) > 0


def test_load_program_sources_returns_list() -> None:
    sources = load_program_sources("data/rules_source")
    assert isinstance(sources, list)
    # May be empty if CSV not present, but test structure


def test_load_eligibility_rules_rejects_unsupported_operator(tmp_path) -> None:
    csv_path = tmp_path / "eligibility_rules.csv"
    csv_path.write_text(
        (
            "program_id,pathway_id,rule_id,rule_type,field_name,operator,value,"
            "outcome_if_true,uncertainty_if_missing,source_id,citation_note\n"
            "snap,pathway_1,RULE_1,inclusion,household_income_total,!=,1000,"
            "likely_applicable,uncertain,SNAP_SRC_01,Example note\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported operator"):
        load_eligibility_rules(tmp_path)


def test_load_priority_heuristics_rejects_unsupported_program_id(tmp_path) -> None:
    csv_path = tmp_path / "priority_heuristics.csv"
    csv_path.write_text(
        (
            "program_id,heuristic_id,field_name,operator,value,weight,reason_text,source_id\n"
            "wic,H_1,food_insecurity_signal,==,clear,3,Reason,SRC_1\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported program_id"):
        load_priority_heuristics(tmp_path)


def test_load_checklist_requirements_rejects_unsupported_program_id(tmp_path) -> None:
    csv_path = tmp_path / "checklist_requirements.csv"
    csv_path.write_text(
        (
            "program_id,pathway_id,item_id,document_name,required_or_likely,source_id,citation_note\n"
            "wic,all,ITEM_1,Document,required,SRC_1,Note\n"
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unsupported program_id"):
        load_checklist_requirements(tmp_path)
