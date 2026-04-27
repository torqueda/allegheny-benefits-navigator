# Version Notes

## v1.0.1 — Evaluation Package Canonicalization (2026-04-26)

This version does not change the core app behavior. It canonicalizes the Phase 3 evaluation package so the reviewer-facing artifacts in `eval/` are authoritative and consistent with the current runner outputs.

### Evaluation artifact roles

- `eval/test_cases.csv`: canonical reviewer-facing test-case file
- `eval/evaluation_results.csv`: canonical reviewer-facing result file
- `eval/failure_log.md`: canonical failure analysis
- `eval/version_notes.md`: canonical version/change log
- `data/agent_test_cases.json`: internal runner/demo fixture
- `data/evaluation_results_phase3.json`: raw internal runner output

### What changed in this package update

- Recreated `eval/evaluation_results.csv` from the current passing raw result set
- Updated `eval/test_cases.csv` so reviewer-facing expectations match current failure-case and edge-case semantics
- Updated `eval/failure_log.md` to describe current limitations instead of obsolete “not implemented” claims
- Updated `scripts/run_agent_test_cases.py` so future runs refresh both:
  - `data/evaluation_results_phase3.json` as raw internal output
  - `eval/evaluation_results.csv` as the reviewer-facing summary
- Labeled the JSON fixture in `data/agent_test_cases.json` as an internal runner/demo artifact

### Canonical current result set

- 10 total evaluation cases completed
- 10 PASS
- 0 FAIL
- Coverage includes:
  - 6 success cases
  - 3 failure-case scenarios
  - 1 edge case

### Current behavioral limitations still open

- Out-of-county inputs are detected at intake but not hard-stopped downstream
- Contradictions trigger `needs_human_followup`, but recommendations may still appear before resolution
- Incomplete-intake fallback remains conservative and safe, but still light on referral guidance
- Evaluation quality remains sensitive to the OpenAI-backed path; fallback-only runs are materially weaker

### Legacy / non-authoritative artifacts

- `data/test_cases.csv`: legacy evaluation artifact, not authoritative for Phase 3
- `data/expected_results.csv`: legacy evaluation artifact, not authoritative for Phase 3
- `data/evaluation_results_phase3.json`: raw internal output only; reviewers should defer to `eval/evaluation_results.csv`
- `eval/evaluation_results.csv.stale.*`: stale local backup copy, not authoritative if present
