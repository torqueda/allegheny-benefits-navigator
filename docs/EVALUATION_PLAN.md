# Evaluation Plan

## Goal
Test whether the Phase 2 prototype can produce transparent, bounded, and mostly correct prescreening behavior across realistic and failure-prone Allegheny County household scenarios.

## Evaluation set
- 10 synthetic cases in `data/test_cases.csv`
- Covers:
  - clear eligible cases
  - clear ineligible cases
  - multi-program cases
  - missing-information cases
  - contradictory-data cases
  - near-threshold cases
  - local-referral-only cases
  - ambiguous composition or insurance cases
  - pregnancy-specific edge cases

## Success criteria
- Program-status matching:
  - For each case, the prototype should match the expected status for each in-scope program.
- Priority-order matching:
  - For cases with a non-empty expected priority list, the prototype should match the expected ranked order.
- Uncertainty handling:
  - Ambiguous or contradictory cases should surface caveats instead of presenting overconfident outputs.
- Bounded output:
  - Every output must remind the user that this is prescreening, not an official determination.

## Measures
- Per-program status agreement against `data/expected_results.csv`
- Priority-order agreement against `data/expected_results.csv`
- Presence or absence of uncertainty flags against expected ambiguity labels
- Existence of a structured trace JSON for each run

## Procedure
1. Run `python3 -m src.evaluate`.
2. Load each synthetic case and expected result row.
3. Execute the full three-component pipeline.
4. Write one trace file per case to `outputs/traces/`.
5. Compare actual program statuses, ranking, and uncertainty behavior to expected values.
6. Write summary results to `data/evaluation_results.csv`.

## Ambiguity definitions
- `missing income`: household income cannot be screened deterministically.
- `contradictory intake`: input conflicts such as employment versus zero income.
- `household-composition uncertainty`: unclear dependent or budget-group membership.
- `insurance uncertainty`: unknown coverage status affecting Medicaid/CHIP confidence.
- `threshold edge`: income is very close to a cutoff and should be verified.

## Current result snapshot
- 10/10 cases matched the expected fixture after the latest prototype run.
- Representative difficult cases:
  - `TC04`: missing income triggers uncertainty plus local referral
  - `TC06`: contradiction triggers uncertain program statuses
  - `TC09`: Medicaid/CHIP remains uncertain while SNAP and LIHEAP stay likely
  - `TC10`: pregnancy-specific Medicaid logic remains likely applicable with a visible caveat

## Limits
- These are synthetic cases, not live users.
- Thresholds are prototype heuristics and need source-dated review before any Phase 3 expansion.
- Local-referral logic is intentionally generic and should not be interpreted as verified service routing.
