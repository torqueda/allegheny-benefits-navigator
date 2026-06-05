# Project Overview

This note is meant to make the codebase easier to navigate now that it contains
both newer retrieval-grounded logic and some older deterministic scaffolding.

## Runtime Path

The current end-to-end flow is:

1. `app.py`
2. `src/rgnavigator/pipeline.py`
3. `src/rgnavigator/intake_agent.py`
4. `src/rgnavigator/eligibility_agent.py`
5. `src/rgnavigator/explanation_agent.py`

### `intake_agent.py`

- Main job: turn plain-language user input into `UserIntake`
- Current primary input: `user_description`
- Still supports optional structured override fields from the Streamlit form
- Uses:
  - regex/rule extraction from free text
  - optional LLM extraction when `OPENAI_API_KEY` is configured
- Output is structured and typed in `models.py`

### `eligibility_agent.py`

- Main job: choose likely programs and rank them
- Current logic is hybrid:
  - retrieval over local handbook chunks
  - LLM-grounded policy reading when API access is available
  - deterministic scoring fallback when LLM is unavailable
  - cross-check between LLM and rule-based results in `_cross_check()`

This file is where the "old rules" and the "new LLM/RAG flow" are most visibly
mixed together. That is intentional right now, but it also explains why the
module can feel harder to read than the others.

### `explanation_agent.py`

- Main job: convert ranked matches into a checklist, next steps, and a plain-
  language explanation
- Uses the structured output from eligibility
- Can optionally use an LLM to rewrite the final message in simpler user-facing
  language

## Data Directories

### `data/policy_corpus/`

- Cleaned markdown corpus used for retrieval
- `*_handbook/` directories are the main retrieval sources
- glossary/popups are auxiliary material

### `data/raw_policy_downloads/`

- Raw HTML downloaded by the scraper
- These are crawl artifacts, not what the app retrieves directly

### `data/policy_index/`

- Built retrieval index
- Includes chunk metadata plus embeddings

### `data/uploaded_policies/`

- Documents added at runtime through the ingestion tab

## Demo and Test Data

### Current

- `data/agent_test_cases.json`
- Natural-language, turn-based scenarios
- Used by the current demo loader and agent-style evaluation scripts

### Legacy

- `data/test_cases.csv`
- `data/expected_results.csv`

These are older structured fixtures from the more deterministic version of the
project. They are no longer the primary data path for the app or smoke tests.

## Scraping Artifacts

### `Retrieval-Grounded Policy Navigator.html`
### `Retrieval-Grounded Policy Navigator_files/`

These are not part of the runtime system.

They are the standard artifacts created by a browser "Save Page As" export of
the Streamlit app:

- the `.html` file is the saved page shell
- the `_files/` directory contains the bundled JS/CSS assets referenced by that
  HTML file

You can keep them as a snapshot/demo artifact, but the app does not import them
and the Python code does not depend on them.
