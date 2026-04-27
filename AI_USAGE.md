# AI Usage Disclosure

**Project:** Retrieval-Grounded Policy Navigator  
**Track:** A — Agentic Systems Studio  
**Team:** Yuhan, Tomas

This document discloses how AI was used both in the runtime prototype and during development, review, and final submission preparation. We used AI as an assistive tool to accelerate repo-scale inspection, documentation, evaluation review, drafting, and revision work, especially because the codebase and artifact set had grown large enough to slow down purely manual review. Final decisions, acceptance of changes, and submission responsibility remained with the team.

## 1. Runtime AI Used by the Prototype

These models are part of the application itself when API-backed mode is enabled.

### 1.1 `gpt-4o-mini` — Intake Extraction and Clarification

**Where:** `src/rgnavigator/intake_agent.py`

**What it does:** Extracts a normalized `UserIntake` profile from the household narrative and optional structured fields. It can also generate clarification questions when required information is missing or contradictory.

**Fallback behavior:** If no API key is available or the call fails, the app falls back to local extraction logic and template-based clarification behavior.

### 1.2 `gpt-4o-mini` — Eligibility Scoring

**Where:** `src/rgnavigator/eligibility_agent.py`

**What it does:** Scores program matches using retrieved policy evidence and returns statuses such as `strong_match`, `possible_match`, or `no_clear_match`, along with rationale tied to retrieved policy text.

**Fallback behavior:** If LLM scoring is unavailable, the system falls back to deterministic rule-based scoring and conservative ambiguity handling.

### 1.3 `gpt-4o-mini` — Explanation Generation

**Where:** `src/rgnavigator/explanation_agent.py`

**What it does:** Produces the user-facing plain-language explanation, next steps, checklist items, and visible caveats.

**Fallback behavior:** If no API key is available or generation fails, the app uses template-rendered output instead.

### 1.4 `text-embedding-3-small` — Retrieval Support

**Where:** `src/rgnavigator/policy_store.py`

**What it does:** Supports vector retrieval over the local policy corpus when OpenAI-backed embeddings are used.

**Fallback behavior:** The repo also supports a local hashed bag-of-words fallback (`hashed-bow-v1`), which is weaker than the OpenAI-backed embedding path.

## 2. Non-AI Logic That Constrains Runtime AI

Not all important decision logic is AI-generated.

- A deterministic rule/profile cross-check in `src/rgnavigator/eligibility_agent.py` constrains or qualifies model-backed recommendations.
- The system is designed to preserve ambiguity and surface caveats rather than overstate certainty.
- The prototype includes explicit prescreening disclaimers and does not present outputs as official determinations.

## 3. Development and Submission AI Tools Used

We used the following AI tools during development and final submission work.

| Tool | How it was used |
|---|---|
| ChatGPT model 5.4 | Repo-scale review assistance, planning next steps, refining work plans, drafting and revising documentation, and helping structure prompts for constrained repo work |
| VS Code integrated Codex | Inspecting code and docs quickly, evaluating changes made to existing code and pipeline documents, checking repo artifacts against assignment constraints, drafting submission-facing files, and helping revise documentation such as `README.md` |

These tools were used to save time on large-file and multi-artifact review, not to replace human judgment.

## 4. What AI Was Used For During Development

AI assistance was used for:

- evaluating existing code, architecture notes, pipeline documents, and evaluation artifacts
- identifying what Phase 3 work was complete versus still missing
- refining the sequence of steps needed to complete the project
- generating or refining prompts for Codex so constraints, non-edit boundaries, and repo-specific considerations were explicit
- drafting and revising reviewer-facing submission files such as `README.md`
- polishing initial drafts of the final report and related documentation
- speeding up repo navigation and consistency checks across many files

AI was not treated as an authoritative source of truth about the repository. Outputs were reviewed against the actual checked-in code and artifacts.

## 5. What Was Changed Manually

The team manually:

- decided which AI suggestions to accept, reject, or rewrite
- selected the final framing for project claims, limitations, and scope boundaries
- verified that reviewer-facing statements matched the repository state
- kept ownership of the final report, screenshots, evaluation framing, and submission packaging
- made final judgment calls on what counted as canonical versus internal/legacy artifacts

In other words, AI helped accelerate drafting and review, but the final submission language and artifact selection were still human-curated.

## 6. What Was Independently Verified

Before accepting AI-assisted documentation or repo-review output, we independently checked relevant claims against the repository. This included:

- reading source files in `src/rgnavigator/` to confirm runtime model usage and fallback paths
- checking reviewer-facing evaluation artifacts in `eval/`
- checking linked docs and submission artifacts in `docs/`, `media/`, and `outputs/`
- verifying file existence and repo navigation claims
- running the local test suite in the repo environment during final documentation work

We did not rely on AI alone for final factual claims about supported features, evaluation status, artifact presence, or privacy behavior.

## 7. Governance Notes on AI Use

The main reasons we used AI were speed, consistency, and scale. By Phase 3, the project had grown into a fairly large code-and-document set, and AI assistance helped reduce the overhead of manual repo review, cross-file comparison, and submission cleanup.

That said, AI assistance has limitations:

- it can overstate what a repo supports if prompts are not explicit
- it can generalize from old documentation instead of the current checked-in state
- it can produce polished but inaccurate summaries if not grounded in actual files

Because of that, we used explicit constrained prompts, asked for artifact inspection before drafting, and manually checked the highest-risk claims.

## 8. Privacy and Data-Handling Note Related to AI Use

When API-backed mode is enabled in the running prototype, user-provided household narratives and structured intake details may be sent to OpenAI for extraction, scoring, explanation, and embedding-related operations where implemented. In fallback/no-key mode, those model-backed paths are replaced by local fallback behavior.

The checked-in runtime code does not intentionally persist live intake sessions to a database or dedicated log file, but this course prototype is not a production deployment and does not implement full privacy, authentication, consent, retention, or deletion controls. Review and demo use should rely on synthetic or fictional household data.

## 9. Prompt Examples Used in Practice

Below are representative examples of the kinds of prompts we used. These are included verbatim as examples of how we constrained AI assistants to inspect the repo first, avoid unsupported claims, and separate drafting help from code changes.

```text
You are helping me produce the final top-level README.md for a Phase 3 Agentic Systems Studio submission.

Goal:
Rewrite README.md so it is a reviewer-facing entry point that lets a professor understand, run, inspect, and evaluate the project in about five minutes.

Important constraints:
- You may edit README.md.
- Do not edit code.
- Do not edit evaluation files.
- Do not edit final_report.md.
- Do not edit AI_USAGE.md.
- Do not edit screenshots or media files.
- Do not invent files, features, metrics, deployment status, or controls that are not present in the repo.
- If a required artifact is missing, mention it clearly as missing or pending rather than pretending it exists.
- Keep the README concise, professional, and easy to scan.
- Prefer links to existing files over long duplicated explanations.
- The README should be accurate for the current committed repo state.

Before editing, inspect at least:

- README.md
- final_report.md
- final_report.pdf, if present
- docs/ARCHITECTURE.md
- docs/AGENTIC_COORDINATION_WALKTHROUGH.md, if present
- docs/PRIORITY_HEURISTIC.md, if present
- docs/PRIVACY_SESSION_GOVERNANCE.md, if present
- docs/pipeline_diagram.png
- docs/screenshots/
- docs/screenshots/screenshot_index.md
- AI_USAGE.md
- eval/test_cases.csv
- eval/evaluation_results.csv
- eval/failure_log.md
- eval/version_notes.md
- data/agent_test_cases.json
- data/evaluation_results_phase3.json
- outputs/
- outputs/sample_runs/
- media/demo_video_link.txt
- requirements.txt
- .env.example
- app.py
- src/rgnavigator/
- scripts/run_agent_test_cases.py
- tests/

README requirements:
The README must include the following sections, in this order unless there is a strong reason to adjust:

1. Project title and short description
   - Project title: Retrieval-Grounded Policy Navigator, or the current final project title used in final_report.md.
   - Explain in 2–4 sentences what the system does.
   - State that this is a prescreening and next-step guidance prototype for Allegheny County public benefits.
   - State clearly that it is not an official eligibility determination, application submission tool, legal advice, or case-management system.

2. Team and course information
   - Team members: Yuhan and Tomas.
   - Course: Agentic Systems Studio.
   - Track: Track A — Technical Build.
   - Phase: Phase 3 final artifact.

3. Reviewer quickstart
   - Give the shortest reliable path to run the app locally.
   - Include commands for:
     - cloning/opening repo, if useful
     - creating/activating a virtual environment
     - installing requirements
     - copying .env.example to .env
     - optionally adding OPENAI_API_KEY
     - running the Streamlit app
   - Include a clear note about behavior with and without OPENAI_API_KEY:
     - API-backed mode uses model/embedding calls where implemented.
     - no-key/fallback mode should still run if supported, but output quality or retrieval/scoring quality may be weaker.
   - Do not claim API-free parity if the repo does not support it.

4. What the system does
   - Summarize the user workflow:
     - user enters household narrative and/or structured overrides
     - intake extracts household profile
     - missing or contradictory information can trigger clarification
     - eligibility agent retrieves policy evidence and scores programs
     - deterministic rule/profile cross-check supports LLM/RAG scoring
     - explanation agent produces plain-language summary, next steps, caveats, and checklist
   - Mention programs currently supported according to current code/docs.
   - Mention uploaded policy support only if it is actually supported and describe it accurately.

5. Architecture and orchestration
   - Link to docs/ARCHITECTURE.md.
   - Link to docs/pipeline_diagram.png.
   - State clearly that the project uses custom Python orchestration rather than LangChain, LangGraph, or another framework.
   - Explain the rationale concisely:
     - deterministic workflow
     - inspectable handoffs
     - explicit uncertainty/stopping behavior
     - session-state visibility
     - lower late-stage integration risk
     - alignment with evaluation artifacts
   - Do not imply that LangChain/LangGraph is implemented.
   - If docs/AGENTIC_COORDINATION_WALKTHROUGH.md exists, link it and summarize the walkthrough in 2–3 sentences.

6. Repository guide
   - Provide a compact folder/file guide.
   - Include at least:
     - app.py
     - src/rgnavigator/
     - data/
     - eval/
     - docs/
     - docs/screenshots/
     - outputs/
     - media/
     - AI_USAGE.md
     - final_report.md / final_report.pdf if present
   - Identify which files are canonical final-submission artifacts.
   - If any legacy/raw/internal files remain, label them clearly as internal/raw/legacy and point reviewers to the canonical files.

7. Evaluation package
   - State that eval/ is the canonical reviewer-facing evaluation package.
   - Link to:
     - eval/test_cases.csv
     - eval/evaluation_results.csv
     - eval/failure_log.md
     - eval/version_notes.md
   - Summarize the latest canonical evaluation results by reading eval/evaluation_results.csv, not by relying on old README text.
   - Mention:
     - number of cases
     - number of PASS/FAIL outcomes
     - types of cases covered, such as clear success, multi-turn, missing info, contradiction, out-of-county, edge/boundary cases, if supported by the files
     - at least two failure/limitation cases from eval/failure_log.md
   - Explain that priority order is evaluated separately from eligibility/program recommendation correctness if that is how current evaluation docs define it.
   - Include the exact command to rerun the evaluation using scripts/run_agent_test_cases.py.
   - Include the exact command to run tests.

8. Priority heuristic
   - Include a short paragraph defining priority order as recommended review/action order, not official eligibility likelihood.
   - Explain that it is based on likely applicability, program-profile fit, urgency/hardship, missing or contradictory evidence, and practical next-step value, if this matches current docs.
   - Link to docs/PRIORITY_HEURISTIC.md if present.

9. Privacy and session governance
   - Include a concise section or subsection.
   - Link to docs/PRIVACY_SESSION_GOVERNANCE.md if present.
   - State that the app handles sensitive household prescreening information such as income, household composition, insurance status, location/county, and hardship indicators.
   - Explain current session handling accurately based on the repo.
   - Do not overclaim "no PII retention" unless the repo proves no intake/user data can persist anywhere.
   - Mention whether API-backed mode may send user-provided household information or structured intake details to a model provider, if current code does that.
   - Tell reviewers to use synthetic or fictional data for demo/testing.
   - State clearly that this is a course prototype and not a production deployment with full privacy controls, authentication, formal retention enforcement, consent management, or deletion workflows unless those are actually implemented.

10. Screenshots and demo materials
   - Link to docs/screenshots/screenshot_index.md.
   - Link to the screenshots folder.
   - Mention that screenshots cover the UI/workflow/evidence/failure or boundary behavior if the screenshot index supports that.
   - Link to media/demo_video_link.txt if present.
   - Link to outputs/sample_runs/ and briefly describe the sample outputs.

11. AI usage disclosure
   - Link to AI_USAGE.md.
   - Summarize in one sentence what the disclosure covers:
     - tools used
     - what they were used for
     - what was changed manually
     - what was independently verified
   - Do not duplicate the whole AI usage disclosure.

12. Known limitations
   - Keep this honest and concise.
   - Include limitations supported by final_report.md, eval/failure_log.md, or docs:
     - prescreening only, not official eligibility
     - possible false positives/false negatives
     - fallback/no-key mode weaker if applicable
     - remaining priority/explanation limitations if present
     - prototype privacy/session controls not production-grade
     - uploaded policy/index governance limitations if applicable
   - Do not hide remaining evaluation failures if the canonical evaluation results still show failures.
   - Do not claim production readiness.

13. Final submission checklist / reviewer navigation
   - Add a compact checklist linking to:
     - final report PDF if present
     - final_report.md
     - architecture diagram
     - screenshot index
     - evaluation files
     - failure log
     - AI usage log
     - outputs/sample_runs/
     - media/demo_video_link.txt
     - app.py or run instructions
   - This should make it easy for a reviewer to inspect every required artifact.

Style requirements:
- Use clear Markdown headings.
- Keep paragraphs short.
- Use tables where they improve navigation.
- Prefer relative links, e.g. [Evaluation results](eval/evaluation_results.csv).
- Use precise language: "prototype", "prescreening", "review/action order", "custom Python orchestration", "synthetic evaluation cases".
- Avoid marketing language.
- Avoid unsupported claims like "secure", "production-ready", "fully accurate", "guaranteed eligible", or "no PII retention" unless directly proven by code/docs.
- Make the README useful both as a course submission artifact and as a portfolio-facing project page.

After editing README.md, report:
1. Files changed.
2. Major sections added or rewritten.
3. Which assignment README requirements are now satisfied.
4. Which Phase 1 / Phase 2 feedback items are addressed.
5. Any artifact links that are missing or point to files that do not exist.
6. Any claims you intentionally avoided because the repo did not support them.
7. Suggested final manual checks before committing.
```

```text
You are helping me write the privacy and session governance section for a Phase 3 Agentic Systems Studio final report.

Do not modify any files yet.

Inspect the current repo for evidence about data handling, session state, persistence, external API use, uploaded documents, logs, and evaluation artifacts.

Inspect at least:

- app.py
- src/rgnavigator/
- src/rgnavigator/pipeline.py
- src/rgnavigator/intake_agent.py
- src/rgnavigator/eligibility_agent.py
- src/rgnavigator/explanation_agent.py
- any session_state or state-management files
- any upload/indexing code
- scripts/run_agent_test_cases.py
- eval/
- data/
- outputs/
- README.md
- final_report.md
- AI_USAGE.md
- docs/ARCHITECTURE.md
- docs/AGENTIC_COORDINATION_WALKTHROUGH.md, if present

Produce a read-only audit answering:

1. What user/household data the app collects or derives.
2. Where raw user input is held during the app session.
3. Where normalized intake profiles are stored.
4. Whether raw user input or normalized intake data is written to disk.
5. Whether model prompts/responses are written to disk.
6. Whether evaluation outputs contain synthetic data only or could contain live user/demo data.
7. Whether sample outputs contain any real or synthetic household data.
8. Whether uploaded policy documents are stored on disk.
9. Whether uploaded policy documents are embedded into a persistent index.
10. Whether there is a reset/clear-session control and what it clears.
11. Whether there are logs, traces, debug payloads, or raw JSON views that expose household details.
12. What information is sent to OpenAI or other external services when API-backed mode is enabled.
13. What happens in fallback/no-key mode.
14. Whether the app has authentication, access control, encryption, consent notice, or retention controls.
15. Any privacy/security claims currently made in README.md, final_report.md, AI_USAGE.md, or docs that are unsupported or too strong.
16. The safest accurate wording for a privacy/session governance section.

Do not invent controls that are not implemented. Clearly separate:
- implemented current behavior
- reviewer/demo guidance
- limitations
- future production requirements
```

```text
I'm working on Phase 3 of Agentic Systems Studio.pdf. I've included here the reports my team wrote for Phases 1 & 2 and their respective feedback from the professor. My partner has already completed a big chunk of Phase 3 and uploaded their progress to our shared GitHub repo. I need to now work on completing whatever is missing for (i) Phase 3 and (ii) the feedback we've been getting from the professor. My initial idea is to split this like so:

1. Everything that goes in the repo can be cloned to my Mac, where I can use Codex integrated into VS Code to check the code and the docs, and through prompting identify everything that has been completed and where, as well as everything that still needs to be done.
2. Then everything that's not part of the repo, like our final report, screenshots, the video recording, etc. I can list separately and go through a checklist to ensure that it's completed to satisfy both the assignment requirements and the feedback. I'm thinking I can also carry out part of this work through VS Code-integrated Codex, since it can quickly go through all the repo files to complete things like the initial report draft, the README file, and such.

Is this a good approach? If so, produce a list of steps I can go through to fully complete Phase 3, be it manual or prompting work. If not, propose an alternative plan that would produce a better outcome for this project. For the plans, keep all the write ups for steps concise, and we'll expand upon each of them as we go through the work.
```

## 10. Summary

AI was used in this project in two distinct ways:

1. as part of the prototype runtime, where OpenAI-backed models support intake extraction, retrieval-backed scoring, explanation generation, and embedding-based retrieval when enabled
2. as a development and submission assistant, where ChatGPT 5.4 and VS Code integrated Codex helped accelerate repo inspection, planning, prompt design, documentation drafting, and final submission cleanup

We used AI to save time and improve consistency, but we did not delegate final judgment to it. Final claims, final artifact selection, and final submission responsibility remained with the team.
