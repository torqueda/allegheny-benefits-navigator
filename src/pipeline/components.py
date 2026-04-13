from __future__ import annotations

from typing import Any, Dict, List, Sequence

from src.loaders.rules import (
    ChecklistRequirement,
    EligibilityRule,
    PriorityHeuristic,
    ProgramSource,
    load_checklist_requirements,
    load_eligibility_rules,
    load_priority_heuristics,
    load_program_sources,
)
from src.models.common import DecisionStatus, FinalStatus, IntakeStatus, ProgramStatus
from src.models.eligibility import EligibilityPrioritizationOutput, ProgramAssessment
from src.models.explanation import ChecklistExplanationOutput
from src.models.intake import HouseholdProfile, IntakeOutput
from src.models.session import SessionState

RULES_DIR = "data/rules_source"
SUPPORTED_PROGRAMS = ("SNAP", "Medicaid/CHIP", "LIHEAP")
PROGRAM_ID_BY_NAME = {
    "SNAP": "snap",
    "Medicaid/CHIP": "medicaid",
    "LIHEAP": "liheap",
}
PROGRAM_NAME_BY_ID = {program_id: name for name, program_id in PROGRAM_ID_BY_NAME.items()}
DEFAULT_VISIBLE_CAVEATS = [
    "This is prescreening only.",
    "This is not an official determination.",
    "This does not replace a caseworker or benefits office.",
]
SOURCE_SCOPE_PRIORITY = {
    "application_docs": 0,
    "application_overview": 1,
    "overview_eligibility_docs_crisis": 2,
    "overview": 3,
}
CHECKLIST_PATHWAY_CAVEATS = {
    "non_magi_review": (
        "Medicaid/CHIP: additional resource or asset documents may be needed for older-adult, "
        "disability, or other non-MAGI review paths."
    ),
    "conditional_noncitizen": (
        "LIHEAP: additional lawful-status documents may be needed for applicants who are not U.S. citizens."
    ),
    "conditional_heat_in_rent": (
        "LIHEAP: lease or rent documentation may be needed if heating costs are included in rent."
    ),
    "conditional_basic_needs_gap": (
        "LIHEAP: extra financial documentation may be needed in hardship cases where income is below basic living needs."
    ),
}


def intake(
    session: SessionState,
    raw_form_input: Dict[str, Any],
) -> IntakeOutput:
    """
    Intake component: validate and normalize raw form input.

    Performs:
    - normalization of fields
    - detection of missing required fields
    - detection of contradictions
    - assignment of intake status
    - generation of clarification questions
    """
    normalized = _normalize_raw_input(raw_form_input)
    profile = HouseholdProfile(**normalized)

    if profile.county != "Allegheny":
        return IntakeOutput(
            household_profile=profile,
            missing_fields=[],
            contradictory_fields=[],
            validation_warnings=["Geography out of scope: only Allegheny County supported"],
            intake_status=IntakeStatus.insufficient_data,
            clarification_questions=["This system is only for Allegheny County households."],
        )

    missing = _detect_missing_fields(normalized)
    contradictions = _detect_contradictions(normalized)
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
    normalized: Dict[str, Any] = {}
    for key, value in raw.items():
        if isinstance(value, str):
            stripped = value.strip()
            normalized[key] = stripped if stripped else None
        elif isinstance(value, (int, float, bool)):
            normalized[key] = value
        else:
            normalized[key] = value

    bool_fields = [
        "child_under_5",
        "pregnant_household_member",
        "elderly_or_disabled_member",
        "heating_assistance_need",
        "recent_job_loss",
    ]
    for field in bool_fields:
        if field not in normalized:
            continue

        value = normalized[field]
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower == "true":
                normalized[field] = True
            elif value_lower == "false":
                normalized[field] = False
            else:
                normalized[field] = None
        elif not isinstance(value, bool):
            normalized[field] = None

    numeric_fields = [
        "num_adults",
        "num_children",
        "monthly_earned_income",
        "monthly_unearned_income",
        "household_income_total",
        "housing_cost",
    ]
    for field in numeric_fields:
        if field in normalized:
            normalized[field] = _normalize_numeric_value(normalized[field])

    return normalized


def _normalize_numeric_value(value: Any) -> int | float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    parsed: int | float | None
    if isinstance(value, (int, float)):
        parsed = value
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = float(stripped) if "." in stripped else int(stripped)
        except ValueError:
            return None
    else:
        return None

    if parsed < 0:
        return None
    return parsed


def _detect_missing_fields(normalized: Dict[str, Any]) -> List[str]:
    """Detect missing required fields."""
    required = ["county", "num_adults", "num_children"]

    has_income = any(
        normalized.get(field) is not None
        for field in ["monthly_earned_income", "monthly_unearned_income", "household_income_total"]
    )
    if not has_income:
        required.append("monthly_earned_income")

    missing = []
    for field in required:
        if normalized.get(field) is None:
            missing.append(field)
    return missing


def _detect_contradictions(normalized: Dict[str, Any]) -> List[str]:
    """Detect contradictory fields."""
    contradictions = []

    if normalized.get("num_children") == 0 and normalized.get("child_under_5") is True:
        contradictions.append("num_children vs child_under_5")

    if normalized.get("num_adults") is not None and normalized["num_adults"] < 1:
        contradictions.append("num_adults must be at least 1")

    earned = normalized.get("monthly_earned_income") or 0
    unearned = normalized.get("monthly_unearned_income") or 0
    total = normalized.get("household_income_total")
    if total is not None and abs((earned + unearned) - total) > 1:
        contradictions.append("income components vs total")

    return contradictions


def _determine_intake_status(
    missing: List[str], contradictions: List[str], normalized: Dict[str, Any]
) -> tuple[IntakeStatus, List[str], List[str]]:
    """Determine intake status, warnings, and questions."""
    warnings: List[str] = []
    questions: List[str] = []

    if contradictions:
        warnings.append("Contradictory information detected.")
        questions.extend([f"Please clarify: {contradictions_item}" for contradictions_item in contradictions])

    if missing:
        warnings.append("Some required fields are missing.")
        questions.extend([f"Please provide: {field_name}" for field_name in missing])

    if not missing and not contradictions:
        status = IntakeStatus.complete
    elif len(missing) <= 2 and not contradictions:
        status = IntakeStatus.needs_clarification
    else:
        status = IntakeStatus.insufficient_data

    return status, warnings, questions


def eligibility_and_prioritization(
    session: SessionState,
) -> EligibilityPrioritizationOutput:
    """
    Eligibility + Prioritization component.

    Evaluates deterministic rules for SNAP, Medicaid/CHIP, and LIHEAP.
    Applies prioritization heuristics.
    """
    profile = session.intake.household_profile
    rules = load_eligibility_rules(RULES_DIR)
    heuristics = load_priority_heuristics(RULES_DIR)

    household_size = (profile.num_adults or 0) + (profile.num_children or 0)
    assessments: List[ProgramAssessment] = []
    uncertainty_flags: List[str] = []
    eligible_programs: List[str] = []
    inapplicable_programs: List[str] = []

    for program in SUPPORTED_PROGRAMS:
        assessment = _evaluate_program(program, profile, household_size, rules)
        assessments.append(assessment)
        if assessment.status == ProgramStatus.likely_applicable:
            eligible_programs.append(program)
        elif assessment.status == ProgramStatus.likely_inapplicable:
            inapplicable_programs.append(program)

        if assessment.status == ProgramStatus.uncertain:
            uncertainty_flags.append(_format_uncertainty_flag(assessment))

    priority_order, priority_rationale = _prioritize_programs(eligible_programs, profile, heuristics)
    decision_status = (
        DecisionStatus.ambiguous if uncertainty_flags else DecisionStatus.ready_for_explanation
    )

    return EligibilityPrioritizationOutput(
        program_assessments=assessments,
        eligible_or_likely_programs=eligible_programs,
        inapplicable_programs=inapplicable_programs,
        uncertainty_flags=_preserve_order_unique(uncertainty_flags),
        priority_order=priority_order,
        priority_rationale=priority_rationale,
        decision_status=decision_status,
    )


def checklist_and_explanation(
    session: SessionState,
) -> ChecklistExplanationOutput:
    """Generate deterministic checklist items, next steps, and explanation text."""
    checklist_requirements = load_checklist_requirements(RULES_DIR)
    program_sources = load_program_sources(RULES_DIR)
    recommended_programs = _derive_recommended_programs(session.eligibility_prioritization)

    checklist_items_by_program: Dict[str, List[str]] = {}
    checklist_caveats: List[str] = []
    referral_notes: List[str] = []
    missing_checklist_programs: List[str] = []

    for program in recommended_programs:
        checklist_items, program_caveats, mapping_found = _generate_program_checklist(
            program,
            session.intake.household_profile,
            checklist_requirements,
        )
        checklist_items_by_program[program] = checklist_items
        checklist_caveats.extend(program_caveats)

        if not mapping_found:
            missing_checklist_programs.append(program)

        source_note = _build_program_source_note(program, program_sources)
        if source_note:
            referral_notes.append(source_note)

    visible_caveats = _build_visible_caveats(
        session,
        recommended_programs,
        checklist_caveats,
    )
    next_steps = _generate_next_steps(
        recommended_programs,
        session,
        missing_checklist_programs,
        program_sources,
    )
    referral_notes = _preserve_order_unique(
        referral_notes + _generate_followup_notes(session, missing_checklist_programs)
    )
    user_explanation = _generate_user_explanation(
        session,
        recommended_programs,
        checklist_items_by_program,
    )
    final_status = _determine_final_status(session, missing_checklist_programs)

    return ChecklistExplanationOutput(
        checklist_items_by_program=checklist_items_by_program,
        recommended_programs=recommended_programs,
        next_steps=next_steps,
        user_explanation=user_explanation,
        visible_caveats=visible_caveats,
        referral_notes=referral_notes,
        final_status=final_status,
    )


def _evaluate_program(
    program: str, profile: HouseholdProfile, household_size: int, rules: List[EligibilityRule]
) -> ProgramAssessment:
    """Evaluate deterministic rules for a single program."""
    program_id = PROGRAM_ID_BY_NAME[program]
    program_rules = [rule for rule in rules if rule.program_id == program_id]

    matched_conditions: List[str] = []
    failed_conditions: List[str] = []
    missing_evidence: List[str] = []
    caveats: List[str] = []
    source_refs = set()
    status = ProgramStatus.likely_inapplicable

    pathways: Dict[str, List[EligibilityRule]] = {}
    for rule in program_rules:
        pathways.setdefault(rule.pathway_id, []).append(rule)

    for path_rules in pathways.values():
        pathway_matched: List[str] = []
        pathway_failed: List[str] = []
        pathway_missing: List[str] = []
        pathway_uncertain = False
        pathway_likely_applicable = False

        for rule in path_rules:
            result = _evaluate_rule(rule, profile, household_size)
            if result == "match":
                pathway_matched.append(rule.rule_id)
                if rule.outcome_if_true == "likely_applicable":
                    pathway_likely_applicable = True
                elif rule.outcome_if_true == "uncertain":
                    pathway_uncertain = True
                source_refs.add(rule.source_id)
            elif result == "fail":
                pathway_failed.append(rule.rule_id)
            elif result == "missing":
                pathway_missing.append(rule.field_name)
                if rule.uncertainty_if_missing == "uncertain":
                    pathway_uncertain = True
            elif result == "uncertain":
                pathway_uncertain = True
                if _get_field_value(rule.field_name, profile, household_size) is None:
                    pathway_missing.append(rule.field_name)
                if rule.citation_note:
                    caveats.append(rule.citation_note)

        if pathway_matched and not pathway_failed and not pathway_uncertain:
            matched_conditions.extend(pathway_matched)
            if pathway_likely_applicable:
                status = ProgramStatus.likely_applicable
        elif pathway_failed:
            failed_conditions.extend(pathway_failed)

        if pathway_missing:
            missing_evidence.extend(pathway_missing)
        if pathway_uncertain:
            status = ProgramStatus.uncertain

    return ProgramAssessment(
        program_name=program,
        status=status,
        matched_conditions=_preserve_order_unique(matched_conditions),
        failed_conditions=_preserve_order_unique(failed_conditions),
        missing_evidence=_preserve_order_unique(missing_evidence),
        caveats=_preserve_order_unique(caveats),
        source_refs=sorted(source_refs),
    )


def _evaluate_rule(rule: EligibilityRule, profile: HouseholdProfile, household_size: int) -> str:
    """Evaluate a single rule against the household profile."""
    field_value = _get_field_value(rule.field_name, profile, household_size)

    if rule.operator == "missing":
        return "match" if field_value is None else "fail"

    if field_value is None:
        return "uncertain" if rule.uncertainty_if_missing == "uncertain" else "missing"

    if rule.operator == "==":
        return "match" if str(field_value).lower() == rule.value.lower() else "fail"
    if rule.operator == "<=":
        return "match" if isinstance(field_value, (int, float)) and field_value <= float(rule.value) else "fail"
    if rule.operator == ">=":
        return "match" if isinstance(field_value, (int, float)) and field_value >= float(rule.value) else "fail"
    if rule.operator == ">":
        return "match" if isinstance(field_value, (int, float)) and field_value > float(rule.value) else "fail"
    if rule.operator == "in":
        values = [value.strip().lower() for value in rule.value.split("|") if value.strip()]
        return "match" if str(field_value).lower() in values else "fail"

    return "fail"


def _get_field_value(field_name: str, profile: HouseholdProfile, household_size: int) -> Any:
    """Get a field value used by deterministic rules."""
    if field_name == "household_size_total":
        return household_size
    return getattr(profile, field_name, None)


def _prioritize_programs(
    eligible_programs: List[str], profile: HouseholdProfile, heuristics: List[PriorityHeuristic]
) -> tuple[List[str], List[str]]:
    """Prioritize programs using transparent heuristic scores."""
    scores = {program: 0 for program in eligible_programs}
    reasons = {program: [] for program in eligible_programs}

    for heuristic in heuristics:
        program = PROGRAM_NAME_BY_ID.get(heuristic.program_id)
        if program not in eligible_programs:
            continue

        field_value = getattr(profile, heuristic.field_name, None)
        if _matches_heuristic(heuristic, field_value):
            scores[program] += heuristic.weight
            reasons[program].append(heuristic.reason_text)

    sorted_programs = sorted(eligible_programs, key=lambda program: (-scores[program], program))
    rationale = []
    for program in sorted_programs:
        if reasons[program]:
            rationale.append(f"{program}: {', '.join(reasons[program])}")
        else:
            rationale.append(f"{program}: no additional prioritization signals were triggered.")

    return sorted_programs, rationale


def _matches_heuristic(heuristic: PriorityHeuristic, field_value: Any) -> bool:
    """Check whether a prioritization heuristic applies."""
    if field_value is None:
        return False

    if heuristic.operator == "==":
        return str(field_value).lower() == heuristic.value.lower()
    if heuristic.operator == ">=":
        return isinstance(field_value, (int, float)) and field_value >= float(heuristic.value)
    return False


def _format_uncertainty_flag(assessment: ProgramAssessment) -> str:
    if assessment.missing_evidence:
        missing = ", ".join(assessment.missing_evidence)
        return f"{assessment.program_name}: more information may change this prescreen ({missing})."
    return f"{assessment.program_name}: this prescreen remains uncertain and may need follow-up."


def _derive_recommended_programs(
    eligibility_output: EligibilityPrioritizationOutput,
) -> List[str]:
    if eligibility_output.priority_order:
        return _preserve_order_unique(
            [program for program in eligibility_output.priority_order if program in SUPPORTED_PROGRAMS]
        )

    return _preserve_order_unique(
        [
            program
            for program in eligibility_output.eligible_or_likely_programs
            if program in SUPPORTED_PROGRAMS
        ]
    )


def _generate_program_checklist(
    program: str,
    profile: HouseholdProfile,
    checklist_requirements: List[ChecklistRequirement],
) -> tuple[List[str], List[str], bool]:
    program_id = PROGRAM_ID_BY_NAME.get(program)
    if program_id is None:
        return [], [f"Checklist items were not available for {program}."], False

    matching_requirements = [
        requirement for requirement in checklist_requirements if requirement.program_id == program_id
    ]
    if not matching_requirements:
        return [], [f"Checklist items were not available for {program}."], False

    checklist_items: List[str] = []
    caveats: List[str] = []

    for requirement in matching_requirements:
        applies = _checklist_requirement_applies(requirement, profile)
        if applies is True:
            checklist_items.append(_format_checklist_item(requirement))
        elif applies is None:
            caveat = CHECKLIST_PATHWAY_CAVEATS.get(
                requirement.pathway_id,
                f"{program}: some checklist items depend on details not captured in this prescreen.",
            )
            caveats.append(caveat)

    return checklist_items, _preserve_order_unique(caveats), True


def _checklist_requirement_applies(
    requirement: ChecklistRequirement,
    profile: HouseholdProfile,
) -> bool | None:
    pathway_id = requirement.pathway_id

    if pathway_id in {"all", "cash"}:
        return True
    if pathway_id == "non_magi_review":
        if profile.elderly_or_disabled_member is None:
            return None
        return profile.elderly_or_disabled_member is True
    if pathway_id in {
        "conditional_noncitizen",
        "conditional_heat_in_rent",
        "conditional_basic_needs_gap",
    }:
        return None
    return None


def _format_checklist_item(requirement: ChecklistRequirement) -> str:
    prefix = "Required" if requirement.required_or_likely == "required" else "Likely useful"
    return f"{prefix}: {requirement.document_name}"


def _build_visible_caveats(
    session: SessionState,
    recommended_programs: List[str],
    checklist_caveats: List[str],
) -> List[str]:
    caveats = list(DEFAULT_VISIBLE_CAVEATS)

    if session.intake.missing_fields:
        missing_fields = ", ".join(session.intake.missing_fields)
        caveats.append(f"Some intake fields are still missing: {missing_fields}.")

    if session.intake.contradictory_fields:
        contradictory_fields = ", ".join(session.intake.contradictory_fields)
        caveats.append(f"Some intake details conflict and need follow-up: {contradictory_fields}.")

    caveats.extend(session.eligibility_prioritization.uncertainty_flags)

    for assessment in session.eligibility_prioritization.program_assessments:
        caveats.extend([f"{assessment.program_name}: {caveat}" for caveat in assessment.caveats])

    if session.eligibility_prioritization.decision_status == DecisionStatus.ambiguous:
        caveats.append(
            "Some program results remain uncertain and may change if missing or conflicting information is clarified."
        )

    if not recommended_programs:
        caveats.append(
            "No clear match was found from the current information. This is not a denial."
        )

    caveats.extend(checklist_caveats)
    return _preserve_order_unique(caveats)


def _generate_next_steps(
    recommended_programs: List[str],
    session: SessionState,
    missing_checklist_programs: List[str],
    program_sources: List[ProgramSource],
) -> List[str]:
    next_steps: List[str] = []

    if recommended_programs:
        next_steps.append("Gather the listed documents for any program you want to pursue.")
        for program in recommended_programs:
            application_step = _build_application_step(program, program_sources)
            if application_step:
                next_steps.append(application_step)
    else:
        next_steps.append(
            "Review your income, household, insurance, and heating-cost details to see whether anything needs clarification."
        )

    if missing_checklist_programs:
        next_steps.append(
            "Confirm document requirements with official program materials when the checklist is incomplete."
        )

    if (
        session.eligibility_prioritization.decision_status == DecisionStatus.ambiguous
        or session.intake.missing_fields
        or session.intake.contradictory_fields
    ):
        next_steps.append(
            "Follow up with a caseworker or official benefits office if key details are missing, contradictory, or still unclear."
        )
    elif not recommended_programs:
        next_steps.append(
            "If your situation changes or you can provide more complete information later, rerun the prescreen."
        )

    return _preserve_order_unique(next_steps)


def _build_application_step(program: str, program_sources: List[ProgramSource]) -> str | None:
    program_id = PROGRAM_ID_BY_NAME.get(program)
    if program_id is None:
        return None

    if not any(source.program_id == program_id for source in program_sources):
        return f"Review the likely application requirements for {program} before taking the next step."

    return f"Review the likely application requirements for {program} using official Pennsylvania program materials."


def _build_program_source_note(program: str, program_sources: List[ProgramSource]) -> str | None:
    program_id = PROGRAM_ID_BY_NAME.get(program)
    if program_id is None:
        return None

    relevant_sources = [source for source in program_sources if source.program_id == program_id]
    if not relevant_sources:
        return None

    relevant_sources.sort(key=lambda source: SOURCE_SCOPE_PRIORITY.get(source.source_scope, 99))
    return f"Use official Pennsylvania source materials to confirm the latest requirements for {program}."


def _generate_followup_notes(
    session: SessionState,
    missing_checklist_programs: List[str],
) -> List[str]:
    notes: List[str] = []

    if missing_checklist_programs:
        missing_programs = ", ".join(missing_checklist_programs)
        notes.append(
            f"Checklist coverage was incomplete for {missing_programs}; confirm document requirements before relying on this output."
        )

    if session.intake.contradictory_fields:
        notes.append(
            "A caseworker or official benefits office should review the conflicting information before you rely on this prescreen."
        )
    elif (
        session.eligibility_prioritization.decision_status == DecisionStatus.ambiguous
        or session.intake.missing_fields
    ):
        notes.append(
            "If uncertainty remains after gathering documents, follow up with a caseworker or official benefits office."
        )

    return _preserve_order_unique(notes)


def _determine_final_status(
    session: SessionState,
    missing_checklist_programs: List[str],
) -> FinalStatus:
    if missing_checklist_programs or session.intake.contradictory_fields:
        return FinalStatus.needs_human_followup

    if (
        session.eligibility_prioritization.decision_status == DecisionStatus.ambiguous
        or session.eligibility_prioritization.uncertainty_flags
        or session.intake.missing_fields
    ):
        return FinalStatus.delivered_with_uncertainty

    return FinalStatus.delivered


def _generate_user_explanation(
    session: SessionState,
    recommended_programs: List[str],
    checklist_items_by_program: Dict[str, List[str]],
) -> str:
    intro = "This is a prescreen only, not an official determination."

    if recommended_programs:
        sentences = [
            intro,
            f"Based on the information provided, the programs that may fit best right now are {_format_list(recommended_programs)}.",
        ]

        if len(recommended_programs) > 1:
            sentences.append(
                f"The current recommendation order is {_format_list(recommended_programs)}."
            )

        for program in recommended_programs:
            sentences.append(_describe_program_fit(program, session))

        document_examples = _summarize_document_examples(checklist_items_by_program)
        if document_examples:
            sentences.append(
                f"Start by gathering the listed documents, especially {document_examples}."
            )
        else:
            sentences.append("Review the checklist below and gather the listed documents before taking the next step.")

        sentences.append(
            "Review the next steps below and confirm current requirements with official program materials before applying."
        )

        uncertainty_summary = _summarize_uncertainty(session)
        if uncertainty_summary:
            sentences.append(f"Important caveat: {uncertainty_summary}.")

        return " ".join(sentences)

    sentences = [
        intro,
        "Based on the current information, no clear match was found among SNAP, Medicaid/CHIP, and LIHEAP.",
        "This is not a denial, and a different result may be possible if missing or conflicting details are clarified.",
    ]

    uncertainty_summary = _summarize_uncertainty(session)
    if uncertainty_summary:
        sentences.append(f"Important caveat: {uncertainty_summary}.")
    else:
        sentences.append("Review the next steps below if you want to clarify the information and try the prescreen again.")

    return " ".join(sentences)


def _describe_program_fit(program: str, session: SessionState) -> str:
    profile = session.intake.household_profile
    assessment = next(
        (
            item
            for item in session.eligibility_prioritization.program_assessments
            if item.program_name == program
        ),
        None,
    )

    reasons: List[str] = []
    if profile.household_income_total is not None:
        reasons.append("the reported income fits the current prescreen range")

    if program == "SNAP":
        if profile.food_insecurity_signal in {"clear", "possible"}:
            reasons.append("food hardship was reported")
        if profile.recent_job_loss:
            reasons.append("recent job loss can increase food-assistance need")
        if (profile.num_children or 0) > 0:
            reasons.append("children are part of the household")
    elif program == "Medicaid/CHIP":
        if profile.insurance_status in {"uninsured", "underinsured", "unknown"}:
            reasons.append("health coverage appears limited or unclear")
        if profile.pregnant_household_member:
            reasons.append("pregnancy can open a Medicaid or CHIP pathway")
        if (profile.num_children or 0) > 0:
            reasons.append("children in the household can matter for family health coverage")
    elif program == "LIHEAP":
        if profile.heating_assistance_need:
            reasons.append("heating assistance need was reported")
        if profile.utility_burden == "high":
            reasons.append("utility burden looks high")
        if profile.recent_job_loss:
            reasons.append("recent income disruption can make heating costs harder to manage")

    if not reasons and assessment is not None and assessment.matched_conditions:
        reasons.append("the current deterministic rules flagged this program as a likely fit")

    if not reasons:
        reasons.append("the current deterministic prescreen flagged this program as worth reviewing")

    return f"{program} may fit because {_format_list(reasons)}."


def _summarize_document_examples(checklist_items_by_program: Dict[str, List[str]]) -> str | None:
    examples: List[str] = []
    for items in checklist_items_by_program.values():
        for item in items:
            label = item.split(": ", 1)[1] if ": " in item else item
            examples.append(label)
            break

    if not examples:
        return None

    return _format_list(_preserve_order_unique(examples[:3]))


def _summarize_uncertainty(session: SessionState) -> str | None:
    summary_points: List[str] = []

    if session.intake.missing_fields:
        summary_points.append("some intake fields are still missing")
    if session.intake.contradictory_fields:
        summary_points.append("some intake details conflict")
    if session.eligibility_prioritization.uncertainty_flags:
        summary_points.append("more documentation could change one or more program results")

    if not summary_points:
        return None
    return _format_list(summary_points)


def _preserve_order_unique(items: Sequence[str]) -> List[str]:
    seen = set()
    ordered_items: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered_items.append(item)
    return ordered_items


def _format_list(items: Sequence[str]) -> str:
    values = [item for item in items if item]
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return f"{', '.join(values[:-1])}, and {values[-1]}"
