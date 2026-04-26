from __future__ import annotations

from typing import Any

import streamlit as st

from src.rgnavigator.demo_data import load_demo_cases
from src.rgnavigator.intake_agent import run_intake, run_intake_turn
from src.rgnavigator.pipeline import run_navigator
from src.rgnavigator.policy_store import load_policy_documents

MAX_CHAT_ROUNDS = 4  # stop asking after this many follow-up rounds

PAGE_TITLE = "Retrieval-Grounded Policy Navigator"
TRI_STATE_OPTIONS = {"Unknown": None, "Yes": True, "No": False}


def _parse_optional_int(value: str) -> int | None:
    value = value.strip()
    return int(value) if value else None


def _parse_optional_float(value: str) -> float | None:
    value = value.strip()
    return float(value) if value else None


def _apply_case(case_id: str, payload: dict[str, Any]) -> None:
    st.session_state["selected_case"] = case_id
    st.session_state["user_description"] = payload.get("scenario_summary", "")
    for key in [
        "zip_code",
        "num_adults",
        "num_children",
        "monthly_earned_income",
        "monthly_unearned_income",
        "household_income_total",
        "housing_cost",
        "language_or_stress_notes",
    ]:
        st.session_state[key] = ""
    for key in ["employment_status", "utility_burden", "food_insecurity_signal", "insurance_status"]:
        st.session_state[key] = ""
    for key in [
        "child_under_5",
        "pregnant_household_member",
        "elderly_or_disabled_member",
        "heating_assistance_need",
        "recent_job_loss",
    ]:
        st.session_state[key] = "Unknown"
    st.session_state["county"] = "Allegheny"


def _raw_input_from_session() -> dict[str, Any]:
    return {
        "user_description": st.session_state.get("user_description") or None,
        "county": st.session_state.get("county") or None,
        "zip_code": st.session_state.get("zip_code") or None,
        "num_adults": _parse_optional_int(st.session_state.get("num_adults", "")),
        "num_children": _parse_optional_int(st.session_state.get("num_children", "")),
        "child_under_5": TRI_STATE_OPTIONS[st.session_state.get("child_under_5", "Unknown")],
        "pregnant_household_member": TRI_STATE_OPTIONS[st.session_state.get("pregnant_household_member", "Unknown")],
        "elderly_or_disabled_member": TRI_STATE_OPTIONS[st.session_state.get("elderly_or_disabled_member", "Unknown")],
        "employment_status": st.session_state.get("employment_status") or None,
        "monthly_earned_income": _parse_optional_float(st.session_state.get("monthly_earned_income", "")),
        "monthly_unearned_income": _parse_optional_float(st.session_state.get("monthly_unearned_income", "")),
        "household_income_total": _parse_optional_float(st.session_state.get("household_income_total", "")),
        "housing_cost": _parse_optional_float(st.session_state.get("housing_cost", "")),
        "utility_burden": st.session_state.get("utility_burden") or None,
        "heating_assistance_need": TRI_STATE_OPTIONS[st.session_state.get("heating_assistance_need", "Unknown")],
        "insurance_status": st.session_state.get("insurance_status") or None,
        "recent_job_loss": TRI_STATE_OPTIONS[st.session_state.get("recent_job_loss", "Unknown")],
        "food_insecurity_signal": st.session_state.get("food_insecurity_signal") or None,
        "language_or_stress_notes": st.session_state.get("language_or_stress_notes") or None,
    }


def _render_results(session) -> None:
    st.subheader("Navigator Output")
    st.caption("This is retrieval-grounded prescreening only. It is not an official eligibility determination.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Intake Status", session.intake.intake_status)
    col2.metric("Decision Status", session.eligibility.decision_status)
    col3.metric("Final Status", session.explanation.final_status)

    st.markdown("### Intake Summary")
    # Use markdown with escaped $ to prevent LaTeX rendering
    safe_summary = session.intake.intake_summary.replace("$", r"\$")
    st.markdown(safe_summary)
    if session.intake.extracted_signals:
        st.caption("Extracted signals: " + ", ".join(session.intake.extracted_signals))
    if session.intake.clarification_questions:
        st.markdown("**Clarifications**")
        for item in session.intake.clarification_questions:
            st.write(f"- {item}")

    st.markdown("### Priority Order")
    if session.eligibility.priority_order:
        st.write(" > ".join(session.eligibility.priority_order))
    else:
        st.write("No clear ranked matches yet.")

    st.markdown("### Program Matches")
    for match in session.eligibility.program_matches:
        if match.status == "strong_match":
            st.success(f"{match.program_name}: {match.status} (score {match.match_score})")
        elif match.status == "possible_match":
            st.warning(f"{match.program_name}: {match.status} (score {match.match_score})")
        else:
            st.info(f"{match.program_name}: {match.status} (score {match.match_score})")

        with st.expander(f"Why {match.program_name}?"):
            for reason in match.rationale:
                st.write(f"- {reason.reason}")
                if reason.evidence_snippet:
                    # Truncate long policy text to keep UI clean
                    snippet = reason.evidence_snippet[:300].rsplit(" ", 1)[0] + "…"
                    st.caption(snippet)
            if match.retrieved_evidence:
                st.markdown("**Retrieved evidence**")
                for chunk in match.retrieved_evidence:
                    label = chunk.section_title or chunk.title
                    snippet = chunk.text[:200].rsplit(" ", 1)[0] + "…"
                    st.write(f"- **[{label}]** {snippet}")
                    if chunk.source_url:
                        st.caption(chunk.source_url)

    left, right = st.columns([1, 1])
    with left:
        st.markdown("### Explanation")
        st.write(session.explanation.plain_language_explanation)
        st.markdown("### Next Steps")
        for step in session.explanation.next_steps:
            st.write(f"- {step}")

    with right:
        st.markdown("### Checklist")
        for program, items in session.explanation.checklist_by_program.items():
            st.write(f"**{program}**")
            for item in items:
                st.write(f"- {item}")
        st.markdown("### Caveats")
        for caveat in session.explanation.visible_caveats:
            st.write(f"- {caveat}")

    with st.expander("Session JSON"):
        st.json(session.model_dump())


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🧭", layout="wide")
    st.title(PAGE_TITLE)
    st.caption(
        "Upgraded project: local policy retrieval, policy ingestion, and agent-assisted prescreening."
    )

    for key, default in [
        ("chat_active", False),
        ("chat_history", []),
        ("chat_raw_input", {}),
        ("chat_rounds", 0),
        ("nav_session", None),
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    cases = load_demo_cases()
    case_options = ["Custom"] + list(cases.keys())

    BUILTIN_PROGRAMS = ["SNAP", "Medicaid/CHIP", "LIHEAP"]
    uploaded_program_names = sorted({
        doc.program_name
        for doc in load_policy_documents()
        if doc.uploaded and doc.program_name not in BUILTIN_PROGRAMS
    })
    all_available_programs = BUILTIN_PROGRAMS + uploaded_program_names

    with st.sidebar:
        st.header("Demo Controls")
        selected = st.selectbox("Load demo case", case_options, index=0)
        if st.button("Load Case", use_container_width=True):
            if selected != "Custom":
                _apply_case(selected, cases[selected])
            st.rerun()
        if selected != "Custom":
            st.write(cases[selected]["scenario_summary"])
            st.caption(f"Case type: {cases[selected]['case_type']}")
            st.caption(f"Turns in fixture: {cases[selected]['turn_count']}")

        st.markdown("---")
        st.subheader("Programs to Evaluate")
        selected_programs = st.multiselect(
            "Select programs",
            options=all_available_programs,
            default=all_available_programs,
            help="Only the selected programs will be screened. Uncheck any you want to exclude.",
        )

    with st.container():
        # ── Phase 1: initial input form ───────────────────────────────────────
        with st.form("navigator_form"):
            st.text_area(
                "Household description",
                key="user_description",
                height=160,
                placeholder="Describe the household in plain language. Example: I am a single adult in Allegheny County, recently lost work hours, struggle to afford groceries, and I am behind on my gas bill.",
            )
            st.caption("Optional structured fields below can fill gaps or override what the intake stage extracts from the description.")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.selectbox("County", ["Allegheny", "Other"], key="county")
                st.text_input("ZIP Code", key="zip_code")
                st.text_input("Number of adults", key="num_adults")
                st.text_input("Number of children", key="num_children")
                st.selectbox(
                    "Employment status",
                    ["", "full_time", "part_time", "self_employed", "recent_job_loss", "unemployed"],
                    key="employment_status",
                )
            with c2:
                st.text_input("Monthly earned income", key="monthly_earned_income")
                st.text_input("Monthly unearned income", key="monthly_unearned_income")
                st.text_input("Household income total", key="household_income_total")
                st.text_input("Housing cost", key="housing_cost")
                st.selectbox("Insurance status", ["", "insured", "underinsured", "uninsured", "unknown"], key="insurance_status")
            with c3:
                st.selectbox("Utility burden", ["", "low", "medium", "high"], key="utility_burden")
                st.selectbox("Food insecurity signal", ["", "none", "possible", "clear"], key="food_insecurity_signal")
                st.selectbox("Child under 5", list(TRI_STATE_OPTIONS), key="child_under_5")
                st.selectbox("Pregnant household member", list(TRI_STATE_OPTIONS), key="pregnant_household_member")
                st.selectbox("Elderly or disabled member", list(TRI_STATE_OPTIONS), key="elderly_or_disabled_member")
                st.selectbox("Heating assistance need", list(TRI_STATE_OPTIONS), key="heating_assistance_need")
                st.selectbox("Recent job loss", list(TRI_STATE_OPTIONS), key="recent_job_loss")
            st.text_area("Language or stress notes", key="language_or_stress_notes", height=120)
            submitted = st.form_submit_button("Run Retrieval-Grounded Navigator", use_container_width=True)

        if submitted:
            raw = _raw_input_from_session()
            try:
                intake = run_intake(raw)
            except ValueError as exc:
                st.error(f"Please correct the input: {exc}")
                st.stop()

            # Reset conversation state on every new submission
            st.session_state["chat_raw_input"] = raw
            st.session_state["chat_rounds"] = 0
            st.session_state["nav_session"] = None

            if intake.intake_status == "complete" or not intake.clarification_questions:
                # Enough info — skip chat and go straight to full pipeline
                st.session_state["chat_history"] = []
                st.session_state["chat_active"] = False
                try:
                    st.session_state["nav_session"] = run_navigator(raw, selected_programs=selected_programs or None)
                except ValueError as exc:
                    st.error(f"Pipeline error: {exc}")
            else:
                # Start conversational clarification loop
                st.session_state["chat_active"] = True
                opening = f"Thanks for sharing. {intake.intake_summary}"
                msgs = [{"role": "assistant", "content": opening}]
                for q in intake.clarification_questions:
                    msgs.append({"role": "assistant", "content": q})
                msgs.append({
                    "role": "assistant",
                    "content": "Feel free to answer in plain language. You can say \"I don't know\" or \"skip\" for anything you'd rather not share.",
                })
                st.session_state["chat_history"] = msgs
            st.rerun()

        # ── Phase 2: conversational clarification chat ────────────────────────
        if st.session_state.get("chat_active"):
            st.markdown("---")
            st.markdown("### Intake Conversation")

            for msg in st.session_state.get("chat_history", []):
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

            reply = st.chat_input("Type your answer here…")
            if reply:
                st.session_state["chat_history"].append({"role": "user", "content": reply})
                st.session_state["chat_rounds"] += 1

                prior_raw = st.session_state["chat_raw_input"]
                new_raw, intake = run_intake_turn(prior_raw, reply)
                st.session_state["chat_raw_input"] = new_raw

                rounds_used = st.session_state["chat_rounds"]
                intake_done = (
                    intake.intake_status == "complete"
                    or not intake.clarification_questions
                    or rounds_used >= MAX_CHAT_ROUNDS
                )

                if intake_done:
                    st.session_state["chat_active"] = False
                    closing = (
                        "Got it — I have enough to check your eligibility now."
                        if intake.intake_status == "complete"
                        else "Thanks for what you shared. I'll work with what we have."
                    )
                    st.session_state["chat_history"].append({"role": "assistant", "content": closing})
                    try:
                        st.session_state["nav_session"] = run_navigator(new_raw, selected_programs=selected_programs or None)
                    except ValueError as exc:
                        st.session_state["chat_history"].append({
                            "role": "assistant",
                            "content": f"Something went wrong: {exc}",
                        })
                else:
                    for q in intake.clarification_questions:
                        st.session_state["chat_history"].append({"role": "assistant", "content": q})

                st.rerun()

        # ── Phase 3: show navigator results ──────────────────────────────────
        if st.session_state.get("nav_session"):
            nav = st.session_state["nav_session"]
            if nav.uploaded_documents_available:
                st.info("Uploaded policies available: " + ", ".join(nav.uploaded_documents_available))
            _render_results(nav)



if __name__ == "__main__":
    main()
