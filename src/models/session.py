from __future__ import annotations

from typing import Any

from src.models.base import BaseModel, Field
from src.models.common import DecisionStatus, FinalStatus, IntakeStatus, ProgramStatus


class HouseholdProfile(BaseModel):
    county: str | None = None
    zip_code: str | None = None
    num_adults: int | None = None
    num_children: int | None = None
    child_under_5: bool | None = None
    pregnant_household_member: bool | None = None
    elderly_or_disabled_member: bool | None = None
    employment_status: str | None = None
    monthly_earned_income: float | None = None
    monthly_unearned_income: float | None = None
    household_income_total: float | None = None
    housing_cost: float | None = None
    utility_burden: str | None = None
    heating_assistance_need: bool | None = None
    insurance_status: str | None = None
    recent_job_loss: bool | None = None
    food_insecurity_signal: str | None = None
    language_or_stress_notes: str | None = None
    scenario_summary: str | None = None
    household_size: int | None = None


class IntakeOutput(BaseModel):
    household_profile: HouseholdProfile
    missing_fields: list[str] = Field(default_factory=list)
    contradictory_fields: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    intake_status: IntakeStatus = IntakeStatus.COMPLETE


class ProgramAssessment(BaseModel):
    program_name: str
    status: ProgramStatus
    matched_conditions: list[str] = Field(default_factory=list)
    failed_conditions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)


class EligibilityPrioritizationOutput(BaseModel):
    program_assessments: list[ProgramAssessment] = Field(default_factory=list)
    eligible_or_likely_programs: list[str] = Field(default_factory=list)
    inapplicable_programs: list[str] = Field(default_factory=list)
    uncertainty_flags: list[str] = Field(default_factory=list)
    priority_order: list[str] = Field(default_factory=list)
    priority_rationale: list[str] = Field(default_factory=list)
    decision_status: DecisionStatus = DecisionStatus.READY_FOR_EXPLANATION


class ChecklistExplanationOutput(BaseModel):
    recommended_programs: list[str] = Field(default_factory=list)
    checklist_items_by_program: dict[str, list[str]] = Field(default_factory=dict)
    next_steps: list[str] = Field(default_factory=list)
    user_explanation: str = ""
    visible_caveats: list[str] = Field(default_factory=list)
    referral_notes: list[str] = Field(default_factory=list)
    final_status: FinalStatus = FinalStatus.DELIVERED


class AuditEvent(BaseModel):
    component: str
    event_type: str
    timestamp: str
    details: dict[str, Any] = Field(default_factory=dict)


class AuditError(BaseModel):
    component: str
    error_type: str
    message: str
    timestamp: str


class AuditTrail(BaseModel):
    events: list[AuditEvent] = Field(default_factory=list)
    errors: list[AuditError] = Field(default_factory=list)
    timings_ms: dict[str, int] = Field(default_factory=dict)


class SessionMeta(BaseModel):
    session_id: str
    run_id: str
    case_id: str | None = None
    mode: str = "synthetic_test"
    created_at: str = ""
    app_version: str = "0.1.0"
    ruleset_version: str = "2026-04-phase2"
    template_version: str = "v1"
    llm_enabled: bool = False
    llm_model: str | None = None


class SessionState(BaseModel):
    session_meta: SessionMeta
    input: dict[str, Any]
    intake: IntakeOutput
    eligibility_prioritization: EligibilityPrioritizationOutput
    checklist_explanation: ChecklistExplanationOutput
    audit: AuditTrail
