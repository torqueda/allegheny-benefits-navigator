# Component Specs

## Implementation notes

- Deterministic eligibility is authoritative.
- The explanation layer cannot override decision state.

## Component 1: Intake

### Purpose
- Collect structured household information through a form-first workflow.
- Validate field completeness and consistency.
- Produce a normalized household profile for downstream reasoning.
- Treat intake as a data-quality component, not a policy component.
- Do not make eligibility claims or prioritize programs.

### Inputs
- User-provided structured fields, including household composition, number of adults, number of children, pregnancy/young-child indicators, employment status, earned and unearned income, insurance status, housing and utility hardship indicators, ZIP code, and any optional notes relevant to ambiguity or stress.

### Outputs
- `IntakeOutput`
  - `household_profile`: validated `HouseholdProfile` with normalized fields
  - `missing_fields`
  - `contradictory_fields`
  - `validation_warnings`
  - `intake_status`: `complete | needs_clarification | insufficient_data`

### State read/write
- Read current session state only.
- Write the structured household profile, validation results, and clarification history to session memory.
- Do not persist data across sessions.
- Do not store personally identifying household data long term.

### Tools/data accessed
- form schema
- field validation rules
- contradiction rules
- optional ZIP/county lookup if implemented
- no eligibility rules
- no external writes

### Stop conditions
- All required fields are present and internally consistent; hand off to Eligibility + Prioritization.
- Too many required fields are missing; stop and request clarification.
- Geography is out of scope or the case type is unsupported; stop and return a bounded message.

### Escalation conditions
- contradictory inputs
- missing core income or household-size fields
- ambiguous coverage status that blocks core eligibility checks
- user attempts to use the system for official determination or application submission

### Logging fields
- `run_id`
- `case_id` if synthetic
- raw input snapshot
- normalized profile
- missing fields
- contradictory fields
- validation warnings
- intake status
- timestamp
- rule/schema version

### User-visible output
- A concise confirmation of captured household facts.
- One of the following:
  - “Thank you. I have enough information to continue.”
  - A short clarification request listing what is missing or inconsistent.

### Key risks
- incorrectly normalized user input
- missing critical fields that later cause false recommendations
- contradictory information passing through silently
- scope creep into policy reasoning

## Component 2: Eligibility + Prioritization

### Purpose
- Apply deterministic program rules to the household profile.
- Determine likely applicability for each in-scope program.
- Flag ambiguity conservatively.
- Rank likely relevant programs using transparent heuristics.
- Keep this component as the core decision layer and ensure it remains inspectable.
- Preserve the original eligibility emphasis on rule-grounded reasoning and ambiguity flags.
- Preserve the original prioritization emphasis on explainability and urgency-sensitive ordering.

### Prototype v1 note
- The initial build may cover 3 programs only.

### Inputs
- validated `HouseholdProfile`
- in-scope program rule files for SNAP, Medicaid/CHIP, LIHEAP, WIC, and one local referral pathway
- prioritization heuristics
- policy dates/source metadata

### Outputs
- `EligibilityPrioritizationOutput`
  - `program_assessments[]`
  - `eligible_or_likely_programs[]`
  - `inapplicable_programs[]`
  - `uncertainty_flags[]`
  - `priority_order[]`
  - `priority_rationale[]`
  - `decision_status`: `ready_for_explanation | ambiguous | insufficient_data`

### Program assessment shape
- `program_name`
- `status`: `likely_applicable | likely_inapplicable | uncertain`
- `matched_conditions`
- `failed_conditions`
- `missing_evidence`
- `notes_or_caveats`

### State read/write
- Read `HouseholdProfile` from session state.
- Write per-program assessments, ambiguity notes, and ranked recommendations back to session state.
- Do not persist state beyond the current run.

### Tools/data accessed
- structured rule store
- prioritization heuristic config
- official-source metadata
- optional local referral metadata
- no external APIs required in v1
- no application submission or external writes

### Stop conditions
- All in-scope programs are evaluated and ranking is generated; hand off to Checklist + Explanation.
- The case is too incomplete for reliable evaluation; return ambiguity or clarification state.
- No programs are likely applicable; still hand off with an empty recommendation set and explanatory notes.

### Escalation conditions
- rule conflict
- threshold-edge case
- missing data that materially changes applicability
- incomplete or unverified local referral information
- heuristic tie or instability in ranking

### Logging fields
- `run_id`
- `case_id`
- `household_profile_hash` or household profile snapshot
- `ruleset_version`
- policy source dates
- per-program outcomes
- matched conditions
- failed conditions
- uncertainty flags
- priority order
- priority rationale
- decision status
- timestamp

### User-visible output
- None directly in the core architecture.
- This component is primarily internal.
- At most, it can produce structured recommendation objects and short rationale strings for downstream use.

### Key risks
- outdated or misencoded rules
- overly brittle threshold logic
- under-triggering ambiguity in borderline cases
- ranking logic that fails to reflect real urgency
- accidental overclaiming if structured caveats are not preserved downstream

## Component 3: Checklist + Explanation

### Purpose
- Translate the structured recommendation state into actionable next steps.
- Map recommended programs to likely-needed documents and preparation steps.
- Generate a plain-language explanation that preserves uncertainty.
- Avoid official-determination language.
- Help the user act.

### Inputs
- `HouseholdProfile`
- `EligibilityPrioritizationOutput`
- document/checklist mappings per program
- explanation templates
- uncertainty notes/caveats
- optional LLM polishing layer for wording only; if used, the model name/version must be explicitly configured and logged

### Outputs
- `ChecklistExplanationOutput`
  - `recommended_programs[]`
  - `checklist_items_by_program{}`
  - `next_steps[]`
  - `user_explanation`
  - `visible_caveats[]`
  - `referral_notes[]`
  - `final_status`: `delivered | delivered_with_uncertainty | needs_human_followup`

### State read/write
- Read all upstream session state.
- Write final checklist, explanation, and visible caveats to session state.
- Do not persist state long term.

### Tools/data accessed
- program-specific checklist mappings
- explanation templates
- optional local language-polish model for wording only; model name/version must be explicit in configuration
- optional citation/source snippets if added later
- no fabricated local claims
- no legal advice
- no official eligibility determination

### Stop conditions
- Explanation and checklist are generated successfully; return final user-facing output.
- No likely programs are found; return a bounded “no clear match” explanation plus next-step guidance.
- Critical upstream state is missing; fail gracefully and request rerun or clarification.

### Escalation conditions
- checklist mapping missing for a recommended program
- uncertainty remains high and must be surfaced explicitly
- local referral information unverified
- output exceeds clarity or brevity threshold and requires template fallback

### Logging fields
- `run_id`
- `case_id`
- recommended programs shown
- checklist items generated
- caveats shown
- final explanation text
- template version
- `llm_used`
- `llm_model_name` if applicable
- `llm_model_version` if applicable
- final status
- timestamp

### User-visible output
- A concise, plain-language result page or message containing:
  - “Based on the information you provided, your household might be eligible for…”
  - ranked list of likely relevant programs
  - short explanation for each
  - documents to gather
  - next steps
  - visible uncertainty/caveat language
  - explicit reminder that this is not an official determination

### Key risks
- suppressing caveats
- overstating confidence
- incomplete checklist mappings
- generic or bureaucratic language
- mismatch between structured outputs and final narrative
