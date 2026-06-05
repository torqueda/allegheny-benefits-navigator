from __future__ import annotations

import json
import uuid
from typing import Any

from .models import NavigatorSession


def build_reviewer_trace(session: NavigatorSession, *, case_id: str | None = None) -> dict[str, Any]:
    return {
        "trace_id": str(uuid.uuid4()),
        "case_id": case_id,
        "llm_mode": _llm_mode(session),
        "raw_input": session.raw_input,
        "intake_object": session.intake.model_dump(),
        "retrieved_chunks": _retrieved_chunks(session),
        "program_scores": _program_scores(session),
        "cross_check_result": _cross_check_result(session),
        "final_recommendations": session.explanation.recommended_programs,
        "final_decision": {
            "intake_status": session.intake.intake_status,
            "geography_status": session.intake.geography_status,
            "decision_status": session.eligibility.decision_status,
            "final_status": session.explanation.final_status,
        },
        "final_explanation": session.explanation.plain_language_explanation,
        "human_followup_or_caveats": session.explanation.visible_caveats,
    }


def render_trace_markdown(trace: dict[str, Any]) -> str:
    lines = [
        "# Reviewer Trace",
        "",
        f"- Trace ID: `{trace['trace_id']}`",
        f"- Case ID: `{trace.get('case_id') or 'n/a'}`",
        f"- LLM mode: `{trace['llm_mode']}`",
        "",
        "## Raw Input",
        "```json",
        json.dumps(trace["raw_input"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Intake Object",
        "```json",
        json.dumps(trace["intake_object"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Retrieved Chunks",
        "```json",
        json.dumps(trace["retrieved_chunks"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Program Scores",
        "```json",
        json.dumps(trace["program_scores"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Final Decision",
        "```json",
        json.dumps(trace["final_decision"], indent=2, ensure_ascii=False),
        "```",
        "",
        "## Final Explanation",
        trace["final_explanation"],
        "",
        "## Caveats",
    ]
    lines.extend([f"- {item}" for item in trace["human_followup_or_caveats"]])
    return "\n".join(lines).strip() + "\n"


def _llm_mode(session: NavigatorSession) -> str:
    statuses = {match.cross_check_status for match in session.eligibility.program_matches}
    if "live_llm_cross_check_used" in statuses or "cross_check_disagreement" in statuses:
        return "live_llm_cross_check_used"
    if "uploaded_policy_rule_only" in statuses:
        return "uploaded_policy_rule_only"
    return "offline_or_rule_only_fallback"


def _retrieved_chunks(session: NavigatorSession) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for match in session.eligibility.program_matches:
        for chunk in match.retrieved_evidence[:3]:
            key = (match.program_name, chunk.document_id)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "program_name": match.program_name,
                    "document_id": chunk.document_id,
                    "title": chunk.title,
                    "section_title": chunk.section_title,
                    "score": chunk.score,
                    "text": chunk.text,
                }
            )
    return rows


def _program_scores(session: NavigatorSession) -> list[dict[str, Any]]:
    return [
        {
            "program_name": match.program_name,
            "status": match.status,
            "decision_state": match.decision_state,
            "match_score": match.match_score,
            "priority_score": match.priority_score,
            "rule_match_score": match.rule_match_score,
            "llm_match_score": match.llm_match_score,
            "cross_check_status": match.cross_check_status,
            "cross_check_summary": match.cross_check_summary,
            "suppression_reason": match.suppression_reason,
            "priority_boost_reason": match.priority_boost_reason,
        }
        for match in session.eligibility.program_matches
    ]


def _cross_check_result(session: NavigatorSession) -> list[dict[str, Any]]:
    return [
        {
            "program_name": match.program_name,
            "cross_check_status": match.cross_check_status,
            "cross_check_summary": match.cross_check_summary,
            "llm_rule_conflict": match.llm_rule_conflict,
        }
        for match in session.eligibility.program_matches
    ]
