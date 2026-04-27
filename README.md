# Retrieval-Grounded Policy Navigator

This project is a prescreening and next-step guidance prototype for Allegheny County public benefits. A user provides a household narrative and optional structured overrides, the system extracts a household profile, retrieves policy evidence, cross-checks recommendations against deterministic program profiles, and returns plain-language guidance with caveats. It is built for course evaluation and inspection, not for operational deployment.

This is not an official eligibility determination, application-submission tool, legal advice service, or case-management system.

## Team and Course Information

| Field | Value |
|---|---|
| Team | Yuhan, Tomas |
| Course | Agentic Systems Studio |
| Track | Track A — Technical Build |
| Phase | Phase 3 final artifact |

## Reviewer Quickstart

If you already have the repository open locally, skip the `git clone` step.

```bash
git clone <repo-url>
cd allegheny-benefits-navigator

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# .env.example is not checked in in the current repo state.
touch .env
# Optional: add OPENAI_API_KEY=your_key_here

streamlit run app.py
```

Mode notes:

- With `OPENAI_API_KEY`, the app uses OpenAI-backed intake extraction, eligibility scoring, explanation generation, and embedding/update paths where implemented.
- Without `OPENAI_API_KEY`, the app still runs through local fallback paths, but intake quality, retrieval quality, and explanation/scoring quality are weaker. The repo does not claim API-free parity.

## What the System Does

The current reviewer-facing workflow is:

1. The user enters a household narrative and can optionally supply structured override fields in the Streamlit UI.
2. The intake stage extracts a normalized household profile and can pause for clarification when required fields are missing or contradictory.
3. The eligibility stage retrieves policy evidence and scores candidate programs.
4. A deterministic rule/profile cross-check supports the LLM/RAG scoring path and can preserve ambiguity rather than overstate confidence.
5. The explanation stage returns a plain-language summary, next steps, checklist items, and caveats.

The built-in programs currently evaluated in the app are `SNAP`, `Medicaid/CHIP`, and `LIHEAP`. The codebase also includes a local ingestion path for uploaded policy text, but there is no reviewer-facing upload UI in `app.py`, and `data/uploaded_policies/` is empty in the current repo state.

## Architecture and Orchestration

Reviewer-facing architecture materials:

- [Architecture note](docs/ARCHITECTURE.md)
- [Pipeline diagram](docs/pipeline_diagram.png)

The project uses custom Python orchestration rather than LangChain, LangGraph, or another orchestration framework. That fits the current repo: the workflow is deterministic, handoffs are inspectable, uncertainty and stopping behavior are explicit, Streamlit session state is visible, late-stage integration risk stays lower, and the runtime lines up directly with the evaluation artifacts and tests.

The repo also includes an [agentic coordination walkthrough](docs/AGENTIC_COORDINATION_WALKTHROUGH.md). It traces `AGENT_04`, where the first turn triggers clarification for missing income, the second turn completes intake, and the pipeline then proceeds through retrieval, prioritization, and explanation with `decision_status = ambiguous` and `final_status = delivered_with_uncertainty`.

## Repository Guide

| Path | What it is | Reviewer note |
|---|---|---|
| [app.py](app.py) | Streamlit entry point | Main local demo/runtime entry |
| [src/rgnavigator/](src/rgnavigator/) | Core pipeline code | Canonical implementation |
| [data/](data/) | Program profiles, corpus, internal fixtures, local index assets | Mixed reviewer + internal/raw assets |
| [eval/](eval/) | Canonical reviewer-facing evaluation package | Canonical for Phase 3 review |
| [docs/](docs/) | Architecture, walkthrough, privacy, heuristic notes | Reviewer-facing documentation |
| [docs/screenshots/](docs/screenshots/) | UI and workflow screenshots | Reviewer-facing visual artifacts |
| [outputs/](outputs/) | Exported sample runs | Reviewer-facing examples |
| [media/](media/) | Demo link artifact | Reviewer-facing media pointer |
| [AI_USAGE.md](AI_USAGE.md) | AI usage disclosure | Canonical disclosure |
| [final_report.md](final_report.md) | Final report in Markdown | Canonical final report in repo |
| `final_report.pdf` | Final report PDF | Not present in the current repo |
| [Final_Report.txt](Final_Report.txt) | Plain-text report draft/export | Treat as working/internal, not canonical |

Canonical final-submission artifacts in this repo are `final_report.md`, the reviewer-facing files in `eval/`, the docs linked above, `AI_USAGE.md`, `outputs/sample_runs/`, `media/demo_video_link.txt`, and the runnable app in `app.py`.

Legacy or internal/raw artifacts still present:

- [data/agent_test_cases.json](data/agent_test_cases.json): internal runner/demo fixture
- [data/evaluation_results_phase3.json](data/evaluation_results_phase3.json): raw internal runner output
- `data/test_cases.csv` and `data/expected_results.csv`: legacy evaluation artifacts called out in [eval/version_notes.md](eval/version_notes.md)

## Evaluation Package

`eval/` is the canonical reviewer-facing evaluation package:

- [Test cases](eval/test_cases.csv)
- [Evaluation results](eval/evaluation_results.csv)
- [Failure log](eval/failure_log.md)
- [Version notes](eval/version_notes.md)

Latest checked-in canonical results from [eval/evaluation_results.csv](eval/evaluation_results.csv):

| Metric | Value |
|---|---|
| Total cases | 10 |
| PASS | 6 |
| FAIL | 4 |

Coverage in the checked-in package includes clear success cases, two multi-turn clarification cases, missing-information behavior, contradiction handling, an out-of-county boundary case, and health-coverage/priority edge cases. The evaluation materials explicitly treat recommended-program correctness separately from priority-order behavior; priority is checked directionally rather than as an exact full ranking.

Open limitations documented in the current evaluation package include:

- `AGENT_02`: the no-match guardrail still produces false-positive recommendations for a high-income insured adult case.
- `AGENT_03`: the pregnancy pathway case still misranks `LIHEAP` ahead of `Medicaid/CHIP` and misses the term `pregnancy` in explanation/caveat text.
- `AGENT_06`: the safe incomplete-intake fallback still misses the expected intake state and full missing-field summary.
- `AGENT_07`: the uninsured-children case still over-prioritizes `LIHEAP` ahead of health coverage.

To rerun the evaluation package:

```bash
python scripts/run_agent_test_cases.py
```

To run the test suite:

```bash
python -m pytest -q
```

## Priority Heuristic

Priority order in this project means recommended review/action order, not official eligibility likelihood. The ranking is intended as a triage heuristic based on likely applicability, program-profile fit, urgency or hardship signals, missing or contradictory evidence, and practical next-step value. See [docs/PRIORITY_HEURISTIC.md](docs/PRIORITY_HEURISTIC.md).

## Privacy and Session Governance

The app handles sensitive household prescreening information such as income, household composition, insurance status, county/location, and hardship indicators. In the current prototype, active intake data, clarification turns, and the assembled `NavigatorSession` live in Streamlit session state while the session is open; the UI also exposes a raw `Session JSON` debug view for reviewer transparency.

When API-backed mode is enabled, user-provided household narratives, structured intake details, and model-supporting context are sent to OpenAI for extraction, scoring, explanation, and embedding/update paths where used. The checked-in runtime does not intentionally persist live intake sessions to a database or dedicated log file, but this is still a course prototype without production-grade privacy controls, authentication, consent management, formal retention/deletion enforcement, or a dedicated clear-session workflow. Reviewers should use synthetic or fictional household data only. See [docs/PRIVACY_SESSION_GOVERNANCE.md](docs/PRIVACY_SESSION_GOVERNANCE.md).

## Screenshots and Demo Materials

- [Screenshot index](docs/screenshots/screenshot_index.md)
- [Screenshots folder](docs/screenshots/)
- [Demo video link](media/demo_video_link.txt)
- [Sample runs](outputs/sample_runs/)

The screenshot index covers the intake UI, example outputs, the multi-turn clarification flow, raw/debug structured output, and a boundary/failure-state example. `outputs/sample_runs/` currently contains exported sample PDFs for `AGENT_02` and `AGENT_04`.

## AI Usage Disclosure

See [AI_USAGE.md](AI_USAGE.md). It documents which AI tools/models were used, what they were used for, what fallback or manual logic exists, and what behavior was independently checked in code and evaluation artifacts.

## Known Limitations

- This is prescreening only, not an official eligibility determination or application system.
- The checked-in evaluation package is still `6 PASS / 4 FAIL`, so false positives, false negatives, ranking misses, and explanation gaps remain.
- No-key/fallback mode runs, but it is weaker than API-backed mode.
- Priority ordering is still imperfect on some health-coverage-centered cases, especially `AGENT_03` and `AGENT_07`.
- Privacy and session controls are prototype-level rather than production-grade.
- Uploaded-policy support exists in code, but the current repo does not include a reviewer-facing upload UI or a checked-in uploaded policy document set.

## Final Submission Checklist

| Artifact | Link / Status |
|---|---|
| Final report PDF | Not present in the current repo |
| Final report Markdown | [final_report.md](final_report.md) |
| Architecture note | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Architecture diagram | [docs/pipeline_diagram.png](docs/pipeline_diagram.png) |
| Coordination walkthrough | [docs/AGENTIC_COORDINATION_WALKTHROUGH.md](docs/AGENTIC_COORDINATION_WALKTHROUGH.md) |
| Screenshot index | [docs/screenshots/screenshot_index.md](docs/screenshots/screenshot_index.md) |
| Evaluation test cases | [eval/test_cases.csv](eval/test_cases.csv) |
| Evaluation results | [eval/evaluation_results.csv](eval/evaluation_results.csv) |
| Failure log | [eval/failure_log.md](eval/failure_log.md) |
| Version notes | [eval/version_notes.md](eval/version_notes.md) |
| AI usage log | [AI_USAGE.md](AI_USAGE.md) |
| Sample runs | [outputs/sample_runs/](outputs/sample_runs/) |
| Demo video | [media/demo_video_link.txt](media/demo_video_link.txt) |
| App entry point | [app.py](app.py) |
| Local run instructions | See [Reviewer Quickstart](#reviewer-quickstart) |
