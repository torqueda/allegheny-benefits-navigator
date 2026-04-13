from __future__ import annotations

import csv
import json
from pathlib import Path


def _parse_bool(value: str) -> bool | None:
    if value == "":
        return None
    return value.strip().lower() == "true"


def _parse_float(value: str) -> float | None:
    if value == "":
        return None
    return float(value)


def _parse_int(value: str) -> int | None:
    if value == "":
        return None
    return int(value)


def _parse_json_list(value: str) -> list[str]:
    if not value:
        return []
    return json.loads(value)


def _parse_priority_order(value: str) -> list[str]:
    if not value:
        return []
    return value.split(" > ")


def _parse_program_list(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",")]


def load_test_cases(path: str | Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "case_id": row["case_id"],
                    "case_type": row["case_type"],
                    "scenario_summary": row["scenario_summary"],
                    "county": row["county"],
                    "zip_code": row["zip_code"],
                    "num_adults": _parse_int(row["num_adults"]),
                    "num_children": _parse_int(row["num_children"]),
                    "child_under_5": _parse_bool(row["child_under_5"]),
                    "pregnant_household_member": _parse_bool(row["pregnant_household_member"]),
                    "elderly_or_disabled_member": _parse_bool(row["elderly_or_disabled_member"]),
                    "employment_status": row["employment_status"],
                    "monthly_earned_income": _parse_float(row["monthly_earned_income"]),
                    "monthly_unearned_income": _parse_float(row["monthly_unearned_income"]),
                    "household_income_total": _parse_float(row["household_income_total"]),
                    "housing_cost": _parse_float(row["housing_cost"]),
                    "utility_burden": row["utility_burden"],
                    "heating_assistance_need": _parse_bool(row["heating_assistance_need"]),
                    "insurance_status": row["insurance_status"],
                    "recent_job_loss": _parse_bool(row["recent_job_loss"]),
                    "food_insecurity_signal": row["food_insecurity_signal"],
                    "missing_fields": _parse_json_list(row["missing_fields"]),
                    "contradictory_fields": _parse_json_list(row["contradictory_fields"]),
                    "language_or_stress_notes": row["language_or_stress_notes"],
                }
            )
    return rows


def load_expected_results(path: str | Path) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows[row["case_id"]] = {
                "SNAP": row["expected_snap"] or None,
                "Medicaid/CHIP": row["expected_medicaid_chip"] or None,
                "LIHEAP": row["expected_liheap"] or None,
                "WIC": row["expected_wic"] or None,
                "Local Referral": row["expected_local_referral"] or None,
                "expected_uncertainty_flag": _parse_bool(row["expected_uncertainty_flag"]),
                "expected_priority_order": _parse_priority_order(row["expected_priority_order"]),
                "expected_checklist_programs": _parse_program_list(row["expected_checklist_programs"]),
                "expected_explanation_notes": row["expected_explanation_notes"] or "",
                "why_this_is_expected": row["why_this_is_expected"] or "",
            }
    return rows
