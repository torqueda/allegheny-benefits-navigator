# Final Report — Retrieval-Grounded Policy Navigator

**Course:** Agentic Systems Studio — Track A
**Team:** Yuhan, Tomas
**Submission date:** 2026-04-25
**Version:** v1.0 (Phase 3)

---

## 1. Problem Statement

Households in Allegheny County who need public benefits — food assistance, health coverage, utility help — often struggle to understand whether they qualify before investing time in a full application. Eligibility rules are long, income thresholds change by household size, and multiple programs have overlapping but distinct criteria. A non-expert reading the PA DPW policy manuals cannot easily self-screen.

Our system provides a plain-language prescreening tool that takes a household narrative, extracts relevant facts, retrieves the applicable policy sections from real government documents, and returns a prioritized list of programs with evidence-backed explanations. The goal is not to replace caseworkers — it is to give households a grounded, honest first answer and a concrete next step.

---

## 2. Architecture

The system is a three-agent pipeline:

```
User Input
    ↓
Intake Agent          — extracts structured profile; triggers clarification if incomplete
    ↓
Eligibility Agent     — RAG retrieval per program + LLM scoring + rule cross-check
    ↓
Explanation Agent     — plain-language output, checklist, caveats
    ↓
Streamlit UI Output
```

### 2.1 Intake Agent

Takes free-text household description plus optional structured override fields. Uses `gpt-4o-mini` to extract a normalized `UserIntake` profile (household size, income, employment, insurance, special signals like pregnancy or utility crisis). If required fields are missing, the agent generates targeted clarification questions and triggers a multi-turn conversation (up to 4 rounds) before running the rest of the pipeline.

Fallback: regex-based extraction when no API key is present.

### 2.2 Eligibility Agent

For each program in scope (SNAP, Medicaid/CHIP, LIHEAP, plus any user-uploaded programs):

1. **RAG retrieval** — generates a program-specific query from the intake profile, retrieves the top-k most relevant policy chunks from the local vector index using cosine similarity against OpenAI `text-embedding-3-small` embeddings
2. **LLM scoring** — `gpt-4o-mini` scores eligibility (`strong_match` / `possible_match` / `no_clear_match`) using the retrieved chunks as grounding context, and produces a rationale with policy section citations
3. **Rule cross-check** — a deterministic scoring function applies explicit thresholds from `program_profiles.json` (income limits, household size, special conditions)
4. **Decision status** — `ready_for_explanation` when intake is complete and all recommended programs are `strong_match`; `ambiguous` when intake is incomplete or any recommended program remains `possible_match`

Priority order is the order in which the navigator suggests a user review recommended programs first. It is a triage/review order based on likely applicability, program-profile fit, immediate hardship urgency, and uncertainty-aware screening signals. Missing or contradictory evidence should increase caveats or human follow-up, not create overconfident ranking. It is not an official statement of legal eligibility certainty, benefit amount, or application difficulty.

### 2.3 Explanation Agent

Takes the ranked program matches and retrieved evidence. Uses `gpt-4o-mini` to produce:
- Plain-language eligibility summary per program
- Concrete next steps
- Itemized checklist of documents and actions per program
- Visible caveats (uncertainty flags, prescreening disclaimer)

Fallback: template-rendered output when no API key is present.

### 2.4 Policy Retrieval Index

2,191 chunks from PA DPW policy manuals (SNAP v8, Medicaid/CHIP, LIHEAP) embedded with `text-embedding-3-small` and stored locally. New documents can be appended incrementally without rebuilding the full index. Local hashed bag-of-words fallback is available but less accurate.

---

## 3. Implementation

### Key design choices

**Per-program RAG queries** — each program generates its own targeted retrieval query rather than sharing a single query across all programs. This prevents Medicaid-specific policy text from contaminating SNAP or LIHEAP scoring.

**Hybrid cross-check** — rather than trusting the LLM alone, every eligibility decision is independently scored by a deterministic rule engine. Missing or contradictory evidence is meant to surface as caveats, `possible_match` outcomes, or human-followup signals rather than as overconfident ranking. This limits false positives in a high-stakes context.

**Incremental indexing** — early versions rebuilt the entire vector index on every document upload. Phase 3 replaced this with `append_document_to_policy_index()`, which embeds only the new document's chunks and appends them — making uploads fast even with a large existing corpus.

**Multi-turn intake** — the system does not fail silently when required fields are missing. It detects which fields are absent and generates specific follow-up questions, supporting up to 4 clarification rounds before proceeding with `insufficient_data` status.

### Phase 3 changes from Phase 2

| Area | Change |
|---|---|
| Retrieval | Per-program query generation (was: single shared query) |
| Indexing | Incremental append on upload (was: full rebuild) |
| UI | Program selector added to sidebar |
| Scoring | Retrieval bonus double-count removed (BUG-02) |
| Sorting | Program sort key unified with priority order (BUG-03) |
| Retrieval | Medicaid terms moved to Medicaid-only query layer (BUG-04) |
| Naming | LIHWAP / LIHEAP disambiguation fixed (BUG-06) |
| Testing | Cross-test contamination from uploaded files fixed (BUG-07) |

---

## 4. Evaluation

### 4.1 Methodology

10 evaluation cases covering: standard success cases (complete intake, clear program match), multi-turn intake cases (income withheld initially), edge cases (pregnancy pathway, children-only coverage), and failure cases (missing income, contradictory data, out-of-county input).

Each case was run through the live application and evaluated against expected behavior: whether intake completed correctly, whether the right programs were recommended, and whether the decision status accurately reflected system confidence. The evaluator treats eligibility correctness separately from priority-order limitations: recommended-program correctness is primary, while priority order is checked only directionally through limited acceptable top-priority sets rather than exact full-ranking matches.

### 4.2 Results Summary

| Case | Type | Outcome | Decision Status |
|---|---|---|---|
| AGENT_01 | success | PASS | ambiguous |
| AGENT_02 | success | FAIL | ambiguous |
| AGENT_03 | edge | FAIL | ambiguous |
| AGENT_04 | success (multi-turn) | PASS | ambiguous |
| AGENT_05 | success (multi-turn) | PASS | ambiguous |
| AGENT_06 | failure (missing income) | FAIL | ambiguous |
| AGENT_07 | success | FAIL | ambiguous |
| AGENT_08 | failure (contradictory data) | PASS | ambiguous |
| AGENT_09 | success | PASS | ambiguous |
| AGENT_10 | failure (out-of-county) | PASS | ambiguous |

**6 PASS / 4 FAIL**

The checked-in `eval/evaluation_results.csv` reflects the latest completed evaluation run with the current best configuration. `AGENT_01`, `AGENT_04`, `AGENT_05`, `AGENT_08`, `AGENT_09`, and `AGENT_10` now pass, while the remaining failures cluster around one no-match guardrail case, one incomplete-intake detail case, and two reviewer-facing priority or explanation alignment cases rather than exact legal eligibility determination.

### 4.3 Notable findings

- AGENT_10 is the clearest governance improvement from the recent patch: the out-of-county case now stops before normal recommendation flow and passes evaluation.
- AGENT_08 is now aligned with the intended safety behavior: contradictory intake suppresses normal actionable recommendations, returns `needs_human_followup`, and passes the current evaluation package.
- AGENT_02 remains the clearest false-positive regression in the checked-in run: the system still recommends programs on a case that should produce a clean no-match outcome.
- AGENT_03 and AGENT_07 now stand out as the clearest remaining reviewer-facing priority-order misses.

---

## 5. Failure Analysis

### GOV-01 — Out-of-County Inputs Now Stop Before Normal Recommendations (AGENT_10) — Severity: Mitigated

A Philadelphia household description is now flagged as outside the supported county scope, and the runtime stops before normal recommendation flow.

**Root cause before the patch:** Intake scope detection existed, but the pipeline did not short-circuit after that warning.

**Current behavior:** Intake marks the case `insufficient_data`, the final response is `needs_human_followup`, and the system withholds normal recommendations and normal `priority_order`. This case now passes the evaluator.

**Remaining risk:** Unsupported geography phrased in ways the intake parser misses could still evade the guard.

### GOV-02 — Contradictory Core Intake Is Suppressed Before Actionable Recommendations (AGENT_08) — Severity: Mitigated

A user reported full-time employment with zero earned income this month. The runtime now preserves the contradiction, suppresses normal actionable recommendations, and surfaces `needs_human_followup`.

**Root cause before the patch:** The pipeline could continue into recommendations even when core income and employment evidence conflicted.

**Current behavior:** The evaluator now records this case as PASS because contradiction handling suppresses normal recommendations until the conflict is resolved.

**Remaining risk:** Other contradiction patterns may still need explicit coverage in intake validation.

### LIMIT-01 — Clear No-Match Guardrail Still Regresses on a High-Income Insured Adult (AGENT_02) — Severity: High

The high-income insured adult case should return a clean no-match result, but the current run still surfaces `Medicaid/CHIP`, `LIHEAP`, and `SNAP` as `possible_match` recommendations.

**Root cause:** The current scoring and retrieval path still produces false-positive secondary match signals on this guardrail case.

**Current behavior:** The evaluator still marks this case FAIL because `SNAP` and `LIHEAP` should not be recommended here.

**Remaining risk:** This remains the clearest false-positive risk in the current best run.

### LIMIT-02 — Pregnancy Pathway Case Still Misranks Priority and Misses Explanation Detail (AGENT_03) — Severity: Medium

The pregnancy-specific health coverage case still fails because `LIHEAP` is ranked first, secondary programs are over-surfaced, and the explanation misses the term `pregnancy`.

**Root cause:** The current ranking and explanation path still underweights the pregnancy-specific Medicaid pathway and over-surfaces secondary programs.

**Current behavior:** The evaluator still marks the case FAIL because `Medicaid/CHIP` should be the primary review candidate in this scenario.

**Remaining risk:** This is the clearest remaining priority-order limitation in the current best run.

### LIMIT-03 — Graceful Degradation Is Safe but Still Misses Expected Detail (AGENT_06) — Severity: Low

When the user declined to share income after two turns, the system correctly avoided false program matches and returned caveated fallback guidance. The remaining gap is that the evaluator still sees the case as under-specified.

**Root cause:** Intake still stays at `needs_clarification` and omits `num_adults` from `missing_fields`, while the reviewer expectation for this case is `insufficient_data` plus a fuller missing-field list.

**Current behavior:** The evaluator still marks the case FAIL even though the runtime remains conservative and suppresses normal recommendations.

**Remaining risk:** The safe degradation path is better than before, but intake-state and missing-field detail remain inconsistent.

### LIMIT-04 — Uninsured-Children Case Still Over-Prioritizes LIHEAP Ahead of Health Coverage (AGENT_07) — Severity: Medium

The uninsured-children case still recommends `LIHEAP`, `SNAP`, and `Medicaid/CHIP`, but the evaluator rejects the ordering because `LIHEAP` is ranked first instead of `Medicaid/CHIP` or `SNAP`.

**Root cause:** The current priority heuristic still overweights a secondary hardship signal relative to the health-coverage need in this scenario.

**Current behavior:** The evaluator still marks this case FAIL because the review order does not match the intended triage emphasis for uninsured children.

**Remaining risk:** This remains a reviewer-facing priority-order miss even though the program set itself is otherwise plausible.

---

## 6. Governance and Safety

| Principle | Implementation |
|---|---|
| No false authority | All outputs include "This is prescreening only" disclaimer; system never claims to make official determinations |
| Conservative by default | LLM defaults to `possible_match` when evidence is present but thresholds are unclear; rule cross-check required before surfacing confident results |
| Transparent uncertainty | `decision_status: ambiguous` and `delivered_with_uncertainty` are surfaced to the user, not hidden |
| Scope limiting | Program selector allows scoping to only relevant programs; avoids returning matches for programs not applicable to the user's situation |
| No PII retention | Intake profiles exist only in session memory; no user data is written to disk or logged |
| Human escalation path | Every output includes "Next Steps" pointing to real offices and phone numbers — the system is designed to route users to human caseworkers, not replace them |

---

## 7. Lessons Learned

**Hybrid scoring is worth the complexity.** Running a deterministic rule engine alongside the LLM and surfacing uncertainty through `possible_match`, caveats, and human-followup signaling — rather than just trusting the LLM — caught several cases where the system would otherwise be too confident. The cross-check adds latency but meaningfully reduces false positives.

**Per-program retrieval prevents cross-contamination.** When we used a single shared retrieval query, Medicaid-specific sections were being retrieved and used to score SNAP eligibility. Moving to program-specific queries, each generated from the intake profile and program context, significantly improved the relevance of cited policy sections.

**Multi-turn intake works but needs better failure guidance.** The clarification chat correctly held the pipeline back when income was missing and successfully resolved the case after a second turn. The failure mode — when the user refuses to share income entirely — produces safe but unhelpful output. Graceful degradation needs a richer fallback path.

**Intake-level validation gaps are high-risk.** The out-of-county case showed that a governance issue can sit outside retrieval and scoring entirely. The recent patch fixed the direct AGENT_10 failure by stopping normal recommendation flow, but it also highlighted how much of the remaining evaluation drift now lives in fallback extraction and state-setting rather than in ranking alone.

**Index management needs attention at scale.** Early versions rebuilt the full 2,191-chunk vector index on every document upload. This was too slow for a live demo. The switch to incremental appending (embed only new chunks, append to existing index) made uploads instant — but it also means the index can accumulate stale or duplicate entries if documents are re-uploaded. Version tracking for the index is a future need.
