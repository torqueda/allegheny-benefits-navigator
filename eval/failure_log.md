# Failure Log

This file tracks the professor-identified issues and where they were addressed in the rebuilt final state.

## Status Summary

| Issue | Status | Handoff | Evidence |
|---|---|---|---|
| High-income false-positive recommendations | Fixed | Handoff 1 | `AGENT_02`, `tests/test_suppression_guardrails.py` |
| Weak no-match path | Fixed | Handoff 1 | `AGENT_02`, `eval/evaluation_results.csv` |
| Pregnancy-pathway misranking | Fixed | Handoff 2 | `AGENT_03`, `tests/test_priority_ranking.py` |
| Uninsured-children prioritization | Fixed | Handoff 2 | `AGENT_07`, `tests/test_priority_ranking.py` |
| Missing-income fallback detail | Fixed | Handoff 3 | `AGENT_06`, `tests/test_intake_boundary_validation.py` |
| Stricter geography validation | Fixed | Handoff 3 | `AGENT_10`, `tests/test_intake_boundary_validation.py` |
| Contradictory-data clarification | Fixed | Handoff 3 | `AGENT_08`, `tests/test_intake_boundary_validation.py` |
| Session/privacy controls | Fixed | Handoff 4 | `tests/test_session_privacy_controls.py` |
| Reviewer traceability | Fixed | Handoff 5 | `REVIEWER_TRACE_INDEX.md`, `tests/test_traceability.py` |
| Evaluation dimension separation | Fixed | Handoff 6 | `eval/evaluation_results.csv`, `tests/test_evaluation_artifacts.py` |
| Naming inconsistency | Fixed | Handoff 7 | `README.md`, `app.py` |
| Final stale reviewer-facing references | Fixed | Handoff 8 | `README.md`, `eval/README.md`, `AI_USAGE.md` |

## Notes

- The checked-in evaluator is now `10 PASS / 0 FAIL`.
- Offline/no-API runs are labeled honestly in the trace and evaluator outputs.
- The remaining environment-dependent note is the upload/embedding smoke test exclusion in offline review environments. That limitation is non-blocking for the professor-feedback regression set.
