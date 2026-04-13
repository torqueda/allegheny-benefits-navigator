from __future__ import annotations

from src.models.common import FinalStatus, ProgramStatus
from src.models.session import (
    ChecklistExplanationOutput,
    EligibilityPrioritizationOutput,
    IntakeOutput,
)


CHECKLISTS = {
    "SNAP": ["Photo ID", "Proof of income", "Recent utility or housing bill"],
    "Medicaid/CHIP": ["Photo ID", "Proof of income", "Insurance information if any"],
    "LIHEAP": ["Recent heating bill", "Proof of income", "Household address verification"],
    "WIC": ["Proof of pregnancy or child age", "Proof of income", "Proof of identity"],
    "Local Referral": ["Short summary of urgent need", "Lease or eviction notice if relevant", "Preferred contact method"],
}


def run_checklist_and_explanation(
    intake: IntakeOutput, eligibility: EligibilityPrioritizationOutput
) -> ChecklistExplanationOutput:
    assessments = {item.program_name: item for item in eligibility.program_assessments}
    recommended_programs = [
        name
        for name in eligibility.priority_order
        if assessments[name].status != ProgramStatus.LIKELY_INAPPLICABLE
    ]
    checklist_items = {
        program: CHECKLISTS.get(program, ["Gather documents relevant to this program."])
        for program in recommended_programs
    }

    visible_caveats = list(eligibility.uncertainty_flags)
    for program in recommended_programs:
        visible_caveats.extend(assessments[program].caveats)

    next_steps = _build_next_steps(recommended_programs, intake, eligibility)
    explanation = _build_explanation(recommended_programs, intake, assessments, visible_caveats)
    referral_notes = []
    if "Local Referral" in recommended_programs:
        referral_notes.append(
            "A local navigator or caseworker may help resolve ambiguity, local housing issues, or application barriers."
        )

    if eligibility.decision_status == eligibility.decision_status.AMBIGUOUS:
        final_status = FinalStatus.DELIVERED_WITH_UNCERTAINTY
    elif "Local Referral" in recommended_programs and intake.intake_status != intake.intake_status.COMPLETE:
        final_status = FinalStatus.NEEDS_HUMAN_FOLLOWUP
    else:
        final_status = FinalStatus.DELIVERED

    return ChecklistExplanationOutput(
        recommended_programs=recommended_programs,
        checklist_items_by_program=checklist_items,
        next_steps=next_steps,
        user_explanation=explanation,
        visible_caveats=visible_caveats,
        referral_notes=referral_notes,
        final_status=final_status,
    )


def _build_next_steps(recommended_programs, intake, eligibility) -> list[str]:
    steps: list[str] = []
    if intake.clarification_questions:
        steps.append("Clarify missing or contradictory intake details before relying on final prescreening.")
    if recommended_programs:
        steps.append("Gather the listed documents for the highest-priority programs first.")
    if "LIHEAP" in recommended_programs:
        steps.append("Address heating-bill urgency first if there is a shutoff or overdue balance.")
    if "Local Referral" in recommended_programs:
        steps.append("Contact a local navigator, benefits helper, or housing-support organization for follow-up.")
    if not recommended_programs:
        steps.append("No clear in-scope match was found; consider a human review if circumstances change.")
    steps.append("Treat this as prescreening only, not an official eligibility determination.")
    return steps


def _build_explanation(recommended_programs, intake, assessments, visible_caveats) -> str:
    if not recommended_programs:
        return (
            "Based on the information provided, this prototype did not find a clear in-scope program match. "
            "That does not mean the household is officially ineligible, only that the bounded screen did not find a strong fit."
        )

    pieces = [
        "Based on the information provided, this household may be a fit for "
        + ", ".join(recommended_programs)
        + "."
    ]
    for program in recommended_programs:
        matched = assessments[program].matched_conditions
        if matched:
            pieces.append(f"{program}: {matched[0]}")
    if visible_caveats:
        pieces.append("Caveats: " + " ".join(visible_caveats))
    pieces.append("This is a prescreening and next-step guide, not an official determination.")
    return " ".join(pieces)
