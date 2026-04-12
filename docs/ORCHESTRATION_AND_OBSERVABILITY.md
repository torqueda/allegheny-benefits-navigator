# Orchestration and Observability

This document defines how components hand off state, when the system escalates or stops, what gets logged during execution, and what is visible to the user.

## Handoff contracts

### Intake -> Eligibility + Prioritization

Handoff occurs when one of the following is true:
- `intake.intake_status == "complete"`
- `intake.intake_status == "needs_clarification"` and the test harness is intentionally evaluating ambiguity handling

Required handoff fields:
- `household_profile`
- `missing_fields`
- `contradictory_fields`
- `validation_warnings`
- `intake_status`

### Eligibility + Prioritization -> Checklist + Explanation

Handoff occurs when one of the following is true:
- `decision_status == "ready_for_explanation"`
- `decision_status == "ambiguous"` and there is still enough signal to present bounded recommendations with caveats

Required handoff fields:
- `program_assessments`
- `uncertainty_flags`
- `priority_order`
- `priority_rationale`
- `decision_status`

## Triggers

### Clarification trigger
Trigger clarification when one or more of the following occurs:
- a required field is missing
- household data is contradictory
- a field value has an invalid type or invalid range

### Ambiguity trigger
Trigger ambiguity when one or more of the following occurs:
- a case is near a rule threshold
- evidence is incomplete in a way that changes program status
- encoded rules conflict with available inputs
- local referral information is incomplete or not fully verified

### Early-stop trigger
Stop early when one or more of the following occurs:
- household data is too incomplete for meaningful prescreening
- the case is out of scope
- a system error occurs in rules loading or profile generation

### Human-followup trigger
Flag human follow-up when one or more of the following occurs:
- unresolved ambiguity remains after all checks
- the user asks for official determination or application action
- missing local information requires referral to external support

## Logging

Each run should log the following:

### Session metadata
- `session_id`
- `run_id`
- `case_id` if synthetic
- `mode`
- `app_version`
- `ruleset_version`
- `template_version`
- `llm_enabled`
- `llm_model`

### Intake log fields
- raw input snapshot
- normalized household profile
- missing fields
- contradictory fields
- validation warnings
- intake status

### Eligibility + Prioritization log fields
- per-program assessments
- matched conditions
- failed conditions
- missing evidence
- uncertainty flags
- priority order
- priority rationale
- decision status

### Checklist + Explanation log fields
- recommended programs shown
- checklist items generated
- visible caveats
- final explanation text
- final status

### Audit and timing fields
- component statuses
- timestamps
- per-component timings
- total runtime
- evaluation comparison fields after full run

## User-visible behavior

### What the user should see
- structured intake form
- clarification prompts if needed
- final ranked recommendations
- short explanation of why each recommendation may fit
- visible caveats and uncertainty
- likely-needed documents
- next steps
- reminder that this is prescreening, not an official determination

### What the user should not see
- raw rule evaluations
- internal heuristic scores
- hidden contradiction traces
- low-level debug logs unless an explicit evidence/debug view is added
