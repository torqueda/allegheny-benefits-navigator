# Failure Log

## Overview

This file is the canonical Phase 3 failure analysis for the checked-in Phase 3 evaluation package.

Artifact roles for the evaluation package:
- `eval/test_cases.csv`: canonical reviewer-facing test cases
- `eval/evaluation_results.csv`: canonical reviewer-facing results
- `eval/failure_log.md`: canonical failure analysis
- `eval/version_notes.md`: canonical version/change log
- `data/agent_test_cases.json`: internal runner/demo fixture
- `data/evaluation_results_phase3.json`: raw internal runner output

The checked-in `eval/evaluation_results.csv` reflects the latest completed evaluation run with the current best configuration. That run produced 6 PASS / 4 FAIL across 10 total cases. Evaluation still treats eligibility correctness separately from priority-order limitations, so this log distinguishes behavior now intentionally handled by governance controls from limitations that remain open in the current runtime.

Priority order is the order in which the navigator suggests a user review recommended programs first. It is based mainly on how likely the household appears to match each program and secondarily on immediate hardship signals such as food need, health coverage need, or heating need. It is a triage heuristic for follow-up, not an official statement of legal urgency, benefit amount, or application difficulty.

Ranking is additionally shaped by program profile fit, practical next-step value, and uncertainty handling. Missing or contradictory evidence should increase caveats or human follow-up rather than create overconfident ranking.

---

## Behavior Now Intentionally Handled by Governance Controls

### GOV-01 — Out-of-County Inputs Stop Before Normal Recommendations (AGENT_10)

| Field | Detail |
|---|---|
| **failure_id** | GOV-01 |
| **date_reviewed** | 2026-04-26 |
| **case_id** | AGENT_10 (`outside_county_boundary`) |
| **trigger** | User reports a household outside Allegheny County. |
| **what_happened** | Intake marks the case `insufficient_data`, the final response is `needs_human_followup`, and the runtime withholds normal recommendations and normal `priority_order` output. The evaluator now records this case as PASS. |
| **why_it_happened** | The recent behavior patch added an out-of-scope guard that stops normal recommendation flow for unsupported geography. |
| **why_it_matters** | Users outside Allegheny County now get an explicit scope boundary instead of a misleading county-specific prescreen. |
| **severity** | Medium before the patch; now mitigated by governance control |
| **current_evaluation_status** | PASS in the current checked-in evaluation run. |
| **fix_attempted_or_mitigation_added** | The pipeline now returns an Allegheny-only scope message and suppresses normal recommendations for clearly out-of-county households. |
| **current_status** | Resolved in the current runtime for the evaluated out-of-county case. Residual risk remains for unsupported geography phrased in ways the intake parser may still miss. |

---

### GOV-02 — Contradictory Core Intake Is Suppressed Before Actionable Recommendations (AGENT_08)

| Field | Detail |
|---|---|
| **failure_id** | GOV-02 |
| **date_reviewed** | 2026-04-26 |
| **case_id** | AGENT_08 (`contradictory_data_cross_check`) |
| **trigger** | User reports conflicting employment and earned-income facts. |
| **what_happened** | Intake preserves the contradiction, the final response is `needs_human_followup`, and the runtime suppresses normal actionable recommendations until the contradiction is resolved. The evaluator now records this case as PASS. |
| **why_it_happened** | The recent behavior patch added contradiction-aware suppression so unresolved core evidence conflicts do not continue into a normal actionable prescreen. |
| **why_it_matters** | Users now receive a safer clarification-first response instead of recommendations presented as ready to act on. |
| **severity** | Medium before the patch; now mitigated by governance control |
| **current_evaluation_status** | PASS in the current checked-in evaluation run. |
| **fix_attempted_or_mitigation_added** | Contradictions now trigger `needs_human_followup`, preserve the contradiction in structured output, and suppress normal actionable recommendations. |
| **current_status** | Resolved in the current runtime for the evaluated contradiction case. Residual risk remains for contradiction patterns not yet covered by the current intake checks. |

---

## Still-Open Limitations Observed in Evaluation

### LIMIT-01 — Clear No-Match Guardrail Still Regresses on a High-Income Insured Adult (AGENT_02)

| Field | Detail |
|---|---|
| **failure_id** | LIMIT-01 |
| **date_reviewed** | 2026-04-26 |
| **case_id** | AGENT_02 (`high_income_no_match`) |
| **trigger** | User reports a high-income insured adult household with needs outside the supported benefit set. |
| **what_happened** | The runtime still recommends `Medicaid/CHIP`, `LIHEAP`, and `SNAP` instead of returning a clean no-match result. |
| **why_it_happened** | The current scoring and retrieval path still produces false-positive `possible_match` signals on this guardrail case. |
| **why_it_matters** | This remains the clearest false-positive regression in the current checked-in run. |
| **severity** | High |
| **current_evaluation_status** | FAIL in the current checked-in evaluation run. |
| **fix_attempted_or_mitigation_added** | No direct fix landed in the recent governance patch; that patch focused on unsafe recommendation suppression for out-of-scope and contradictory cases. |
| **current_status** | Open. This remains the clearest false-positive regression in the current checked-in run. |

---

### LIMIT-02 — Pregnancy Pathway Case Still Misranks Priority and Misses Explanation Detail (AGENT_03)

| Field | Detail |
|---|---|
| **failure_id** | LIMIT-02 |
| **date_reviewed** | 2026-04-26 |
| **case_id** | AGENT_03 (`pregnancy_pathway_edge_case`) |
| **trigger** | User reports pregnancy, existing insurance, and a scenario where Medicaid/CHIP should remain the primary review candidate. |
| **what_happened** | The runtime recommends `LIHEAP`, `SNAP`, and `Medicaid/CHIP`, puts `LIHEAP` first, and misses the term `pregnancy` in the explanation or caveat text. |
| **why_it_happened** | The current ranking and explanation path still underweights the pregnancy-specific Medicaid pathway and over-surfaces secondary programs. |
| **why_it_matters** | This is the clearest remaining priority-order limitation in the checked-in run because the evaluator expects Medicaid/CHIP to be the top review candidate here. |
| **severity** | Medium |
| **current_evaluation_status** | FAIL in the current checked-in evaluation run. |
| **fix_attempted_or_mitigation_added** | Priority order remains documented and evaluated as a triage heuristic rather than a legal determination, which keeps this issue scoped as a ranking and explanation problem rather than an official eligibility claim. |
| **current_status** | Open. Priority and explanation alignment remain incomplete for this edge case. |

---

### LIMIT-03 — Incomplete-Intake Fallback Is Safe but Still Misses Expected Detail (AGENT_06)

| Field | Detail |
|---|---|
| **failure_id** | LIMIT-03 |
| **date_reviewed** | 2026-04-26 |
| **case_id** | AGENT_06 (`missing_info_graceful_degradation`) |
| **trigger** | User declines or cannot provide enough income detail to complete intake. |
| **what_happened** | The runtime avoids false matches and keeps recommendations suppressed, but the case still fails evaluation because intake remains `needs_clarification` instead of `insufficient_data` and omits `num_adults` from the reported `missing_fields`. |
| **why_it_happened** | The fallback intake parser infers one adult from the narrative and stays in clarification mode longer than the reviewer expectation for this case. |
| **why_it_matters** | The safe behavior is preserved, but the evaluator still sees a mismatch in how incomplete evidence is summarized and escalated. |
| **severity** | Low |
| **current_evaluation_status** | FAIL in the current checked-in evaluation run. |
| **fix_attempted_or_mitigation_added** | The recent patch keeps the fallback conservative, suppresses normal recommendations, and adds clearer gather-this-information guidance. |
| **current_status** | Open. Guidance is better than before, but intake-state and missing-field detail still lag the expected behavior. |

---

### LIMIT-04 — Uninsured-Children Case Still Over-Prioritizes LIHEAP Ahead of Health Coverage (AGENT_07)

| Field | Detail |
|---|---|
| **failure_id** | LIMIT-04 |
| **date_reviewed** | 2026-04-26 |
| **case_id** | AGENT_07 (`uninsured_children_priority_case`) |
| **trigger** | User reports uninsured children and a scenario where Medicaid/CHIP or SNAP should rank ahead of LIHEAP. |
| **what_happened** | The runtime recommends `LIHEAP`, `SNAP`, and `Medicaid/CHIP`, but the evaluator rejects the case because `LIHEAP` is ranked first instead of `Medicaid/CHIP` or `SNAP`. |
| **why_it_happened** | The current priority heuristic still overweights a secondary hardship signal relative to the health-coverage need in this case. |
| **why_it_matters** | This is a current reviewer-facing priority-order miss, even though the program set itself is otherwise plausible. |
| **severity** | Medium |
| **current_evaluation_status** | FAIL in the current checked-in evaluation run. |
| **fix_attempted_or_mitigation_added** | Priority order is now documented consistently as a triage heuristic, which keeps this issue framed as a review-order limitation rather than an official eligibility determination. |
| **current_status** | Open. The remaining gap is review-order alignment for this household type. |

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
