"""
Phase 3 evaluation runner.
Uses directional behavioral checks instead of exact string matching,
and validates Phase 3-specific behaviors: cross-check rationale, decision_status,
final_status, and contradiction detection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rgnavigator.intake_agent import run_intake, run_intake_turn
from src.rgnavigator.pipeline import run_navigator


def _load_cases() -> list[dict]:
    path = ROOT / "data" / "agent_test_cases.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["cases"]


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


# ── Main runner ──────────────────────────────────────────────────────────────

def main() -> None:
    cases = _load_cases()

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

    # Write results to eval output file
    out_path = ROOT / "data" / "evaluation_results_phase3.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Results saved to {out_path.name}")


if __name__ == "__main__":
    main()
