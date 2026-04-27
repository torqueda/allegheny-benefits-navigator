# Failure Log

## Overview

This file is the canonical Phase 3 failure analysis for final submission.

Artifact roles for the evaluation package:
- `eval/test_cases.csv`: canonical reviewer-facing test cases
- `eval/evaluation_results.csv`: canonical reviewer-facing results
- `eval/failure_log.md`: canonical failure analysis
- `eval/version_notes.md`: canonical version/change log
- `data/agent_test_cases.json`: internal runner/demo fixture
- `data/evaluation_results_phase3.json`: raw internal runner output

The current canonical result set passes all 10 evaluation cases, including failure and boundary scenarios. This log therefore focuses on remaining behavioral limitations surfaced by those cases rather than on obsolete PASS/PARTIAL/FAIL packaging from older runs.

---

## Open Limitations Observed in Evaluation

### LIMIT-01 — Out-of-County Inputs Are Detected but Not Hard-Stopped (AGENT_10)

| Field | Detail |
|---|---|
| **limitation_id** | LIMIT-01 |
| **date_reviewed** | 2026-04-26 |
| **case** | AGENT_10 (`outside_county_boundary`) |
| **current_behavior** | Intake correctly marks the case `insufficient_data` and adds an Allegheny-only warning for a Philadelphia household. The downstream pipeline may still continue into a caveated prototype walkthrough and surface recommended programs. |
| **why_it_matters** | Users outside Allegheny County can still see recommendations that are not intended as county-specific determinations. |
| **severity** | Medium |
| **current_evaluation_status** | The failure-case scenario passes the evaluator because the intake guard now fires as expected. |
| **remaining_gap** | The pipeline does not currently short-circuit after out-of-scope county detection. |
| **recommended_future_fix** | Halt eligibility/explanation after the out-of-county intake guard, or replace the walkthrough with an explicit out-of-scope handoff. |

---

### LIMIT-02 — Contradictions Trigger Human-Followup, but Recommendations May Still Appear (AGENT_08)

| Field | Detail |
|---|---|
| **limitation_id** | LIMIT-02 |
| **date_reviewed** | 2026-04-26 |
| **case** | AGENT_08 (`contradictory_data_cross_check`) |
| **current_behavior** | Intake detects the contradiction, keeps the case at `needs_clarification`, and the explanation output surfaces `needs_human_followup`. Under the current prototype flow, recommendations may still appear downstream. |
| **why_it_matters** | The system communicates uncertainty more honestly than before, but it still produces recommendations on top of contradictory facts. |
| **severity** | Medium |
| **current_evaluation_status** | The failure-case scenario passes the evaluator because contradiction detection and human-followup signaling now behave as expected. |
| **remaining_gap** | The pipeline does not force contradiction resolution before continuing into eligibility/explanation. |
| **recommended_future_fix** | Short-circuit after unresolved contradictions, or suppress recommended programs until the contradiction is resolved. |

---

### LIMIT-03 — Incomplete-Intake Fallback Is Safe but Still Light on Guidance (AGENT_06)

| Field | Detail |
|---|---|
| **limitation_id** | LIMIT-03 |
| **date_reviewed** | 2026-04-26 |
| **case** | AGENT_06 (`missing_info_graceful_degradation`) |
| **current_behavior** | Intake reaches `insufficient_data`, no programs are recommended, and the evaluator treats the case as a successful safe degradation path. |
| **why_it_matters** | The system avoids false matches, but the fallback user guidance is still modest relative to a real service handoff. |
| **severity** | Low |
| **current_evaluation_status** | The failure-case scenario passes the evaluator because the system remains conservative and does not hallucinate program matches. |
| **remaining_gap** | Users who refuse or cannot share enough information do not yet get richer alternative pathways or referral guidance. |
| **recommended_future_fix** | Add a dedicated insufficient-data fallback block with local contact/referral guidance and clearer next-step instructions. |

---

## Previously Fixed Issues Preserved in This Version

These fixes remain reflected in the current codebase and evaluation package.

### FIX-01 — Clarification Questions No Longer Leak into Caveats

| Field | Detail |
|---|---|
| **what_happened** | Earlier versions surfaced intake follow-up questions in the caveats section. |
| **current_state** | Fixed. Clarification prompts no longer appear as caveats. |

### FIX-02 — Retrieval Bonus Is No Longer Double-Counted in Priority Score

| Field | Detail |
|---|---|
| **what_happened** | Earlier priority scoring over-weighted retrieved evidence. |
| **current_state** | Fixed. Priority ordering now uses the intended score composition. |

### FIX-03 — Program Ranking Now Matches Priority Order

| Field | Detail |
|---|---|
| **what_happened** | Earlier program sort order could diverge from the reported priority order. |
| **current_state** | Fixed. The visible ranking and priority order are now aligned. |

### FIX-04 — Medicaid Query Terms No Longer Contaminate Other Programs

| Field | Detail |
|---|---|
| **what_happened** | Earlier shared retrieval terms could leak Medicaid evidence into SNAP/LIHEAP evaluations. |
| **current_state** | Fixed. Program-specific retrieval terms now separate that path more cleanly. |

### FIX-05 — Uploaded-Policy Ingestion Uses Incremental Indexing

| Field | Detail |
|---|---|
| **what_happened** | Earlier uploads rebuilt the full index. |
| **current_state** | Fixed. Upload ingestion appends new chunks instead of rebuilding everything. |

### FIX-06 — LIHWAP and LIHEAP Are Distinguished Correctly

| Field | Detail |
|---|---|
| **what_happened** | Earlier program-name guessing could map LIHWAP content to LIHEAP. |
| **current_state** | Fixed. The LIHWAP-specific check now runs before the LIHEAP fallback. |

### FIX-07 — Test Cleanup Removes Uploaded Policy Residue

| Field | Detail |
|---|---|
| **what_happened** | Earlier test runs could leave uploaded policies behind and contaminate later evaluations. |
| **current_state** | Fixed. `tests/conftest.py` removes uploaded policy markdown files after each test. |
