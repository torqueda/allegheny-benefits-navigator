# Allegheny Benefits Navigator

Deterministic prototype for bounded benefits prescreening and next-step guidance for Allegheny County households.

This repository contains a working prototype, not a production benefits system. It is designed to help a reviewer inspect a simple end-to-end prescreening pipeline with typed models, deterministic rules, structured evaluation fixtures, and reproducible evaluation artifacts.

Safety boundaries:
- Prescreening only, not an official eligibility determination
- No application submission
- No legal advice
- Not a replacement for caseworkers or benefits offices

Project metadata:
- Team / authors: TODO if needed for an external review package
- Selected track: TODO if needed for an external review package

## Reviewer Quick Start

### What this project does

This prototype takes structured household intake data, applies deterministic prescreening rules for a small set of benefits programs, ranks the likely-relevant programs using transparent heuristics, and generates a bounded checklist plus explanation for the user.

### Problem being addressed

People seeking benefits often do not know which programs to look at first, what documents they may need, or how to interpret incomplete or ambiguous intake information. The prototype is meant to make that early triage step more inspectable and easier to evaluate.

### Intended use context

- Allegheny County household prescreening
- Form-based intake
- Research / prototype evaluation setting
- Synthetic fixture-driven evaluation, not live case processing

### What the prototype currently supports

- 3-component flow only:
  - Intake
  - Eligibility + Prioritization
  - Checklist + Explanation
- Plain Python sequential controller
- Deterministic encoded rules
- Transparent prioritization heuristics
- Deterministic checklist generation
- Template-first explanation output
- Initial 3-program scope only:
  - SNAP
  - Medicaid/CHIP
  - LIHEAP
- Fixture-driven evaluation runner and checked-in evaluation artifacts

### What is intentionally out of scope

- Official eligibility determinations
- Application submission
- UI / frontend product work
- LLM decision logic
- Programs beyond the current 3-program prototype scope
- Counties beyond Allegheny in this prototype

### Why the architecture is split into 3 components

The architecture separates data quality checks, deterministic policy reasoning, and user-facing communication so each step is easier to inspect, test, and evaluate. That boundary is intentional: Intake should not make policy decisions, and the explanation layer should not rewrite or invent decision state.

## Architecture

Current flow:

```text
intake() -> eligibility_and_prioritization() -> checklist_and_explanation()
```

### 1. Intake

Validates and normalizes structured household inputs, identifies missing or contradictory fields, and produces a typed household profile. This is a data-quality component, not a policy component.

### 2. Eligibility + Prioritization

Applies deterministic rules for the current in-scope programs, preserves uncertainty conservatively, and ranks supported programs with transparent heuristics. This is the core decision layer.

### 3. Checklist + Explanation

Consumes upstream state and produces deterministic checklist items, next steps, visible caveats, and a template-first explanation. It does not override eligibility outcomes.

### Current program scope

- SNAP
- Medicaid/CHIP
- LIHEAP

## Setup And Local Run

This repo expects Python 3.11.

### Environment setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

### Run the full test suite

```bash
.venv/bin/python -m pytest -q
```

### Run the evaluation-readiness tests

These tests validate full-pipeline execution across the fixture set without regenerating the checked-in evaluation artifacts.

```bash
.venv/bin/python -m pytest -q tests/test_evaluation_readiness.py tests/test_evaluation_runner.py
```

### Run the full evaluation artifact generator

This runs the full prototype across all rows in `data/test_cases.csv`, compares outputs to `data/expected_results.csv`, overwrites the evaluation artifact CSV, and overwrites the failure log.

```bash
.venv/bin/python -m src.evaluation.run_evaluation
```

### Output locations

- Evaluation artifact CSV: [data/evaluation_results.csv]
- Failure log: [failure_log.md]

## Repository Guide

### Top-level files

- [AGENTS.md]: repository rules and implementation constraints used during development
- [README.md]: reviewer-facing overview and run instructions
- [requirements.txt]: Python dependencies
- [failure_log.md]: latest evaluation mismatches and exceptions

### Main code

- [src/models/]: typed Pydantic schemas for intake, eligibility, explanation, session state, and shared enums
- [src/pipeline/]: 3-component pipeline implementation, controller, and session-state wiring
- [src/loaders/]: CSV/rule loaders for fixtures and authored rule sources
- [src/evaluation/]: fixture-driven evaluation runner that writes the checked-in evidence artifacts

### Design and data

- [docs/]: architecture, component specs, orchestration rules, and schema examples
- [data/]: evaluation fixtures and generated evaluation output
- [data/rules_source/]: authored CSV rule inputs used by the deterministic prototype

### Tests

- [tests/]: model, loader, component, controller, evaluation-readiness, and evaluation-runner tests

## Evaluation

### How evaluation works

- [data/test_cases.csv] contains simulated user inputs
- [data/expected_results.csv] contains structured expectations
- [src/evaluation/run_evaluation.py] runs the full pipeline across all cases
- Results are written to:
  - [data/evaluation_results.csv]
  - [failure_log.md]

### Comparison behavior

- Each test-case row is converted into `raw_form_input` by excluding fixture-only metadata fields
- The runner uses the existing pipeline entrypoint with `ambiguity_mode=True`
- Blank expected-result fields mean no expectation is provided for that field
- Structured comparisons are prioritized over long-form explanation text
- Comparisons currently focus on the in-scope programs:
  - SNAP
  - Medicaid/CHIP
  - LIHEAP

### Current checked-in evaluation snapshot

The current checked-in artifacts show:

- 10 processed cases
- 5 full matches
- 5 mismatches
- 0 exceptions

The current failure log shows mismatches only in priority ordering for a subset of cases; it does not show runtime exceptions.

## Known Limitations

- Only 3 programs are implemented in the current prototype
- Rules are deterministic and encoded from curated sources; they are not a full policy engine
- Scope is limited to Allegheny County prototype use
- The system is for prescreening and next-step guidance only
- Ambiguous cases may still require visible caveats or human follow-up
- Checklist coverage depends on the intake signals currently modeled in the prototype
- The explanation layer is template-first and intentionally bounded rather than conversationally flexible

## Key Files For Review

If you only have a few minutes, start here:

1. [README.md]
2. [docs/ARCHITECTURE.md]
3. [docs/COMPONENT_SPECS.md]
4. [src/pipeline/controller.py]
5. [src/pipeline/components.py]
6. [src/evaluation/run_evaluation.py]
7. [data/evaluation_results.csv]
8. [failure_log.md]
