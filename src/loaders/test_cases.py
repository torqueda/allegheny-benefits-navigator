from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional, Self

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    value = value.strip().lower()
    if value == "":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    value = value.strip()
    if value == "":
        return None
    return float(value)


def _parse_json_array(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    value = value.strip()
    if value == "":
        return []
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected JSON array string, got: {value}")
    return [str(item) for item in parsed]


class TestCaseRow(BaseModel):
    __test__ = False

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
    food_insecurity_signal: Optional[str] = None
    missing_fields: List[str] = Field(default_factory=list)
    contradictory_fields: List[str] = Field(default_factory=list)
    language_or_stress_notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator(
        "case_id",
        "case_type",
        "scenario_summary",
        "county",
        "zip_code",
        "employment_status",
        "utility_burden",
        "insurance_status",
        "food_insecurity_signal",
        "language_or_stress_notes",
        mode="before",
    )
    @classmethod
    def _clean_text(cls, value: Any) -> Optional[str]:
        return _normalize_text(value)

    @field_validator(
        "child_under_5",
        "pregnant_household_member",
        "elderly_or_disabled_member",
        "heating_assistance_need",
        "recent_job_loss",
        mode="before",
    )
    @classmethod
    def _clean_bool(cls, value: Any) -> Optional[bool]:
        return _parse_boolean(value)

    @field_validator(
        "num_adults",
        "num_children",
        mode="before",
    )
    @classmethod
    def _clean_int(cls, value: Any) -> Optional[int]:
        if value is None:
            return None
        value = str(value).strip()
        if value == "":
            return None
        return int(value)

    @field_validator(
        "monthly_earned_income",
        "monthly_unearned_income",
        "household_income_total",
        "housing_cost",
        mode="before",
    )
    @classmethod
    def _clean_float(cls, value: Any) -> Optional[float]:
        return _parse_optional_float(value)

    @field_validator("missing_fields", "contradictory_fields", mode="before")
    @classmethod
    def _clean_json_list(cls, value: Any) -> List[str]:
        return _parse_json_array(value)

    @model_validator(mode="after")
    def _validate_case_id(self) -> Self:
        if not self.case_id:
            raise ValueError("case_id is required")
        return self


def load_test_cases(csv_path: str | Path) -> List[TestCaseRow]:
    path = Path(csv_path)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    rows: List[TestCaseRow] = []
    for _, record in df.iterrows():
        row = TestCaseRow(**record.to_dict())
        rows.append(row)
    return rows
