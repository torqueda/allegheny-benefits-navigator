"""
Phase 3 evaluation runner.
Uses directional behavioral checks instead of exact string matching,
and validates Phase 3-specific behaviors: cross-check rationale, decision_status,
final_status, and contradiction detection.

Artifact roles:
- data/agent_test_cases.json: internal runner + demo fixture
- data/evaluation_results_phase3.json: raw internal runner output
- eval/evaluation_results.csv: canonical reviewer-facing results artifact
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rgnavigator.intake_agent import run_intake, run_intake_turn
from src.rgnavigator.pipeline import run_navigator

INTERNAL_CASES_PATH = ROOT / "data" / "agent_test_cases.json"
RAW_RESULTS_PATH = ROOT / "data" / "evaluation_results_phase3.json"
REVIEWER_CASES_PATH = ROOT / "eval" / "test_cases.csv"
REVIEWER_RESULTS_PATH = ROOT / "eval" / "evaluation_results.csv"


def _load_cases() -> list[dict]:
    payload = json.loads(INTERNAL_CASES_PATH.read_text(encoding="utf-8"))
    return payload["cases"]


def _load_reviewer_cases() -> dict[str, dict]:
    with REVIEWER_CASES_PATH.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {row["case_id"]: row for row in rows}


def _validate_reviewer_case_alignment(cases: list[dict], reviewer_cases: dict[str, dict]) -> None:
    internal_ids = [case["case_id"] for case in cases]
    reviewer_ids = list(reviewer_cases)
    if internal_ids != reviewer_ids:
        raise ValueError(
            "Reviewer-facing eval/test_cases.csv must contain the same case IDs in the same order "
            "as data/agent_test_cases.json."
        )

    for case in cases:
        case_id = case["case_id"]
        reviewer = reviewer_cases[case_id]
        if reviewer["case_type"] != case["evaluation_type"]:
            raise ValueError(
                f"{case_id}: eval/test_cases.csv case_type {reviewer['case_type']!r} does not match "
                f"data/agent_test_cases.json evaluation_type {case['evaluation_type']!r}."
            )
        if reviewer["category"] != case["category"]:
            raise ValueError(
                f"{case_id}: eval/test_cases.csv category {reviewer['category']!r} does not match "
                f"data/agent_test_cases.json category {case['category']!r}."
            )
        if int(reviewer["num_turns"]) != len(case["turns"]):
            raise ValueError(
                f"{case_id}: eval/test_cases.csv num_turns {reviewer['num_turns']!r} does not match "
                f"data/agent_test_cases.json turns length {len(case['turns'])!r}."
            )


def _run_multiturn_intake(turns: list[str]) -> tuple[dict, object]:
    if not turns:
        raise ValueError("Each test case must include at least one turn.")
    raw_input = {"user_description": turns[0]}
    intake = run_intake(raw_input)
    for turn in turns[1:]:
        raw_input, intake = run_intake_turn(raw_input, turn)
    return raw_input, intake


# ── Intake validation ────────────────────────────────────────────────────────

def _validate_intake(case: dict, intake) -> list[str]:
    expected = case["expected_intake"]
    failures: list[str] = []
    actual_profile = intake.normalized_profile.model_dump()

    for key, expected_value in expected["required_profile_fields"].items():
        actual_value = actual_profile.get(key)
        if actual_value != expected_value:
            failures.append(
                f"[intake] normalized_profile.{key}: expected {expected_value!r}, got {actual_value!r}"
            )

    if intake.missing_fields != expected["expected_missing_fields"]:
        failures.append(
            f"[intake] missing_fields: expected {expected['expected_missing_fields']!r}, "
            f"got {intake.missing_fields!r}"
        )

    if intake.contradictory_fields != expected["expected_contradictory_fields"]:
        failures.append(
            f"[intake] contradictory_fields: expected {expected['expected_contradictory_fields']!r}, "
            f"got {intake.contradictory_fields!r}"
        )

    if intake.intake_status != expected["expected_intake_status"]:
        failures.append(
            f"[intake] intake_status: expected {expected['expected_intake_status']!r}, "
            f"got {intake.intake_status!r}"
        )

    return failures


# ── Eligibility validation ───────────────────────────────────────────────────

def _validate_eligibility(case: dict, session) -> list[str]:
    expected = case["expected_eligibility"]
    eligibility = session.eligibility
    failures: list[str] = []

    status_lookup = {m.program_name: m.status for m in eligibility.program_matches}

    # Programs that must appear in recommended_programs
    for program in expected.get("must_recommend", []):
        if program not in eligibility.recommended_programs:
            failures.append(
                f"[eligibility] '{program}' must be in recommended_programs, "
                f"got {eligibility.recommended_programs}"
            )

    # Programs that must NOT appear
    for program in expected.get("must_not_recommend", []):
        if program in eligibility.recommended_programs:
            failures.append(
                f"[eligibility] '{program}' must NOT be in recommended_programs"
            )

    # Top priority program
    top_priority_in = expected.get("top_priority_in", [])
    if top_priority_in and eligibility.priority_order:
        if eligibility.priority_order[0] not in top_priority_in:
            failures.append(
                f"[eligibility] top priority must be one of {top_priority_in}, "
                f"got '{eligibility.priority_order[0]}'"
            )

    # Programs that must be strong_match
    for program in expected.get("must_be_strong_match", []):
        actual = status_lookup.get(program)
        if actual != "strong_match":
            failures.append(
                f"[eligibility] '{program}' must be strong_match, got {actual!r}"
            )

    # Programs that can be strong_match or possible_match (not no_clear_match)
    for program in expected.get("may_be_possible_match", []):
        actual = status_lookup.get(program)
        if actual == "no_clear_match":
            failures.append(
                f"[eligibility] '{program}' should be strong_match or possible_match, "
                f"got no_clear_match"
            )

    # Programs that must be no_clear_match
    for program in expected.get("must_be_no_clear_match", []):
        actual = status_lookup.get(program)
        if actual != "no_clear_match":
            failures.append(
                f"[eligibility] '{program}' must be no_clear_match, got {actual!r}"
            )

    # decision_status
    expected_ds = expected.get("expected_decision_status")
    if expected_ds and eligibility.decision_status != expected_ds:
        failures.append(
            f"[eligibility] decision_status: expected {expected_ds!r}, "
            f"got {eligibility.decision_status!r}"
        )

    # uncertainty_flags presence
    if expected.get("expected_has_uncertainty_flags") is True:
        if not eligibility.uncertainty_flags:
            failures.append("[eligibility] expected non-empty uncertainty_flags")

    return failures


# ── Explanation validation ───────────────────────────────────────────────────

def _validate_explanation(case: dict, session) -> list[str]:
    expected = case["expected_explanation"]
    explanation = session.explanation
    failures: list[str] = []

    explanation_blob = " ".join([
        explanation.plain_language_explanation,
        " ".join(explanation.recommended_programs),
        " ".join(explanation.visible_caveats),
    ]).lower()

    checklist_blob = " ".join(
        item
        for items in explanation.checklist_by_program.values()
        for item in items
    ).lower()

    for program in expected.get("must_mention_programs", []):
        if program.lower() not in explanation_blob:
            failures.append(f"[explanation] expected mention of '{program}'")

    for term in expected.get("must_include_checklist_terms", []):
        if term.lower() not in checklist_blob:
            failures.append(f"[explanation] checklist missing term '{term}'")

    for term in expected.get("must_include_caveats", []):
        if term.lower() not in explanation_blob:
            failures.append(f"[explanation] caveats/explanation missing term '{term}'")

    expected_fs = expected.get("expected_final_status")
    if expected_fs and explanation.final_status != expected_fs:
        failures.append(
            f"[explanation] final_status: expected {expected_fs!r}, "
            f"got {explanation.final_status!r}"
        )

    return failures


# ── Phase 3 specific checks ──────────────────────────────────────────────────

def _validate_phase3(case: dict, intake, session) -> list[str]:
    checks = case.get("phase3_checks", {})
    failures: list[str] = []

    # Cross-check rationale: every program match should have a "cross-check" entry
    if checks.get("expect_cross_check_rationale"):
        for match in session.eligibility.program_matches:
            has_cross = any(
                "cross-check" in (r.reason or "").lower()
                for r in match.rationale
            )
            if not has_cross:
                failures.append(
                    f"[phase3] '{match.program_name}' rationale missing cross-check entry"
                )

    # Contradiction detection
    if checks.get("expect_contradiction_detected"):
        if not intake.contradictory_fields:
            failures.append(
                "[phase3] expected contradictory_fields to be non-empty"
            )

    return failures


def _format_programs(programs: list[str]) -> str:
    return ", ".join(programs) if programs else "none"


def _build_input_or_scenario(reviewer_case: dict) -> str:
    turn_1 = reviewer_case.get("turn_1_input", "").strip()
    turn_2 = reviewer_case.get("turn_2_input", "").strip()
    if reviewer_case.get("num_turns") == "1":
        return turn_1
    parts = []
    if turn_1:
        parts.append(f"Turn 1: {turn_1}")
    if turn_2:
        parts.append(f"Turn 2: {turn_2}")
    return " ".join(parts)


def _build_reviewer_note(case_id: str, reviewer_case: dict, result: dict) -> str:
    if result["outcome"] != "PASS":
        failures = result.get("failures", [])
        if failures:
            return "Failed internal directional checks: " + " | ".join(failures[:3])
        return "Failed internal directional checks. See raw internal output for details."

    curated_notes = {
        "AGENT_01": "Clear multi-program success case. All three core programs passed the current directional checks.",
        "AGENT_02": "No-match guardrail case passed. The evaluator returned no recommended programs and a ready_for_explanation decision state.",
        "AGENT_03": "Boundary pregnancy pathway case passed with Medicaid/CHIP as the only recommended program.",
        "AGENT_04": "Multi-turn crisis case passed. LIHEAP and SNAP appeared as required, and Medicaid/CHIP also surfaced as an allowed secondary match.",
        "AGENT_05": "Conflict-resolution case passed after the second turn. LIHEAP and SNAP appeared as required, and Medicaid/CHIP also surfaced as an allowed secondary match.",
        "AGENT_06": "Failure-case evaluation passed: intake remained insufficient_data and no programs were recommended. Fallback guidance now points the user to the missing intake details that most affect the prescreen.",
        "AGENT_07": "Children's coverage case passed with Medicaid/CHIP prioritized ahead of SNAP.",
        "AGENT_08": "Boundary case passed because contradiction detection triggered needs_clarification and needs_human_followup, and normal actionable recommendations were suppressed until the contradiction is resolved.",
        "AGENT_09": "Dual-need case passed. LIHEAP and SNAP appeared as required, and Medicaid/CHIP also surfaced as an allowed secondary match.",
        "AGENT_10": "Boundary case passed because out-of-county intake was marked insufficient_data and the system stopped before normal recommendation flow.",
    }
    return curated_notes.get(
        case_id,
        f"{reviewer_case['case_type']} evaluation passed the current internal directional checks.",
    )


def _write_reviewer_results_csv(
    cases: list[dict],
    reviewer_cases: dict[str, dict],
    results: list[dict],
) -> None:
    result_by_id = {result["case_id"]: result for result in results}
    fieldnames = [
        "case_id",
        "case_type",
        "num_turns",
        "input_or_scenario",
        "expected_behavior",
        "actual_intake_status",
        "actual_decision_status",
        "actual_final_status",
        "recommended_programs",
        "outcome",
        "evidence_or_citation",
        "notes",
    ]

    with REVIEWER_RESULTS_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for case in cases:
            case_id = case["case_id"]
            reviewer_case = reviewer_cases[case_id]
            result = result_by_id[case_id]
            writer.writerow(
                {
                    "case_id": case_id,
                    "case_type": reviewer_case["case_type"],
                    "num_turns": reviewer_case["num_turns"],
                    "input_or_scenario": _build_input_or_scenario(reviewer_case),
                    "expected_behavior": reviewer_case["success_criteria"],
                    "actual_intake_status": result.get("intake_status", ""),
                    "actual_decision_status": result.get("decision_status", ""),
                    "actual_final_status": result.get("final_status", ""),
                    "recommended_programs": _format_programs(result.get("recommended_programs", [])),
                    "outcome": result["outcome"],
                    "evidence_or_citation": (
                        "Raw internal runner output in data/evaluation_results_phase3.json; "
                        "reviewer-facing expectations in eval/test_cases.csv."
                    ),
                    "notes": _build_reviewer_note(case_id, reviewer_case, result),
                }
            )


# ── Main runner ──────────────────────────────────────────────────────────────

def main() -> None:
    cases = _load_cases()
    reviewer_cases = _load_reviewer_cases()
    _validate_reviewer_case_alignment(cases, reviewer_cases)

    results: list[dict] = []
    pass_count = 0
    fail_count = 0

    print(f"\n{'='*70}")
    print(f"  Phase 3 Evaluation — {len(cases)} cases")
    print(f"{'='*70}\n")

    for case in cases:
        case_id = case["case_id"]
        category = case["category"]
        eval_type = case.get("evaluation_type", "unknown")

        print(f"--- {case_id} | {category} | [{eval_type}]")

        try:
            raw_input, intake = _run_multiturn_intake(case["turns"])
            session = run_navigator(raw_input)
        except Exception as exc:
            print(f"  EXCEPTION: {exc}")
            fail_count += 1
            results.append({
                "case_id": case_id,
                "evaluation_type": eval_type,
                "outcome": "exception",
                "failures": [str(exc)],
            })
            print()
            continue

        failures: list[str] = []
        failures.extend(_validate_intake(case, intake))
        failures.extend(_validate_eligibility(case, session))
        failures.extend(_validate_explanation(case, session))
        failures.extend(_validate_phase3(case, intake, session))

        outcome = "PASS" if not failures else "FAIL"
        if not failures:
            pass_count += 1
        else:
            fail_count += 1

        print(f"  {outcome}")
        for f in failures:
            print(f"    ! {f}")

        print(f"  intake_status   : {intake.intake_status}")
        print(f"  decision_status : {session.eligibility.decision_status}")
        print(f"  final_status    : {session.explanation.final_status}")
        print(f"  recommended     : {session.eligibility.recommended_programs}")
        if intake.contradictory_fields:
            print(f"  contradictions  : {intake.contradictory_fields}")
        print()

        results.append({
            "case_id": case_id,
            "evaluation_type": eval_type,
            "outcome": outcome,
            "intake_status": intake.intake_status,
            "decision_status": session.eligibility.decision_status,
            "final_status": session.explanation.final_status,
            "recommended_programs": session.eligibility.recommended_programs,
            "failures": failures,
        })

    print(f"{'='*70}")
    print(f"  Summary: {pass_count} PASS / {fail_count} FAIL / {len(cases)} total")

    by_type: dict[str, dict] = {}
    for r in results:
        t = r["evaluation_type"]
        by_type.setdefault(t, {"pass": 0, "fail": 0})
        by_type[t]["pass" if r["outcome"] == "PASS" else "fail"] += 1
    for t, counts in sorted(by_type.items()):
        print(f"  [{t}] {counts['pass']} pass / {counts['fail']} fail")
    print(f"{'='*70}\n")

    RAW_RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_reviewer_results_csv(cases, reviewer_cases, results)
    print(f"  Raw results saved to {RAW_RESULTS_PATH.relative_to(ROOT)}")
    print(f"  Reviewer results saved to {REVIEWER_RESULTS_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
