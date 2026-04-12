# Allegheny Benefits Navigator

Prototype for a bounded benefits prescreening and next-step guidance system for Allegheny County households.

## Prototype scope
Initial prototype:
- 3 components: Intake, Eligibility + Prioritization, Checklist + Explanation
- deterministic eligibility logic
- transparent prioritization heuristics
- template-first checklist and explanation
- synthetic test-case evaluation

## Architecture
The prototype uses a plain Python sequential controller:

intake() -> eligibility_and_prioritization() -> checklist_and_explanation()

### Component boundaries
- **Intake** handles structured input only.
- **Eligibility + Prioritization** handles deterministic decision logic only.
- **Checklist + Explanation** handles communication only.

## Current build plan
Phase 1 Codex scaffolding should:
- generate typed Pydantic models
- generate session-state models
- generate tests for model validation and serialization
- avoid business logic in the first pass

Later passes will add:
- CSV loaders
- pipeline/controller skeleton
- deterministic component logic
- logging and evaluation output

## Repo structure
- `docs/` design inputs and schemas
- `data/` test cases and expected results
- `src/` code
- `tests/` automated tests

## Important design constraints
- This system is for prescreening and next-step guidance only.
- It must never present results as official eligibility determinations.
- Eligibility logic must remain deterministic.
- Any future LLM usage must be limited to wording polish or ambiguity phrasing, not core eligibility decisions.

## Quick start
1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Keep design changes in `docs/` and evaluation inputs in `data/`.
4. Use Codex to scaffold typed models before implementing pipeline logic.

## Current status
Repository initialized for prototype scaffolding with Codex.

## Out of scope
- official eligibility determinations
- application submission
- legal advice
- counties beyond Allegheny in v1
