from __future__ import annotations

import unittest

from src.loaders.csv_loader import load_expected_results, load_test_cases
from src.pipeline import run_case


class PipelineTests(unittest.TestCase):
    def test_loader_parses_fixture_shapes(self) -> None:
        cases = load_test_cases("data/test_cases.csv")
        expected = load_expected_results("data/expected_results.csv")
        self.assertEqual(len(cases), 10)
        self.assertIn("TC01", expected)
        self.assertEqual(expected["TC01"]["expected_priority_order"], ["LIHEAP", "SNAP", "Medicaid/CHIP"])

    def test_pipeline_runs_one_case_end_to_end(self) -> None:
        case = load_test_cases("data/test_cases.csv")[0]
        state = run_case(case)
        self.assertEqual(state.session_meta.case_id, "TC01")
        self.assertTrue(state.checklist_explanation.recommended_programs)
        self.assertIn("prescreening", state.checklist_explanation.user_explanation.lower())


if __name__ == "__main__":
    unittest.main()
