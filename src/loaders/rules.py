from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, List, Sequence

import pandas as pd
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

SUPPORTED_PROGRAM_IDS = {"snap", "medicaid", "liheap"}
SUPPORTED_RULE_TYPES = {"inclusion", "ambiguity"}
SUPPORTED_RULE_OPERATORS = {"==", "<=", ">=", ">", "in", "missing"}
SUPPORTED_HEURISTIC_OPERATORS = {"==", ">="}
SUPPORTED_SOURCE_TYPES = {"webpage", "pdf"}


def _normalize_required_text(value: Any, field_name: str) -> str:
    normalized = str(value).strip()
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    return normalized


class EligibilityRule(BaseModel):
    _program_ids: ClassVar[set[str]] = SUPPORTED_PROGRAM_IDS
    _rule_types: ClassVar[set[str]] = SUPPORTED_RULE_TYPES
    _operators: ClassVar[set[str]] = SUPPORTED_RULE_OPERATORS

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

    @field_validator("program_id", mode="before")
    @classmethod
    def _validate_program_id(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "program_id").lower()
        if normalized not in cls._program_ids:
            raise ValueError(f"Unsupported program_id: {normalized}")
        return normalized

    @field_validator("pathway_id", "rule_id", "field_name", "source_id", "citation_note", mode="before")
    @classmethod
    def _validate_required_text_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("rule_type", mode="before")
    @classmethod
    def _validate_rule_type(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "rule_type").lower()
        if normalized not in cls._rule_types:
            raise ValueError(f"Unsupported rule_type: {normalized}")
        return normalized

    @field_validator("operator", mode="before")
    @classmethod
    def _validate_operator(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "operator")
        if normalized not in cls._operators:
            raise ValueError(f"Unsupported operator: {normalized}")
        return normalized

    @field_validator("outcome_if_true", "uncertainty_if_missing", mode="before")
    @classmethod
    def _validate_outcome_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @model_validator(mode="after")
    def _validate_missing_operator_value(self) -> "EligibilityRule":
        if self.operator == "missing" and self.value.strip():
            raise ValueError("value must be blank when operator is 'missing'")
        if self.operator != "missing" and not self.value.strip():
            raise ValueError("value must be non-empty when operator is not 'missing'")
        return self


class PriorityHeuristic(BaseModel):
    _program_ids: ClassVar[set[str]] = SUPPORTED_PROGRAM_IDS
    _operators: ClassVar[set[str]] = SUPPORTED_HEURISTIC_OPERATORS

    program_id: str
    heuristic_id: str
    field_name: str
    operator: str
    value: str
    weight: int
    reason_text: str
    source_id: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("program_id", mode="before")
    @classmethod
    def _validate_program_id(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "program_id").lower()
        if normalized not in cls._program_ids:
            raise ValueError(f"Unsupported program_id: {normalized}")
        return normalized

    @field_validator("heuristic_id", "field_name", "value", "reason_text", "source_id", mode="before")
    @classmethod
    def _validate_required_text_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("operator", mode="before")
    @classmethod
    def _validate_operator(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "operator")
        if normalized not in cls._operators:
            raise ValueError(f"Unsupported operator: {normalized}")
        return normalized


class ProgramSource(BaseModel):
    _program_ids: ClassVar[set[str]] = SUPPORTED_PROGRAM_IDS

    program_id: str
    source_id: str
    source_title: str
    source_url: str
    source_type: str
    accessed_date: str
    effective_date: str
    source_scope: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("program_id", mode="before")
    @classmethod
    def _validate_program_id(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "program_id").lower()
        if normalized not in cls._program_ids:
            raise ValueError(f"Unsupported program_id: {normalized}")
        return normalized

    @field_validator(
        "source_id",
        "source_title",
        "source_url",
        "accessed_date",
        "source_scope",
        mode="before",
    )
    @classmethod
    def _validate_required_text_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)

    @field_validator("source_type", mode="before")
    @classmethod
    def _validate_source_type(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "source_type").lower()
        if normalized not in SUPPORTED_SOURCE_TYPES:
            raise ValueError(f"Unsupported source_type: {normalized}")
        return normalized


class ChecklistRequirement(BaseModel):
    _program_ids: ClassVar[set[str]] = SUPPORTED_PROGRAM_IDS

    program_id: str
    pathway_id: str
    item_id: str
    document_name: str
    required_or_likely: str
    source_id: str
    citation_note: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("program_id", mode="before")
    @classmethod
    def _validate_program_id(cls, value: Any) -> str:
        normalized = _normalize_required_text(value, "program_id").lower()
        if normalized not in cls._program_ids:
            raise ValueError(f"Unsupported program_id: {normalized}")
        return normalized

    @field_validator(
        "pathway_id",
        "item_id",
        "document_name",
        "required_or_likely",
        "source_id",
        "citation_note",
        mode="before",
    )
    @classmethod
    def _validate_required_text_fields(cls, value: Any, info) -> str:
        return _normalize_required_text(value, info.field_name)


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
