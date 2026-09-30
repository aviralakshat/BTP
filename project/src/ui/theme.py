"""Visual language for the dashboard: palette, Plotly template, formatters.

The palette is the validated reference instance. It was checked with the
data-viz validator for the four adjacent categorical slots used here against the
light chart surface #fcfcfb:

    Lightness band      PASS   all 4 inside L 0.43-0.77
    Chroma floor        PASS   all 4 >= 0.1
    CVD separation      PASS   worst adjacent pair dE 9.1 (protan), target >= 8
    Normal-vision floor PASS   worst adjacent pair dE 22.9, floor >= 15
    Contrast vs surface WARN   aqua 2.74 and yellow 2.11 are below 3:1

That contrast warning is not dismissable: it obligates relief. Every chart in
charts.py therefore carries visible direct labels AND a table-view twin, which is
how the obligation is discharged.

Only the light mode is shipped. Dark mode is a *selected* set of steps validated
against the dark surface, not an automatic inversion, so the app pins the light
surface in .streamlit/config.toml rather than shipping an unvalidated flip.
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# --- surfaces and ink ------------------------------------------------------
SURFACE = "#fcfcfb"
PAGE = "#f9f9f7"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
BASELINE = "#c3c2b7"
BORDER = "rgba(11,11,11,0.10)"

# --- categorical slots, in fixed order (never cycled) ----------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
          "#e87ba4", "#008300", "#4a3aa7", "#e34948"]

# --- sequential blue ramp --------------------------------------------------
BLUE = {100: "#cde2fb", 150: "#b7d3f6", 200: "#9ec5f4", 250: "#86b6ef",
        300: "#6da7ec", 350: "#5598e7", 400: "#3987e5", 450: "#2a78d6",
        500: "#256abf", 550: "#1c5cab", 600: "#184f95", 650: "#104281",
        700: "#0d366b"}

# --- diverging pair: warm/cool poles with a neutral gray midpoint ----------
# Cost added vs credit received is a genuine polarity, so it gets a diverging
# pair rather than two categorical slots. blue<->orange is used in preference to
# blue<->red because a credit is a good outcome and red reads as alarm.
DIVERGING_POS = SERIES[0]
DIVERGING_NEG = SERIES[1]
DIVERGING_MID = "#f0efec"

# --- status palette (reserved; never reused for a series) ------------------
STATUS = {"good": "#0ca30c", "warning": "#fab219",
          "serious": "#ec835a", "critical": "#d03b3b"}
#: Status always ships as icon + label so hue never carries the meaning alone.
VERDICT = {
    "PASS": {"color": STATUS["good"], "icon": "●", "label": "Pass"},
    "WARN": {"color": STATUS["warning"], "icon": "▲", "label": "Warning"},
    "FAIL": {"color": STATUS["critical"], "icon": "■", "label": "Fail"},
    "INFO": {"color": INK_MUTED, "icon": "○", "label": "Reference"},
}
PROVENANCE = {
    "verified": {"color": STATUS["good"], "icon": "●", "label": "Verified"},
    "needs_citation": {"color": STATUS["warning"], "icon": "▲",
                       "label": "Needs Citation"},
    "physical_constant": {"color": INK_MUTED, "icon": "○",
                          "label": "Physical Constant"},
    "derived": {"color": INK_MUTED, "icon": "○", "label": "Derived"},
}

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'
#: Bars are capped rather than filling their band, so the leftover is air.
BAR_CORNER_RADIUS = 4


def register_template() -> str:
    """Register and select the Plotly template used by every chart."""
    axis = dict(
        showgrid=True, gridcolor=GRIDLINE, gridwidth=1, griddash="solid",
        zeroline=False, showline=False, ticks="outside", ticklen=4,
        tickcolor=BASELINE,
        tickfont=dict(color=INK_MUTED, size=12, family=FONT),
        title=dict(font=dict(color=INK_SECONDARY, size=12, family=FONT)),
        automargin=True,
    )
    pio.templates["dri"] = go.layout.Template(
        layout=dict(
            font=dict(family=FONT, color=INK_SECONDARY, size=13),
            paper_bgcolor=SURFACE,
            plot_bgcolor=SURFACE,
            colorway=SERIES,
            xaxis=axis, yaxis=axis,
            margin=dict(l=8, r=24, t=8, b=8),
            hoverlabel=dict(
                bgcolor=SURFACE, bordercolor=BORDER, align="left",
                font=dict(family=FONT, color=INK_PRIMARY, size=13)),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, x=0,
                bgcolor="rgba(0,0,0,0)",
                font=dict(color=INK_SECONDARY, size=12, family=FONT)),
            bargap=0.45,
            separators=".,",
        )
    )
    pio.templates.default = "dri"
    return "dri"


# --- formatters ------------------------------------------------------------
def compact(value: float, unit: str = "") -> str:
    """Auto-compact a stat-tile value: 5.77 / 1,284 / 12.9K / 4.2M.

    Abbreviation starts at ten thousand, so four-digit counts stay readable as
    themselves. Precision tightens as magnitude grows.
    """
    v = float(value)
    suffix = ""
    for cut, s in ((1e9, "B"), (1e6, "M"), (1e4, "K")):
        if abs(v) >= cut:
            v, suffix = v / (1e3 if s == "K" else cut), s
            break
    if suffix:
        text = f"{v:,.1f}".removesuffix(".0")
    elif abs(v) >= 100:
        text = f"{v:,.0f}"
    elif abs(v) >= 10:
        text = f"{v:,.1f}"
    else:
        text = f"{v:,.2f}"
    return f"{text}{suffix}{(' ' + unit) if unit else ''}"


def rupees(value: float, compact_form: bool = False) -> str:
    """Currency with the sign outside the symbol: -₹170, never ₹-170."""
    sign = "-" if value < 0 else ""
    v = abs(value)
    if compact_form and v >= 1e7:
        return f"{sign}₹{v / 1e7:,.2f} Cr"
    if compact_form and v >= 1e5:
        return f"{sign}₹{v / 1e5:,.2f} L"
    return f"{sign}₹{v:,.0f}"


def signed(value: float, decimals: int = 2, unit: str = "") -> str:
    return f"{value:+,.{decimals}f}{(' ' + unit) if unit else ''}"


def rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def fits_inside(label: str, fraction_of_axis: float) -> bool:
    """Whether a direct label fits inside its own mark, with padding.

    Labels are measured before placement rather than clipped: a mark shorter
    than roughly 9px per character plus padding gets its label outside the end.
    """
    return fraction_of_axis >= (len(label) + 3) * 0.011
