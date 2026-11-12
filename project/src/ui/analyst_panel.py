"""Chat that quotes the plant tools. No language-model API is called."""
from __future__ import annotations

import json

import streamlit as st

from src.agent.analyst import answer

_CAP = 12


def render(*, capacity_tpd: float, utilization: float, preset: str,
           overrides: dict) -> None:
    st.caption(
        f"A session holds {_CAP} questions. Try “what does this kiln cost”, "
        "“cheapest way to cut 20% of CO2”, or “set the coal price”.")
    if "analyst_turns" not in st.session_state:
        st.session_state.analyst_turns = []
    for turn in st.session_state.analyst_turns:
        with st.chat_message(turn["role"]):
            st.write(turn["text"])
            if turn.get("tools"):
                with st.expander("Show calculation"):
                    st.code(json.dumps(turn["tools"], default=str, indent=2),
                            language="json")
    prompt = st.chat_input("Ask about this plant")
    if not prompt:
        return
    asked = sum(1 for turn in st.session_state.analyst_turns if turn["role"] == "user")
    st.session_state.analyst_turns.append({"role": "user", "text": prompt})
    reply = answer(prompt, capacity_tpd=capacity_tpd, utilization=utilization,
                   preset=preset, overrides=overrides, turns_so_far=asked)
    text = reply["text"]
    if not reply["grounded"]:
        text = ("This answer quoted a number that is not in the calculation, "
                "so it is withheld.")
    st.session_state.analyst_turns.append({
        "role": "assistant",
        "text": text,
        "tools": reply["tools"],
    })
    st.rerun()
