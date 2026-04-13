from __future__ import annotations

from pathlib import Path
from typing import List

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
    source_id: str
    source_name: str
    source_type: str
    effective_date: str
    url: str
    notes: str

    model_config = ConfigDict(extra="forbid")


def load_eligibility_rules(rules_dir: str | Path) -> List[EligibilityRule]:
    path = Path(rules_dir) / "eligibility_rules.csv"
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rules = []
    for _, row in df.iterrows():
        rules.append(EligibilityRule(**row.to_dict()))
    return rules


def load_priority_heuristics(rules_dir: str | Path) -> List[PriorityHeuristic]:
    path = Path(rules_dir) / "priority_heuristics.csv"
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    heuristics = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        row_dict["weight"] = int(row_dict["weight"])
        heuristics.append(PriorityHeuristic(**row_dict))
    return heuristics


def load_program_sources(rules_dir: str | Path) -> List[ProgramSource]:
    path = Path(rules_dir) / "program_sources.csv"
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    sources = []
    for _, row in df.iterrows():
        sources.append(ProgramSource(**row.to_dict()))
    return sources