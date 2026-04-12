# AGENTS.md

## Project expectations
This repository contains a deterministic prototype for a benefits eligibility navigator.

## Architecture rules
- Preserve the 3-component flow:
  intake() -> eligibility_and_prioritization() -> checklist_and_explanation()
- Do not collapse component boundaries unless explicitly requested.
- Eligibility decisions must remain deterministic.
- LLM usage, if added later, must be limited to wording polish or ambiguity phrasing.

## Implementation rules
- Use Python 3.11.
- Use Pydantic models for shared schemas and component contracts.
- Put shared enums in `src/models/common.py`.
- Use these enums:
  - IntakeStatus
  - ProgramStatus
  - DecisionStatus
  - FinalStatus
- Keep business logic separate from data models.
- Prefer explicit typed models over unstructured dicts.

## Schema authoring rules
- Treat `SESSION_SCHEMA.json` as an authoritative example payload for code generation.
- Do not encode enum options as pipe-delimited union strings in `SESSION_SCHEMA.json`.
- Use one valid placeholder value in `SESSION_SCHEMA.json` for every enum-backed field.
- Put enum definitions and allowed values in `src/models/common.py`, not in JSON example payloads.
- Keep `SESSION_SCHEMA.json` aligned with the session-state handoff shape used across components.

## Data rules
- `data/test_cases.csv` and `data/expected_results.csv` are authoritative evaluation inputs.
- Rules are authored in spreadsheets and exported to structured JSON.
- Do not infer missing policy rules that are not documented.

## Evaluation fixture conventions
- Treat `case_id` as the primary key for evaluation rows.
- In `data/test_cases.csv`, use strict lowercase booleans: `true` / `false`.
- In `data/test_cases.csv`, encode `missing_fields` and `contradictory_fields` as JSON-array strings.
- In `data/test_cases.csv`, use `[]` to represent no missing or contradictory fields.
- In `data/expected_results.csv`, keep intentionally blank fields blank.
- Loaders must interpret blank expected-result fields as “no expected value provided”, not as errors.
- In `data/expected_results.csv`, use strict lowercase booleans for `expected_uncertainty_flag`: `true` / `false`.
- In `data/expected_results.csv`, encode `expected_priority_order` using the delimiter format `Program A > Program B > Program C`.
- Loaders must parse blank `expected_priority_order` as an empty list.
- Loaders must parse non-blank `expected_priority_order` by splitting on ` > `.

## Safety rules
- Never present results as official eligibility determinations.
- Preserve uncertainty flags and caveats in user-facing outputs.
- Do not fabricate local referral details or checklist requirements.

## Testing rules
- Add tests for models and loaders before implementing full pipeline logic.
- Prefer small, high-confidence changes.
- Add loader tests that verify evaluation fixture normalization and parsing behavior.
