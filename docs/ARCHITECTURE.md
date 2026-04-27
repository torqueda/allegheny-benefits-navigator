# Upgraded Architecture

The upgraded project keeps the original three-stage user flow:

`intake -> eligibility_and_prioritization -> checklist_and_explanation`

It adds two new supporting capabilities:

- `policy_retrieval`: retrieves evidence from local policy text
- `policy_ingestion_agent`: stores newly provided policy documents and makes
  them available to retrieval

## Components

### 1. Intake Agent

- starts from natural-language household descriptions
- normalizes user input
- detects missing fields and contradictions
- produces a structured household profile
- can optionally use an LLM to extract fields more robustly when
  `OPENAI_API_KEY` is present

### 2. Policy Retrieval Layer

- loads local policy text from `data/policy_corpus/`
- loads newly ingested policy text from `data/uploaded_policies/`
- retrieves the most relevant chunks for the household context

### 3. Eligibility + Prioritization Agent

- retrieves program-relevant chunks from the local handbook corpus
- uses an LLM-grounded evaluation as the primary path when available
- keeps the older rule-based scorer as fallback and cross-check
- ranks likely matches
- marks uncertainty when evidence is incomplete or contradictory

Priority order is the order in which the navigator suggests a user review recommended programs first. It is based mainly on how likely the household appears to match each program and secondarily on immediate hardship signals such as food need, health coverage need, or heating need. It is a triage heuristic for follow-up, not an official statement of legal urgency, benefit amount, or application difficulty.

In practice, ranking is influenced by urgency and hardship signals, likely applicability, program profile fit, practical next-step value, and uncertainty handling. Missing or contradictory evidence should increase caveats or human follow-up rather than create overconfident ranking. See `docs/PRIORITY_HEURISTIC.md` for the reviewer-facing definition and evaluation note.

### 4. Checklist + Explanation Agent

- generates next steps and checklist items
- uses retrieved evidence snippets to ground the explanation
- preserves caveats and safety language

### 5. Policy Ingestion Agent

- accepts new policy text during the session
- stores the raw text locally
- makes the new document available to the retrieval layer immediately

## What Is Legacy vs Current

- Current user input path: natural language in `user_description`
- Current demo/test fixtures: `data/agent_test_cases.json`
- Legacy support path: manually entered structured fields in the UI
- Legacy evaluation logic: deterministic scoring inside
  `eligibility_agent.py`, now mainly used as fallback/cross-check
