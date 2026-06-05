from __future__ import annotations

import json
from pathlib import Path

def load_demo_cases() -> dict[str, dict]:
    """Load demo cases from the natural-language agent fixtures only."""
    cases: dict[str, dict] = {}
    agent_path = Path(__file__).resolve().parents[2] / "data" / "agent_test_cases.json"
    agent_payload = json.loads(agent_path.read_text(encoding="utf-8"))
    for case in agent_payload["cases"]:
        case_id = case["case_id"]
        cases[case_id] = {
            "source": "agent",
            "case_type": case.get("evaluation_type", "unknown"),
            "scenario_summary": case["turns"][0],
            "category": case.get("category", ""),
            "turn_count": len(case.get("turns", [])),
        }

    return cases
