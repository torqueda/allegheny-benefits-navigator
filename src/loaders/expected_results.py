from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, root_validator, validator

from src.models.common import ProgramStatus


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized != "" else None


def _parse_boolean(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized == "":
        return None
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_priority_order(value: Optional[str]) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    value = value.strip()
    if value == "":
        return []
    return [item.strip() for item in value.split(" > ") if item.strip()]


def _parse_program_list(value: Optional[str]) -> Optional[List[str]]:
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

    @validator(
        "case_id",
        "expected_explanation_notes",
        "why_this_is_expected",
        pre=True,
        always=True,
    )
    def _clean_text(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_text(value)

    @validator(
        "expected_snap",
        "expected_medicaid_chip",
        "expected_liheap",
        "expected_wic",
        "expected_local_referral",
        pre=True,
        always=True,
    )
    def _clean_program_status(cls, value: Optional[str]) -> Optional[ProgramStatus]:
        if value is None:
            return None
        normalized = value.strip()
        if normalized == "":
            return None
        return ProgramStatus(normalized)

    @validator("expected_uncertainty_flag", pre=True, always=True)
    def _clean_uncertainty_flag(cls, value: Optional[str]) -> Optional[bool]:
        return _parse_boolean(value)

    @validator("expected_priority_order", pre=True, always=True)
    def _clean_priority_order(cls, value: Optional[str]) -> List[str]:
        return _parse_priority_order(value)

    @validator("expected_checklist_programs", pre=True, always=True)
    def _clean_program_list(cls, value: Optional[str]) -> Optional[List[str]]:
        return _parse_program_list(value)

    @root_validator(skip_on_failure=True)
    def _validate_case_id(cls, values):
        case_id = values.get("case_id")
        if not case_id:
            raise ValueError("case_id is required")
        return values


def load_expected_results(csv_path: str | Path) -> List[ExpectedResultRow]:
    path = Path(csv_path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows: List[ExpectedResultRow] = []
    for _, record in df.iterrows():
        row = ExpectedResultRow(**record.to_dict())
        rows.append(row)
    return rows
