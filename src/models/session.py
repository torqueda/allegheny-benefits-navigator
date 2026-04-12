from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from src.models.eligibility import EligibilityPrioritizationOutput
from src.models.explanation import ChecklistExplanationOutput
from src.models.intake import IntakeOutput


class SessionMeta(BaseModel):
    session_id: str
    run_id: str
    case_id: Optional[str] = None
    mode: str
    created_at: str
    app_version: str
    ruleset_version: str
    template_version: str
    program_scope: List[str]
    policy_snapshot_version: str
    llm_enabled: bool
    llm_model: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class RunInput(BaseModel):
    raw_form_input: Dict[str, Any]
    source: str

    model_config = ConfigDict(extra="forbid")


class AuditEvent(BaseModel):
    component: str
    event_type: str
    timestamp: str
    details: Dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class AuditError(BaseModel):
    component: str
    error_type: str
    message: str
    timestamp: str

    model_config = ConfigDict(extra="forbid")


class Audit(BaseModel):
    events: List[AuditEvent]
    errors: List[AuditError]
    timings_ms: Dict[str, int]

    model_config = ConfigDict(extra="forbid")


class SessionState(BaseModel):
    session_meta: SessionMeta
    input: RunInput
    intake: IntakeOutput
    eligibility_prioritization: EligibilityPrioritizationOutput
    checklist_explanation: ChecklistExplanationOutput
    audit: Audit

    model_config = ConfigDict(extra="forbid")
