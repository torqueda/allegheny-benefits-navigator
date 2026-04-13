from __future__ import annotations

from enum import Enum


class IntakeStatus(str, Enum):
    COMPLETE = "complete"
    NEEDS_CLARIFICATION = "needs_clarification"
    INSUFFICIENT_DATA = "insufficient_data"


class ProgramStatus(str, Enum):
    LIKELY_APPLICABLE = "likely_applicable"
    LIKELY_INAPPLICABLE = "likely_inapplicable"
    UNCERTAIN = "uncertain"


class DecisionStatus(str, Enum):
    READY_FOR_EXPLANATION = "ready_for_explanation"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_DATA = "insufficient_data"


class FinalStatus(str, Enum):
    DELIVERED = "delivered"
    DELIVERED_WITH_UNCERTAINTY = "delivered_with_uncertainty"
    NEEDS_HUMAN_FOLLOWUP = "needs_human_followup"
