# AI Usage Log

**Project:** Retrieval-Grounded Policy Navigator
**Track:** A — Agentic Systems Studio
**Team:** Yuhan, Tomas

This document records every use of AI models in building and running this system — model roles, prompt strategies, known failure modes, and governance decisions.

---

## Runtime Models (Used at Inference Time)

### 1. `gpt-4o-mini` — Intake Extraction

**Where:** `src/rgnavigator/intake_agent.py`

**What it does:** Given a free-text household narrative and any structured fields the user filled in, extracts a normalized `UserIntake` profile — household size, income, employment status, insurance status, and special signals (pregnancy, utility crisis, food insecurity, recent job loss). Also generates clarification questions when required fields are missing.

**Prompt strategy:** System prompt specifies the exact JSON schema of `UserIntake` and instructs the model to extract only what is explicitly stated in the user's input — not to infer or guess missing fields. This prevents the model from filling in plausible-sounding but unconfirmed values.

**Fallback:** If no API key is present or the call fails, regex-based field extraction is used. This is less accurate — particularly for implicit signals like "I'm behind on my gas bill" mapping to `heating_assistance_need`.

---

### 2. `gpt-4o-mini` — Eligibility Scoring

**Where:** `src/rgnavigator/eligibility_agent.py`

**What it does:** For each program in scope, scores eligibility as `strong_match`, `possible_match`, or `no_clear_match` using retrieved policy chunks as grounding context. Produces a rationale with specific policy section references (e.g., "SNAP §568 Appendix A income limits").

**Prompt strategy:** Each program is evaluated in its own independent call — no cross-program context. The system prompt instructs the model to cite the specific policy section that supports each determination, and to default to `possible_match` (not `strong_match`) when thresholds are close or evidence is partial. This conservative default is intentional: we would rather understate confidence than overstate it.

**Fallback:** If LLM call fails, rule-based scoring is used exclusively and `decision_status` is set to `rule_only`.

---

### 3. `gpt-4o-mini` — Explanation Generation

**Where:** `src/rgnavigator/explanation_agent.py`

**What it does:** Takes ranked program matches and retrieved policy evidence. Produces plain-language eligibility summary, next steps, itemized application checklist, and visible caveats.

**Prompt strategy:** System prompt instructs the model to write at approximately a 6th-grade reading level, avoid legal jargon, and include the policy citations already present in the retrieved evidence. The model is explicitly told it is writing prescreening output — not legal advice — and must include the standard disclaimer.

**Fallback:** Template-rendered string output when no API key is present.

---

### 4. `text-embedding-3-small` — Policy Retrieval Index

**Where:** `src/rgnavigator/policy_store.py`

**What it does:** Embeds all 2,191 policy document chunks (SNAP v8, Medicaid/CHIP, LIHEAP PA DPW manuals) into a local vector index. At query time, encodes per-program retrieval queries and retrieves the top-k most relevant chunks by cosine similarity.

**Index management:** Built once and saved to disk. New uploaded documents are appended incrementally — only the new document's chunks are re-embedded, not the full corpus.

**Fallback:** If no API key is present, hashed bag-of-words (`hashed-bow-v1`) embeddings are used. Retrieval quality is significantly lower; policy sections may be irrelevant or missing.

---

## Rule-Based Cross-Check (No AI)

**Where:** `src/rgnavigator/eligibility_agent.py` — `_rule_score()` function

A deterministic scoring function that applies explicit program eligibility rules from `data/program_profiles.json` — income thresholds by household size, insurance requirements, energy and food need signals. Scores are compared against LLM scores after each program evaluation:

- LLM and rules agree → `decision_status: ready_for_explanation`
- LLM and rules disagree → `decision_status: ambiguous`

This is not an AI model. It is included here because it directly controls how AI outputs are presented to users.

---

## Governance Decisions

| Decision | Rationale |
|---|---|
| LLM output always cross-checked against rules | Prevents LLM overconfidence from producing false positives in high-stakes prescreening |
| `gpt-4o-mini` over `gpt-4o` | Cost and latency — eligibility scoring requires parallel per-program calls; `gpt-4o-mini` is sufficient for structured extraction and scoring |
| Retrieval is per-program, not shared | Prevents Medicaid-specific policy text from influencing SNAP or LIHEAP scoring |
| LLM defaults to `possible_match` when uncertain | Conservative bias — understate confidence rather than overstate it |
| Clarification triggered only on specific missing fields | Avoids unnecessary questions when the narrative provides sufficient context |
| All outputs include prescreening disclaimer | System never represents results as official eligibility determinations |
| No user data written to disk | Intake profiles exist only in session memory; no PII is logged or persisted |

---

## Known AI Failure Modes (from Evaluation)

See `eval/failure_log.md` for full details.

- **FAILURE-01** — LLM intake extraction does not validate county against a supported list. Philadelphia input is accepted and processed as if it were Allegheny County.
- **FAILURE-02** — LLM does not detect contradictory structured inputs (full-time employed + zero income). It flags `needs_clarification` but does not halt the pipeline or prompt the user to resolve the conflict.
- **FAILURE-03** — LLM explanation agent produces minimal output when intake status is `insufficient_data`. No actionable fallback guidance is generated.

---

## Tools Used in Development (Not Runtime)

- **Claude (Anthropic)** — Used during development for code review, architecture discussion, evaluation case design, and documentation drafting. Not invoked at inference time by the application.
- **GitHub Copilot** — Not used.
- **ChatGPT** — Not used.
