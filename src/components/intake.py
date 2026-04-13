from __future__ import annotations

from src.models.common import IntakeStatus
from src.models.session import HouseholdProfile, IntakeOutput


REQUIRED_FIELDS = [
    "county",
    "num_adults",
    "num_children",
    "household_income_total",
    "insurance_status",
]


def run_intake(case: dict[str, object]) -> IntakeOutput:
    household_size = int(case["num_adults"] or 0) + int(case["num_children"] or 0)
    profile = HouseholdProfile(
        county=case["county"],
        zip_code=str(case["zip_code"]),
        num_adults=case["num_adults"],
        num_children=case["num_children"],
        child_under_5=case["child_under_5"],
        pregnant_household_member=case["pregnant_household_member"],
        elderly_or_disabled_member=case["elderly_or_disabled_member"],
        employment_status=case["employment_status"],
        monthly_earned_income=case["monthly_earned_income"],
        monthly_unearned_income=case["monthly_unearned_income"],
        household_income_total=case["household_income_total"],
        housing_cost=case["housing_cost"],
        utility_burden=case["utility_burden"],
        heating_assistance_need=case["heating_assistance_need"],
        insurance_status=case["insurance_status"],
        recent_job_loss=case["recent_job_loss"],
        food_insecurity_signal=case["food_insecurity_signal"],
        language_or_stress_notes=case["language_or_stress_notes"],
        scenario_summary=case["scenario_summary"],
        household_size=household_size,
    )

    missing_fields = list(case["missing_fields"])
    contradictory_fields = list(case["contradictory_fields"])
    validation_warnings: list[str] = []
    clarification_questions: list[str] = []

    for field_name in REQUIRED_FIELDS:
        if getattr(profile, field_name) in (None, "") and field_name not in missing_fields:
            missing_fields.append(field_name)

    if profile.county != "Allegheny":
        validation_warnings.append("Out-of-scope geography detected.")
        clarification_questions.append("This prototype only supports Allegheny County households.")

    if profile.insurance_status == "unknown":
        validation_warnings.append("Insurance status is unknown and may affect Medicaid/CHIP results.")

    if missing_fields:
        clarification_questions.append(
            "Please clarify missing fields: " + ", ".join(sorted(missing_fields))
        )

    if contradictory_fields:
        clarification_questions.append(
            "Please resolve contradictory inputs: " + ", ".join(contradictory_fields)
        )

    if len(missing_fields) >= 3:
        intake_status = IntakeStatus.INSUFFICIENT_DATA
    elif missing_fields or contradictory_fields:
        intake_status = IntakeStatus.NEEDS_CLARIFICATION
    else:
        intake_status = IntakeStatus.COMPLETE

    return IntakeOutput(
        household_profile=profile,
        missing_fields=missing_fields,
        contradictory_fields=contradictory_fields,
        validation_warnings=validation_warnings,
        clarification_questions=clarification_questions,
        intake_status=intake_status,
    )
