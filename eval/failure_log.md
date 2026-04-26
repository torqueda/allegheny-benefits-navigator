# Failure Log

## Overview

This log documents failures and limitations discovered during evaluation of the Retrieval-Grounded Policy Navigator. It covers both system-level bugs fixed during development and known design limitations identified through test case evaluation.

---

## Evaluation Failures

### FAILURE-01 — Out-of-County Case Not Detected (AGENT_10)

| Field | Detail |
|-------|--------|
| **failure_id** | FAILURE-01 |
| **date** | 2026-04-25 |
| **version_tested** | v1.0 (Phase 3) |
| **case** | AGENT_10 (`outside_county_boundary`) |
| **what_triggered_the_problem** | User described a Philadelphia household. System is designed for Allegheny County programs only. |
| **what_happened** | System ran the full eligibility pipeline and returned program matches (Medicaid/CHIP strong match, SNAP possible match, LIHEAP possible match) without warning the user that the results may not apply to their county. |
| **severity** | High — user could act on incorrect prescreening results |
| **fix_attempted** | No fix implemented in current version. County field defaults to Allegheny if not explicitly set. |
| **current_status** | Open — known limitation. Mitigation: output includes disclaimer "This is prescreening only. It is not an official determination." |

---

### FAILURE-02 — Contradictory Data Not Explicitly Challenged (AGENT_08)

| Field | Detail |
|-------|--------|
| **failure_id** | FAILURE-02 |
| **date** | 2026-04-25 |
| **version_tested** | v1.0 (Phase 3) |
| **case** | AGENT_08 (`contradictory_data_cross_check`) |
| **what_triggered_the_problem** | User stated they work full-time but have zero earned income this month — a direct contradiction. |
| **what_happened** | Intake agent flagged `needs_clarification` but did not prompt the user to resolve the conflict. Pipeline ran with ambiguous profile. Cross-check diverged on program scores, decision status: ambiguous. No explicit message to user about the contradiction. |
| **severity** | Medium — output is marked uncertain, but user is not told why |
| **fix_attempted** | No targeted fix. Hybrid cross-check partially handles this by surfacing disagreement. |
| **current_status** | Open — design limitation. Future fix: add explicit contradiction detection in intake normalization step. |

---

### FAILURE-03 — Graceful Degradation Produces Unhelpful Output (AGENT_06)

| Field | Detail |
|-------|--------|
| **failure_id** | FAILURE-03 |
| **date** | 2026-04-25 |
| **version_tested** | v1.0 (Phase 3) |
| **case** | AGENT_06 (`missing_info_graceful_degradation`) |
| **what_triggered_the_problem** | User declined to share income information after two turns. |
| **what_happened** | System correctly reached `insufficient_data` intake status and did not produce false program matches. However, the output to the user was minimal — no actionable guidance, no suggested next steps for obtaining help without income disclosure. |
| **severity** | Low — system behaves safely (no false positives) but is not useful |
| **fix_attempted** | No fix. Caveats are shown. |
| **current_status** | Open — known limitation. Future improvement: add fallback guidance for users who cannot or will not share income (e.g., "contact a local caseworker who can assess your situation in person"). |

---

## Development Bugs Fixed During Testing

These bugs were identified and fixed before the Phase 3 evaluation runs.

### BUG-01 — Clarification Questions Shown as Caveats

| Field | Detail |
|-------|--------|
| **what_happened** | `explanation_agent.py` appended `intake.clarification_questions` to `visible_caveats`, causing intake follow-up questions to appear in the Caveats section of the output. |
| **fix** | Removed `visible_caveats.extend(intake.clarification_questions[:3])` from explanation agent. |
| **status** | Fixed |

### BUG-02 — Double-Counted Retrieval Bonus in Priority Score

| Field | Detail |
|-------|--------|
| **what_happened** | `eligibility_agent.py` added `retrieval_bonus` twice when computing `priority_score`, causing programs with retrieved evidence to be ranked higher than intended. |
| **fix** | Changed `priority_score += retrieval_bonus + max(score, 0)` to `priority_score += max(score, 0)`. |
| **status** | Fixed |

### BUG-03 — Program Sort Order Inconsistent with Priority Order

| Field | Detail |
|-------|--------|
| **what_happened** | `program_matches` list was sorted only by `match_score`, while `priority_order` was computed from `priority_score`. The two lists could disagree on ranking. |
| **fix** | Changed sort key to `(priority_score, match_score)` to match `priority_order`. |
| **status** | Fixed |

### BUG-04 — Medicaid Terms Leaked into General Retrieval Query

| Field | Detail |
|-------|--------|
| **what_happened** | Terms like "medicaid", "chip", and "insurance" were included in the general intake query layer, causing Medicaid chunks to be retrieved when evaluating SNAP and LIHEAP. |
| **fix** | Moved those terms from `_intake_query_terms` to the Medicaid-specific branch of `_program_specific_intake_terms`. |
| **status** | Fixed |

### BUG-05 — Ingestion Rebuilt Entire Vector Index on Each Upload

| Field | Detail |
|-------|--------|
| **what_happened** | `ingest_policy_text()` called `build_and_save_policy_index()`, which re-embedded all 2,191 existing chunks on every upload — slow and wasteful. |
| **fix** | Replaced with `append_document_to_policy_index()`, which embeds only the new document's chunks and appends them to the existing index. |
| **status** | Fixed |

### BUG-06 — LIHWAP Misclassified as LIHEAP

| Field | Detail |
|-------|--------|
| **what_happened** | `_guess_program_name()` matched "utility" keyword in LIHWAP content and returned "LIHEAP" instead of "LIHWAP". |
| **fix** | Added LIHWAP keyword check before the LIHEAP check in `policy_store.py`. |
| **status** | Fixed |

### BUG-07 — Test Cleanup Left Uploaded Policy Files Between Runs

| Field | Detail |
|-------|--------|
| **what_happened** | Smoke tests wrote files to `data/uploaded_policies/` but did not clean up, causing AGENT_04 and AGENT_09 tests to fail on subsequent runs due to unexpected uploaded program appearing in results. |
| **fix** | Added `autouse=True` pytest fixture in `tests/conftest.py` to delete all `uploaded_policies/*.md` files after every test. |
| **status** | Fixed |
