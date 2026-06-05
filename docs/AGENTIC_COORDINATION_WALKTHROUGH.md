# Agentic Coordination Walkthrough

This walkthrough uses `AGENT_04` because it shows the project’s full clarification-to-recommendation flow in one case.

## Case

- Household in Pittsburgh
- One child
- Utility shutoff notice
- Income missing on turn 1, supplied on turn 2

## Flow

1. Intake extracts household structure and hardship signals from the first turn.
2. Intake stops and asks clarification questions because income is still missing.
3. After the second turn, intake becomes `complete`.
4. Eligibility retrieval and scoring run for SNAP, Medicaid/CHIP, and LIHEAP.
5. Explanation returns plain-language recommendations, next steps, and caveats.
6. The reviewer trace exposes the raw input, intake object, retrieved chunks, program scores, cross-check state, and final explanation.

## Current Evaluated Outcome

For the checked-in offline evaluation run:
- `intake_status = complete`
- `decision_status = ambiguous`
- `final_status = delivered_with_uncertainty`
- `recommended_programs = LIHEAP, Medicaid/CHIP, SNAP`

## Where to Inspect It

- [eval/evaluation_results.csv](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/eval/evaluation_results.csv)
- [outputs/sample_runs/agent_04_reviewer_trace.json](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/outputs/sample_runs/agent_04_reviewer_trace.json)
- [outputs/sample_runs/agent_04_reviewer_trace.md](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/outputs/sample_runs/agent_04_reviewer_trace.md)
- [app.py](/Users/tomasorqueda/Downloads/CMU/Agentic Technologies/Github Repo/allegheny-benefits-navigator-final/app.py)
