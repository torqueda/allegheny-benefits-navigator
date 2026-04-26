from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserIntake(BaseModel):
    user_description: Optional[str] = None
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
    food_insecurity_signal: Optional[str] = None
    language_or_stress_notes: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class IntakeOutput(BaseModel):
    normalized_profile: UserIntake
    missing_fields: List[str]
    contradictory_fields: List[str]
    extracted_signals: List[str]
    intake_status: str
    intake_summary: str
    clarification_questions: List[str]

    model_config = ConfigDict(extra="forbid")


class PolicyDocument(BaseModel):
    document_id: str
    title: str
    program_name: str
    source_type: str
    content: str
    source_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    uploaded: bool = False

    model_config = ConfigDict(extra="forbid")


class PolicyChunk(BaseModel):
    chunk_id: str
    document_id: str
    program_name: str
    title: str
    section_title: Optional[str] = None
    source_url: Optional[str] = None
    text: str

    model_config = ConfigDict(extra="forbid")


class RetrievedChunk(BaseModel):
    document_id: str
    program_name: str
    title: str
    section_title: Optional[str] = None
    source_url: Optional[str] = None
    text: str
    score: float

    model_config = ConfigDict(extra="forbid")


class MatchReason(BaseModel):
    reason: str
    score: float
    evidence_snippet: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ProgramMatch(BaseModel):
    program_name: str
    status: str
    match_score: float
    priority_score: float
    rationale: List[MatchReason]
    caveats: List[str]
    retrieved_evidence: List[RetrievedChunk]
    checklist_items: List[str]
    uploaded_policy_backed: bool = False

    model_config = ConfigDict(extra="forbid")


class EligibilityOutput(BaseModel):
    query_summary: str
    program_matches: List[ProgramMatch]
    recommended_programs: List[str]
    uncertainty_flags: List[str]
    priority_order: List[str]
    decision_status: str

    model_config = ConfigDict(extra="forbid")


class ExplanationOutput(BaseModel):
    recommended_programs: List[str]
    checklist_by_program: Dict[str, List[str]]
    next_steps: List[str]
    plain_language_explanation: str
    visible_caveats: List[str]
    evidence_quotes: List[str]
    final_status: str

    model_config = ConfigDict(extra="forbid")


class NavigatorSession(BaseModel):
    intake: IntakeOutput
    eligibility: EligibilityOutput
    explanation: ExplanationOutput
    uploaded_documents_available: List[str]

    model_config = ConfigDict(extra="forbid")
