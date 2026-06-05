from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rgnavigator.intake_agent import run_intake, run_intake_turn
from src.rgnavigator.pipeline import run_navigator
from src.rgnavigator.traceability import build_reviewer_trace, render_trace_markdown


def _raw_input_for_case(case_id: str) -> dict:
    payload = json.loads((ROOT / "data" / "agent_test_cases.json").read_text(encoding="utf-8"))
    case_lookup = {case["case_id"]: case for case in payload["cases"]}
    if case_id not in case_lookup:
        raise KeyError(f"Unknown case_id: {case_id}")
    turns = case_lookup[case_id]["turns"]
    raw_input = {"user_description": turns[0]}
    intake = run_intake(raw_input)
    for turn in turns[1:]:
        raw_input, intake = run_intake_turn(raw_input, turn)
    return raw_input


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python scripts/export_reviewer_trace.py <CASE_ID>")
        return 1

    case_id = sys.argv[1]
    raw_input = _raw_input_for_case(case_id)
    session = run_navigator(raw_input)
    trace = build_reviewer_trace(session, case_id=case_id)

    output_dir = ROOT / "outputs" / "sample_runs"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{case_id.lower()}_reviewer_trace.json"
    md_path = output_dir / f"{case_id.lower()}_reviewer_trace.md"

    json_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_trace_markdown(trace), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
