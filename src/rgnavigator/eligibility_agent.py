from __future__ import annotations

import json
import os
from pathlib import Path
import re

import numpy as np

from .models import EligibilityOutput, MatchReason, ProgramMatch, RetrievedChunk, UserIntake
from .policy_store import (
    build_and_save_policy_index,
    data_dir,
    embed_texts,
    load_policy_documents,
    load_policy_index,
)

QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "have",
    "i",
    "in",
    "is",
    "it",
    "last",
    "me",
    "month",
    "my",
    "no",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "they",
    "this",
    "to",
    "was",
    "we",
    "with",
}


def run_eligibility_and_prioritization(
    profile: UserIntake,
    intake_status: str,
    *,
    missing_fields: list[str] | None = None,
    contradictory_fields: list[str] | None = None,
    selected_programs: list[str] | None = None,
) -> EligibilityOutput:
    missing_fields = missing_fields or []
    contradictory_fields = contradictory_fields or []

    # Priority order is only meaningful for actionable review candidates.
    # If the intake is out of scope or contains core contradictions, return a
    # safe structured response without normal recommendations or ranking.
    if _should_suppress_recommendations(profile, intake_status, missing_fields, contradictory_fields):
        return EligibilityOutput(
            query_summary=", ".join(_intake_query_terms(profile)) or "no_retrieval_terms",
            program_matches=[],
            recommended_programs=[],
            uncertainty_flags=_safe_uncertainty_flags(profile, missing_fields, contradictory_fields),
            priority_order=[],
            decision_status="ambiguous",
        )

    all_profiles = _load_program_profiles()
    known_program_names = {p["program_name"] for p in all_profiles}
    profiles = [p for p in all_profiles if selected_programs is None or p["program_name"] in selected_programs]

    documents = load_policy_documents()
    retrieved_index_chunks, retrieved_index_embeddings = _load_or_build_index()
    program_matches: list[ProgramMatch] = []
    uncertainty_flags: list[str] = []

    for program_profile in profiles:
        program_query_terms = _program_query_terms(profile, program_profile)
        match = _evaluate_known_program(
            profile,
            program_query_terms,
            documents,
            program_profile,
            retrieved_index_chunks,
            retrieved_index_embeddings,
        )
        program_matches.append(match)
        if match.status == "possible_match":
            uncertainty_flags.append(
                f"{match.program_name}: additional evidence may change this prescreen."
            )

    uploaded_only_names = {
        document.program_name
        for document in documents
        if document.uploaded
        and document.program_name not in known_program_names
        and (selected_programs is None or document.program_name in selected_programs)
    }
    for uploaded_name in sorted(uploaded_only_names):
        uploaded_query_terms = _uploaded_program_query_terms(profile, uploaded_name)
        match = _evaluate_uploaded_program(
            profile,
            uploaded_query_terms,
            documents,
            uploaded_name,
            retrieved_index_chunks,
            retrieved_index_embeddings,
        )
        if match:
            program_matches.append(match)
            uncertainty_flags.append(
                f"{match.program_name}: this uploaded policy was matched through retrieval and may need human review."
            )

    recommended = [match for match in program_matches if match.status in {"strong_match", "possible_match"}]
    recommended = _sort_review_candidates(recommended)
    decision_status = (
        "ambiguous"
        if intake_status != "complete" or any(match.status == "possible_match" for match in recommended)
        else "ready_for_explanation"
    )

    return EligibilityOutput(
        query_summary=", ".join(_intake_query_terms(profile)) or "no_retrieval_terms",
        program_matches=_sort_review_candidates(program_matches),
        recommended_programs=[match.program_name for match in recommended],
        uncertainty_flags=uncertainty_flags,
        priority_order=[match.program_name for match in recommended],
        decision_status=decision_status,
    )


def _evaluate_known_program(
    profile: UserIntake,
    query_terms: list[str],
    documents,
    program_profile: dict,
    index_chunks,
    index_embeddings,
) -> ProgramMatch:
    document_lookup = {document.document_id: document for document in documents}
    program_name = program_profile["program_name"]

    retrieved = retrieve_relevant_chunks(
        query_terms,
        index_chunks,
        index_embeddings,
        program_name=program_name,
        top_k=6,
    )

    rule_match = _rule_based_evaluation(profile, program_profile, retrieved, document_lookup)

    if retrieved and os.getenv("OPENAI_API_KEY"):
        try:
            llm_match = _llm_grounded_evaluation(profile, program_profile, retrieved, document_lookup)
            return _cross_check(llm_match, rule_match)
        except Exception:
            pass  # fall through to rule-based result

    return rule_match


def _llm_grounded_evaluation(
    profile: UserIntake,
    program_profile: dict,
    retrieved: list[RetrievedChunk],
    document_lookup: dict,
) -> ProgramMatch:
    """Primary path: LLM reads retrieved policy chunks and decides eligibility."""
    from openai import OpenAI

    program_name = program_profile["program_name"]

    policy_context = "\n\n---\n\n".join(
        f"[{c.title}{' / ' + c.section_title if c.section_title else ''}]\n{c.text}"
        for c in retrieved
    )

    profile_dict = {k: v for k, v in profile.model_dump().items() if v is not None}
    profile_summary = json.dumps(profile_dict, indent=2)

    prompt = f"""You are an eligibility screener for Allegheny County public benefits.

TASK: Evaluate whether the household below likely qualifies for {program_name}.

POLICY SECTIONS (retrieved from the official {program_name} handbook):
{policy_context}

HOUSEHOLD PROFILE:
{profile_summary}

Rules:
- Base your assessment ONLY on the policy sections provided above.
- Do not use outside knowledge about eligibility thresholds not mentioned in the text.
- If the policy sections do not contain enough information to decide, say so explicitly.

Respond with valid JSON and nothing else:
{{
  "status": "strong_match" | "possible_match" | "no_clear_match",
  "confidence": <float 0.0-1.0>,
  "reasons": [<1-4 short reasons directly tied to policy text>],
  "conditions_met": [<specific policy conditions this household meets>],
  "conditions_unclear": [<conditions that cannot be verified from the profile>],
  "missing_info": [<information that would change this assessment>]
}}"""

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)

    status = result.get("status", "no_clear_match")
    confidence = float(result.get("confidence", 0.5))
    reasons = result.get("reasons", [])
    conditions_met = result.get("conditions_met", [])
    conditions_unclear = result.get("conditions_unclear", [])
    missing_info = result.get("missing_info", [])

    # Status is the authoritative LLM judgment; confidence fine-tunes within
    # that status band so score and status never contradict each other.
    _STATUS_BASE = {"strong_match": 7.0, "possible_match": 4.0, "no_clear_match": 1.0}
    _STATUS_RANGE = {"strong_match": 1.5, "possible_match": 1.5, "no_clear_match": 1.0}
    base = _STATUS_BASE.get(status, 1.0)
    spread = _STATUS_RANGE.get(status, 1.0)
    match_score = round(max(0.0, min(10.0, base + (confidence - 0.5) * 2 * spread)), 3)
    priority_score = round(match_score + (2.0 if status == "strong_match" else 1.0 if status == "possible_match" else 0.0), 3)

    all_reasons = (reasons + [f"Policy condition met: {c}" for c in conditions_met])[:5]
    rationale = [
        MatchReason(
            reason=r,
            score=round(match_score / max(len(all_reasons), 1), 3),
            evidence_snippet=_best_matching_chunk(r, retrieved),
        )
        for r in all_reasons
    ]

    caveats = list(program_profile["base_caveats"])
    for item in conditions_unclear[:2]:
        caveats.append(f"Unclear from profile: {item}")
    for item in missing_info[:2]:
        caveats.append(f"Missing info: {item}")

    checklist_items = _merge_checklist_items(program_profile["checklist_items"], retrieved, document_lookup)

    return ProgramMatch(
        program_name=program_name,
        status=status,
        match_score=match_score,
        priority_score=priority_score,
        rationale=rationale,
        caveats=_dedupe(caveats),
        retrieved_evidence=retrieved,
        checklist_items=checklist_items,
        uploaded_policy_backed=False,
    )


def _rule_based_evaluation(
    profile: UserIntake,
    program_profile: dict,
    retrieved: list[RetrievedChunk],
    document_lookup: dict,
) -> ProgramMatch:
    """Fallback path: hardcoded signal weights when LLM is unavailable."""
    program_name = program_profile["program_name"]
    rationale: list[MatchReason] = []

    score = 0.0
    priority_score = 0.0

    for signal in program_profile["fit_signals"]:
        if _signal_matches(profile, signal):
            score += signal["weight"]
            rationale.append(MatchReason(reason=signal["reason"], score=float(signal["weight"])))

    income_limit = _income_limit_for_profile(program_profile, profile)
    if income_limit is not None and profile.household_income_total is not None:
        if profile.household_income_total <= income_limit:
            score += 2.0
            rationale.append(MatchReason(
                reason=f"Reported income appears within the current {program_name} screening band.",
                score=2.0,
            ))
        else:
            score -= 2.0
            rationale.append(MatchReason(
                reason=f"Reported income appears above the current {program_name} screening band.",
                score=-2.0,
            ))

    retrieval_bonus = round(sum(chunk.score for chunk in retrieved[:3]), 3)
    if retrieved:
        score += retrieval_bonus
        rationale.append(MatchReason(
            reason=f"Retrieved {program_name} policy sections aligned with the household profile.",
            score=retrieval_bonus,
            evidence_snippet=_format_evidence_label(retrieved[0]),
        ))

    for signal in program_profile["priority_signals"]:
        if _signal_matches(profile, signal):
            priority_score += signal["weight"]
    priority_score += max(score, 0)

    caveats = list(program_profile["base_caveats"])
    if profile.household_income_total is None:
        caveats.append("Household income is missing, so the result remains uncertain.")
    if profile.insurance_status == "unknown" and program_name == "Medicaid/CHIP":
        caveats.append("Current coverage details are unclear, which may change the result.")
    if profile.employment_status == "full_time" and profile.monthly_earned_income == 0:
        caveats.append("Conflicting employment and earned-income details reduce confidence in this result.")

    status = _status_from_score(score, profile, program_name, retrieved)
    updated_rationale = []
    for reason in rationale[:6]:
        evidence = reason.evidence_snippet or (retrieved[0].text if retrieved else None)
        updated_rationale.append(reason.model_copy(update={"evidence_snippet": evidence}))

    checklist_items = _merge_checklist_items(program_profile["checklist_items"], retrieved, document_lookup)

    return ProgramMatch(
        program_name=program_name,
        status=status,
        match_score=round(score, 3),
        priority_score=round(priority_score, 3),
        rationale=updated_rationale,
        caveats=_dedupe(caveats),
        retrieved_evidence=retrieved,
        checklist_items=checklist_items,
        uploaded_policy_backed=False,
    )


def _evaluate_uploaded_program(
    profile: UserIntake,
    query_terms: list[str],
    documents,
    uploaded_name: str,
    index_chunks,
    index_embeddings,
) -> ProgramMatch | None:
    retrieved = retrieve_relevant_chunks(
        query_terms,
        index_chunks,
        index_embeddings,
        program_name=uploaded_name,
        top_k=4,
    )
    if not retrieved:
        return None

    score = sum(chunk.score for chunk in retrieved[:3]) + _generic_intake_need_score(profile)
    status = "possible_match" if score >= 2.5 else "no_clear_match"
    rationale = [
        MatchReason(
            reason="A newly uploaded policy retrieved relevant evidence for this household profile.",
            score=round(score, 3),
            evidence_snippet=retrieved[0].text,
        )
    ]
    checklist_items = [
        "Review the uploaded policy text for any listed documents or proofs.",
        "Confirm the program name, geography, and effective date before relying on this output.",
    ]

    return ProgramMatch(
        program_name=uploaded_name,
        status=status,
        match_score=round(score, 3),
        priority_score=round(score, 3),
        rationale=rationale,
        caveats=[
            "This recommendation is grounded in a newly uploaded policy and should be treated as preliminary.",
            "A human review may still be needed before relying on the uploaded-policy match.",
        ],
        retrieved_evidence=retrieved,
        checklist_items=checklist_items,
        uploaded_policy_backed=True,
    )


_STATUS_RANK = {"strong_match": 2, "possible_match": 1, "no_clear_match": 0}


def _cross_check(llm: ProgramMatch, rules: ProgramMatch) -> ProgramMatch:
    """Compare LLM and rule-based judgments; resolve disagreements conservatively."""
    llm_rank  = _STATUS_RANK.get(llm.status, 0)
    rule_rank = _STATUS_RANK.get(rules.status, 0)
    gap = abs(llm_rank - rule_rank)

    # Add rule-based result as an extra rationale entry so users can see both
    cross_reason = MatchReason(
        reason=(
            f"Rule-based cross-check: {rules.status} (score {rules.match_score}). "
            + ("Both methods agree." if gap == 0
               else f"LLM says {llm.status}; rules say {rules.status}.")
        ),
        score=rules.match_score,
        evidence_snippet=None,
    )
    rationale = list(llm.rationale)

    caveats = list(llm.caveats)
    if gap == 1:
        caveats.append(
            f"Mild disagreement: policy-text analysis suggests {llm.status} "
            f"while rule-based screening gives {rules.status}. "
            f"Review with a caseworker if uncertain."
        )
    elif gap == 2:
        caveats.append(
            f"Strong disagreement: policy-text analysis suggests {llm.status} "
            f"but rule-based screening gives {rules.status}. "
            f"Result downgraded to possible_match pending human review."
        )

    # gap == 0 → trust LLM score unchanged
    # gap == 1 → trust LLM but note the difference
    # gap == 2 → downgrade to possible_match and average the scores
    if gap == 2:
        final_status = "possible_match"
        final_score  = round((llm.match_score + rules.match_score) / 2, 3)
    else:
        final_status = llm.status
        final_score  = llm.match_score

    final_priority = round(
        final_score
        + (2.0 if final_status == "strong_match" else 1.0 if final_status == "possible_match" else 0.0),
        3,
    )

    return ProgramMatch(
        program_name=llm.program_name,
        status=final_status,
        match_score=final_score,
        priority_score=final_priority,
        rationale=rationale[:5] + [cross_reason],
        caveats=_dedupe(caveats),
        retrieved_evidence=llm.retrieved_evidence,
        checklist_items=llm.checklist_items,
        uploaded_policy_backed=False,
    )


def _status_from_score(score: float, profile: UserIntake, program_name: str, retrieved) -> str:
    if not retrieved and score < 4:
        return "no_clear_match"
    if profile.household_income_total is None:
        return "possible_match"
    if profile.employment_status == "full_time" and profile.monthly_earned_income == 0:
        return "possible_match"
    if program_name == "Medicaid/CHIP" and profile.insurance_status == "unknown":
        return "possible_match" if score >= 3 else "no_clear_match"
    if score >= 5:
        return "strong_match"
    if score >= 2.5:
        return "possible_match"
    return "no_clear_match"


def _signal_matches(profile: UserIntake, signal: dict) -> bool:
    value = getattr(profile, signal["field"])
    operator = signal["operator"]
    target = signal["value"]
    if value is None:
        return False
    if operator == "==":
        return value == target
    if operator == "in":
        return value in target
    if operator == ">=":
        return isinstance(value, (int, float)) and value >= target
    return False


def _income_limit_for_profile(program_profile: dict, profile: UserIntake) -> float | None:
    household_size = (profile.num_adults or 0) + (profile.num_children or 0)
    if program_profile["program_name"] == "Medicaid/CHIP" and profile.pregnant_household_member:
        household_size += 1
    if household_size <= 0:
        return None
    key = str(min(household_size, 6))
    limit = program_profile.get("income_limits_by_household_size", {}).get(key)
    return float(limit) if limit is not None else None


def _generic_intake_need_score(profile: UserIntake) -> float:
    score = 0.0
    if profile.food_insecurity_signal in {"possible", "clear"}:
        score += 1.0
    if profile.heating_assistance_need:
        score += 1.0
    if profile.insurance_status in {"uninsured", "underinsured"}:
        score += 1.0
    return score


def _dedupe(items: list[str]) -> list[str]:
    output = []
    for item in items:
        if item not in output:
            output.append(item)
    return output


def _sort_review_candidates(matches: list[ProgramMatch]) -> list[ProgramMatch]:
    # Review ordering is driven primarily by match likelihood and secondarily by
    # program-specific hardship or urgency signals already reflected in
    # priority_score. It is not a legal determination or benefit-value ranking.
    return sorted(matches, key=lambda item: (item.priority_score, item.match_score), reverse=True)


def _should_suppress_recommendations(
    profile: UserIntake,
    intake_status: str,
    missing_fields: list[str],
    contradictory_fields: list[str],
) -> bool:
    return (
        _is_out_of_scope(profile)
        or bool(contradictory_fields)
        or intake_status == "insufficient_data"
        or bool(missing_fields)
    )


def _is_out_of_scope(profile: UserIntake) -> bool:
    county = (profile.county or "").strip().lower()
    return bool(county) and county != "allegheny"


def _safe_uncertainty_flags(
    profile: UserIntake,
    missing_fields: list[str],
    contradictory_fields: list[str],
) -> list[str]:
    flags: list[str] = []
    if _is_out_of_scope(profile):
        flags.append(
            "This prototype currently supports Allegheny County households only."
        )
    if contradictory_fields:
        flags.append(
            "Core intake details conflict, so recommendations are withheld until the contradiction is resolved."
        )
    if missing_fields:
        flags.append(
            f"Key intake details are still missing: {', '.join(missing_fields)}."
        )
    return flags


def _merge_checklist_items(base_items: list[str], retrieved, document_lookup: dict) -> list[str]:
    combined = list(base_items)
    for chunk in retrieved[:2]:
        document = document_lookup.get(chunk.document_id)
        if not document:
            continue
        combined.extend(_extract_checklist_hints(document.content))
    return _dedupe(combined)[:6]


def _format_evidence_label(chunk) -> str:
    if chunk.section_title and chunk.section_title != chunk.title:
        return f"{chunk.title} / {chunk.section_title}: {chunk.text}"
    return chunk.text


def _load_program_profiles() -> list[dict]:
    path = data_dir() / "program_profiles.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["programs"]


def _intake_query_terms(profile: UserIntake) -> list[str]:
    tokens: list[str] = []
    if profile.user_description:
        tokens.extend(_tokenize(profile.user_description))
    if profile.food_insecurity_signal in {"possible", "clear"}:
        tokens.extend(["food", "groceries", "nutrition"])
    if profile.heating_assistance_need:
        tokens.extend(["heating", "utility", "energy"])
    if profile.utility_burden == "high":
        tokens.extend(["utility", "shutoff", "bill"])
    if profile.insurance_status in {"uninsured", "underinsured", "unknown"}:
        tokens.extend(["coverage"])
    if profile.pregnant_household_member:
        tokens.extend(["pregnancy", "pregnant"])
    if (profile.num_children or 0) > 0:
        tokens.extend(["children", "family"])
    if profile.recent_job_loss:
        tokens.extend(["job_loss", "income", "hardship"])
    if profile.language_or_stress_notes:
        tokens.extend(_tokenize(profile.language_or_stress_notes))
    if profile.household_income_total is not None:
        tokens.extend(["income", "household", "low_income"])
    if profile.household_income_total is not None and profile.household_income_total <= 2500:
        tokens.extend(["low income", "reduced income"])
    return _dedupe(tokens)


def _program_query_terms(profile: UserIntake, program_profile: dict) -> list[str]:
    tokens = _intake_query_terms(profile)
    tokens.extend(program_profile.get("retriever_terms", []))
    tokens.extend(_program_specific_intake_terms(profile, program_profile["program_name"]))
    return _dedupe(tokens)


def _uploaded_program_query_terms(profile: UserIntake, uploaded_name: str) -> list[str]:
    tokens = _intake_query_terms(profile)
    tokens.append(uploaded_name.lower())
    return _dedupe(tokens)


def _program_specific_intake_terms(profile: UserIntake, program_name: str) -> list[str]:
    tokens: list[str] = []

    if program_name == "SNAP":
        if profile.food_insecurity_signal in {"possible", "clear"}:
            tokens.extend(["meals", "groceries", "food", "food assistance", "nutrition support"])
        if profile.recent_job_loss:
            tokens.extend(["job loss", "reduced income", "lost wages"])
        if (profile.num_children or 0) > 0:
            tokens.extend(["children", "household", "family size"])
        if profile.household_income_total is not None and profile.household_income_total <= 2500:
            tokens.extend(["low income eligibility", "monthly income"])

    elif program_name == "Medicaid/CHIP":
        if profile.insurance_status in {"uninsured", "underinsured", "unknown"}:
            tokens.extend(["health insurance", "insurance", "medicaid", "coverage", "medical", "uninsured"])
        if profile.pregnant_household_member:
            tokens.extend(["pregnancy", "pregnant"])
        if (profile.num_children or 0) > 0:
            tokens.extend(["child", "children", "chip", "kids coverage"])
        if profile.household_income_total is not None:
            tokens.extend(["income limit", "household size"])

    elif program_name == "LIHEAP":
        if profile.heating_assistance_need:
            tokens.extend(["heating bill", "shutoff", "energy assistance", "crisis benefit"])
        if profile.utility_burden in {"medium", "high"}:
            tokens.extend(["utility bill", "gas bill", "energy", "past due utility"])
        if profile.recent_job_loss:
            tokens.extend(["reduced income", "hardship"])
        if profile.household_income_total is not None and profile.household_income_total <= 2500:
            tokens.extend(["income eligibility", "household income"])

    return tokens


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9/+-]+", text.lower())
    return [token for token in tokens if token not in QUERY_STOPWORDS and len(token) > 1]


def _load_or_build_index():
    try:
        chunks, embeddings, _manifest = load_policy_index()
    except FileNotFoundError:
        build_and_save_policy_index()
        chunks, embeddings, _manifest = load_policy_index()
    return chunks, embeddings


def retrieve_relevant_chunks(
    query_terms: list[str],
    index_chunks,
    index_embeddings,
    *,
    program_name: str | None = None,
    top_k: int = 3,
):
    query_text = " ".join(_dedupe(query_terms)).strip()
    if not query_text:
        return []

    candidate_pairs = []
    use_embedding_search = index_embeddings.size > 0
    query_embedding = None

    if use_embedding_search:
        try:
            query_embedding = embed_texts([query_text])[0]
            if index_embeddings.ndim != 2 or index_embeddings.shape[1] != len(query_embedding):
                use_embedding_search = False
        except Exception:
            use_embedding_search = False

    query_token_set = set(_tokenize(query_text))
    for idx, chunk in enumerate(index_chunks):
        if program_name and chunk.program_name != program_name:
            continue

        if use_embedding_search and query_embedding is not None:
            score = float(np.dot(index_embeddings[idx], query_embedding))
        else:
            score = _lexical_retrieval_score(query_token_set, chunk.text)

        if score <= 0:
            continue
        candidate_pairs.append((score, chunk))

    candidate_pairs.sort(key=lambda item: item[0], reverse=True)
    return [
        RetrievedChunk(
            document_id=chunk.document_id,
            program_name=chunk.program_name,
            title=chunk.title,
            section_title=chunk.section_title,
            source_url=chunk.source_url,
            text=chunk.text,
            score=round(score, 3),
        )
        for score, chunk in candidate_pairs[:top_k]
    ]


def _extract_checklist_hints(text: str) -> list[str]:
    hints = []
    for line in text.splitlines():
        line = line.lstrip("- ").strip()
        normalized = line.lower()
        if any(keyword in normalized for keyword in ("proof", "document", "application", "submit", "bring")):
            hints.append(line)
    return _dedupe(hints)[:6]


def _best_matching_chunk(reason: str, retrieved: list) -> str | None:
    if not retrieved:
        return None
    reason_tokens = set(_tokenize(reason))
    best_chunk = max(retrieved, key=lambda c: len(reason_tokens & set(_tokenize(c.text))))
    return best_chunk.text if reason_tokens & set(_tokenize(best_chunk.text)) else None


def _lexical_retrieval_score(query_tokens: set[str], chunk_text: str) -> float:
    if not query_tokens:
        return 0.0

    chunk_tokens = _tokenize(chunk_text)
    if not chunk_tokens:
        return 0.0

    overlap = sum(1 for token in chunk_tokens if token in query_tokens)
    unique_overlap = len(query_tokens.intersection(chunk_tokens))
    if unique_overlap == 0:
        return 0.0

    density = overlap / max(len(chunk_tokens), 1)
    return round(unique_overlap + density, 6)
