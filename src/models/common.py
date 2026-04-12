from enum import Enum


class IntakeStatus(str, Enum):
    complete = "complete"
    needs_clarification = "needs_clarification"
    insufficient_data = "insufficient_data"


class ProgramStatus(str, Enum):
    likely_applicable = "likely_applicable"
    likely_inapplicable = "likely_inapplicable"
    uncertain = "uncertain"


class DecisionStatus(str, Enum):
    ready_for_explanation = "ready_for_explanation"
    ambiguous = "ambiguous"
    insufficient_data = "insufficient_data"


class FinalStatus(str, Enum):
    delivered = "delivered"
    delivered_with_uncertainty = "delivered_with_uncertainty"
    needs_human_followup = "needs_human_followup"
