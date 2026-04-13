from __future__ import annotations

import csv
import json
from pathlib import Path

from src.loaders.csv_loader import load_expected_results, load_test_cases
from src.pipeline import run_case, summarize_case


PROGRAMS = ["SNAP", "Medicaid/CHIP", "LIHEAP", "WIC", "Local Referral"]


def _match_programs(actual: dict[str, str], expected: dict[str, object]) -> tuple[bool, list[str]]:
    mismatches: list[str] = []
    for program in PROGRAMS:
        expected_value = expected.get(program)
        if expected_value is None:
            continue
        if actual.get(program) != expected_value:
            mismatches.append(f"{program}: expected {expected_value}, got {actual.get(program)}")
    return not mismatches, mismatches


def _match_priority(actual_order: list[str], expected_order: list[str]) -> tuple[bool, str]:
    if not expected_order:
        return True, ""
    if actual_order[: len(expected_order)] == expected_order:
        return True, ""
    return False, f"priority mismatch: expected {expected_order}, got {actual_order}"


def _match_uncertainty(actual_flags: list[str], expected_flag: bool | None) -> tuple[bool, str]:
    if expected_flag is None:
        return True, ""
    actual_flag = bool(actual_flags)
    if actual_flag == expected_flag:
        return True, ""
    return False, f"uncertainty mismatch: expected {expected_flag}, got {actual_flag}"


def run_evaluation(
    test_cases_path: str | Path = "data/test_cases.csv",
    expected_path: str | Path = "data/expected_results.csv",
    output_csv_path: str | Path = "data/evaluation_results.csv",
    traces_dir: str | Path = "outputs/traces",
) -> list[dict[str, str]]:
    cases = load_test_cases(test_cases_path)
    expected_by_case = load_expected_results(expected_path)
    traces_path = Path(traces_dir)
    traces_path.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, str]] = []
    for case in cases:
        state = run_case(case)
        actual_statuses, eligibility, checklist = summarize_case(state)
        expected = expected_by_case[str(case["case_id"])]

        program_match, program_mismatches = _match_programs(actual_statuses, expected)
        priority_match, priority_note = _match_priority(
            eligibility.priority_order, expected["expected_priority_order"]
        )
        uncertainty_match, uncertainty_note = _match_uncertainty(
            eligibility.uncertainty_flags, expected["expected_uncertainty_flag"]
        )

        notes = [item for item in program_mismatches + [priority_note, uncertainty_note] if item]
        outcome = "pass" if program_match and priority_match and uncertainty_match else "partial"

        trace_file = traces_path / f"{case['case_id']}.json"
        trace_file.write_text(state.model_dump_json(indent=2), encoding="utf-8")

        results.append(
            {
                "case_id": str(case["case_id"]),
                "case_type": str(case["case_type"]),
                "input_or_scenario": str(case["scenario_summary"]),
                "expected_behavior": str(expected["why_this_is_expected"]),
                "actual_behavior": checklist.user_explanation,
                "outcome": outcome,
                "evidence_or_citation": str(trace_file),
                "notes": " | ".join(notes) if notes else "Matched expected prototype behavior.",
            }
        )

    _write_results(output_csv_path, results)
    return results


def _write_results(path: str | Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "case_id",
        "case_type",
        "input_or_scenario",
        "expected_behavior",
        "actual_behavior",
        "outcome",
        "evidence_or_citation",
        "notes",
    ]
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    rows = run_evaluation()
    print(json.dumps(rows, indent=2))
