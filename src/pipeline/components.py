from __future__ import annotations

from typing import Dict, Any, List

from src.models.common import IntakeStatus
from src.models.intake import HouseholdProfile, IntakeOutput
from src.models.session import SessionState


def intake(
    session: SessionState,
    raw_form_input: Dict[str, Any],
) -> IntakeOutput:
    """
    Intake component: validate and normalize raw form input.

    Performs:
    - Normalization of fields
    - Detection of missing required fields
    - Detection of contradictions
    - Assignment of intake status
    - Generation of clarification questions
    """
    # Normalize input
    normalized = _normalize_raw_input(raw_form_input)

    # Create household profile
    profile = HouseholdProfile(**normalized)

    # Validate geography
    if profile.county != "Allegheny":
        return IntakeOutput(
            household_profile=profile,
            missing_fields=[],
            contradictory_fields=[],
            validation_warnings=["Geography out of scope: only Allegheny County supported"],
            intake_status=IntakeStatus.insufficient_data,
            clarification_questions=["This system is only for Allegheny County households."],
        )

    # Detect missing fields
    missing = _detect_missing_fields(normalized)

    # Detect contradictions
    contradictions = _detect_contradictions(normalized)

    # Determine status
    status, warnings, questions = _determine_intake_status(missing, contradictions, normalized)

    return IntakeOutput(
        household_profile=profile,
        missing_fields=missing,
        contradictory_fields=contradictions,
        validation_warnings=warnings,
        intake_status=status,
        clarification_questions=questions,
    )


def _normalize_raw_input(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw form input fields."""
    normalized = {}
    for key, value in raw.items():
        if isinstance(value, str):
            stripped = value.strip()
            normalized[key] = stripped if stripped else None
        elif isinstance(value, (int, float)):
            normalized[key] = value
        elif isinstance(value, bool):
            normalized[key] = value
        else:
            normalized[key] = value  # Preserve as-is for now

    # Special handling for booleans
    bool_fields = [
        "child_under_5", "pregnant_household_member", "elderly_or_disabled_member",
        "heating_assistance_need", "recent_job_loss", "food_insecurity_signal"
    ]
    for field in bool_fields:
        if field in normalized:
            val = normalized[field]
            if isinstance(val, str):
                val_lower = val.lower()
                if val_lower == "true":
                    normalized[field] = True
                elif val_lower == "false":
                    normalized[field] = False
                else:
                    normalized[field] = None
            elif not isinstance(val, bool):
                normalized[field] = None

    # Validate numeric fields
    numeric_fields = [
        "num_adults", "num_children", "monthly_earned_income", "monthly_unearned_income",
        "household_income_total", "housing_cost"
    ]
    for field in numeric_fields:
        if field in normalized:
            val = normalized[field]
            if isinstance(val, str):
                try:
                    normalized[field] = float(val) if "." in val else int(val)
                except ValueError:
                    normalized[field] = None
            if isinstance(val, (int, float)) and val < 0:
                normalized[field] = None  # Invalid negative

    return normalized


def _detect_missing_fields(normalized: Dict[str, Any]) -> List[str]:
    """Detect missing required fields."""
    required = ["county", "num_adults", "num_children"]
    # At least one income field
    has_income = any(
        normalized.get(field) is not None
        for field in ["monthly_earned_income", "monthly_unearned_income", "household_income_total"]
    )
    if not has_income:
        required.append("monthly_earned_income")  # Placeholder for income requirement

    missing = []
    for field in required:
        if normalized.get(field) is None:
            missing.append(field)
    return missing


def _detect_contradictions(normalized: Dict[str, Any]) -> List[str]:
    """Detect contradictory fields."""
    contradictions = []

    # num_children == 0 but child_under_5 == true
    if normalized.get("num_children") == 0 and normalized.get("child_under_5") is True:
        contradictions.append("num_children vs child_under_5")

    # num_adults < 1
    if normalized.get("num_adults") is not None and normalized["num_adults"] < 1:
        contradictions.append("num_adults must be at least 1")

    # Income inconsistency
    earned = normalized.get("monthly_earned_income") or 0
    unearned = normalized.get("monthly_unearned_income") or 0
    total = normalized.get("household_income_total")
    if total is not None and abs((earned + unearned) - total) > 1:  # Small tolerance
        contradictions.append("income components vs total")

    # Negative values already handled in normalization

    return contradictions


def _determine_intake_status(
    missing: List[str], contradictions: List[str], normalized: Dict[str, Any]
) -> tuple[IntakeStatus, List[str], List[str]]:
    """Determine intake status, warnings, and questions."""
    warnings = []
    questions = []

    if contradictions:
        warnings.append("Contradictory information detected.")
        questions.extend([f"Please clarify: {c}" for c in contradictions])

    if missing:
        warnings.append("Some required fields are missing.")
        questions.extend([f"Please provide: {f}" for f in missing])

    # Status logic
    if not missing and not contradictions:
        status = IntakeStatus.complete
    elif len(missing) <= 2 and not contradictions:  # Allow some missing if no contradictions
        status = IntakeStatus.needs_clarification
    else:
        status = IntakeStatus.insufficient_data

    return status, warnings, questions


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