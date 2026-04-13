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

## Current implementation
The repository now includes a runnable Phase 2 prototype:
- typed shared models with a lightweight fallback when `pydantic` is not installed
- CSV loaders for synthetic evaluation fixtures
- deterministic intake, eligibility/prioritization, and checklist/explanation components
- session-state trace generation for each synthetic case
- evaluation output written to `data/evaluation_results.csv`
- basic end-to-end tests using the Python standard library `unittest`

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
2. Install dependencies from `requirements.txt` if desired, though the current prototype can run in a standard-library-only environment.
3. Run `python3 -m unittest -q` to check the prototype tests.
4. Run `python3 -m src.evaluate` to execute the 10 synthetic cases and regenerate traces plus `data/evaluation_results.csv`.
5. Keep design changes in `docs/` and evaluation inputs in `data/`.

## Current status
Prototype implemented for the core Phase 2 flow, with 10/10 synthetic cases matching the expected evaluation fixture.

## Out of scope
- official eligibility determinations
- application submission
- legal advice
- counties beyond Allegheny in v1
