"""First page: the recommendation, the kiln as it is set, and what moves the cost."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui import components as ui


def recommendation(rec: dict | None, target_label: str, unreachable_note: str) -> None:
    if rec is None:
        st.warning(unreachable_note, icon="⚠")
        return
    pay = rec["payback_yr"]
    label = rec["label"]
    ui.exhibit(
        f"Cheapest route to a {target_label} cut",
        label[:1].upper() + label[1:],
        [
            ("A tonne then costs", rec["cost_text"]),
            ("Carbon dioxide", rec["cut_text"]),
            ("Paid back", "—" if pay is None or pay >= 50 else f"{pay:.1f} years"),
        ])


def headlines(items: list[dict]) -> None:
    ui.section("This kiln as set", "Everything set in the sidebar, including any retrofit switched on.")
    c = st.columns(len(items))
    for col, item in zip(c, items):
        with col:
            ui.stat_tile(item["label"], item["value"], item["unit"])


def swings(rows: list[dict]) -> None:
    ui.section("What moves the cost most",
               "Each assumption is pushed to both ends of its published range "
               "while every other assumption stays at the base case.")
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.caption("No assumption in the sweep moves the cost enough to list.")
