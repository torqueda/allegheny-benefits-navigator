# Walkthrough: TC04 Missing Income Case

## Scenario
Two adults and one child report irregular gig-work income, a utility shutoff risk, and no reliable monthly income number yet.

## Why this case matters
This is a realistic Phase 2 stress test because it checks whether the prototype can:
- avoid overclaiming statewide eligibility when income is missing
- still preserve urgency around LIHEAP and local navigation
- route ambiguity forward rather than collapsing to a generic chatbot answer

## Component-by-component behavior

### 1. Intake
- Normalizes the household profile.
- Detects missing `monthly_earned_income` and `household_income_total`.
- Marks the intake status as `needs_clarification`.
- Preserves the utility-hardship signal for downstream reasoning.

### 2. Eligibility + Prioritization
- Marks SNAP, Medicaid/CHIP, and LIHEAP as uncertain where income is required for a firm determination.
- Elevates Local Referral because the case is both urgent and incomplete.
- Orders the result as:
  - Local Referral
  - LIHEAP
  - SNAP
  - Medicaid/CHIP

### 3. Checklist + Explanation
- Produces a bounded explanation instead of a definitive answer.
- Keeps the caveat that income is missing.
- Recommends gathering proof of income and contacting a local navigator or benefits helper.
- Preserves the disclaimer that this is not an official eligibility determination.

## Evidence
- Trace file: `outputs/traces/TC04.json`
- Evaluation row: `data/evaluation_results.csv`

## Why this is useful in the Phase 2 report
- It demonstrates the core workflow.
- It shows why the 3-component architecture is safer than a single-step assistant.
- It gives you a concrete failure-mode example to discuss in the writeup.
