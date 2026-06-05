from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_reviewer_csv_contains_dimension_columns() -> None:
    path = ROOT / "eval" / "evaluation_results.csv"
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []

    expected = {
        "eligibility_outcome",
        "priority_outcome",
        "explanation_outcome",
        "safety_suppression_outcome",
        "intake_boundary_outcome",
        "decision_state",
        "geography_status",
        "suppression_reason",
        "priority_boost_reason",
        "cross_check_status",
        "trace_id",
        "trace_file",
    }
    assert expected.issubset(set(fieldnames))


def test_raw_json_results_are_all_pass_and_include_metadata() -> None:
    results = json.loads((ROOT / "data" / "evaluation_results_phase3.json").read_text(encoding="utf-8"))

    assert results
    assert all(row["outcome"] == "PASS" for row in results)
    assert all("geography_status" in row for row in results)
    assert all("trace_id" in row for row in results)


def test_evidence_index_and_trace_docs_exist() -> None:
    required = [
        ROOT / "eval" / "README.md",
        ROOT / "eval" / "failure_log.md",
        ROOT / "eval" / "version_notes.md",
        ROOT / "REVIEWER_TRACE_INDEX.md",
        ROOT / "outputs" / "sample_runs" / "agent_04_reviewer_trace.json",
    ]
    for path in required:
        assert path.exists(), path


def test_root_readme_uses_canonical_project_name() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Allegheny County Benefits Navigator" in readme
    assert "Retrieval-Grounded Policy Navigator" not in readme
    assert "10 PASS / 0 FAIL" in readme
    assert "ingested_policy_becomes_available_to_session" in readme


def test_no_reviewer_facing_final_report_references_remain() -> None:
    for rel in ["README.md", "eval/README.md", "AI_USAGE.md"]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "final_report.md" not in text
        assert "Final_Report.txt" not in text
