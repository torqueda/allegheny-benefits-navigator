from __future__ import annotations

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .models import IntakeOutput, UserIntake

NON_ANSWER_MARKERS = {
    "unknown",
    "i don't know",
    "dont know",
    "do not know",
    "not sure",
    "unsure",
    "skip",
    "pass",
    "n/a",
    "na",
    "prefer not to say",
}

SUPPORTED_COUNTY = "Allegheny"
OUT_OF_SCOPE_COUNTY_MARKER = "Outside Supported Geography"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


load_dotenv(_project_root() / ".env")


def run_intake(raw_input: dict) -> IntakeOutput:
    normalized = _normalize_raw_input(raw_input)
    description = normalized.get("user_description")
    rules_extracted = _extract_from_description(description)
    llm_extracted = _extract_with_llm(normalized)
    normalized = {
        **rules_extracted,
        **llm_extracted,
        **{key: value for key, value in normalized.items() if value is not None},
    }
    normalized = _apply_intake_normalization_overrides(normalized, description)
    profile = UserIntake(**normalized)

    geography_status = _determine_geography_status(profile, description)
    missing_fields = _detect_missing_fields(profile, geography_status)
    contradictory_fields = _detect_contradictions(profile, description, geography_status)
    validation_reasons = _build_validation_reasons(profile, missing_fields, contradictory_fields, geography_status)
    questions = _build_clarification_questions(
        profile,
        missing_fields,
        contradictory_fields,
        normalized,
        geography_status,
    )
    status = _determine_intake_status(missing_fields, contradictory_fields, geography_status)

    summary = _build_intake_summary(profile, missing_fields, contradictory_fields)
    return IntakeOutput(
        normalized_profile=profile,
        missing_fields=missing_fields,
        contradictory_fields=contradictory_fields,
        extracted_signals=_build_extracted_signals(
            profile,
            normalized.get("user_description"),
            geography_status=geography_status,
            llm_used=bool(llm_extracted),
        ),
        intake_status=status,
        geography_status=geography_status,
        validation_reasons=validation_reasons,
        intake_summary=summary,
        clarification_questions=questions,
    )


def run_intake_turn(
    prior_raw_input: dict | None,
    new_user_message: str,
    *,
    append_to_user_description: bool = True,
) -> tuple[dict, IntakeOutput]:
    merged_input = merge_intake_inputs(
        prior_raw_input or {},
        {"user_description": new_user_message},
        append_to_user_description=append_to_user_description,
    )
    return merged_input, run_intake(merged_input)


def merge_intake_inputs(
    base_input: dict,
    update_input: dict,
    *,
    append_to_user_description: bool = True,
) -> dict:
    merged = dict(base_input)

    for key, value in update_input.items():
        if key == "user_description" and append_to_user_description:
            if isinstance(value, str) and value.strip():
                previous = merged.get("user_description")
                if isinstance(previous, str) and previous.strip():
                    merged[key] = f"{previous.rstrip()}\n\nFollow-up: {value.strip()}"
                else:
                    merged[key] = value.strip()
            continue

        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                continue
            if key != "user_description" and stripped.lower() in NON_ANSWER_MARKERS:
                continue
            merged[key] = stripped
            continue

        if value is not None:
            merged[key] = value

    return merged


def _normalize_raw_input(raw: dict) -> dict:
    normalized = {}
    for key, value in raw.items():
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                normalized[key] = None
            elif key != "user_description" and stripped.lower() in NON_ANSWER_MARKERS:
                normalized[key] = None
            else:
                normalized[key] = stripped
        else:
            normalized[key] = value
    return normalized


def _extract_from_description(description: str | None) -> dict:
    if not description:
        return {}

    text = description.lower()
    extracted: dict = {"user_description": description}

    county = _extract_county_from_text(text)
    if county:
        extracted["county"] = county

    adults = _extract_people_count(text, "adult")
    if adults is not None:
        extracted["num_adults"] = adults
    elif "single adult" in text or "single person" in text:
        extracted["num_adults"] = 1
    elif any(phrase in text for phrase in ("with my husband", "with my wife", "with my spouse", "with my partner")):
        extracted["num_adults"] = 2
    elif any(phrase in text for phrase in ("by myself", "live alone", "i live alone", "alone")):
        extracted["num_adults"] = 1

    children = _extract_people_count(text, "child")
    if children is not None:
        extracted["num_children"] = children
    elif "no children" in text:
        extracted["num_children"] = 0
    elif any(phrase in text for phrase in ("with my son", "with my daughter", "my son.", "my daughter.")):
        extracted["num_children"] = 1
    elif any(phrase in text for phrase in ("by myself", "live alone", "i live alone", "alone")):
        extracted["num_children"] = 0

    if extracted.get("num_adults") is None and ("i live" in text or text.startswith("i am")):
        extracted["num_adults"] = 1

    income_match = re.search(r"\$?\s*([0-9]{3,5})(?:\s*(?:/|per|a)?\s*month|\s*monthly)", text)
    if income_match:
        extracted["household_income_total"] = float(income_match.group(1))
    else:
        contextual_income_match = re.search(
            r"\$?\s*([0-9]{3,5})(?:[^.\n]{0,40})\b(?:income|unemployment|child support|wages|earned income|benefits)\b",
            text,
        )
        if contextual_income_match:
            extracted["household_income_total"] = float(contextual_income_match.group(1))
    if "zero earned income" in text or "0 earned income" in text:
        extracted["monthly_earned_income"] = 0.0

    if any(phrase in text for phrase in ("uninsured", "no insurance", "without insurance")):
        extracted["insurance_status"] = "uninsured"
    elif any(phrase in text for phrase in ("do not have health insurance", "do not have insurance", "kids do not have health insurance")):
        extracted["insurance_status"] = "uninsured"
    elif any(phrase in text for phrase in ("insured through", "i have insurance", "we have insurance")):
        extracted["insurance_status"] = "insured"
    elif "underinsured" in text:
        extracted["insurance_status"] = "underinsured"
    elif "plan is expensive" in text or "coverage is expensive" in text:
        extracted["insurance_status"] = "underinsured"

    if any(phrase in text for phrase in ("struggling to afford groceries", "food insecurity", "can't afford food", "cannot afford food", "struggling with food", "cutting back on food")):
        extracted["food_insecurity_signal"] = "clear"
    elif any(phrase in text for phrase in ("trouble buying groceries",)):
        extracted["food_insecurity_signal"] = "possible"
    elif any(word in text for word in ("groceries", "food pantry", "food bank", "food hardship")):
        extracted["food_insecurity_signal"] = "possible"

    if any(phrase in text for phrase in ("past-due gas bill", "behind on my gas bill", "behind on our gas bill", "behind on our heating bill", "running out of heating fuel", "shutoff", "utility burden", "overdue utility", "shutoff notice")):
        extracted["utility_burden"] = "high"
        extracted["heating_assistance_need"] = True
    elif any(word in text for word in ("gas bill", "heating bill", "utility bill", "heating cost", "cold spell", "heating fuel")):
        extracted["utility_burden"] = "medium"

    if any(phrase in text for phrase in ("lost my job", "laid off", "job loss", "hours cut", "lost work hours", "working limited part-time hours")):
        extracted["recent_job_loss"] = True
        extracted["employment_status"] = "recent_job_loss"
    elif "part-time" in text or "part time" in text:
        extracted["employment_status"] = "part_time"
    elif "full-time" in text or "full time" in text:
        extracted["employment_status"] = "full_time"

    if any(word in text for word in ("pregnant", "pregnancy")):
        extracted["pregnant_household_member"] = True
        extracted.setdefault("num_children", 0)
    if any(word in text for word in ("disabled", "disability", "elderly", "senior")):
        extracted["elderly_or_disabled_member"] = True
    if any(word in text for word in ("infant", "toddler", "under 5", "under five")):
        extracted["child_under_5"] = True

    return extracted


def _extract_county_from_text(text: str) -> str | None:
    if any(phrase in text for phrase in ("outside allegheny county", "outside allegheny", "not in allegheny county")):
        return OUT_OF_SCOPE_COUNTY_MARKER

    county_match = re.search(r"\b([a-z]+)\s+county\b", text)
    if county_match:
        return county_match.group(1).title()

    if "allegheny" in text or "pittsburgh" in text:
        return SUPPORTED_COUNTY
    if "philadelphia" in text:
        return "Philadelphia"
    return None


def _apply_intake_normalization_overrides(normalized: dict, description: str | None) -> dict:
    updated = dict(normalized)
    text = (description or "").lower()

    if updated.get("pregnant_household_member") is True and updated.get("num_children") is None:
        updated["num_children"] = 0

    if (
        updated.get("insurance_status") == "insured"
        and any(phrase in text for phrase in ("plan is expensive", "coverage is expensive", "high deductible"))
    ):
        updated["insurance_status"] = "underinsured"

    return updated


def _extract_with_llm(normalized_input: dict) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {}

    if not any(value is not None for value in normalized_input.values()):
        return {}

    client = OpenAI(api_key=api_key)
    model = os.getenv("INTAKE_LLM_MODEL", "gpt-4o-mini")
    raw_payload = json.dumps(normalized_input, ensure_ascii=False)

    schema = {
        "type": "object",
        "properties": {
            "user_description": {"type": ["string", "null"]},
            "county": {"type": ["string", "null"]},
            "zip_code": {"type": ["string", "null"]},
            "num_adults": {"type": ["integer", "null"]},
            "num_children": {"type": ["integer", "null"]},
            "child_under_5": {"type": ["boolean", "null"]},
            "pregnant_household_member": {"type": ["boolean", "null"]},
            "elderly_or_disabled_member": {"type": ["boolean", "null"]},
            "employment_status": {"type": ["string", "null"]},
            "monthly_earned_income": {"type": ["number", "null"]},
            "monthly_unearned_income": {"type": ["number", "null"]},
            "household_income_total": {"type": ["number", "null"]},
            "housing_cost": {"type": ["number", "null"]},
            "utility_burden": {"type": ["string", "null"]},
            "heating_assistance_need": {"type": ["boolean", "null"]},
            "insurance_status": {"type": ["string", "null"]},
            "recent_job_loss": {"type": ["boolean", "null"]},
            "food_insecurity_signal": {"type": ["string", "null"]},
            "language_or_stress_notes": {"type": ["string", "null"]},
        },
        "additionalProperties": False,
    }

    instructions = (
        "You extract structured benefits-intake data from a user submission. "
        "Use only facts supported by the submission. "
        "Do not guess. Leave fields null when unclear. "
        "Normalize county names, monthly income amounts, household composition, employment, hardship, and coverage details when stated. "
        "Use these enums when possible: "
        "employment_status in [full_time, part_time, unemployed, recent_job_loss, self_employed, unknown]; "
        "utility_burden in [low, medium, high]; "
        "insurance_status in [insured, uninsured, underinsured, unknown]; "
        "food_insecurity_signal in [none, possible, clear]."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": (
                        "Return a JSON object matching this schema:\n"
                        f"{json.dumps(schema, ensure_ascii=False)}\n\n"
                        "Submission:\n"
                        f"{raw_payload}"
                    ),
                },
            ],
        )
    except Exception:
        return {}

    content = response.choices[0].message.content
    if not content:
        return {}

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return {}

    allowed_keys = set(UserIntake.model_fields.keys())
    sanitized = {key: value for key, value in parsed.items() if key in allowed_keys and value is not None}
    if "county" in sanitized and isinstance(sanitized["county"], str):
        sanitized["county"] = sanitized["county"].strip()
    return sanitized


def _extract_people_count(text: str, noun: str) -> int | None:
    noun_patterns = {
        "adult": r"(?:adult|adults)",
        "child": r"(?:child|children|kid|kids)",
    }
    noun_pattern = noun_patterns.get(noun, rf"{noun}s?")

    digit_match = re.search(rf"(\d+)\s+{noun_pattern}\b", text)
    if digit_match:
        return int(digit_match.group(1))
    word_map = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
    }
    for word, value in word_map.items():
        if re.search(rf"\b{word}\s+{noun_pattern}\b", text):
            return value
    return None


def _determine_geography_status(profile: UserIntake, description: str | None) -> str:
    text = (description or "").lower()
    county = (profile.county or "").strip().lower()
    mentions_in_scope = any(token in text for token in ("allegheny", "pittsburgh"))
    mentions_other_county = any(token in text for token in ("philadelphia", "outside allegheny county"))

    if mentions_in_scope and mentions_other_county:
        return "unknown_or_ambiguous_geography"
    if not county:
        return "unknown_or_ambiguous_geography"
    if county == SUPPORTED_COUNTY.lower():
        return "in_scope_geography"
    if county == OUT_OF_SCOPE_COUNTY_MARKER.strip().lower() or county != SUPPORTED_COUNTY.lower():
        return "out_of_scope_geography"
    return "unknown_or_ambiguous_geography"


def _detect_missing_fields(profile: UserIntake, geography_status: str) -> list[str]:
    missing = []
    if geography_status == "unknown_or_ambiguous_geography":
        missing.append("county")
    if profile.num_adults is None:
        missing.append("num_adults")
    if profile.num_children is None:
        missing.append("num_children")
    if profile.household_income_total is None:
        missing.append("household_income_total")
    return _dedupe_preserve_order(missing)


def _detect_contradictions(
    profile: UserIntake,
    description: str | None,
    geography_status: str,
) -> list[str]:
    contradictions = []
    text = (description or "").lower()
    if profile.num_children == 0 and profile.child_under_5 is True:
        contradictions.append("num_children vs child_under_5")
    if profile.employment_status == "full_time" and profile.monthly_earned_income == 0:
        contradictions.append("employment_status vs monthly_earned_income")
    if (
        profile.household_income_total is not None
        and profile.monthly_earned_income is not None
        and profile.monthly_unearned_income is not None
        and abs((profile.monthly_earned_income + profile.monthly_unearned_income) - profile.household_income_total) > 1
    ):
        contradictions.append("income components vs total")
    if geography_status == "unknown_or_ambiguous_geography":
        contradictions.append("geography_conflict")
    if (
        "insured through" in text
        and any(phrase in text for phrase in ("kids do not have health insurance", "children do not have health insurance"))
    ):
        contradictions.append("insured_household_vs_uninsured_children")
    return _dedupe_preserve_order(contradictions)


def _build_validation_reasons(
    profile: UserIntake,
    missing_fields: list[str],
    contradictory_fields: list[str],
    geography_status: str,
) -> list[str]:
    reasons: list[str] = []
    if geography_status == "out_of_scope_geography":
        reasons.append("Household appears to be outside Allegheny County.")
    elif geography_status == "unknown_or_ambiguous_geography":
        reasons.append("Household county is missing or ambiguous.")
    if "household_income_total" in missing_fields:
        reasons.append("Monthly household income is needed for income-tested programs.")
    if contradictory_fields:
        reasons.append("Some household facts conflict and need clarification.")
    if not reasons and profile.household_income_total is not None:
        reasons.append("Core screening fields are complete enough to continue.")
    return reasons


def _determine_intake_status(
    missing_fields: list[str],
    contradictory_fields: list[str],
    geography_status: str,
) -> str:
    if geography_status == "out_of_scope_geography":
        return "insufficient_data"
    if contradictory_fields or missing_fields or geography_status == "unknown_or_ambiguous_geography":
        return "needs_clarification"
    return "complete"


def _build_intake_summary(
    profile: UserIntake,
    missing_fields: list[str],
    contradictory_fields: list[str],
) -> str:
    pieces = []
    if profile.user_description:
        pieces.append(f"User described the household as: {profile.user_description.strip()}")
    pieces.append(
        f"Household: {profile.num_adults if profile.num_adults is not None else '?'} adult(s), "
        f"{profile.num_children if profile.num_children is not None else '?'} child(ren) in "
        f"{profile.county or 'unknown county'}."
    )
    if profile.household_income_total is not None:
        pieces.append(f"Reported household income: ${profile.household_income_total:.0f} per month.")
    if profile.food_insecurity_signal in {"possible", "clear"}:
        pieces.append("Food hardship is present in the intake.")
    if profile.heating_assistance_need or profile.utility_burden == "high":
        pieces.append("Utility or heating strain is present in the intake.")
    if profile.insurance_status:
        pieces.append(f"Insurance status is reported as {profile.insurance_status}.")
    if _is_out_of_scope_county(profile.county):
        pieces.append("The household appears to be outside the Allegheny County scope supported by this prototype.")
    if missing_fields:
        pieces.append(f"Missing fields: {', '.join(missing_fields)}.")
    if contradictory_fields:
        pieces.append(f"Contradictions detected: {', '.join(contradictory_fields)}.")
    return " ".join(pieces)


def _build_extracted_signals(
    profile: UserIntake,
    description: str | None,
    *,
    geography_status: str,
    llm_used: bool = False,
) -> list[str]:
    signals: list[str] = []
    if description:
        signals.append("free_text_description_received")
    if llm_used:
        signals.append("llm_intake_extraction_used")
    if profile.food_insecurity_signal in {"possible", "clear"}:
        signals.append("food_need_detected")
    if profile.heating_assistance_need or profile.utility_burden in {"medium", "high"}:
        signals.append("energy_need_detected")
    if profile.insurance_status in {"uninsured", "underinsured"}:
        signals.append("coverage_need_detected")
    if profile.recent_job_loss:
        signals.append("income_disruption_detected")
    if geography_status == "out_of_scope_geography":
        signals.append("out_of_scope_geography_detected")
    elif geography_status == "unknown_or_ambiguous_geography":
        signals.append("geography_clarification_needed")
    return signals


def _build_clarification_questions(
    profile: UserIntake,
    missing_fields: list[str],
    contradictory_fields: list[str],
    normalized_input: dict,
    geography_status: str,
) -> list[str]:
    llm_questions = _generate_clarification_questions_with_llm(
        profile,
        missing_fields,
        contradictory_fields,
        normalized_input,
        geography_status,
    )
    if llm_questions:
        return llm_questions
    return _template_clarification_questions(missing_fields, contradictory_fields, geography_status)


def _template_clarification_questions(
    missing_fields: list[str],
    contradictory_fields: list[str],
    geography_status: str,
) -> list[str]:
    questions: list[str] = []

    field_questions = {
        "county": "Which county does the household live in? If you are not sure, you can say 'I don't know'.",
        "num_adults": "How many adults live in the household? If you are not sure, you can say 'I don't know' or skip it.",
        "num_children": "How many children live in the household? If none, you can say 0. If you are not sure, you can say 'I don't know'.",
        "household_income_total": "About how much total household income comes in each month before taxes? An estimate is okay. You can also say 'I don't know'.",
    }
    contradiction_questions = {
        "num_children vs child_under_5": "You indicated there may be a child under 5, but the household currently shows no children. How many children are in the household, and is any child under age 5?",
        "employment_status vs monthly_earned_income": "The intake shows full-time work but $0 earned income. Is the person currently working full time, or is the monthly earned income amount missing or incorrect?",
        "income components vs total": "The earned income, unearned income, and total income do not match. Which number should we trust, or would you like to update the monthly amounts?",
        "geography_conflict": "You mentioned more than one location. Which county does the household currently live in?",
        "insured_household_vs_uninsured_children": "You described insured adults and uninsured children. Are the children currently uninsured even if an adult has job-based coverage?",
    }

    if geography_status == "out_of_scope_geography":
        questions.append(
            "This prescreen is limited to Allegheny County. If the household is outside Allegheny County, please use local county resources or a human caseworker."
        )
        return questions

    for field in missing_fields:
        question = field_questions.get(field)
        if question and question not in questions:
            questions.append(question)

    for conflict in contradictory_fields:
        question = contradiction_questions.get(conflict)
        if question and question not in questions:
            questions.append(question)

    if not questions and (missing_fields or contradictory_fields):
        questions.append("There are still a few missing or conflicting details. You can answer in plain language, or say 'I don't know' for anything you want to skip.")

    return questions


def _generate_clarification_questions_with_llm(
    profile: UserIntake,
    missing_fields: list[str],
    contradictory_fields: list[str],
    normalized_input: dict,
    geography_status: str,
) -> list[str]:
    if (
        not missing_fields
        and not contradictory_fields
        and geography_status == "in_scope_geography"
    ):
        return []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return []

    client = OpenAI(api_key=api_key)
    model = os.getenv("INTAKE_LLM_MODEL", "gpt-4o-mini")
    prompt_payload = {
        "current_profile": profile.model_dump(),
        "missing_fields": missing_fields,
        "contradictory_fields": contradictory_fields,
        "geography_status": geography_status,
        "raw_input": normalized_input,
    }

    instructions = (
        "You are writing follow-up intake questions for a public-benefits navigator. "
        "Ask at most 3 short, friendly questions. "
        "Only ask for information that is missing or contradictory. "
        "Questions should be easy for a resident to answer in plain language. "
        "Every question should allow the user to say they do not know or prefer to skip. "
        "Return JSON with a single key named questions whose value is an array of strings."
    )

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": instructions},
                {
                    "role": "user",
                    "content": json.dumps(prompt_payload, ensure_ascii=False),
                },
            ],
        )
    except Exception:
        return []

    content = response.choices[0].message.content
    if not content:
        return []

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return []

    questions = parsed.get("questions", [])
    if not isinstance(questions, list):
        return []

    cleaned: list[str] = []
    for item in questions:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if not text:
            continue
        if text not in cleaned:
            cleaned.append(text)
    return cleaned[:3]


def _is_out_of_scope_county(county: str | None) -> bool:
    if not county:
        return False
    normalized = county.strip().lower()
    if not normalized:
        return False
    return normalized != SUPPORTED_COUNTY.lower()


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        if item not in output:
            output.append(item)
    return output
