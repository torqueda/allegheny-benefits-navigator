from __future__ import annotations

from typing import Dict, Any, List

from src.loaders.rules import (
    EligibilityRule,
    PriorityHeuristic,
    load_eligibility_rules,
    load_priority_heuristics,
)
from src.models.common import DecisionStatus, IntakeStatus, ProgramStatus
from src.models.eligibility import EligibilityPrioritizationOutput, ProgramAssessment
from src.models.explanation import ChecklistExplanationOutput
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
    Eligibility + Prioritization component.

    Evaluates deterministic rules for SNAP, Medicaid/CHIP, LIHEAP.
    Applies prioritization heuristics.
    """
    profile = session.intake.household_profile

    # Load rules
    rules = load_eligibility_rules("data/rules_source")
    heuristics = load_priority_heuristics("data/rules_source")

    # Derive household_size_total
    household_size = (profile.num_adults or 0) + (profile.num_children or 0)

    # Evaluate each program
    programs = ["SNAP", "Medicaid/CHIP", "LIHEAP"]
    assessments = []
    uncertainty_flags = []
    eligible_programs = []
    inapplicable_programs = []

    for program in programs:
        assessment = _evaluate_program(program, profile, household_size, rules)
        assessments.append(assessment)
        if assessment.status == ProgramStatus.likely_applicable:
            eligible_programs.append(program)
        elif assessment.status == ProgramStatus.likely_inapplicable:
            inapplicable_programs.append(program)
        if assessment.status == ProgramStatus.uncertain:
            uncertainty_flags.append(f"{program}: {', '.join(assessment.missing_evidence)}")

    # Prioritize
    priority_order, priority_rationale = _prioritize_programs(eligible_programs, profile, heuristics)

    # Determine decision status
    if eligible_programs:
        decision_status = DecisionStatus.ready_for_explanation
    elif uncertainty_flags:
        decision_status = DecisionStatus.ambiguous
    else:
        decision_status = DecisionStatus.insufficient_data

    return EligibilityPrioritizationOutput(
        program_assessments=assessments,
        eligible_or_likely_programs=eligible_programs,
        inapplicable_programs=inapplicable_programs,
        uncertainty_flags=uncertainty_flags,
        priority_order=priority_order,
        priority_rationale=priority_rationale,
        decision_status=decision_status,
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


def _evaluate_program(
    program: str, profile: HouseholdProfile, household_size: int, rules: List[EligibilityRule]
) -> ProgramAssessment:
    """Evaluate rules for a program."""
    program_id_map = {"SNAP": "snap", "Medicaid/CHIP": "medicaid", "LIHEAP": "liheap"}
    program_id = program_id_map[program]

    program_rules = [r for r in rules if r.program_id == program_id]

    matched_conditions = []
    failed_conditions = []
    missing_evidence = []
    caveats = []
    source_refs = set()

    status = ProgramStatus.likely_inapplicable  # Default

    # Group by pathway
    pathways = {}
    for rule in program_rules:
        pathways.setdefault(rule.pathway_id, []).append(rule)

    for pathway_id, path_rules in pathways.items():
        pathway_matched = []
        pathway_failed = []
        pathway_missing = []
        pathway_uncertain = False

        for rule in path_rules:
            result = _evaluate_rule(rule, profile, household_size)
            if result == "match":
                pathway_matched.append(rule.rule_id)
                if rule.outcome_if_true == "likely_applicable":
                    status = ProgramStatus.likely_applicable
                source_refs.add(rule.source_id)
            elif result == "fail":
                pathway_failed.append(rule.rule_id)
            elif result == "missing":
                pathway_missing.append(rule.field_name)
                if rule.uncertainty_if_missing == "uncertain":
                    pathway_uncertain = True
            elif result == "uncertain":
                pathway_uncertain = True

        if pathway_matched and not pathway_failed and not pathway_uncertain:
            matched_conditions.extend(pathway_matched)
        elif pathway_failed:
            failed_conditions.extend(pathway_failed)
        if pathway_missing:
            missing_evidence.extend(pathway_missing)
        if pathway_uncertain:
            status = ProgramStatus.uncertain

    return ProgramAssessment(
        program_name=program,
        status=status,
        matched_conditions=matched_conditions,
        failed_conditions=failed_conditions,
        missing_evidence=missing_evidence,
        caveats=caveats,
        source_refs=list(source_refs),
    )


def _evaluate_rule(rule: EligibilityRule, profile: HouseholdProfile, household_size: int) -> str:
    """Evaluate a single rule."""
    field_value = _get_field_value(rule.field_name, profile, household_size)

    if rule.operator == "missing":
        if field_value is None:
            return "match"
        return "fail"

    if field_value is None:
        if rule.uncertainty_if_missing == "uncertain":
            return "uncertain"
        return "missing"

    if rule.operator == "==":
        if str(field_value).lower() == rule.value.lower():
            return "match"
        return "fail"
    elif rule.operator == "<=":
        if isinstance(field_value, (int, float)) and float(rule.value) >= field_value:
            return "match"
        return "fail"
    elif rule.operator == ">=":
        if isinstance(field_value, (int, float)) and float(rule.value) <= field_value:
            return "match"
        return "fail"
    elif rule.operator == ">":
        if isinstance(field_value, (int, float)) and field_value > float(rule.value):
            return "match"
        return "fail"
    elif rule.operator == "in":
        values = rule.value.split("|")
        if str(field_value).lower() in [v.lower() for v in values]:
            return "match"
        return "fail"

    return "fail"


def _get_field_value(field_name: str, profile: HouseholdProfile, household_size: int) -> Any:
    """Get field value from profile."""
    if field_name == "household_size_total":
        return household_size
    elif field_name == "household_income_total":
        return profile.household_income_total
    elif field_name == "num_adults":
        return profile.num_adults
    elif field_name == "elderly_or_disabled_member":
        return profile.elderly_or_disabled_member
    elif field_name == "employment_status":
        return profile.employment_status
    # Add more as needed
    return getattr(profile, field_name, None)


def _prioritize_programs(
    eligible_programs: List[str], profile: HouseholdProfile, heuristics: List[PriorityHeuristic]
) -> tuple[List[str], List[str]]:
    """Prioritize programs using heuristics."""
    scores = {prog: 0 for prog in eligible_programs}
    reasons = {prog: [] for prog in eligible_programs}

    for h in heuristics:
        program = {"snap": "SNAP", "medicaid": "Medicaid/CHIP", "liheap": "LIHEAP"}.get(h.program_id)
        if program not in eligible_programs:
            continue

        field_value = getattr(profile, h.field_name, None)
        if _matches_heuristic(h, field_value):
            scores[program] += h.weight
            reasons[program].append(h.reason_text)

    # Sort by score descending, then by name for tie-break
    sorted_programs = sorted(eligible_programs, key=lambda p: (-scores[p], p))
    rationale = [f"{p}: {', '.join(reasons[p])}" for p in sorted_programs]

    return sorted_programs, rationale


def _matches_heuristic(h: PriorityHeuristic, field_value: Any) -> bool:
    """Check if heuristic matches."""
    if h.operator == "==":
        return str(field_value).lower() == h.value.lower()
    elif h.operator == ">=":
        return isinstance(field_value, (int, float)) and field_value >= int(h.value)
    # Add more operators if needed
    return False