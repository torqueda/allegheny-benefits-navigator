import csv
from pathlib import Path

from src.evaluation.run_evaluation import EVALUATION_RESULT_COLUMNS, run_evaluation
from src.loaders import load_test_cases


def _fixture_row_by_case_id(csv_path: str, case_id: str) -> tuple[list[str], dict[str, str]]:
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        for row in reader:
            if row["case_id"] == case_id:
                return fieldnames, row
    raise AssertionError(f"Missing fixture row for {case_id}")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_result_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_run_evaluation_writes_artifacts_for_current_fixture_set(tmp_path: Path) -> None:
    output_csv = tmp_path / "evaluation_results.csv"
    failure_log = tmp_path / "failure_log.md"
    expected_case_count = len(load_test_cases("data/test_cases.csv"))

    summary = run_evaluation(output_csv_path=output_csv, failure_log_path=failure_log)
    rows = _read_result_rows(output_csv)

    assert summary.processed_count == expected_case_count
    assert summary.full_match_count + summary.mismatch_count + summary.exception_count == expected_case_count
    assert output_csv.exists()
    assert failure_log.exists()
    assert list(rows[0].keys()) == EVALUATION_RESULT_COLUMNS
    assert [row["case_id"] for row in rows] == sorted(row["case_id"] for row in rows)
    assert failure_log.read_text(encoding="utf-8").startswith("# Evaluation Failures")


def test_run_evaluation_respects_blank_expected_fields_in_overall_match(tmp_path: Path) -> None:
    test_case_headers, test_case_row = _fixture_row_by_case_id("data/test_cases.csv", "TC01")
    expected_headers, _ = _fixture_row_by_case_id("data/expected_results.csv", "TC01")

    test_cases_csv = tmp_path / "test_cases.csv"
    expected_csv = tmp_path / "expected_results.csv"
    output_csv = tmp_path / "evaluation_results.csv"
    failure_log = tmp_path / "failure_log.md"

    _write_csv(test_cases_csv, test_case_headers, [test_case_row])
    _write_csv(
        expected_csv,
        expected_headers,
        [
            {
                "case_id": "TC01",
                "expected_snap": "likely_applicable",
                "expected_medicaid_chip": "",
                "expected_liheap": "",
                "expected_wic": "",
                "expected_local_referral": "",
                "expected_uncertainty_flag": "",
                "expected_priority_order": "",
                "expected_checklist_programs": "",
                "expected_explanation_notes": "",
                "why_this_is_expected": "",
            }
        ],
    )

    run_evaluation(
        test_cases_path=test_cases_csv,
        expected_results_path=expected_csv,
        output_csv_path=output_csv,
        failure_log_path=failure_log,
    )

    row = _read_result_rows(output_csv)[0]
    failure_log_text = failure_log.read_text(encoding="utf-8")

    assert row["snap_match"] == "true"
    assert row["uncertainty_match"] == ""
    assert row["priority_match"] == ""
    assert row["recommended_programs_match"] == ""
    assert row["overall_match"] == "true"
    assert "No failures recorded." in failure_log_text


def test_run_evaluation_records_mismatch_in_failure_log(tmp_path: Path) -> None:
    test_case_headers, test_case_row = _fixture_row_by_case_id("data/test_cases.csv", "TC01")
    expected_headers, _ = _fixture_row_by_case_id("data/expected_results.csv", "TC01")

    test_cases_csv = tmp_path / "test_cases.csv"
    expected_csv = tmp_path / "expected_results.csv"
    output_csv = tmp_path / "evaluation_results.csv"
    failure_log = tmp_path / "failure_log.md"

    _write_csv(test_cases_csv, test_case_headers, [test_case_row])
    _write_csv(
        expected_csv,
        expected_headers,
        [
            {
                "case_id": "TC01",
                "expected_snap": "likely_inapplicable",
                "expected_medicaid_chip": "",
                "expected_liheap": "",
                "expected_wic": "",
                "expected_local_referral": "",
                "expected_uncertainty_flag": "",
                "expected_priority_order": "",
                "expected_checklist_programs": "",
                "expected_explanation_notes": "",
                "why_this_is_expected": "",
            }
        ],
    )

    summary = run_evaluation(
        test_cases_path=test_cases_csv,
        expected_results_path=expected_csv,
        output_csv_path=output_csv,
        failure_log_path=failure_log,
    )

    row = _read_result_rows(output_csv)[0]
    failure_log_text = failure_log.read_text(encoding="utf-8")

    assert summary.mismatch_count == 1
    assert summary.exception_count == 0
    assert row["snap_match"] == "false"
    assert row["overall_match"] == "false"
    assert "snap_mismatch" in failure_log_text
    assert "TC01" in failure_log_text


def test_run_evaluation_records_pipeline_exception(tmp_path: Path) -> None:
    test_case_headers, test_case_row = _fixture_row_by_case_id("data/test_cases.csv", "TC01")
    expected_headers, expected_row = _fixture_row_by_case_id("data/expected_results.csv", "TC01")

    test_cases_csv = tmp_path / "test_cases.csv"
    expected_csv = tmp_path / "expected_results.csv"
    output_csv = tmp_path / "evaluation_results.csv"
    failure_log = tmp_path / "failure_log.md"

    _write_csv(test_cases_csv, test_case_headers, [test_case_row])
    _write_csv(expected_csv, expected_headers, [expected_row])

    def failing_runner(*args, **kwargs):
        raise RuntimeError("boom")

    summary = run_evaluation(
        test_cases_path=test_cases_csv,
        expected_results_path=expected_csv,
        output_csv_path=output_csv,
        failure_log_path=failure_log,
        pipeline_runner=failing_runner,
    )

    row = _read_result_rows(output_csv)[0]
    failure_log_text = failure_log.read_text(encoding="utf-8")

    assert summary.exception_count == 1
    assert summary.mismatch_count == 0
    assert row["overall_match"] == "false"
    assert row["notes"] == "pipeline_exception"
    assert "RuntimeError: boom" in failure_log_text
    assert "pipeline_exception" in failure_log_text


def test_run_evaluation_is_deterministic_for_current_fixture_set(tmp_path: Path) -> None:
    output_csv_one = tmp_path / "evaluation_one.csv"
    output_csv_two = tmp_path / "evaluation_two.csv"
    failure_log_one = tmp_path / "failure_one.md"
    failure_log_two = tmp_path / "failure_two.md"

    summary_one = run_evaluation(output_csv_path=output_csv_one, failure_log_path=failure_log_one)
    summary_two = run_evaluation(output_csv_path=output_csv_two, failure_log_path=failure_log_two)

    assert summary_one.processed_count == summary_two.processed_count
    assert summary_one.full_match_count == summary_two.full_match_count
    assert summary_one.mismatch_count == summary_two.mismatch_count
    assert summary_one.exception_count == summary_two.exception_count
    assert output_csv_one.read_text(encoding="utf-8") == output_csv_two.read_text(encoding="utf-8")
    assert failure_log_one.read_text(encoding="utf-8") == failure_log_two.read_text(encoding="utf-8")
