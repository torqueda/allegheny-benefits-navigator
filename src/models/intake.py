from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from src.models.common import IntakeStatus


class HouseholdProfile(BaseModel):
    county: Optional[str] = None
    zip_code: Optional[str] = None
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
    language_or_stress_notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class IntakeOutput(BaseModel):
    household_profile: HouseholdProfile
    missing_fields: List[str]
    contradictory_fields: List[str]
    validation_warnings: List[str]
    intake_status: IntakeStatus
    clarification_questions: List[str]

    model_config = ConfigDict(extra="forbid")
