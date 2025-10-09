import importlib

import streamlit as st


def test_responsive_sidebar_toggle_only_creates_checkbox_once(monkeypatch):
    # Ensure a clean session state
    st.session_state.clear()

    call_count = {"calls": 0}


    def fake_checkbox(label, key=None):
        # Increment on call and set the session state like Streamlit would
        call_count["calls"] += 1
        if key is not None:
            st.session_state[key] = st.session_state.get(key, False)
        return st.session_state.get(key, False)


    # Monkeypatch the sidebar.checkbox
    monkeypatch.setattr(st.sidebar, "checkbox", fake_checkbox)

    # Import the module under test and call twice
    mod = importlib.import_module("src.utils.responsive")
    mod.responsive_sidebar_toggle()
    mod.responsive_sidebar_toggle()

    # The checkbox should have been created only once
    assert call_count["calls"] == 1
