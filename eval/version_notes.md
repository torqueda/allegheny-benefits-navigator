# Version Notes

## v1.0.2 — Post-Patch Evaluation Reconciliation (2026-04-26)

This reconciliation does not change source code. It updates the reviewer-facing evaluation artifacts so they match the latest completed evaluation run with the current best configuration.

Priority order is the order in which the navigator suggests a user review recommended programs first. It is based mainly on how likely the household appears to match each program and secondarily on immediate hardship signals such as food need, health coverage need, or heating need. It is a triage heuristic for follow-up, not an official statement of legal urgency, benefit amount, or application difficulty.

Reviewer-facing interpretation:
- ranking is influenced by urgency or hardship, likely applicability, program profile fit, practical next-step value, and uncertainty handling
- missing or contradictory evidence should increase caveats or human follow-up rather than create overconfident ranking
- evaluation treats program applicability separately from priority order, so a PASS result does not mean every priority limitation is resolved

### Evaluation artifact roles

- `eval/test_cases.csv`: canonical reviewer-facing test-case file
- `eval/evaluation_results.csv`: canonical reviewer-facing result file
- `eval/failure_log.md`: canonical failure analysis
- `eval/version_notes.md`: canonical version/change log
- `data/agent_test_cases.json`: internal runner/demo fixture
- `data/evaluation_results_phase3.json`: raw internal runner output

### What changed in this package update

- Re-ran the repository evaluation runner after the governance and priority-behavior patch
- Updated `eval/evaluation_results.csv` to match the actual completed run output
- Rewrote `eval/failure_log.md` so it separates:
  - governance behavior now intentionally handled
  - limitations mitigated but still open
  - broader evaluation gaps still open
- Updated stale evaluation summaries in `README.md` and `final_report.md`

### Current checked-in result set

- 10 total evaluation cases completed
- 6 PASS
- 4 FAIL
- Coverage includes:
  - 6 success cases
  - 3 failure-case scenarios
  - 1 edge case
- Passing cases in the checked-in run:
  - `AGENT_01`, `AGENT_04`, `AGENT_05`, `AGENT_08`, `AGENT_09`, `AGENT_10`

### Prior limitations fixed or materially mitigated by the recent patch

- `AGENT_10`: out-of-county inputs now stop before normal recommendation flow and return a safe `needs_human_followup` response with no normal recommendations
- `AGENT_08`: contradictory intake now preserves the contradiction, suppresses normal actionable recommendations, and asks the user to resolve the conflict before relying on the prescreen

### Risks still open in the checked-in runtime

- `AGENT_03` and `AGENT_07`: the current best run still shows reviewer-facing priority-order misses on health-coverage-centered cases
- `AGENT_06`: incomplete-intake fallback remains conservative, but intake-state and missing-field detail still fail the evaluator
- `AGENT_02`: the no-match guardrail still regresses in the current best run
- A 6 PASS / 4 FAIL run is a substantial improvement over the earlier fallback-only run, but it still does not mean all priority or governance issues are solved

### Legacy / non-authoritative artifacts

- `data/test_cases.csv`: legacy evaluation artifact, not authoritative for Phase 3
- `data/expected_results.csv`: legacy evaluation artifact, not authoritative for Phase 3
- `data/evaluation_results_phase3.json`: raw internal output only; reviewers should defer to `eval/evaluation_results.csv`
- `eval/evaluation_results.csv.stale.*`: stale local backup copy, not authoritative if present
