from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

import pandas as pd
from pydantic import BaseModel, ConfigDict


class EligibilityRule(BaseModel):
    program_id: str
    pathway_id: str
    rule_id: str
    rule_type: str  # inclusion, ambiguity
    field_name: str
    operator: str  # ==, <=, >=, >, in, missing
    value: str  # empty for missing
    outcome_if_true: str
    uncertainty_if_missing: str
    source_id: str
    citation_note: str

    model_config = ConfigDict(extra="forbid")


class PriorityHeuristic(BaseModel):
    program_id: str
    heuristic_id: str
    field_name: str
    operator: str
    value: str
    weight: int
    reason_text: str
    source_id: str

    model_config = ConfigDict(extra="forbid")


class ProgramSource(BaseModel):
    program_id: str
    source_id: str
    source_title: str
    source_url: str
    source_type: str
    accessed_date: str
    effective_date: str
    source_scope: str

    model_config = ConfigDict(extra="forbid")


class ChecklistRequirement(BaseModel):
    program_id: str
    pathway_id: str
    item_id: str
    document_name: str
    required_or_likely: str
    source_id: str
    citation_note: str

    model_config = ConfigDict(extra="forbid")


def _read_rules_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def _validate_required_columns(
    df: pd.DataFrame,
    required_columns: Sequence[str],
    path: Path,
) -> None:
    missing_columns = [column for column in required_columns if column not in df.columns]
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns in {path.name}: {missing}")


def load_eligibility_rules(rules_dir: str | Path) -> List[EligibilityRule]:
    path = Path(rules_dir) / "eligibility_rules.csv"
    df = _read_rules_csv(path)
    _validate_required_columns(
        df,
        [
            "program_id",
            "pathway_id",
            "rule_id",
            "rule_type",
            "field_name",
            "operator",
            "value",
            "outcome_if_true",
            "uncertainty_if_missing",
            "source_id",
            "citation_note",
        ],
        path,
    )
    rules = []
    for _, row in df.iterrows():
        rules.append(EligibilityRule(**row.to_dict()))
    return rules


def load_priority_heuristics(rules_dir: str | Path) -> List[PriorityHeuristic]:
    path = Path(rules_dir) / "priority_heuristics.csv"
    df = _read_rules_csv(path)
    _validate_required_columns(
        df,
        [
            "program_id",
            "heuristic_id",
            "field_name",
            "operator",
            "value",
            "weight",
            "reason_text",
            "source_id",
        ],
        path,
    )
    heuristics = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        row_dict["weight"] = int(row_dict["weight"])
        heuristics.append(PriorityHeuristic(**row_dict))
    return heuristics


def load_program_sources(rules_dir: str | Path) -> List[ProgramSource]:
    path = Path(rules_dir) / "program_sources.csv"
    df = _read_rules_csv(path)
    _validate_required_columns(
        df,
        [
            "program_id",
            "source_id",
            "source_title",
            "source_url",
            "source_type",
            "accessed_date",
            "effective_date",
            "source_scope",
        ],
        path,
    )
    sources = []
    for _, row in df.iterrows():
        sources.append(ProgramSource(**row.to_dict()))
    return sources


def load_checklist_requirements(rules_dir: str | Path) -> List[ChecklistRequirement]:
    path = Path(rules_dir) / "checklist_requirements.csv"
    df = _read_rules_csv(path)
    _validate_required_columns(
        df,
        [
            "program_id",
            "pathway_id",
            "item_id",
            "document_name",
            "required_or_likely",
            "source_id",
            "citation_note",
        ],
        path,
    )

    requirements = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        requirement_level = row_dict["required_or_likely"].strip().lower()
        if requirement_level not in {"required", "likely"}:
            raise ValueError(
                f"Invalid required_or_likely value in {path.name}: {row_dict['required_or_likely']}"
            )
        row_dict["required_or_likely"] = requirement_level
        requirements.append(ChecklistRequirement(**row_dict))
    return requirements
