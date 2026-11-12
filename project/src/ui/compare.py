"""Three plants side by side: the sidebar, imported coal, and domestic coal."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.ui import components as ui
from src.ui.labels import plain_parameter


def render(rows: list[dict], diffs: list[dict]) -> None:
    ui.section(
        "Three columns, one kiln size",
        "Domestic coal is the published coal with the ash raised. "
        "It is not a sample from an Indian mine.")
    table = pd.DataFrame(rows)
    st.dataframe(table, width="stretch", hide_index=True)
    ui.section(
        "What you changed from the published file",
        "A downloaded scenario stores these settings, the model version and "
        "the fingerprint of the assumption file. It does not store a second set of results.")
    if diffs:
        def _cell(value) -> str:
            if value is None:
                return ""
            if isinstance(value, float):
                return f"{value:.6g}"
            return str(value)

        shown = pd.DataFrame([{
            "Assumption changed": plain_parameter(row["parameter"]),
            "Figure in the published file": _cell(row["left"]),
            "Figure in this run": _cell(row["right"]),
        } for row in diffs])
        st.dataframe(shown, width="stretch", hide_index=True)
    else:
        st.caption("The sidebar is the parameter file, with nothing overridden.")
