# Privacy and Session Governance

This note summarizes the current repository's implemented behavior around household data handling, session state, uploads, and reviewer-facing artifacts.

## Current behavior

- The prototype handles sensitive prescreening information such as household composition, income, insurance status, county/location context, and hardship indicators.
- The live Streamlit app keeps active input in session memory while the session is open, including form fields, clarification chat state, merged multi-turn input, and the in-memory `NavigatorSession`.
- The checked-in runtime code does not intentionally persist live household intake sessions to a database or dedicated log file.
- The UI includes a raw `Session JSON` debug view for reviewer transparency, so screenshots or copied output can expose household details.
- When OpenAI-backed mode is enabled, household narratives, structured intake context, retrieved policy context, and embedding inputs are sent to OpenAI for extraction, scoring, explanation, and retrieval support.
- In fallback/no-key mode, the system relies on local parsing, rule-based scoring, and lower-accuracy retrieval behavior instead of OpenAI-backed LLM steps.

## Uploads and index governance

- Uploaded policy documents are treated as reference material, not applicant records.
- The ingestion path stores uploaded policy text locally under `data/uploaded_policies/`.
- Uploaded policy text is appended into the persistent local retrieval index under `data/policy_index/main/`.
- Users should not upload household-specific personal documents through that path.

## Demo and reviewer assumptions

- The course-demo and checked-in evaluation artifacts use synthetic test cases and reviewer fixtures rather than live applicant records.
- Raw/debug views and sample outputs are included for transparency during review and would need redaction or access restriction before public deployment.

## Limits of the current prototype

- This is a prescreening and next-step guidance prototype only, not an official eligibility determination, application-submission tool, legal-advice service, or case-management platform.
- The current prototype does not implement authentication, role-based access control, formal consent management, retention enforcement, deletion workflows, or a dedicated clear-session / clear-uploads control.

## Production requirements

- Privacy notice and third-party processing disclosure before intake
- Authentication and role-based access if hosted
- Formal retention and deletion controls
- Redaction or removal of raw/debug views
- Clear governance for uploaded policy documents and index lifecycle management
