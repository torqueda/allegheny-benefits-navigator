# Version Notes

## Rebuilt Final State

This repo copy was reconstructed to match the saved final handoff history after lost local changes.

## Handoff Summary

### Handoff 1
- Added conservative suppression and no-match behavior.
- Introduced richer per-program decision states and safer rule/LLM conflict handling.

### Handoff 2
- Added bounded post-suppression priority boosts for pregnancy and uninsured-children cases.
- Preserved guardrail authority over ranking.

### Handoff 3
- Added geography status, clearer clarification handling, contradiction metadata, and normalized evaluator expectations.
- Brought the evaluator to `10 PASS / 0 FAIL`.

### Handoff 4
- Added visible session/privacy copy and `Clear current screening`.

### Handoff 5
- Added compact reviewer traces in the app and exported trace artifacts.

### Handoff 6
- Expanded the evaluation harness to separate eligibility, priority, explanation, safety suppression, and intake/boundary behavior.

### Handoff 7
- Cleaned up naming so the public project name is consistently `Allegheny County Benefits Navigator`.

### Handoff 8
- Removed stale reviewer-facing references and documented the environment-dependent ingestion/embedding smoke test exclusion clearly.

## Current Evidence State

- Evaluator: `10 PASS / 0 FAIL`
- Core reviewer package: `eval/`
- Trace artifacts: `outputs/sample_runs/`
- Raw evaluator JSON: `data/evaluation_results_phase3.json`

## Non-Blocking Limitation

The upload/embedding smoke test remains environment-dependent and is intentionally excluded in offline review runs:

```bash
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_pipeline_smoke.py -k 'not ingested_policy_becomes_available_to_session' -q
```
