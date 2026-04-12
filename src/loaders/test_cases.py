from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, root_validator, validator


def _normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    return normalized if normalized != "" else None


def _parse_boolean(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    value = value.strip().lower()
    if value == "":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_optional_float(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    value = value.strip()
    if value == "":
        return None
    return float(value)


def _parse_json_array(value: Optional[str]) -> List[str]:
    if value is None:
        return []
    value = value.strip()
    if value == "":
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array string, got: {value}")
    return [str(item) for item in parsed]


class TestCaseRow(BaseModel):
    case_id: str
    case_type: str
    scenario_summary: str
    county: str
    zip_code: str
    num_adults: Optional[int] = None
    num_children: Optional[int] = None
    child_under_5: Optional[bool] = None
    pregnant_household_member: Optional[bool] = None
    elderly_or_disabled_member: Optional[bool] = None
    employment_status: Optional[str] = None
    monthly_earned_income: Optional[float] = None
    monthly_unearned_income: Optional[float] = None
    household_income_total: Optional[float] = None
    housing_cost: Optional[float] = None
    utility_burden: Optional[str] = None
    heating_assistance_need: Optional[bool] = None
    insurance_status: Optional[str] = None
    recent_job_loss: Optional[bool] = None
    food_insecurity_signal: Optional[bool] = None
    missing_fields: List[str] = Field(default_factory=list)
    contradictory_fields: List[str] = Field(default_factory=list)
    language_or_stress_notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @validator(
        "case_id",
        "case_type",
        "scenario_summary",
        "county",
        "zip_code",
        "employment_status",
        "utility_burden",
        "insurance_status",
        "language_or_stress_notes",
        pre=True,
        always=True,
    )
    def _clean_text(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_text(value)

    @validator(
        "child_under_5",
        "pregnant_household_member",
        "elderly_or_disabled_member",
        "heating_assistance_need",
        "recent_job_loss",
        "food_insecurity_signal",
        pre=True,
        always=True,
    )
    def _clean_bool(cls, value: Optional[str]) -> Optional[bool]:
        return _parse_boolean(value)

    @validator(
        "num_adults",
        "num_children",
        pre=True,
        always=True,
    )
    def _clean_int(cls, value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        value = str(value).strip()
        if value == "":
            return None
        return int(value)

    @validator(
        "monthly_earned_income",
        "monthly_unearned_income",
        "household_income_total",
        "housing_cost",
        pre=True,
        always=True,
    )
    def _clean_float(cls, value: Optional[str]) -> Optional[float]:
        return _parse_optional_float(value)

    @validator("missing_fields", "contradictory_fields", pre=True, always=True)
    def _clean_json_list(cls, value: Optional[str]) -> List[str]:
        return _parse_json_array(value)

    @root_validator
    def _validate_case_id(cls, values):
        case_id = values.get("case_id")
        if not case_id:
            raise ValueError("case_id is required")
        return values


def load_test_cases(csv_path: str | Path) -> List[TestCaseRow]:
    path = Path(csv_path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows: List[TestCaseRow] = []
    for _, record in df.iterrows():
        row = TestCaseRow(**record.to_dict())
        rows.append(row)
    return rows
