from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, ConfigDict

from src.models.common import DecisionStatus, ProgramStatus


class ProgramAssessment(BaseModel):
    program_name: str
    status: ProgramStatus
    matched_conditions: List[str]
    failed_conditions: List[str]
    missing_evidence: List[str]
    caveats: List[str]
    source_refs: List[str]

    model_config = ConfigDict(extra="forbid")


class EligibilityPrioritizationOutput(BaseModel):
    program_assessments: List[ProgramAssessment]
    eligible_or_likely_programs: List[str]
    inapplicable_programs: List[str]
    uncertainty_flags: List[str]
    priority_order: List[str]
    priority_rationale: List[str]
    decision_status: DecisionStatus

    model_config = ConfigDict(extra="forbid")
