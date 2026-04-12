from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, ConfigDict

from src.models.common import FinalStatus


class ChecklistExplanationOutput(BaseModel):
    checklist_items_by_program: Dict[str, List[str]]
    recommended_programs: List[str]
    next_steps: List[str]
    user_explanation: str
    visible_caveats: List[str]
    referral_notes: List[str]
    final_status: FinalStatus

    model_config = ConfigDict(extra="forbid")
