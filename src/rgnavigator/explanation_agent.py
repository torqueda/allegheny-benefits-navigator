from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .models import EligibilityOutput, ExplanationOutput, IntakeOutput


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


load_dotenv(_project_root() / ".env")


def run_checklist_and_explanation(intake: IntakeOutput, eligibility: EligibilityOutput) -> ExplanationOutput:
    recommended_matches = [
        match for match in eligibility.program_matches if match.program_name in eligibility.recommended_programs
    ]

    checklist_by_program = {
        match.program_name: _clean_checklist_items(match.checklist_items)
        for match in recommended_matches
    }
    visible_caveats = _base_visible_caveats(intake, eligibility, recommended_matches)
    evidence_quotes = _build_evidence_quotes(recommended_matches)
    next_steps = _build_next_steps(intake, eligibility)
    explanation = _build_explanation(intake, recommended_matches, eligibility)

    if _should_use_llm_explanation(intake, eligibility):
        llm_content = _generate_explanation_with_llm(
            intake=intake,
            eligibility=eligibility,
            recommended_matches=recommended_matches,
            fallback_checklist=checklist_by_program,
            fallback_next_steps=next_steps,
            fallback_explanation=explanation,
            fallback_caveats=visible_caveats,
        )
        if llm_content:
            checklist_by_program = llm_content.get("checklist_by_program", checklist_by_program)
            next_steps = llm_content.get("next_steps", next_steps)
            explanation = llm_content.get("plain_language_explanation", explanation)
            visible_caveats = llm_content.get("visible_caveats", visible_caveats)

    final_status = (
        "needs_human_followup"
        if _requires_human_followup(intake)
        else "delivered_with_uncertainty"
        if eligibility.decision_status == "ambiguous"
        else "delivered"
    )

    return ExplanationOutput(
        recommended_programs=eligibility.recommended_programs,
        checklist_by_program=checklist_by_program,
        next_steps=next_steps,
        plain_language_explanation=explanation,
        visible_caveats=_dedupe(visible_caveats),
        evidence_quotes=evidence_quotes,
        final_status=final_status,
    )


def _base_visible_caveats(intake: IntakeOutput, eligibility: EligibilityOutput, recommended_matches) -> list[str]:
    visible_caveats = [
        "This is prescreening only.",
        "This is not an official determination.",
    ]
    visible_caveats.extend(eligibility.uncertainty_flags)
    if _is_out_of_scope(intake):
        visible_caveats.append("This prototype currently supports Allegheny County households only.")
    if intake.contradictory_fields:
        visible_caveats.append("Conflicting intake details must be resolved before relying on this prescreen.")
    if intake.missing_fields:
        visible_caveats.append(f"Key details are still missing: {', '.join(intake.missing_fields)}.")
    for match in recommended_matches:
        visible_caveats.extend(match.caveats[:2])
    return _dedupe(visible_caveats)


def _build_evidence_quotes(recommended_matches) -> list[str]:
    evidence_quotes = []
    for match in recommended_matches:
        if match.retrieved_evidence:
            top_chunk = match.retrieved_evidence[0]
            label = top_chunk.section_title or top_chunk.title
            quote = f"{match.program_name} ({label}): {top_chunk.text}"
            if quote not in evidence_quotes:
                evidence_quotes.append(quote)
    return evidence_quotes


def _build_next_steps(intake: IntakeOutput, eligibility: EligibilityOutput) -> list[str]:
    steps = []
    if _is_out_of_scope(intake):
        steps.append("This prototype supports Allegheny County households only.")
        steps.append("Contact the local county assistance office or a human caseworker in the household's county.")
        steps.append("Do not rely on this prescreen for out-of-county eligibility decisions.")
        return _dedupe(steps)
    if intake.contradictory_fields:
        steps.append("Resolve the contradictory intake details before relying on this prescreen.")
        steps.append(f"Conflicting details: {', '.join(intake.contradictory_fields)}.")
        steps.append("Update the household facts, then rerun the prescreen or review with a caseworker.")
        return _dedupe(steps)
    if eligibility.recommended_programs:
        steps.append("Review the recommended programs in the order shown and compare each one against the retrieved policy sections.")
    else:
        steps.append("No clear program match was found from the current information. Review the intake and policy evidence.")
    if intake.extracted_signals:
        steps.append("Confirm the structured intake fields extracted from the household description before relying on the ranking.")
    if intake.missing_fields:
        steps.append(f"Gather or confirm these missing details: {', '.join(intake.missing_fields)}.")
        steps.append("The most important missing information is the evidence that would change program fit or income screening.")
    if intake.contradictory_fields:
        steps.append("Resolve contradictory intake details before relying on this prescreen.")
    if eligibility.decision_status == "ambiguous":
        steps.append("Use the retrieved policy evidence as guidance, then confirm the result with official materials or a caseworker.")
    else:
        steps.append("Use official program materials to confirm the most current requirements before applying.")
    return _dedupe(steps)


def _build_explanation(intake: IntakeOutput, matches, eligibility: EligibilityOutput) -> str:
    intro = "This upgraded navigator turns the household description into structured intake fields, then ranks programs using retrieved local policy evidence."
    if _is_out_of_scope(intake):
        return (
            "This prototype currently supports Allegheny County households only. "
            "The household appears to be outside that supported geography, so the system is stopping before normal recommendations. "
            "Use county-specific official resources or a human caseworker before relying on any benefits prescreen."
        )
    if intake.contradictory_fields:
        return (
            f"{intro} The current intake contains contradictory core details ({', '.join(intake.contradictory_fields)}), "
            "so the system is withholding normal actionable recommendations. "
            "Please resolve the contradiction and rerun the prescreen before relying on any eligibility guidance."
        )
    if not matches:
        if intake.missing_fields:
            return (
                f"{intro} The system is not making a normal recommendation because key details are still missing "
                f"({', '.join(intake.missing_fields)}). "
                "Gathering those facts will most affect whether the prescreen can safely estimate program fit."
            )
        return (
            f"{intro} Based on the information currently available, no clear program match stood out strongly enough to recommend. "
            "That does not mean the household is ineligible; it means the current profile and retrieved evidence did not produce a strong enough match."
        )

    program_list = ", ".join(match.program_name for match in matches)
    pieces = [
        intro,
        f"Based on the intake handoff and the retrieved policy chunks, the strongest current matches are {program_list}.",
    ]
    if intake.missing_fields or intake.contradictory_fields:
        pieces.append(
            "The system is preserving uncertainty because some details are missing or contradictory."
        )
    for match in matches:
        if match.rationale:
            pieces.append(f"For {match.program_name}, the main reason is: {match.rationale[0].reason}")
        if match.retrieved_evidence:
            top_chunk = match.retrieved_evidence[0]
            section = top_chunk.section_title or top_chunk.title
            pieces.append(f"Retrieved evidence for {match.program_name} highlights the section '{section}': {top_chunk.text}")
    pieces.append("Treat this as a guided prescreen and next-step summary, not a final eligibility decision.")
    return " ".join(pieces)


def _is_out_of_scope(intake: IntakeOutput) -> bool:
    county = (intake.normalized_profile.county or "").strip().lower()
    return bool(county) and county != "allegheny"


def _requires_human_followup(intake: IntakeOutput) -> bool:
    return _is_out_of_scope(intake) or bool(intake.contradictory_fields)


def _should_use_llm_explanation(intake: IntakeOutput, eligibility: EligibilityOutput) -> bool:
    if _requires_human_followup(intake):
        return False
    if intake.intake_status == "insufficient_data" and not eligibility.recommended_programs:
        return False
    return True


def _generate_explanation_with_llm(
    *,
    intake: IntakeOutput,
    eligibility: EligibilityOutput,
    recommended_matches,
    fallback_checklist: dict[str, list[str]],
    fallback_next_steps: list[str],
    fallback_explanation: str,
    fallback_caveats: list[str],
) -> dict | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    client = OpenAI(api_key=api_key)
    model = os.getenv("EXPLANATION_LLM_MODEL", "gpt-4o-mini")

    payload = {
        "intake_summary": intake.intake_summary,
        "intake_status": intake.intake_status,
        "priority_order": eligibility.priority_order,
        "recommended_programs": eligibility.recommended_programs,
        "decision_status": eligibility.decision_status,
        "matches": [
            {
                "program_name": match.program_name,
                "status": match.status,
                "match_score": match.match_score,
                "priority_score": match.priority_score,
                "main_reasons": [reason.reason for reason in match.rationale[:2]],
                "top_evidence_section": (
                    (match.retrieved_evidence[0].section_title or match.retrieved_evidence[0].title)
                    if match.retrieved_evidence
                    else None
                ),
                "top_evidence_snippet": (
                    match.retrieved_evidence[0].text[:500]
                    if match.retrieved_evidence
                    else None
                ),
                "checklist_items": match.checklist_items,
                "caveats": match.caveats[:3],
            }
            for match in recommended_matches
        ],
        "fallback": {
            "plain_language_explanation": fallback_explanation,
            "next_steps": fallback_next_steps,
            "checklist_by_program": fallback_checklist,
            "visible_caveats": fallback_caveats,
        },
    }

    schema = {
        "type": "object",
        "properties": {
            "plain_language_explanation": {"type": "string"},
            "next_steps": {"type": "array", "items": {"type": "string"}},
            "visible_caveats": {"type": "array", "items": {"type": "string"}},
            "checklist_by_program": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
        "required": [
            "plain_language_explanation",
            "next_steps",
            "visible_caveats",
            "checklist_by_program",
        ],
        "additionalProperties": False,
    }

    instructions = (
        "You are generating a plain-language benefits prescreen explanation for a resident. "
        "Stay grounded in the provided structured results. "
        "Do not invent eligibility facts or policy rules. "
        "Write clearly and simply. "
        "Keep the explanation concise, supportive, and user-facing. "
        "The explanation should be 3 to 5 sentences and mention each recommended program with a concrete reason it may fit. "
        "Checklist items should be short, concrete document or action items, not policy quotations, chapter names, rejection reasons, or long copied text. "
        "Each checklist item should usually be under 12 words. "
        "Next steps should be practical and ordered. "
        "Visible caveats should be short and understandable. "
        "Do not mention internal scoring, chunks, retrieval, or system architecture. "
        "Return only JSON matching the requested schema."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": (
                        "Return JSON matching this schema:\n"
                        f"{json.dumps(schema, ensure_ascii=False)}\n\n"
                        "Use this structured prescreen context:\n"
                        f"{json.dumps(payload, ensure_ascii=False)}"
                    ),
                },
            ],
        )
    except Exception:
        return None

    content = response.choices[0].message.content
    if not content:
        return None

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return None

    explanation = parsed.get("plain_language_explanation")
    next_steps = parsed.get("next_steps")
    visible_caveats = parsed.get("visible_caveats")
    checklist_by_program = parsed.get("checklist_by_program")

    cleaned_checklists: dict[str, list[str]] = {}
    if isinstance(checklist_by_program, dict):
        for program_name, items in checklist_by_program.items():
            if not isinstance(program_name, str) or not isinstance(items, list):
                continue
            cleaned_items = [item.strip() for item in items if isinstance(item, str) and item.strip()]
            if cleaned_items:
                cleaned_checklists[program_name] = _dedupe(cleaned_items)[:6]

    cleaned_next_steps = []
    if isinstance(next_steps, list):
        cleaned_next_steps = _dedupe(
            [item.strip() for item in next_steps if isinstance(item, str) and item.strip()]
        )[:6]

    cleaned_caveats = []
    if isinstance(visible_caveats, list):
        cleaned_caveats = _dedupe(
            [item.strip() for item in visible_caveats if isinstance(item, str) and item.strip()]
        )[:8]

    cleaned_explanation = explanation.strip() if isinstance(explanation, str) and explanation.strip() else None

    if not any([cleaned_explanation, cleaned_next_steps, cleaned_caveats, cleaned_checklists]):
        return None

    return {
        "plain_language_explanation": cleaned_explanation or fallback_explanation,
        "next_steps": cleaned_next_steps or fallback_next_steps,
        "visible_caveats": cleaned_caveats or fallback_caveats,
        "checklist_by_program": {
            program_name: _clean_checklist_items(items)
            for program_name, items in (cleaned_checklists or fallback_checklist).items()
        },
    }


def _dedupe(items: list[str]) -> list[str]:
    result = []
    for item in items:
        if item and item not in result:
            result.append(item)
    return result


def _clean_checklist_items(items: list[str]) -> list[str]:
    cleaned: list[str] = []
    for item in items:
        if not item:
            continue
        normalized = item.strip()
        lowered = normalized.lower()
        if not normalized:
            continue
        if len(normalized) > 140:
            continue
        if lowered.startswith("chapter "):
            continue
        if lowered.startswith("# "):
            continue
        if "appendix" in lowered and len(normalized.split()) <= 6:
            continue
        if "rejection" in lowered or "entered in error" in lowered or "duplicate application" in lowered:
            continue
        if "state plan" in lowered and len(normalized.split()) > 10:
            continue
        if normalized not in cleaned:
            cleaned.append(normalized)
    return cleaned[:6]
