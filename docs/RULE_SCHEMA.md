# Rule Schema

This document defines the normalized structure for program rules, checklist mappings, priority heuristics, and source metadata.

## Design principles
- Rules are curated from official sources.
- Rules are encoded in structured form for deterministic evaluation.
- Ambiguous or incomplete edge cases should be represented explicitly rather than guessed.
- Every rule should link back to at least one source record.

## Runtime rule object
Each program should export to JSON with the following top-level structure:

- program_id
- program_name
- version
- geography_scope
- policy_effective_date
- sources[]
- eligibility_rules[]
- checklist_items[]
- priority_heuristics[]
- notes

## Source object
Each source record should include:
- source_id
- source_title
- source_url
- source_type
- accessed_date
- effective_date
- notes

## Eligibility rule object
Each eligibility rule should include:
- rule_id
- rule_type
- field_name
- operator
- value
- value_units
- applies_when
- outcome_if_true
- uncertainty_if_missing
- severity
- source_id
- source_note

Allowed rule_type values:
- inclusion
- exclusion
- ambiguity
- priority_signal

## Checklist item object
Each checklist item should include:
- item_id
- document_name
- document_type
- required_or_likely
- applies_when
- source_id
- notes

## Priority heuristic object
Each priority heuristic should include:
- heuristic_id
- signal_name
- condition
- weight
- reason_text
- notes

## Spreadsheet-to-JSON mapping
The Excel authoring layer should be normalized into:
- one row per source
- one row per eligibility rule
- one row per checklist item
- one row per priority heuristic

The runtime should not parse narrative policy prose directly.
Narrative source briefs are for human review; structured rule rows are for code.
