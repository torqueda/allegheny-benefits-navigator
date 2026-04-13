from __future__ import annotations

import argparse
import csv
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

from src.loaders import ExpectedResultRow, TestCaseRow, load_expected_results, load_test_cases
from src.models.common import ProgramStatus
from src.models.session import SessionState
from src.pipeline import run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEST_CASES_PATH = REPO_ROOT / "data" / "test_cases.csv"
DEFAULT_EXPECTED_RESULTS_PATH = REPO_ROOT / "data" / "expected_results.csv"
DEFAULT_EVALUATION_RESULTS_PATH = REPO_ROOT / "data" / "evaluation_results.csv"
DEFAULT_FAILURE_LOG_PATH = REPO_ROOT / "failure_log.md"

SUPPORTED_PROGRAMS = ("SNAP", "Medicaid/CHIP", "LIHEAP")
FIXTURE_ONLY_FIELDS = frozenset(
    {"case_id", "case_type", "scenario_summary", "missing_fields", "contradictory_fields"}
)
EXPECTED_STATUS_FIELDS = {
    "SNAP": "expected_snap",
    "Medicaid/CHIP": "expected_medicaid_chip",
    "LIHEAP": "expected_liheap",
}
EXCEPTION_CATEGORIES = {"pipeline_exception", "serialization_failure"}

# Priority order uses ` > ` to preserve ranking; recommended programs use comma separation
# because the fixture field is an unordered program list rather than a strict ranking signal.
EVALUATION_RESULT_COLUMNS = [
    "case_id",
    "case_type",
    "scenario_summary",
    "intake_status",
    "decision_status",
    "final_status",
    "snap_actual",
    "medicaid_chip_actual",
    "liheap_actual",
    "uncertainty_flag_actual",
    "priority_order_actual",
    "recommended_programs_actual",
    "snap_expected",
    "medicaid_chip_expected",
    "liheap_expected",
    "uncertainty_flag_expected",
    "priority_order_expected",
    "recommended_programs_expected",
    "snap_match",
    "medicaid_chip_match",
    "liheap_match",
    "uncertainty_match",
    "priority_match",
    "recommended_programs_match",
    "overall_match",
    "notes",
]

PipelineRunner = Callable[..., SessionState]


@dataclass(frozen=True)
class FailureDetail:
    category: str
    expected: str = ""
    actual: str = ""
    note: str = ""
    stack_trace: str | None = None


@dataclass(frozen=True)
class CaseFailure:
    case_id: str
    scenario_summary: str
    failures: tuple[FailureDetail, ...]


@dataclass(frozen=True)
class EvaluationSummary:
    processed_count: int
    full_match_count: int
    mismatch_count: int
    exception_count: int
    output_csv_path: Path
    failure_log_path: Path


def _case_to_raw_form_input(case: TestCaseRow) -> dict[str, Any]:
    return case.model_dump(exclude=FIXTURE_ONLY_FIELDS)


def _program_statuses(session: SessionState) -> dict[str, ProgramStatus]:
    return {
        assessment.program_name: assessment.status
        for assessment in session.eligibility_prioritization.program_assessments
    }


def _filter_supported(values: Sequence[str] | None) -> list[str]:
    if values is None:
        return []
    return [value for value in values if value in SUPPORTED_PROGRAMS]


def _format_bool(value: bool | None) -> str:
    if value is None:
        return ""
    return "true" if value else "false"


def _format_priority_order(values: Sequence[str] | None) -> str:
    if not values:
        return ""
    return " > ".join(values)


def _format_program_list(values: Sequence[str] | None) -> str:
    if not values:
        return ""
    return ", ".join(values)


def _format_status(value: ProgramStatus | None) -> str:
    return value.value if value is not None else ""


def _supported_expected_priority(expected: ExpectedResultRow | None) -> list[str] | None:
    if expected is None:
        return None
    filtered = _filter_supported(expected.expected_priority_order)
    return filtered or None


def _supported_expected_programs(expected: ExpectedResultRow | None) -> list[str] | None:
    if expected is None or expected.expected_checklist_programs is None:
        return None
    filtered = _filter_supported(expected.expected_checklist_programs)
    return filtered or None


def _write_results_csv(path: Path, rows: Sequence[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=EVALUATION_RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _write_failure_log(
    path: Path,
    failures: Sequence[CaseFailure],
    summary: EvaluationSummary,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Evaluation Failures",
        "",
        f"Processed cases: {summary.processed_count}",
        f"Full matches: {summary.full_match_count}",
        f"Mismatches: {summary.mismatch_count}",
        f"Exceptions: {summary.exception_count}",
        "",
    ]

    if not failures:
        lines.append("No failures recorded.")
        lines.append("")
    else:
        for case_failure in failures:
            lines.append(f"## {case_failure.case_id}")
            if case_failure.scenario_summary:
                lines.append(f"Scenario: {case_failure.scenario_summary}")
            lines.append("")
            for detail in case_failure.failures:
                lines.append(f"- Failure category: {detail.category}")
                if detail.expected:
                    lines.append(f"- Expected: {detail.expected}")
                if detail.actual:
                    lines.append(f"- Actual: {detail.actual}")
                if detail.note:
                    lines.append(f"- Diagnostic note: {detail.note}")
                if detail.stack_trace:
                    lines.append("- Stack trace:")
                    lines.append("```text")
                    lines.append(detail.stack_trace.rstrip())
                    lines.append("```")
                lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def run_evaluation(
    test_cases_path: str | Path = DEFAULT_TEST_CASES_PATH,
    expected_results_path: str | Path = DEFAULT_EXPECTED_RESULTS_PATH,
    output_csv_path: str | Path = DEFAULT_EVALUATION_RESULTS_PATH,
    failure_log_path: str | Path = DEFAULT_FAILURE_LOG_PATH,
    ambiguity_mode: bool = True,
    pipeline_runner: PipelineRunner = run_pipeline,
) -> EvaluationSummary:
    test_cases = sorted(load_test_cases(test_cases_path), key=lambda row: row.case_id)
    expected_by_case = {
        row.case_id: row
        for row in sorted(load_expected_results(expected_results_path), key=lambda row: row.case_id)
    }

    rows: list[dict[str, str]] = []
    case_failures: list[CaseFailure] = []
    mismatch_count = 0
    exception_count = 0

    for case in test_cases:
        expected = expected_by_case.get(case.case_id)
        failure_details: list[FailureDetail] = []

        if expected is None:
            failure_details.append(
                FailureDetail(
                    category="missing_expected_row",
                    note="No expected-results row was found for this case.",
                )
            )

        session: SessionState | None = None
        try:
            session = pipeline_runner(
                case_id=case.case_id,
                raw_form_input=_case_to_raw_form_input(case),
                ambiguity_mode=ambiguity_mode,
            )
        except Exception as exc:
            failure_details.append(
                FailureDetail(
                    category="pipeline_exception",
                    actual=f"{type(exc).__name__}: {exc}",
                    note="Pipeline execution raised an exception for this fixture row.",
                    stack_trace=traceback.format_exc(),
                )
            )
        else:
            try:
                serialized = session.model_dump_json()
                SessionState.model_validate_json(serialized)
            except Exception as exc:
                failure_details.append(
                    FailureDetail(
                        category="serialization_failure",
                        actual=f"{type(exc).__name__}: {exc}",
                        note="Session output was not serializable or schema-compatible.",
                        stack_trace=traceback.format_exc(),
                    )
                )

        actual_statuses = _program_statuses(session) if session is not None else {}
        actual_priority = (
            list(session.eligibility_prioritization.priority_order) if session is not None else []
        )
        actual_recommended = (
            list(session.checklist_explanation.recommended_programs) if session is not None else []
        )
        actual_uncertainty = (
            bool(session.eligibility_prioritization.uncertainty_flags)
            if session is not None
            else None
        )

        missing_programs = [program for program in SUPPORTED_PROGRAMS if program not in actual_statuses]
        if session is not None and missing_programs:
            failure_details.append(
                FailureDetail(
                    category="missing_program_assessment",
                    expected=_format_program_list(SUPPORTED_PROGRAMS),
                    actual=_format_program_list(actual_statuses.keys()),
                    note="Eligibility output omitted one or more supported programs.",
                )
            )

        unexpected_assessments = sorted(set(actual_statuses) - set(SUPPORTED_PROGRAMS))
        if unexpected_assessments:
            failure_details.append(
                FailureDetail(
                    category="unexpected_program_assessment",
                    actual=_format_program_list(unexpected_assessments),
                    note="Eligibility output included programs outside the current prototype scope.",
                )
            )

        if session is not None and list(session.session_meta.program_scope) != list(SUPPORTED_PROGRAMS):
            failure_details.append(
                FailureDetail(
                    category="program_scope_mismatch",
                    expected=_format_program_list(SUPPORTED_PROGRAMS),
                    actual=_format_program_list(session.session_meta.program_scope),
                    note="Session metadata program scope did not match the current 3-program prototype.",
                )
            )

        unexpected_priority = [program for program in actual_priority if program not in SUPPORTED_PROGRAMS]
        if unexpected_priority:
            failure_details.append(
                FailureDetail(
                    category="unexpected_priority_program",
                    actual=_format_priority_order(unexpected_priority),
                    note="Priority output included programs outside the current prototype scope.",
                )
            )

        unexpected_recommended = [
            program for program in actual_recommended if program not in SUPPORTED_PROGRAMS
        ]
        if unexpected_recommended:
            failure_details.append(
                FailureDetail(
                    category="unexpected_recommended_program",
                    actual=_format_program_list(unexpected_recommended),
                    note="Checklist output included programs outside the current prototype scope.",
                )
            )

        snap_match: bool | None = None
        medicaid_match: bool | None = None
        liheap_match: bool | None = None
        uncertainty_match: bool | None = None
        priority_match: bool | None = None
        recommended_match: bool | None = None

        if expected is not None and session is not None:
            for program, expected_field in EXPECTED_STATUS_FIELDS.items():
                expected_status = getattr(expected, expected_field)
                if expected_status is None:
                    continue

                actual_status = actual_statuses.get(program)
                matches = actual_status == expected_status
                if program == "SNAP":
                    snap_match = matches
                elif program == "Medicaid/CHIP":
                    medicaid_match = matches
                elif program == "LIHEAP":
                    liheap_match = matches

                if not matches:
                    failure_details.append(
                        FailureDetail(
                            category=f"{program.lower().replace('/', '_').replace(' ', '_')}_mismatch",
                            expected=expected_status.value,
                            actual=_format_status(actual_status),
                            note=f"{program} status did not match the populated expected result.",
                        )
                    )

            if expected.expected_uncertainty_flag is not None:
                uncertainty_match = actual_uncertainty == expected.expected_uncertainty_flag
                if not uncertainty_match:
                    failure_details.append(
                        FailureDetail(
                            category="uncertainty_mismatch",
                            expected=_format_bool(expected.expected_uncertainty_flag),
                            actual=_format_bool(actual_uncertainty),
                            note="Uncertainty-flag presence did not match the populated expected result.",
                        )
                    )

            expected_priority = _supported_expected_priority(expected)
            if expected_priority is not None:
                priority_match = actual_priority == expected_priority
                if not priority_match:
                    failure_details.append(
                        FailureDetail(
                            category="priority_mismatch",
                            expected=_format_priority_order(expected_priority),
                            actual=_format_priority_order(actual_priority),
                            note="Priority order comparison uses the current 3-program prototype scope only.",
                        )
                    )

            expected_programs = _supported_expected_programs(expected)
            if expected_programs is not None:
                recommended_match = set(actual_recommended) == set(expected_programs)
                if not recommended_match:
                    failure_details.append(
                        FailureDetail(
                            category="recommended_programs_mismatch",
                            expected=_format_program_list(expected_programs),
                            actual=_format_program_list(actual_recommended),
                            note="Recommended-program comparison is set-based because the fixture field is not ordered.",
                        )
                    )

        overall_match = not failure_details
        notes = "; ".join(detail.category for detail in failure_details)

        row = {
            "case_id": case.case_id,
            "case_type": case.case_type,
            "scenario_summary": case.scenario_summary,
            "intake_status": session.intake.intake_status.value if session is not None else "",
            "decision_status": (
                session.eligibility_prioritization.decision_status.value if session is not None else ""
            ),
            "final_status": (
                session.checklist_explanation.final_status.value if session is not None else ""
            ),
            "snap_actual": _format_status(actual_statuses.get("SNAP")),
            "medicaid_chip_actual": _format_status(actual_statuses.get("Medicaid/CHIP")),
            "liheap_actual": _format_status(actual_statuses.get("LIHEAP")),
            "uncertainty_flag_actual": _format_bool(actual_uncertainty),
            "priority_order_actual": _format_priority_order(actual_priority),
            "recommended_programs_actual": _format_program_list(actual_recommended),
            "snap_expected": _format_status(expected.expected_snap if expected is not None else None),
            "medicaid_chip_expected": _format_status(
                expected.expected_medicaid_chip if expected is not None else None
            ),
            "liheap_expected": _format_status(expected.expected_liheap if expected is not None else None),
            "uncertainty_flag_expected": _format_bool(
                expected.expected_uncertainty_flag if expected is not None else None
            ),
            "priority_order_expected": _format_priority_order(
                _supported_expected_priority(expected)
            ),
            "recommended_programs_expected": _format_program_list(
                _supported_expected_programs(expected)
            ),
            "snap_match": _format_bool(snap_match),
            "medicaid_chip_match": _format_bool(medicaid_match),
            "liheap_match": _format_bool(liheap_match),
            "uncertainty_match": _format_bool(uncertainty_match),
            "priority_match": _format_bool(priority_match),
            "recommended_programs_match": _format_bool(recommended_match),
            "overall_match": _format_bool(overall_match),
            "notes": notes,
        }
        rows.append(row)

        if failure_details:
            case_failures.append(
                CaseFailure(
                    case_id=case.case_id,
                    scenario_summary=case.scenario_summary,
                    failures=tuple(failure_details),
                )
            )
            if any(detail.category in EXCEPTION_CATEGORIES for detail in failure_details):
                exception_count += 1
            else:
                mismatch_count += 1

    summary = EvaluationSummary(
        processed_count=len(test_cases),
        full_match_count=len(test_cases) - mismatch_count - exception_count,
        mismatch_count=mismatch_count,
        exception_count=exception_count,
        output_csv_path=Path(output_csv_path),
        failure_log_path=Path(failure_log_path),
    )

    _write_results_csv(summary.output_csv_path, rows)
    _write_failure_log(summary.failure_log_path, case_failures, summary)

    return summary


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the prototype fixture evaluation.")
    parser.add_argument("--test-cases", default=str(DEFAULT_TEST_CASES_PATH))
    parser.add_argument("--expected-results", default=str(DEFAULT_EXPECTED_RESULTS_PATH))
    parser.add_argument("--output-csv", default=str(DEFAULT_EVALUATION_RESULTS_PATH))
    parser.add_argument("--failure-log", default=str(DEFAULT_FAILURE_LOG_PATH))
    parser.add_argument(
        "--ambiguity-mode",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Allow documented ambiguity handoffs during fixture evaluation.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_argument_parser().parse_args(argv)
    summary = run_evaluation(
        test_cases_path=args.test_cases,
        expected_results_path=args.expected_results,
        output_csv_path=args.output_csv,
        failure_log_path=args.failure_log,
        ambiguity_mode=args.ambiguity_mode,
    )

    print(f"Cases processed: {summary.processed_count}")
    print(f"Full matches: {summary.full_match_count}")
    print(f"Mismatches: {summary.mismatch_count}")
    print(f"Exceptions: {summary.exception_count}")
    print(f"Evaluation results: {summary.output_csv_path}")
    print(f"Failure log: {summary.failure_log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
