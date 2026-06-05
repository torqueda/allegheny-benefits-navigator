# Evaluation Package

This folder is the reviewer-facing evidence package for Allegheny County Benefits Navigator.

## What to Read

- `test_cases.csv`: canonical reviewer case list
- `evaluation_results.csv`: latest checked-in reviewer results
- `failure_log.md`: status of professor-identified issues
- `version_notes.md`: handoff-by-handoff evidence history
- `../REVIEWER_TRACE_INDEX.md`: trace artifacts and how to inspect them

## Current Result

The checked-in evaluator result is `10 PASS / 0 FAIL`.

The reviewer CSV separates:
- `eligibility_outcome`
- `priority_outcome`
- `explanation_outcome`
- `safety_suppression_outcome`
- `intake_boundary_outcome`

Supporting evidence fields include:
- `decision_state`
- `geography_status`
- `missing_fields`
- `suppression_reason`
- `priority_boost_reason`
- `cross_check_status`
- `trace_id`
- `trace_file`

## Reproduce

```bash
OPENAI_API_KEY='' .venv/bin/python scripts/run_agent_test_cases.py
```

The raw internal runner output is written to:
- `data/evaluation_results_phase3.json`

## Offline Review Note

The core evaluator is reproducible without an API key.

The only intentionally excluded smoke-test path in offline review environments is:

```bash
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_pipeline_smoke.py -k 'not ingested_policy_becomes_available_to_session' -q
```

That excluded test covers the embedding/index upload path and is not part of the professor-feedback regression set.
