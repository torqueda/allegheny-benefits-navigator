# Agentic Coordination Walkthrough

This note gives one concise, current-repo example of the system's agentic coordination behavior.

## Walkthrough Case: AGENT_04

Case summary:
- User scenario: a Pittsburgh household with one child, a shutoff notice, and no income amount provided in the first turn
- Source fixture: `eval/test_cases.csv`
- Current evaluated result: PASS in `eval/evaluation_results.csv`

### 1. Intake behavior

The first user turn gives enough information to extract household structure and a utility-heating hardship signal, but not enough to complete intake. The intake stage therefore marks the case for clarification and asks follow-up questions instead of immediately running the rest of the pipeline.

Evidence:
- `eval/test_cases.csv`
- `docs/screenshots/multi_turn_dialogue.png`
- `app.py`
- `src/rgnavigator/intake_agent.py`

### 2. Eligibility and prioritization behavior

After the second turn supplies income information, the workflow advances to the main pipeline. The eligibility stage receives the normalized intake profile, runs per-program retrieval, evaluates SNAP, Medicaid/CHIP, and LIHEAP, and returns a ranked set of recommendations with `decision_status = ambiguous`.

Evidence:
- `eval/evaluation_results.csv`
- `data/evaluation_results_phase3.json`
- `src/rgnavigator/pipeline.py`
- `src/rgnavigator/eligibility_agent.py`

### 3. Checklist and explanation behavior

The explanation stage receives the intake and eligibility outputs and produces the user-facing explanation, next steps, checklist items, and caveats. The structured post-handoff output can be inspected in the debug screenshot.

Evidence:
- `docs/screenshots/output3.png`
- `src/rgnavigator/explanation_agent.py`

### 4. Uncertainty and final status

This case shows clarification and uncertainty, but not human-follow-up suppression. In the current checked-in results, AGENT_04 ends with:
- `intake_status = complete`
- `decision_status = ambiguous`
- `final_status = delivered_with_uncertainty`
- `recommended_programs = SNAP, Medicaid/CHIP, LIHEAP`

Evidence:
- `eval/evaluation_results.csv`
- `data/evaluation_results_phase3.json`
