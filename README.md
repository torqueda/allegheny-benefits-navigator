# Retrieval-Grounded, Agent-Assisted Policy Navigator

**Track A — Agentic Systems Studio | Phase 3 Final Submission**
**Team:** Yuhan, Tomas

This folder contains the Phase 3 upgraded version of the Allegheny Benefits Navigator. It adds a local retrieval layer grounded in real PA DPW policy text and a multi-agent pipeline with LLM + rule-based cross-checking.

---

## What This Version Demonstrates

- Structured user intake with multi-turn clarification chat
- Retrieval-grounded policy matching (per-program RAG queries against PA policy corpus)
- Hybrid LLM + rule-based cross-check producing explicit confidence signals
- Checklist and explanation generation with policy citations
- Incremental policy ingestion (no full index rebuild on upload)
- Program selector UI to scope which programs are evaluated

## Architecture

Three-agent pipeline:

```
Intake Agent → Eligibility Agent (RAG + Rule Cross-Check) → Explanation Agent
```

- **Intake Agent** — extracts structured profile from free-text narrative; triggers clarification chat when required fields are missing
- **Eligibility Agent** — retrieves policy chunks per program, scores with LLM, cross-checks against deterministic rule engine; outputs `decision_status: ready_for_explanation` (agree) or `ambiguous` (disagree)
- **Explanation Agent** — generates plain-language summary, next steps, checklist, and caveats with policy section citations

See [`docs/pipeline_diagram.png`](docs/pipeline_diagram.png) for a visual overview.

## Evaluation Summary (Phase 3)

10 evaluation cases across success, edge, and failure scenarios:

| Outcome | Count |
|---|---|
| PASS | 7 |
| PARTIAL | 2 |
| FAIL | 1 |

Known open failures:
- **FAILURE-01** — Out-of-county input not detected (Philadelphia case processed as Allegheny)
- **FAILURE-02** — Contradictory structured inputs not explicitly challenged
- **FAILURE-03** — Graceful degradation produces minimal output when income withheld

See [`eval/evaluation_results.csv`](eval/evaluation_results.csv) and [`eval/failure_log.md`](eval/failure_log.md) for full details.

## Safety Boundaries

- Prescreening and next-step guidance only — not an official eligibility determination
- All outputs include explicit disclaimer
- Ambiguous or low-confidence results surface `delivered_with_uncertainty` status and caveats

## Project Layout

```
app.py                          Streamlit demo UI
src/rgnavigator/                Agent pipeline source code
  intake_agent.py               Intake extraction + clarification chat
  eligibility_agent.py          RAG retrieval + LLM scoring + rule cross-check
  explanation_agent.py          Plain-language output generation
  policy_store.py               Vector index management (build, append, query)
data/
  policy_corpus/                PA DPW policy text used for retrieval
  program_profiles.json         Structured program rules and thresholds
  agent_test_cases.json         Demo and evaluation case fixtures
docs/
  pipeline_diagram.png          Architecture diagram
  screenshots/                  Annotated UI screenshots from Phase 3 evaluation
    screenshot_index.md         Index describing each screenshot
eval/
  evaluation_results.csv        10-case evaluation results
  failure_log.md                Bug fixes and known failure analysis
  version_notes.md              Phase 3 changelog from Phase 2 prototype
media/
  demo_video_link.txt           Link to 5-minute demo video
outputs/
  sample_runs/                  PDF exports from selected demo runs (AGENT_02, AGENT_04)
scripts/                        Corpus crawling and cleaning utilities
```

## Run The Demo

```bash
pip install -r requirements.txt
cp .env          # add your OpenAI API key
streamlit run app.py
```

## Embeddings

Requires an OpenAI API key for full accuracy. Set in `.env`:

```bash
OPENAI_API_KEY=your_key_here
```

Local fallback (hashed bag-of-words) is available but significantly less accurate:

```bash
POLICY_ALLOW_LOCAL_EMBEDDING_FALLBACK=true
```

To rebuild the policy index after changes:

```bash
python3 -c "from src.rgnavigator.policy_store import build_and_save_policy_index; print(build_and_save_policy_index())"
```
