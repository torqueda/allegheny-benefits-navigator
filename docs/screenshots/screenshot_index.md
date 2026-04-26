# Screenshot Index

Screenshots captured from the live Streamlit application during Phase 3 evaluation (2026-04-25).

---

## homepage.png — Application Home Screen

**What it shows:** The full intake form on first load before any case is submitted.

Key UI elements visible:
- **Demo Controls** sidebar (left): dropdown to load a preset demo case (AGENT_01–AGENT_10), "Load Case" button
- **Programs to Evaluate** selector: SNAP, Medicaid/CHIP, LIHEAP chips — user can scope which programs are screened
- **Household description** text area: free-text narrative input field
- **Structured override fields**: County (default: Allegheny), ZIP Code, Number of adults, Number of children, Monthly earned income, Monthly unearned income, Household income total, Housing cost, Employment status, Insurance status, Utility burden, Food insecurity signal, Child under 5, Pregnant household member, Elderly or disabled member, Heating assistance need, Recent job loss, Language or stress notes
- **Run Retrieval-Grounded Navigator** submit button at bottom

---

## output1.png — AGENT_02 Output (Top Half): Status + Program Match Detail

**Case:** AGENT_02 — single employed adult, $3,200/month, insured; no clear program match expected.

**What it shows:**
- **Navigator Output** header with three status badges: Intake Status = `complete`, Decision Status = `ambiguous`, Final Status = `delivered_with_uncertainty`
- **Priority Order** bar showing ranked program list
- **Program Matches** section — each program card shows match score, match type (strong_match / possible_match / no_clear_match), and an expandable "Why?" section with policy citations
- Policy citations visible (e.g., SNAP §568 Appendix A income limits, LIHEAP §619.1 heating responsibility, Medicaid §319.1)
- Sidebar on left shows the narrative input text the user submitted

---

## output2.png — AGENT_02 Output (Bottom Half): Explanation, Checklist, Caveats

**Case:** AGENT_02 continued (same run as output1.png).

**What it shows:**
- **Explanation** section: plain-language summary of why the user does not appear eligible, with program-by-program reasoning
- **Next Steps** section: actionable guidance for the user (e.g., contact local SNAP office, seek legal aid for housing)
- **Checklist** section: itemized checklist organized by program (SNAP, Medicaid, LIHEAP) listing documents and steps the user would need if they were to apply
- **Caveats** section: system-level disclaimers, including "This is prescreening only. It is not an official eligibility determination."

---

## output3.png — Raw Structured Agent Output (Debug View)

**What it shows:** The raw JSON / structured data payload returned by the pipeline, displayed in the UI's expandable debug section. Includes:
- Full `intake` object with all extracted fields and `intake_status`
- `program_matches` list with `match_score`, `priority_score`, `retrieval_bonus`, `rule_score`, `llm_score`, `decision_status` per program
- `explanation` object with `summary`, `next_steps`, `checklist`, `visible_caveats`
- `cross_check` object showing LLM vs rule agreement/disagreement per program
- Demonstrates the hybrid LLM + rule cross-check architecture producing `decision_status: ambiguous`

---

## multi_turn_dialogue.png — AGENT_04 Multi-Turn Intake Conversation

**Case:** AGENT_04 — household with shutoff notice, income not provided in first turn.

**What it shows:**
- **Demo Controls** sidebar: AGENT_04 loaded, Case type = `income_case`, Turns in fixture = 3
- **Programs to Evaluate**: SNAP, Medicaid/CHIP, LIHEAP all selected
- **Intake Conversation** panel (triggered because income was missing):
  - System message: "Thanks for sharing. User described the household as: I live in Pittsburgh with my daughter. We got a shutoff notice but I did not say how much income we have yet. Household: 1 adult(s), 1 child(ren) in Allegheny. Utility or heating strain is present in the intake. Missing fields: household_income_total."
  - Clarification questions displayed:
    1. "Can you tell me your total household income each month?"
    2. "Do you have any other sources of income, like benefits or support?"
    3. "Is there anything else about your situation that you think I should know?"
    4. "Feel free to answer in plain language. You can say 'I don't know' or 'skip' for anything you'd rather not share."
  - Text input box at bottom: "Type your answer here..."
- Illustrates the multi-turn clarification flow: intake was incomplete on Turn 1, so the system paused and prompted the user before running the pipeline.

---

## failure_case.png — AGENT_10 Out-of-County Failure (FAILURE-01)

**Case:** AGENT_10 — Philadelphia household; system is designed for Allegheny County only.

**What it shows:**
- **Demo Controls** sidebar: AGENT_10 loaded, Case type = `failure_case`
- Household description: "I live in Philadelphia with my daughter. I have no insurance, my income is about $900 a month, and I am behind on my gas bill."
- **Navigator Output**:
  - Intake Status = `complete` — system accepted the Philadelphia input without flagging it
  - Decision Status = `ambiguous`
  - Final Status = `delivered_with_uncertainty`
- **Priority Order**: Medicaid/CHIP > SNAP > LIHEAP
- **Program Matches**:
  - Medicaid/CHIP: `strong_match` (score 8.2)
  - SNAP: `possible_match` (score 4.6)
  - LIHEAP: `possible_match` (score 4.6)
- **Demonstrates FAILURE-01**: The system ran the full pipeline and returned program matches for a Philadelphia household without any warning that these results are for Allegheny County programs and may not apply. County boundary enforcement is a known open limitation (see `eval/failure_log.md`).
