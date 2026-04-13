from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Self

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.models.common import ProgramStatus


def _normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized if normalized != "" else None


def _parse_boolean(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized == "":
        return None
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_priority_order(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    value = value.strip()
    if value == "":
        return []
    return [item.strip() for item in value.split(" > ") if item.strip()]


def _parse_program_list(value: Any) -> Optional[List[str]]:
    if value is None:
        return None
    if isinstance(value, list):
        parsed = [str(item).strip() for item in value if str(item).strip()]
        return parsed or None
    normalized = value.strip()
    if normalized == "":
        return None
    return [item.strip() for item in normalized.split(",") if item.strip()]


class ExpectedResultRow(BaseModel):
    case_id: str
    expected_snap: Optional[ProgramStatus] = None
    expected_medicaid_chip: Optional[ProgramStatus] = None
    expected_liheap: Optional[ProgramStatus] = None
    expected_wic: Optional[ProgramStatus] = None
    expected_local_referral: Optional[ProgramStatus] = None
    expected_uncertainty_flag: Optional[bool] = None
    expected_priority_order: List[str] = Field(default_factory=list)
    expected_checklist_programs: Optional[List[str]] = None
    expected_explanation_notes: Optional[str] = None
    why_this_is_expected: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "case_id",
        "expected_explanation_notes",
        "why_this_is_expected",
        mode="before",
    )
    @classmethod
    def _clean_text(cls, value: Any) -> Optional[str]:
        return _normalize_text(value)

    @field_validator(
        "expected_snap",
        "expected_medicaid_chip",
        "expected_liheap",
        "expected_wic",
        "expected_local_referral",
        mode="before",
    )
    @classmethod
    def _clean_program_status(cls, value: Any) -> Optional[ProgramStatus]:
        if value is None:
            return None
        if isinstance(value, ProgramStatus):
            return value
        normalized = str(value).strip()
        if normalized == "":
            return None
        return ProgramStatus(normalized)

    @field_validator("expected_uncertainty_flag", mode="before")
    @classmethod
    def _clean_uncertainty_flag(cls, value: Any) -> Optional[bool]:
        return _parse_boolean(value)

    @field_validator("expected_priority_order", mode="before")
    @classmethod
    def _clean_priority_order(cls, value: Any) -> List[str]:
        return _parse_priority_order(value)

    @field_validator("expected_checklist_programs", mode="before")
    @classmethod
    def _clean_program_list(cls, value: Any) -> Optional[List[str]]:
        return _parse_program_list(value)

    @model_validator(mode="after")
    def _validate_case_id(self) -> Self:
        if not self.case_id:
            raise ValueError("case_id is required")
        return self


def load_expected_results(csv_path: str | Path) -> List[ExpectedResultRow]:
    path = Path(csv_path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows: List[ExpectedResultRow] = []
    for _, record in df.iterrows():
        row = ExpectedResultRow(**record.to_dict())
        rows.append(row)
    return rows
