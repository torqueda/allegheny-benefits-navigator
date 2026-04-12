# Architecture

## Project summary
This project is a benefits eligibility navigator for low-income households in Allegheny County. The prototype helps users understand which public assistance programs they may be eligible for, which ones to prioritize first, and what documents and next steps they should prepare.

The system is intentionally bounded to prescreening and next-step guidance. It does not make official eligibility determinations, submit applications, provide legal advice, or replace caseworkers or benefits offices.

## Initial prototype architecture
The prototype uses a 3-component flow:

intake() -> eligibility_and_prioritization() -> checklist_and_explanation()

### 1) Intake
Collects and validates structured household information, checks for missing or contradictory fields, and outputs a normalized household profile.
It must not make eligibility claims.

### 2) Eligibility + Prioritization
Applies deterministic program rules to the household profile, flags ambiguity conservatively, and ranks likely-relevant programs using transparent heuristics such as urgency, likely usefulness, and application burden.
This is the core decision layer.

### 3) Checklist + Explanation
Takes structured outputs from the prior step, generates program-specific document checklists and next steps, and produces a plain-language explanation with visible caveats.
This component communicates results without inventing eligibility logic.

## Why this architecture instead of one larger program
The system is split into components because the task has different responsibilities with different failure modes.

- If Intake is merged into reasoning, incomplete or contradictory inputs can lead to policy assumptions.
- If reasoning is merged into explanation, caveats and uncertainty can be smoothed away in user-facing language.
- If everything is merged into one step, failures become harder to localize, test, and debug.

The value of the architecture is in the separation of concerns, inspectable handoffs, safer boundaries, and clearer evaluation.

## Deterministic core
The prototype keeps the policy logic deterministic:
- structured intake
- deterministic eligibility checks
- transparent prioritization heuristics
- template-based checklist generation
- template-first explanation

A lightweight LLM can be added later for wording polish or ambiguity phrasing, but it will not take over the actual eligibility decision responsibility.

## Prototype scope
For the first runnable prototype, we implement only a smaller subset of in-scope programs for faster testing. The architecture will still support expansion to the full intended program set later.