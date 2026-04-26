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
4. **Hybrid decision** — if LLM and rules agree → `ready_for_explanation`; if they disagree → `ambiguous`

Programs are then ranked by `priority_score` (a composite of match score, rule score, and retrieval signal strength).

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

**Hybrid cross-check** — rather than trusting the LLM alone, every eligibility decision is independently scored by a deterministic rule engine. Disagreements are surfaced explicitly as `ambiguous` rather than hidden. This limits false positives in a high-stakes context.

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

Each case was run through the live application and evaluated against expected behavior: whether intake completed correctly, whether the right programs were recommended, and whether the decision status accurately reflected system confidence.

### 4.2 Results Summary

| Case | Type | Outcome | Decision Status |
|---|---|---|---|
| AGENT_01 | success | PASS | ambiguous |
| AGENT_02 | success | PASS | ready_for_explanation |
| AGENT_03 | edge | PASS | ambiguous |
| AGENT_04 | success (multi-turn) | PASS | ambiguous |
| AGENT_05 | success (multi-turn) | PASS | ambiguous |
| AGENT_06 | failure (missing income) | PARTIAL | ambiguous |
| AGENT_07 | success | PASS | ambiguous |
| AGENT_08 | failure (contradictory data) | PARTIAL | ambiguous |
| AGENT_09 | success | PASS | ambiguous |
| AGENT_10 | failure (out-of-county) | FAIL | ambiguous |

**7 PASS / 2 PARTIAL / 1 FAIL**

`decision_status: ambiguous` appearing on most PASS cases is expected and correct behavior — it indicates that the LLM and rule engine scored programs differently in confidence level, not that the recommendation itself is wrong. The hybrid architecture is conservative by design.

### 4.3 Notable findings

- AGENT_02 cleanly returned `no_clear_match` for all programs on a high-income insured adult — the key test that the system avoids false positives. Both LLM and rules agreed, producing `ready_for_explanation`.
- AGENT_04 demonstrated correct multi-turn behavior: pipeline held back after Turn 1 (missing income), asked clarifying questions, and ran successfully after Turn 2.
- AGENT_03 correctly identified the pregnancy-specific Medicaid pathway even for an insured household — a non-obvious eligibility edge case.

---

## 5. Failure Analysis

### FAILURE-01 — Out-of-County Case Not Detected (AGENT_10) — Severity: High

A Philadelphia household description was accepted and processed without any warning. The system returned `strong_match` for Medicaid/CHIP — results that may not reflect Philadelphia County program rules or offices. County field defaults to Allegheny if not explicitly set; there is no validation step that checks whether the county is within scope.

**Root cause:** No county boundary check in intake agent. The intake schema accepts `county` as a free-text field but does not validate it against a list of supported counties.

**Mitigation in current version:** Output includes disclaimer "This is prescreening only. It is not an official eligibility determination." — but no county-specific warning.

**Planned fix:** Add explicit county check in intake agent. If county is outside Allegheny, surface a warning before running the pipeline rather than silently continuing.

### FAILURE-02 — Contradictory Data Not Challenged (AGENT_08) — Severity: Medium

A user reported full-time employment with zero earned income this month. The intake agent flagged `needs_clarification` but the pipeline ran anyway. The cross-check diverged on program scores and produced `ambiguous` output, but no message explained to the user what the contradiction was or asked them to resolve it.

**Root cause:** Contradiction detection is not implemented in the intake normalization step. The LLM extracts fields independently and does not compare them for consistency.

**Planned fix:** Add explicit contradiction detection in intake agent (e.g., `employment_status == full_time AND earned_income == 0`) that halts the pipeline and generates a targeted resolution prompt.

### FAILURE-03 — Graceful Degradation Produces Unhelpful Output (AGENT_06) — Severity: Low

When the user declined to share income after two turns, the system correctly reached `insufficient_data` status and did not produce false program matches. However, the output to the user was nearly empty — no actionable guidance, no suggested alternative paths (e.g., "contact a local caseworker").

**Root cause:** Explanation agent has no fallback template for `insufficient_data` cases. It renders minimal output because no program matches are present to explain.

**Planned fix:** Add a fallback guidance block for `insufficient_data` that surfaces general next steps regardless of whether program matches exist.

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

**Hybrid scoring is worth the complexity.** Running a deterministic rule engine alongside the LLM and surfacing disagreements as `ambiguous` — rather than just trusting the LLM — caught several cases where the LLM was overconfident on borderline incomes. The cross-check adds latency but meaningfully reduces false positives.

**Per-program retrieval prevents cross-contamination.** When we used a single shared retrieval query, Medicaid-specific sections were being retrieved and used to score SNAP eligibility. Moving to program-specific queries, each generated from the intake profile and program context, significantly improved the relevance of cited policy sections.

**Multi-turn intake works but needs better failure guidance.** The clarification chat correctly held the pipeline back when income was missing and successfully resolved the case after a second turn. The failure mode — when the user refuses to share income entirely — produces safe but unhelpful output. Graceful degradation needs a richer fallback path.

**Intake-level validation gaps are high-risk.** The out-of-county failure (FAILURE-01) is not a retrieval or scoring problem — it is an input validation problem. The system accepted a Philadelphia address and ran as if it were Allegheny County. Boundary checks need to happen before the pipeline runs, not after.

**Index management needs attention at scale.** Early versions rebuilt the full 2,191-chunk vector index on every document upload. This was too slow for a live demo. The switch to incremental appending (embed only new chunks, append to existing index) made uploads instant — but it also means the index can accumulate stale or duplicate entries if documents are re-uploaded. Version tracking for the index is a future need.
