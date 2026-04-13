from __future__ import annotations

from dataclasses import dataclass

from src.models.common import DecisionStatus, ProgramStatus
from src.models.session import EligibilityPrioritizationOutput, IntakeOutput, ProgramAssessment


SNAP_LIMITS = {1: 1800, 2: 2800, 3: 3600, 4: 4200, 5: 5200, 6: 6000}
LIHEAP_MONTHLY_LIMITS = {1: 2200, 2: 4200, 3: 4500, 4: 4200, 5: 5200, 6: 6200}
MEDICAID_ADULT_LIMITS = {1: 1800, 2: 2600, 3: 3200, 4: 3800, 5: 4500, 6: 5200}
MEDICAID_CHILD_LIMITS = {1: 2600, 2: 3600, 3: 4200, 4: 4300, 5: 5200, 6: 6200}
WIC_LIMITS = {1: 2900, 2: 3900, 3: 4900, 4: 5900, 5: 6900, 6: 7900}


@dataclass
class ProgramRuleContext:
    income: float | None
    household_size: int
    intake: IntakeOutput


def _limit(table: dict[int, int], household_size: int) -> int:
    return table.get(household_size, table[max(table)])


def _is_near_limit(income: float | None, limit: int, tolerance: float = 0.05) -> bool:
    if income is None:
        return False
    return abs(income - limit) <= limit * tolerance


def _needs_local_referral(
    profile_summary: str, notes: str, has_structured_ambiguity: bool
) -> bool:
    text = f"{profile_summary} {notes}".lower()
    strong_keywords = ["eviction", "housing", "rental", "legal", "spanish", "shutoff", "rushed"]
    return has_structured_ambiguity or any(keyword in text for keyword in strong_keywords)


def _make_assessment(program_name: str, status: ProgramStatus) -> ProgramAssessment:
    return ProgramAssessment(program_name=program_name, status=status)


def _contradiction_text(intake: IntakeOutput) -> str:
    return " | ".join(intake.contradictory_fields).lower()


def _has_income_contradiction(intake: IntakeOutput) -> bool:
    text = _contradiction_text(intake)
    return any(keyword in text for keyword in ["income", "employment_status", "monthly_earned_income"])


def _has_household_composition_contradiction(intake: IntakeOutput) -> bool:
    text = _contradiction_text(intake)
    return any(keyword in text for keyword in ["household composition", "dependent status"])


def run_eligibility_and_prioritization(intake: IntakeOutput) -> EligibilityPrioritizationOutput:
    profile = intake.household_profile
    income = profile.household_income_total
    household_size = profile.household_size or 1
    ctx = ProgramRuleContext(income=income, household_size=household_size, intake=intake)

    uncertainty_flags: list[str] = []
    if intake.missing_fields:
        uncertainty_flags.append("Missing core fields limit deterministic prescreening.")
    if intake.contradictory_fields:
        uncertainty_flags.append("Contradictory intake data requires follow-up.")
    if profile.insurance_status == "unknown":
        uncertainty_flags.append("Unknown insurance status affects Medicaid/CHIP confidence.")
    if profile.pregnant_household_member:
        uncertainty_flags.append(
            "Pregnancy-related coverage may apply differently across household members."
        )

    assessments = [
        _evaluate_snap(ctx, uncertainty_flags),
        _evaluate_medicaid_chip(ctx, uncertainty_flags),
        _evaluate_liheap(ctx, uncertainty_flags),
        _evaluate_wic(ctx, uncertainty_flags),
        _evaluate_local_referral(ctx, uncertainty_flags),
    ]

    likely_programs = [
        item.program_name for item in assessments if item.status == ProgramStatus.LIKELY_APPLICABLE
    ]
    inapplicable_programs = [
        item.program_name for item in assessments if item.status == ProgramStatus.LIKELY_INAPPLICABLE
    ]

    if any(item.status == ProgramStatus.UNCERTAIN for item in assessments):
        decision_status = DecisionStatus.AMBIGUOUS
    elif intake.intake_status == intake.intake_status.INSUFFICIENT_DATA:
        decision_status = DecisionStatus.INSUFFICIENT_DATA
    else:
        decision_status = DecisionStatus.READY_FOR_EXPLANATION

    priority_order, priority_rationale = _rank_programs(profile, assessments, uncertainty_flags)

    return EligibilityPrioritizationOutput(
        program_assessments=assessments,
        eligible_or_likely_programs=likely_programs,
        inapplicable_programs=inapplicable_programs,
        uncertainty_flags=uncertainty_flags,
        priority_order=priority_order,
        priority_rationale=priority_rationale,
        decision_status=decision_status,
    )


def _evaluate_snap(ctx: ProgramRuleContext, uncertainty_flags: list[str]) -> ProgramAssessment:
    assessment = _make_assessment("SNAP", ProgramStatus.LIKELY_INAPPLICABLE)
    limit = _limit(SNAP_LIMITS, ctx.household_size)
    assessment.source_refs = ["PA SNAP gross-income guidance (curated)"]

    if ctx.income is None:
        assessment.status = ProgramStatus.UNCERTAIN
        assessment.missing_evidence.append("household_income_total")
        assessment.caveats.append("Income is missing, so SNAP cannot be screened reliably.")
        return assessment

    if ctx.income <= limit:
        assessment.status = ProgramStatus.LIKELY_APPLICABLE
        assessment.matched_conditions.extend(
            [
                f"Household income {ctx.income:.0f} is within the prototype SNAP threshold {limit}.",
                "Food hardship or low-income signal supports prescreening relevance."
                if ctx.intake.household_profile.food_insecurity_signal in {"clear", "possible"}
                else "Income threshold fit is the main positive signal.",
            ]
        )
        if _is_near_limit(ctx.income, limit):
            assessment.caveats.append("Income appears close to the SNAP threshold and should be verified.")
            uncertainty_flags.append("SNAP threshold edge case.")
        if _has_income_contradiction(ctx.intake):
            assessment.status = ProgramStatus.UNCERTAIN
            assessment.caveats.append("Contradictory intake data blocks a firm SNAP read.")
    else:
        assessment.failed_conditions.append(
            f"Household income {ctx.income:.0f} exceeds the prototype SNAP threshold {limit}."
        )
    return assessment


def _evaluate_medicaid_chip(
    ctx: ProgramRuleContext, uncertainty_flags: list[str]
) -> ProgramAssessment:
    assessment = _make_assessment("Medicaid/CHIP", ProgramStatus.LIKELY_INAPPLICABLE)
    profile = ctx.intake.household_profile
    assessment.source_refs = ["PA Medicaid/CHIP eligibility snapshot (curated)"]

    if ctx.income is None:
        assessment.status = ProgramStatus.UNCERTAIN
        assessment.missing_evidence.append("household_income_total")
        return assessment

    if profile.insurance_status == "insured":
        assessment.failed_conditions.append("Current insurance status reduces likely fit for Medicaid/CHIP.")
        return assessment

    pregnancy_adjusted_size = ctx.household_size + (2 if profile.pregnant_household_member else 0)
    adult_limit = _limit(MEDICAID_ADULT_LIMITS, pregnancy_adjusted_size)
    child_limit = _limit(MEDICAID_CHILD_LIMITS, pregnancy_adjusted_size)

    if profile.pregnant_household_member and ctx.income <= child_limit:
        assessment.status = ProgramStatus.LIKELY_APPLICABLE
        assessment.matched_conditions.append(
            "Pregnancy increases the effective household size for the prototype Medicaid screen."
        )
        assessment.caveats.append("Pregnancy-specific Medicaid may apply even if other adults do not qualify.")
        return assessment

    if profile.num_children and profile.num_children > 0 and ctx.income <= child_limit:
        assessment.status = ProgramStatus.LIKELY_APPLICABLE
        assessment.matched_conditions.append(
            f"Children in the household keep income within the prototype Medicaid/CHIP threshold {child_limit}."
        )
        if profile.insurance_status == "unknown":
            assessment.caveats.append("Coverage status is unclear and should be verified during follow-up.")
        if profile.child_under_5 and _is_near_limit(ctx.income, child_limit, tolerance=0.08):
            assessment.caveats.append("Child age bands may split Medicaid vs CHIP outcomes.")
            uncertainty_flags.append("Child coverage may vary by age band.")
        if _has_household_composition_contradiction(ctx.intake):
            assessment.status = ProgramStatus.UNCERTAIN
            assessment.caveats.append("Household-composition contradictions block a firm Medicaid/CHIP read.")
        if _has_income_contradiction(ctx.intake):
            assessment.status = ProgramStatus.UNCERTAIN
            assessment.caveats.append("Contradictory income details block a firm Medicaid/CHIP read.")
        return assessment

    if ctx.income <= adult_limit:
        assessment.status = ProgramStatus.LIKELY_APPLICABLE
        assessment.matched_conditions.append(
            f"Adult household income is within the prototype Medicaid limit {adult_limit}."
        )
        if profile.insurance_status == "unknown":
            assessment.status = ProgramStatus.UNCERTAIN
            assessment.missing_evidence.append("insurance_status")
            assessment.caveats.append("Coverage status is unclear, so Medicaid/CHIP fit cannot be finalized.")
        if _has_income_contradiction(ctx.intake):
            assessment.status = ProgramStatus.UNCERTAIN
            assessment.caveats.append("Contradictory intake data blocks a firm Medicaid/CHIP read.")
        return assessment

    if profile.insurance_status == "unknown":
        assessment.status = ProgramStatus.UNCERTAIN
        assessment.missing_evidence.append("insurance_status")
        assessment.caveats.append("Coverage status is unclear, so Medicaid/CHIP fit cannot be finalized.")
        return assessment

    assessment.failed_conditions.append(
        f"Household income {ctx.income:.0f} is above the prototype Medicaid/CHIP threshold."
    )
    return assessment


def _evaluate_liheap(ctx: ProgramRuleContext, uncertainty_flags: list[str]) -> ProgramAssessment:
    assessment = _make_assessment("LIHEAP", ProgramStatus.LIKELY_INAPPLICABLE)
    profile = ctx.intake.household_profile
    limit = _limit(LIHEAP_MONTHLY_LIMITS, ctx.household_size)
    assessment.source_refs = ["PA LIHEAP income snapshot (curated)"]

    if not profile.heating_assistance_need:
        assessment.failed_conditions.append("No heating-assistance need was reported.")
        return assessment

    if ctx.income is None:
        assessment.status = ProgramStatus.UNCERTAIN
        assessment.missing_evidence.append("household_income_total")
        return assessment

    if ctx.income <= limit:
        assessment.status = ProgramStatus.LIKELY_APPLICABLE
        assessment.matched_conditions.append(
            f"Heating-assistance need is present and income {ctx.income:.0f} is within the prototype LIHEAP limit {limit}."
        )
        if _is_near_limit(ctx.income, limit):
            assessment.caveats.append("LIHEAP appears close to the income cutoff and should be verified.")
            uncertainty_flags.append("LIHEAP threshold edge case.")
        if _has_income_contradiction(ctx.intake):
            assessment.status = ProgramStatus.UNCERTAIN
            assessment.caveats.append("Contradictory intake data blocks a firm LIHEAP read.")
    else:
        assessment.failed_conditions.append(
            f"Income {ctx.income:.0f} exceeds the prototype LIHEAP limit {limit}."
        )
    return assessment


def _evaluate_wic(ctx: ProgramRuleContext, uncertainty_flags: list[str]) -> ProgramAssessment:
    assessment = _make_assessment("WIC", ProgramStatus.LIKELY_INAPPLICABLE)
    profile = ctx.intake.household_profile
    limit = _limit(WIC_LIMITS, ctx.household_size + (2 if profile.pregnant_household_member else 0))
    assessment.source_refs = ["PA WIC income snapshot (curated)"]

    if not (profile.child_under_5 or profile.pregnant_household_member):
        assessment.failed_conditions.append("No child under 5 or pregnancy signal was provided.")
        return assessment

    if ctx.income is None:
        assessment.status = ProgramStatus.UNCERTAIN
        assessment.missing_evidence.append("household_income_total")
        return assessment

    if ctx.income <= limit:
        assessment.status = ProgramStatus.LIKELY_APPLICABLE
        assessment.matched_conditions.append(
            f"Income {ctx.income:.0f} is within the prototype WIC limit {limit}."
        )
    else:
        assessment.failed_conditions.append(
            f"Income {ctx.income:.0f} exceeds the prototype WIC limit {limit}."
        )
    return assessment


def _evaluate_local_referral(
    ctx: ProgramRuleContext, uncertainty_flags: list[str]
) -> ProgramAssessment:
    assessment = _make_assessment("Local Referral", ProgramStatus.LIKELY_INAPPLICABLE)
    profile = ctx.intake.household_profile
    summary = profile.scenario_summary or ""
    notes = profile.language_or_stress_notes or ""
    has_structured_ambiguity = bool(ctx.intake.missing_fields or ctx.intake.contradictory_fields)

    if _needs_local_referral(summary, notes, has_structured_ambiguity):
        assessment.status = ProgramStatus.LIKELY_APPLICABLE
        assessment.matched_conditions.append(
            "The case includes navigation, ambiguity, or local-support signals that warrant a human/community referral."
        )
        if "housing" in f"{summary} {notes}".lower() or "eviction" in f"{summary} {notes}".lower():
            assessment.caveats.append("Local referral should focus on housing stabilization resources.")
    else:
        assessment.failed_conditions.append("No strong local referral trigger was detected in the prototype rules.")
    return assessment


def _rank_programs(
    profile, assessments: list[ProgramAssessment], uncertainty_flags: list[str]
) -> tuple[list[str], list[str]]:
    scores: dict[str, int] = {}
    for assessment in assessments:
        score = 0
        is_likely = assessment.status == ProgramStatus.LIKELY_APPLICABLE
        is_uncertain = assessment.status == ProgramStatus.UNCERTAIN

        if is_likely:
            score += 100
        elif is_uncertain:
            score += 70
        else:
            score += 0

        if assessment.program_name == "LIHEAP" and profile.heating_assistance_need:
            score += 35 if is_likely else 20
        if assessment.program_name == "LIHEAP" and (profile.household_size or 0) == 1:
            score += 15 if is_likely else 5
        if assessment.program_name == "SNAP" and profile.food_insecurity_signal == "clear":
            score += 45 if is_likely else 25
        if assessment.program_name == "SNAP" and profile.food_insecurity_signal == "possible":
            score += 15 if is_likely else 8
        if assessment.program_name == "SNAP" and profile.num_children and profile.num_children > 0:
            score += 10 if is_likely else 4
        if (
            assessment.program_name == "SNAP"
            and profile.heating_assistance_need
            and profile.food_insecurity_signal in {"clear", "possible"}
            and profile.num_children
            and profile.num_children > 0
        ):
            score += 6 if is_likely else 3
        if assessment.program_name == "Medicaid/CHIP" and profile.insurance_status in {"uninsured", "underinsured"}:
            score += 20 if is_likely else 8
        if assessment.program_name == "WIC" and (profile.child_under_5 or profile.pregnant_household_member):
            score += 5 if is_likely else 2
        if assessment.program_name == "Medicaid/CHIP" and profile.num_children and profile.num_children > 0:
            score += 8 if is_likely else 4
        if assessment.program_name == "Local Referral" and (profile.language_or_stress_notes or "").lower().find("spanish") >= 0:
            score += 20
        if assessment.program_name == "Local Referral" and (
            profile.scenario_summary or ""
        ).lower().find("housing") >= 0:
            score += 10
        if assessment.program_name == "Local Referral" and (
            profile.scenario_summary or ""
        ).lower().find("eviction") >= 0:
            score += 50
        if assessment.program_name == "Local Referral" and (
            profile.scenario_summary or ""
        ).lower().find("shutoff") >= 0:
            score += 20
        if assessment.program_name == "Local Referral" and (
            profile.language_or_stress_notes or ""
        ).lower().find("rushed") >= 0:
            score += 10
        if assessment.program_name == "Local Referral" and (
            profile.language_or_stress_notes or ""
        ).lower().find("stressed") >= 0:
            score += 5
        if assessment.program_name == "Local Referral" and (
            profile.scenario_summary or ""
        ).lower().find("recent layoff") >= 0:
            score += 10
        if assessment.program_name == "Local Referral" and uncertainty_flags:
            score += 45
        scores[assessment.program_name] = score

    ranked = [
        name for name, score in sorted(scores.items(), key=lambda item: (-item[1], item[0])) if score > 0
    ]
    rationale = [f"{name} ranked with prototype score {scores[name]}." for name in ranked]
    return ranked, rationale
