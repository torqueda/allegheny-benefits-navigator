from __future__ import annotations

import streamlit as st

from app import _clear_current_screening


def test_clear_current_screening_resets_sensitive_inputs() -> None:
    st.session_state.clear()
    st.session_state["user_description"] = "Sensitive household details"
    st.session_state["household_income_total"] = "1200"
    st.session_state["pregnant_household_member"] = "Yes"
    st.session_state["nav_session"] = {"debug": "payload"}

    _clear_current_screening()

    assert st.session_state["user_description"] == ""
    assert st.session_state["household_income_total"] == ""
    assert st.session_state["pregnant_household_member"] == "Unknown"
    assert st.session_state["nav_session"] is None


def test_clear_current_screening_resets_chat_and_case_state() -> None:
    st.session_state.clear()
    st.session_state["selected_case"] = "AGENT_04"
    st.session_state["chat_active"] = True
    st.session_state["chat_history"] = [{"role": "user", "content": "hello"}]
    st.session_state["chat_raw_input"] = {"user_description": "test"}
    st.session_state["chat_rounds"] = 2

    _clear_current_screening()

    assert st.session_state["selected_case"] == "Custom"
    assert st.session_state["chat_active"] is False
    assert st.session_state["chat_history"] == []
    assert st.session_state["chat_raw_input"] == {}
    assert st.session_state["chat_rounds"] == 0
