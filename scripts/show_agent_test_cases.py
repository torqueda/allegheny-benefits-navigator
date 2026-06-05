from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "data" / "agent_test_cases.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    print(f"schema_version: {payload['schema_version']}")
    print(f"description: {payload['description']}")
    print(f"case_count: {len(payload['cases'])}")
    print()

    for case in payload["cases"]:
        print(f"[{case['case_id']}] {case['category']}")
        print(f"  turns: {len(case['turns'])}")
        print(f"  intake_status: {case['expected_intake']['expected_intake_status']}")
        print(f"  must_recommend: {case['expected_eligibility']['must_recommend']}")
        print(f"  top_priority_in: {case['expected_eligibility']['top_priority_in']}")
        print()


if __name__ == "__main__":
    main()
