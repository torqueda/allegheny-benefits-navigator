"""
Interactive CLI walkthrough of the full navigator pipeline.
Simulates the same conversation loop that app.py now provides in Streamlit.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.rgnavigator.intake_agent import run_intake, run_intake_turn
from src.rgnavigator.pipeline import run_navigator

DIVIDER = "=" * 70
THIN    = "-" * 70
MAX_CHAT_ROUNDS = 4


def banner(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def section(title: str) -> None:
    print(f"\n{THIN}")
    print(f"  {title}")
    print(THIN)


def wrap(text: str, indent: int = 4) -> str:
    prefix = " " * indent
    return textwrap.fill(text, width=70, initial_indent=prefix, subsequent_indent=prefix)


def print_intake(intake) -> None:
    section("IntakeOutput")
    print(f"  intake_status      : {intake.intake_status}")
    print(f"  missing_fields     : {intake.missing_fields}")
    print(f"  contradictory      : {intake.contradictory_fields}")
    print(f"  extracted_signals  : {intake.extracted_signals}")
    print(f"\n  intake_summary:")
    print(wrap(intake.intake_summary))
    if intake.clarification_questions:
        print(f"\n  clarification_questions ({len(intake.clarification_questions)}):")
        for i, q in enumerate(intake.clarification_questions, 1):
            print(wrap(f"[Q{i}] {q}"))


def print_eligibility(elig) -> None:
    section("EligibilityOutput")
    print(f"  decision_status : {elig.decision_status}")
    print(f"  priority_order  : {' > '.join(elig.priority_order) or '(none)'}")
    for match in elig.program_matches:
        icon = {"strong_match": "✓", "possible_match": "~", "no_clear_match": "✗"}.get(match.status, "?")
        print(f"\n  [{icon}] {match.program_name}  status={match.status}  score={match.match_score}")
        for r in match.rationale[:3]:
            print(wrap(f"• {r.reason}", indent=6))
        if match.caveats:
            print(wrap(f"  caveats: {match.caveats[0]}", indent=6))


def print_explanation(exp) -> None:
    section("ExplanationOutput")
    print(f"  final_status : {exp.final_status}")
    print(f"\n  Plain-language explanation:")
    print(wrap(exp.plain_language_explanation))
    print(f"\n  Checklists:")
    for prog, items in exp.checklist_by_program.items():
        print(f"    {prog}:")
        for item in items[:3]:
            print(wrap(f"- {item}", indent=6))
    print(f"\n  Next steps (first 3):")
    for step in exp.next_steps[:3]:
        print(wrap(f"- {step}"))


def ask_user(question: str) -> str:
    print()
    print(wrap(f"[SYSTEM] {question}"))
    try:
        reply = input("  You > ").strip()
    except (EOFError, KeyboardInterrupt):
        reply = "skip"
    return reply or "skip"


def run() -> None:
    banner("ALLEGHENY BENEFITS NAVIGATOR — Full Flow CLI Test")
    print("""
  This script walks through the same stages as the Streamlit app:
    Phase 1 → Initial intake from your description
    Phase 2 → Conversational follow-up for missing info
    Phase 3 → Eligibility scoring + explanation

  You can answer questions in plain language.
  Say "skip" or "I don't know" to skip any question.
""")

    # ── Phase 1: get initial description ─────────────────────────────────────
    banner("PHASE 1 — Initial Description")
    print(wrap(
        "Describe the household in plain language. "
        "You don't need to be complete — the system will ask follow-up questions."
    ))
    print()
    try:
        description = input("  You > ").strip()
    except (EOFError, KeyboardInterrupt):
        description = "I live in Allegheny County and I'm struggling to afford groceries."

    if not description:
        description = "I live in Allegheny County and I'm struggling to afford groceries."

    raw_input: dict = {"user_description": description}

    banner("PHASE 1 — Running run_intake()")
    print(f"\n  INPUT  raw_input = {json.dumps(raw_input, indent=4)}\n")

    intake = run_intake(raw_input)
    print_intake(intake)

    # ── Phase 2: conversational follow-up ────────────────────────────────────
    chat_rounds = 0

    while (
        intake.intake_status != "complete"
        and intake.clarification_questions
        and chat_rounds < MAX_CHAT_ROUNDS
    ):
        banner(f"PHASE 2 — Clarification Round {chat_rounds + 1} / {MAX_CHAT_ROUNDS}")

        for q in intake.clarification_questions:
            reply = ask_user(q)
            print(f"\n  INPUT  new_user_message = {repr(reply)}")

            raw_input, intake = run_intake_turn(raw_input, reply)
            chat_rounds += 1

            print(f"\n  After merging reply:")
            print_intake(intake)

            if intake.intake_status == "complete" or not intake.clarification_questions:
                break

    # ── Transition message ────────────────────────────────────────────────────
    banner("PHASE 2 → PHASE 3 — Intake Complete, Running Full Pipeline")
    if intake.intake_status == "complete":
        print(wrap("  Got it — intake is complete. Running eligibility and explanation..."))
    else:
        print(wrap("  Proceeding with available information (some fields still missing)."))

    print(f"\n  Final accumulated raw_input:")
    printable = {k: v for k, v in raw_input.items() if v is not None}
    print(json.dumps(printable, indent=4))

    # ── Phase 3: full pipeline ────────────────────────────────────────────────
    banner("PHASE 3 — run_navigator()")
    session = run_navigator(raw_input)

    print_eligibility(session.eligibility)
    print_explanation(session.explanation)

    banner("DONE")
    print(wrap(
        f"Pipeline complete. "
        f"Recommended programs: {', '.join(session.eligibility.recommended_programs) or 'none'}. "
        f"Final status: {session.explanation.final_status}."
    ))
    print()


if __name__ == "__main__":
    run()
