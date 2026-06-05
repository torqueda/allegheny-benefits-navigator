# PII TODO

This file tracks deferred privacy and PII-handling work for the program.

## Current decision

Hold off on implementing the final PII-handling model until all in-scope programs are included, so the team can see the full set of household data fields that may be collected.

## Questions to resolve later

- What exact household fields are required across all in-scope programs?
- Which fields are strictly necessary for screening, and which can be dropped?
- Which fields should remain only in transient memory during a live session?
- Which fields, if any, should be retained in derived or coarsened form only?
- What fields should be excluded from traces, debug views, exports, and sample artifacts?
- What additional consent or disclosure text is required before third-party API processing?

## Candidate PII-related work items

- Review every currently collected field in `app.py` and `UserIntake`.
- Classify fields as direct identifiers, quasi-identifiers, sensitive attributes, or non-sensitive operational metadata.
- Decide whether income should be:
  - stored only ephemerally,
  - converted into bands,
  - converted into per-program threshold flags,
  - or some combination of the above.
- Remove raw household data from any reviewer/debug output that would not be appropriate in production.
- Revisit `Session JSON` and `Reviewer trace` exposure for non-reviewer users.
- Define retention, deletion, and session-expiration behavior.
- Define uploaded-document governance if user-provided documents are ever allowed.

## Inputs to review when this work starts

- `app.py`
- `src/rgnavigator/models.py`
- `src/rgnavigator/intake_agent.py`
- `src/rgnavigator/pipeline.py`
- `src/rgnavigator/traceability.py`
- `docs/PRIVACY_SESSION_GOVERNANCE.md`
