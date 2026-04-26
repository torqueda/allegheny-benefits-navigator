# Retrieval-Grounded, Agent-Assisted Policy Navigator

This folder contains an upgraded version of the original deterministic
prototype. It preserves the three-stage user workflow:

`intake -> eligibility_and_prioritization -> checklist_and_explanation`

but adds two new capabilities:

- a local retrieval layer grounded in stored policy text
- a policy-ingestion agent for newly provided policy documents

## What This Version Demonstrates

- structured user intake
- retrieval-grounded policy matching
- agent-style modular orchestration
- checklist and explanation generation with evidence snippets
- local ingestion of new policy text during the demo

## Safety Boundaries

- Prescreening and next-step guidance only
- Not an official eligibility determination
- Uploaded policies are treated as supporting context, not authoritative legal
  advice
- Ambiguous or newly ingested policies should still trigger caveats and human
  follow-up when appropriate

## Project Layout

- `app.py`: Streamlit demo
- `scripts/`: crawling and cleaning utilities for building the local policy
  corpus
- `src/rgnavigator/`: upgraded code
- `data/policy_corpus/`: local stored policy text used for retrieval
  - `snap_v8_handbook/`: cleaned handbook chapters used for main retrieval
  - `snap_v8_glossary/`: glossary and popup definitions kept as auxiliary text
- `data/raw_policy_downloads/`: raw downloaded handbook pages before cleaning
- `data/uploaded_policies/`: ingested policy text added during runtime
- `data/program_profiles.json`: structured program profiles for matching,
  prioritization, and checklist generation
- `data/agent_test_cases.json`: natural-language demo and evaluation cases used
  by the current app/test flow
- `data/test_cases.csv` and `data/expected_results.csv`: legacy structured
  fixtures kept for reference only
- `Retrieval-Grounded Policy Navigator.html` and
  `Retrieval-Grounded Policy Navigator_files/`: saved browser export artifacts,
  not runtime code

## Run The Demo

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Embeddings

The retrieval index is designed to use OpenAI embeddings by default.

Set the following in `.env` before rebuilding the policy index:

```bash
OPENAI_API_KEY=your_key_here
POLICY_EMBEDDING_PROVIDER=openai
```

Optional local fallback is available only if you explicitly enable it:

```bash
POLICY_ALLOW_LOCAL_EMBEDDING_FALLBACK=true
```

If you want to rebuild the index after changing the embedding setup:

```bash
python3 -c "from src.rgnavigator.policy_store import build_and_save_policy_index; print(build_and_save_policy_index())"
```

## Optional API-Ready Extension

The current upgraded version is organized so an API-backed policy extractor or
language-polish step can be attached later. The policy-ingestion and
checklist/explanation stages are the most natural places to add that behavior.

## Current Decision Flow

The current project is hybrid, not purely rule-based and not purely LLM-based:

- `run_intake()` starts from plain-language input, normalizes it into a
  structured profile, and optionally lets an LLM fill fields when an API key is
  available
- `run_eligibility_and_prioritization()` retrieves policy chunks first, then
  uses an LLM-grounded program evaluation when available
- the older rule-based scoring is still present as a fallback and as a
  cross-check against the retrieval-grounded LLM result
- `run_checklist_and_explanation()` turns those structured results into user-
  facing explanations, with an optional LLM polish step

If you are trying to understand "what is current" versus "what is legacy," see
`docs/PROJECT_OVERVIEW.md`.

## Building A Better Corpus

If you want to replace the initial policy briefs with real handbook content, use
the scripts documented in `docs/CORPUS_BUILDING.md`.

To split a cleaned handbook corpus into main handbook chapters and glossary popup
entries, run:

```bash
python3 scripts/split_handbook_corpus.py \
  --source-dir "data/policy_corpus/snap_v8_clean" \
  --handbook-dir "data/policy_corpus/snap_v8_handbook" \
  --glossary-dir "data/policy_corpus/snap_v8_glossary"
```
