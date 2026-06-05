# Allegheny County Benefits Navigator

Allegheny County Benefits Navigator is a Streamlit-based benefits prescreening prototype for Allegheny County households. It turns a household narrative into structured intake data, retrieves local policy evidence, cross-checks deterministic rules against LLM-backed reasoning when available, and returns plain-language next-step guidance with caveats.

This is a course prototype for prescreening and reviewer inspection. It is not an official eligibility determination, legal advice tool, or application-submission system.

## Run the App

```bash
python3 -m venv .venv
source .venv/bin/activate
.venv/bin/pip install -r requirements.txt
touch .env
# optional: add OPENAI_API_KEY=your_key_here

streamlit run app.py
```

Notes:
- Without `OPENAI_API_KEY`, the app still runs in an offline/rule-first fallback mode.
- The checked-in evaluation flow is reproducible offline.
- The environment-dependent ingestion smoke test is intentionally excluded in offline review environments:

```bash
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_pipeline_smoke.py -k 'not ingested_policy_becomes_available_to_session' -q
```

That excluded test covers the embedding/index upload path and is not part of the professor-feedback regression set.

## Reviewer Quick Path

If you have five minutes:

1. Run the app with `streamlit run app.py`.
2. Load `AGENT_04` in the sidebar to see the multi-turn clarification flow.
3. Open the `Reviewer trace` expander after a run.
4. Review the evaluation package in [eval/README.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/eval/README.md).
5. Review trace artifacts in [REVIEWER_TRACE_INDEX.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/REVIEWER_TRACE_INDEX.md).

## Architecture

Main flow:

1. `app.py` collects narrative and optional structured overrides.
2. `intake_agent.py` extracts and validates the household profile.
3. `eligibility_agent.py` retrieves policy evidence, scores programs, applies guardrails, and ranks recommendations.
4. `explanation_agent.py` generates the plain-language explanation, next steps, checklist items, and caveats.
5. `traceability.py` builds the compact reviewer trace shown in the UI and exported to artifacts.

Key supporting docs:
- [docs/ARCHITECTURE.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/docs/ARCHITECTURE.md)
- [docs/AGENTIC_COORDINATION_WALKTHROUGH.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/docs/AGENTIC_COORDINATION_WALKTHROUGH.md)
- [docs/PRIVACY_SESSION_GOVERNANCE.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/docs/PRIVACY_SESSION_GOVERNANCE.md)

## Verification

Targeted regression suites:

```bash
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_suppression_guardrails.py -q
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_priority_ranking.py -q
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_intake_boundary_validation.py -q
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_session_privacy_controls.py -q
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_traceability.py -q
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_evaluation_artifacts.py -q
OPENAI_API_KEY='' .venv/bin/python -m pytest tests/test_pipeline_smoke.py -k 'not ingested_policy_becomes_available_to_session' -q
```

Evaluator:

```bash
OPENAI_API_KEY='' .venv/bin/python scripts/run_agent_test_cases.py
```

Current checked-in evaluator result: `10 PASS / 0 FAIL`.

Reviewer trace export:

```bash
OPENAI_API_KEY='' .venv/bin/python scripts/export_reviewer_trace.py AGENT_04
```

## Evidence Package

Core reviewer-facing evidence:
- [eval/README.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/eval/README.md)
- [eval/test_cases.csv](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/eval/test_cases.csv)
- [eval/evaluation_results.csv](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/eval/evaluation_results.csv)
- [eval/failure_log.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/eval/failure_log.md)
- [eval/version_notes.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/eval/version_notes.md)
- [REVIEWER_TRACE_INDEX.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/REVIEWER_TRACE_INDEX.md)
- [outputs/sample_runs](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/outputs/sample_runs)
- [data/evaluation_results_phase3.json](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/data/evaluation_results_phase3.json)

## Repo Guide

- [app.py](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/app.py): Streamlit entry point
- [src/rgnavigator](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/src/rgnavigator): core package
- [scripts](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/scripts): evaluation and export helpers
- [tests](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/tests): regression suites
- [assignment-docs](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/assignment-docs): course requirements, feedback, and saved prompt history

## Current Scope and Limitations

- This is prescreening only.
- The app is Allegheny County-specific and suppresses normal recommendations for out-of-scope geography.
- Offline mode is honest about missing live LLM cross-check evidence and trace fields.
- The upload/embedding smoke test remains environment-dependent and intentionally excluded in offline review runs.
