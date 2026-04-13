from __future__ import annotations

from typing import Dict, Any

from src.models.common import DecisionStatus, FinalStatus, IntakeStatus
from src.models.eligibility import EligibilityPrioritizationOutput, ProgramAssessment
from src.models.explanation import ChecklistExplanationOutput
from src.models.intake import HouseholdProfile, IntakeOutput
from src.models.session import SessionState


def intake(
    session: SessionState,
    raw_form_input: Dict[str, Any],
) -> IntakeOutput:
    """
    Placeholder for intake component.

    TODO: Implement real intake validation, normalization, missing/contradiction detection.
    For now, returns a minimal valid output based on input.
    """
    # Placeholder: assume complete for happy path
    household_profile = HouseholdProfile(
        county=raw_form_input.get("county"),
        zip_code=raw_form_input.get("zip_code"),
        num_adults=raw_form_input.get("num_adults"),
        num_children=raw_form_input.get("num_children"),
        # ... other fields as needed
    )

    return IntakeOutput(
        household_profile=household_profile,
        missing_fields=[],  # TODO: detect missing fields
        contradictory_fields=[],  # TODO: detect contradictions
        validation_warnings=[],  # TODO: add warnings
        intake_status=IntakeStatus.complete,  # Placeholder
        clarification_questions=[],  # TODO: generate questions
    )


def eligibility_and_prioritization(
    session: SessionState,
) -> EligibilityPrioritizationOutput:
    """
    Placeholder for eligibility and prioritization component.

    TODO: Implement real deterministic rule evaluation, prioritization heuristics.
    For now, returns minimal valid output.
    """
    # Placeholder assessments
    assessments = [
        ProgramAssessment(
            program_name="SNAP",
            status="likely_applicable",  # Placeholder
            matched_conditions=[],  # TODO: matched rules
            failed_conditions=[],  # TODO: failed rules
            missing_evidence=[],  # TODO: missing evidence
            caveats=[],  # TODO: caveats
            source_refs=[],  # TODO: sources
        )
    ]

    return EligibilityPrioritizationOutput(
        program_assessments=assessments,
        eligible_or_likely_programs=["SNAP"],  # TODO: compute
        inapplicable_programs=[],  # TODO: compute
        uncertainty_flags=[],  # TODO: flags
        priority_order=["SNAP"],  # TODO: prioritize
        priority_rationale=["Placeholder rationale"],  # TODO: rationale
        decision_status=DecisionStatus.ready_for_explanation,  # Placeholder
    )


def checklist_and_explanation(
    session: SessionState,
) -> ChecklistExplanationOutput:
    """
    Placeholder for checklist and explanation component.

    TODO: Implement real checklist mapping, explanation generation.
    For now, returns minimal valid output.
    """
    return ChecklistExplanationOutput(
        checklist_items_by_program={"SNAP": ["Bring ID", "Proof of income"]},  # TODO: map
        recommended_programs=["SNAP"],  # TODO: from eligibility
        next_steps=["Apply online"],  # TODO: generate
        user_explanation="Based on the information provided, you may be eligible for SNAP. This is not an official determination.",  # TODO: generate
        visible_caveats=["Not an official determination"],  # TODO: from eligibility
        referral_notes=[],  # TODO: referrals
        final_status=FinalStatus.delivered,  # Placeholder
    )