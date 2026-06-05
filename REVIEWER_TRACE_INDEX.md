# Reviewer Trace Index

The compact reviewer trace is the fastest way to inspect the project’s main technical contribution:

`raw input -> intake object -> retrieved chunks -> deterministic rules -> cross-check status -> final explanation`

## Where to Look

In the app:
- Open the `Reviewer trace` expander after a screening run.

Checked-in trace artifacts:
- [outputs/sample_runs/agent_02_reviewer_trace.json](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/outputs/sample_runs/agent_02_reviewer_trace.json)
- [outputs/sample_runs/agent_03_reviewer_trace.json](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/outputs/sample_runs/agent_03_reviewer_trace.json)
- [outputs/sample_runs/agent_04_reviewer_trace.json](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/outputs/sample_runs/agent_04_reviewer_trace.json)
- [outputs/sample_runs/agent_06_reviewer_trace.json](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/outputs/sample_runs/agent_06_reviewer_trace.json)
- [outputs/sample_runs/agent_10_reviewer_trace.json](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/outputs/sample_runs/agent_10_reviewer_trace.json)

Markdown companions:
- `outputs/sample_runs/*_reviewer_trace.md`

## What the Trace Shows

- `raw_input`
- `intake_object`
- `retrieved_chunks`
- `program_scores`
- `cross_check_result`
- `final_recommendations`
- `final_decision`
- `final_explanation`
- `human_followup_or_caveats`

## Regenerate

```bash
OPENAI_API_KEY='' .venv/bin/python scripts/export_reviewer_trace.py AGENT_04
```

## Offline Honesty

Offline runs do not invent live LLM evidence. In offline mode the trace shows:
- `llm_mode = offline_or_rule_only_fallback`
- `llm_match_score = null`
- `cross_check_status = rule_only_fallback` or `uploaded_policy_rule_only`
