"""Small presentation components: hero figure, stat tiles, status chips.

Only values and labels the app itself controls are interpolated into HTML.
Free text that originates in the config files (parameter sources, notes) is
rendered through Streamlit's own widgets instead, never through raw HTML.
"""
from __future__ import annotations

import html

import streamlit as st

from src.ui import theme as T

CSS = f"""
<style>
  .block-container {{ padding-top: 2.6rem; padding-bottom: 4rem; max-width: 1180px; }}
  /* The header holds the button that reopens a collapsed sidebar, so it stays. */
  header[data-testid="stHeader"] {{ background: transparent; }}
  [data-testid="stAppDeployButton"], footer {{ display: none; }}
  section[data-testid="stSidebar"] {{
    background: {T.PAGE}; border-right: 1px solid {T.GRIDLINE}; }}
  section[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
  section[data-testid="stSidebar"] label {{ font-family: {T.FONT}; }}
  .dri-side-h {{ font-family: {T.FONT}; font-size: .68rem; font-weight: 650;
                 letter-spacing: .14em; text-transform: uppercase;
                 color: {T.BLUE[650]}; margin: 1.1rem 0 .2rem 0;
                 padding-top: .7rem; border-top: 1px solid {T.GRIDLINE}; }}
  .dri-side-h.first {{ border-top: 0; padding-top: 0; margin-top: 0; }}

  .dri-kicker {{ font-family: {T.FONT}; font-size: .68rem;
                 font-weight: 600; letter-spacing: .16em; text-transform: uppercase;
                 color: {T.BLUE[650]}; margin: 0 0 .35rem 0; }}
  .dri-head {{ display:flex; align-items:flex-end; justify-content:space-between;
               gap: 1rem; flex-wrap: wrap;
               border-bottom: 1px solid {T.INK_PRIMARY}; padding-bottom: .7rem;
               margin-bottom: .55rem; }}
  .dri-head h1 {{ font-family: {T.DISPLAY}; font-size: 2.15rem;
                  font-weight: 400; color: {T.INK_PRIMARY}; margin: 0;
                  letter-spacing: -.02em; line-height: 1; }}
  .dri-sub {{ font-family: {T.FONT}; font-size: .92rem;
              color: {T.INK_SECONDARY}; margin: .35rem 0 0 0; }}
  .dri-chips {{ display:flex; gap: .4rem; flex-wrap: wrap; justify-content: flex-end; }}

  .dri-hero-label {{ font-family:{T.FONT}; font-size:.78rem; font-weight:600;
                     letter-spacing:.07em; text-transform:uppercase;
                     color:{T.INK_MUTED}; margin-bottom:.15rem; }}
  .dri-hero-value {{ font-family: {T.DISPLAY}; font-size: 3.6rem;
                     font-weight: 400; line-height: 1; color: {T.INK_PRIMARY};
                     letter-spacing: -.03em; }}
  .dri-hero-unit {{ font-size:1.05rem; font-weight:500; color:{T.INK_SECONDARY};
                    margin-left:.35rem; letter-spacing:0; }}
  .dri-hero-note {{ font-family:{T.FONT}; font-size:.84rem;
                    color:{T.INK_SECONDARY}; margin-top:.35rem; }}

  .dri-tile {{ background: transparent; border: 0; border-top: 2px solid {T.BLUE[650]};
               border-radius: 0; padding: .7rem 0 .2rem 0; height: 100%; }}
  .dri-tile-label {{ font-family: {T.FONT}; font-size: .68rem;
                     font-weight: 600; letter-spacing: .12em; text-transform: uppercase;
                     color: {T.INK_MUTED}; margin-bottom: .35rem; }}
  .dri-tile-value {{ font-family: {T.DISPLAY}; font-size: 1.7rem;
                     font-weight: 400; color: {T.INK_PRIMARY}; line-height: 1.05;
                     letter-spacing: -.02em; }}
  .dri-tile-unit {{ font-size:.8rem; font-weight:500; color:{T.INK_MUTED};
                    margin-left:.28rem; letter-spacing:0; }}
  .dri-tile-delta {{ font-family:{T.FONT}; font-size:.8rem; font-weight:550;
                     margin-top:.22rem; }}
  .dri-tile-flat {{ color:{T.INK_MUTED}; }}

  .dri-chip {{ display:inline-flex; align-items:center; gap:.35rem;
               font-family: {T.FONT}; font-size: .72rem; font-weight: 600;
               letter-spacing: .02em; padding: 0; border: 0; background: transparent;
               color: {T.INK_SECONDARY}; }}
  .dri-chip-bar {{ width: 9px; height: 9px; display: inline-block; }}

  .dri-section {{ font-family: {T.DISPLAY}; font-size: 1.25rem;
                  font-weight: 400; color: {T.INK_PRIMARY}; margin: 1.6rem 0 .15rem 0; }}
  .dri-section-note {{ font-family: {T.FONT}; font-size: .82rem;
                       color: {T.INK_MUTED}; margin: 0 0 .65rem 0; max-width: 46rem; }}

  .dri-lead-q {{ font-family: {T.DISPLAY}; font-size: 1.55rem;
                 font-weight: 400; color: {T.INK_PRIMARY}; margin: .2rem 0 .15rem 0;
                 letter-spacing: -.02em; }}
  .dri-exhibit {{ border-top: 1px solid {T.INK_PRIMARY};
                  border-bottom: 1px solid {T.GRIDLINE};
                  padding: 1rem 0 1.1rem; margin: .2rem 0 1.1rem; }}
  .dri-exhibit-metrics {{ display: grid; grid-template-columns: repeat(3, 1fr);
                          gap: 1.25rem; margin-top: 1rem; }}
  .dri-exhibit-kicker {{ font-family: {T.FONT}; font-size: .68rem;
                         font-weight: 600; letter-spacing: .14em; text-transform: uppercase;
                         color: {T.BLUE[650]}; margin-bottom: .35rem; }}
  .dri-exhibit-title {{ font-family: {T.DISPLAY}; font-size: 1.55rem;
                        font-weight: 400; line-height: 1.15; color: {T.INK_PRIMARY};
                        margin: 0; }}
  .dri-steps {{ display: none; }}
  .dri-step {{ background:{T.SURFACE}; border:1px solid {T.BORDER};
               border-radius:0; padding:.75rem .85rem; }}
  .dri-step-n {{ font-family:{T.FONT}; font-size:.7rem; font-weight:650;
                 letter-spacing:.06em; text-transform:uppercase;
                 color:{T.INK_MUTED}; }}
  .dri-step-t {{ font-family:{T.FONT}; font-size:.92rem; font-weight:620;
                 color:{T.INK_PRIMARY}; margin:.18rem 0 .12rem 0; }}
  .dri-step-d {{ font-family:{T.FONT}; font-size:.8rem; color:{T.INK_SECONDARY};
                 margin:0; line-height:1.35; }}

  .dri-kiln {{ width: 100%; height: auto; display: block; margin: .2rem 0 1rem; }}
  .dri-note {{ font-family: {T.FONT}; font-size: .8rem; color: {T.INK_SECONDARY};
               background: {T.PAGE}; border-left: 3px solid {T.BLUE[250]};
               padding: .45rem .7rem; margin: .1rem 0 .8rem 0; }}
  @media (max-width: 860px) {{
    .dri-exhibit-metrics {{ grid-template-columns: 1fr 1fr; }}
    .dri-head h1 {{ font-size: 1.7rem; }}
    .dri-hero-value {{ font-size: 2.6rem; }}
  }}

  div[data-testid="stMetricValue"] {{ font-family: {T.DISPLAY}; }}
  .stTabs [role="tablist"] {{ gap: .15rem; border-bottom: 1px solid {T.GRIDLINE}; }}
  .stTabs [role="tab"] {{ font-family: {T.FONT};
    font-weight: 600; font-size: .9rem; letter-spacing: .01em;
    background: transparent; border-radius: 0; padding: .6rem .85rem; }}
  .stTabs [role="tab"][aria-selected="true"] {{ color: {T.INK_PRIMARY}; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str, chips: list[tuple[str, str]]) -> None:
    """Exhibit header: a kicker, a serif title, and the status of this run."""
    chip_html = "".join(
        f'<span class="dri-chip"><span class="dri-chip-bar" '
        f'style="background:{color}"></span>{html.escape(text)}</span>'
        for text, color in chips)
    st.markdown(
        f'<p class="dri-kicker">Sponge iron plant</p>'
        f'<div class="dri-head"><div><h1>{html.escape(title)}</h1>'
        f'<p class="dri-sub">{html.escape(subtitle)}</p></div>'
        f'<div class="dri-chips">{chip_html}</div></div>',
        unsafe_allow_html=True)


def exhibit(kicker: str, title: str, metrics: list[tuple[str, str]]) -> None:
    """One recommendation across the page. Metrics are a label and a value."""
    cells = "".join(
        f'<div><div class="dri-tile-label">{html.escape(label)}</div>'
        f'<div class="dri-tile-value">{html.escape(value)}</div></div>'
        for label, value in metrics)
    st.markdown(
        f'<div class="dri-exhibit"><div>'
        f'<div class="dri-exhibit-kicker">{html.escape(kicker)}</div>'
        f'<p class="dri-exhibit-title">{html.escape(title)}</p></div>'
        f'<div class="dri-exhibit-metrics">{cells}</div></div>',
        unsafe_allow_html=True)


def kiln_schematic(feeds: list[tuple[str, str]], products: list[tuple[str, str]]) -> None:
    """The kiln as a figure. Each pair is a stream name and its live rate."""
    def column(items: list[tuple[str, str]], x: int, anchor: str) -> str:
        rows = []
        for i, (name, value) in enumerate(items):
            y = 48 + i * 58
            rows.append(
                f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
                f"font-family='{T.FONT}' font-size=\"11\" "
                f'fill="{T.INK_MUTED}" letter-spacing="1.2">{html.escape(name.upper())}</text>'
                f'<text x="{x}" y="{y + 20}" text-anchor="{anchor}" '
                f"font-family='{T.DISPLAY}' font-size=\"16\" "
                f'fill="{T.INK_PRIMARY}">{html.escape(value)}</text>')
        return "".join(rows)

    svg = f'''<svg class="dri-kiln" viewBox="0 0 1000 300" role="img"
        aria-label="Inclined rotary kiln with the live feed and product rates">
      <text x="500" y="26" text-anchor="middle"
        font-family='{T.FONT}' font-size="11" letter-spacing="2"
        fill="{T.BLUE[650]}">PER TONNE OF SPONGE IRON</text>
      {column(feeds, 16, "start")}
      <line x1="150" y1="70" x2="210" y2="168" stroke="{T.GRIDLINE}" stroke-width="1"/>
      <line x1="150" y1="128" x2="230" y2="188" stroke="{T.GRIDLINE}" stroke-width="1"/>
      <line x1="150" y1="186" x2="250" y2="208" stroke="{T.GRIDLINE}" stroke-width="1"/>
      <line x1="150" y1="244" x2="270" y2="228" stroke="{T.GRIDLINE}" stroke-width="1"/>
      <polygon points="210,150 760,78 790,132 240,204"
        fill="{T.BLUE[150]}" stroke="{T.BLUE[650]}" stroke-width="1.5"/>
      <polygon points="210,150 240,204 228,214 198,160"
        fill="{T.BLUE[250]}" stroke="{T.BLUE[650]}" stroke-width="1.5"/>
      <polygon points="760,78 790,132 802,122 772,68"
        fill="{T.SURFACE}" stroke="{T.BLUE[650]}" stroke-width="1.5"/>
      <rect x="300" y="196" width="36" height="10" fill="{T.BLUE[650]}"/>
      <rect x="470" y="158" width="36" height="10" fill="{T.BLUE[650]}"/>
      <rect x="640" y="122" width="36" height="10" fill="{T.BLUE[650]}"/>
      <text x="500" y="128" text-anchor="middle"
        font-family='{T.DISPLAY}' font-size="18"
        fill="{T.BLUE[700]}">Rotary kiln</text>
      <text x="500" y="148" text-anchor="middle"
        font-family='{T.FONT}' font-size="12"
        fill="{T.INK_SECONDARY}">feed hood to discharge hood</text>
      <line x1="820" y1="70" x2="760" y2="90" stroke="{T.GRIDLINE}" stroke-width="1"/>
      <line x1="820" y1="128" x2="790" y2="120" stroke="{T.GRIDLINE}" stroke-width="1"/>
      <line x1="820" y1="186" x2="800" y2="140" stroke="{T.GRIDLINE}" stroke-width="1"/>
      <line x1="820" y1="244" x2="790" y2="150" stroke="{T.GRIDLINE}" stroke-width="1"/>
      {column(products, 984, "end")}
    </svg>'''
    st.markdown(svg, unsafe_allow_html=True)


def hero(label: str, value: str, unit: str, note: str = "") -> None:
    """The single number the view leads with. Exactly one per view."""
    note_html = (f'<div class="dri-hero-note">{html.escape(note)}</div>'
                 if note else "")
    st.markdown(
        f'<div class="dri-hero-label">{html.escape(label)}</div>'
        f'<div class="dri-hero-value">{html.escape(value)}'
        f'<span class="dri-hero-unit">{html.escape(unit)}</span></div>'
        f'{note_html}', unsafe_allow_html=True)


def stat_tile(label: str, value: str, unit: str = "",
              delta: float | None = None, delta_text: str = "",
              lower_is_better: bool = True) -> None:
    """label / value / optional delta against a named comparison."""
    if delta is None or abs(delta) < 1e-9:
        delta_html = (f'<div class="dri-tile-delta dri-tile-flat">'
                      f'{html.escape(delta_text or "No change")}</div>'
                      if delta is not None else "")
    else:
        good = (delta < 0) if lower_is_better else (delta > 0)
        color = "#006300" if good else T.STATUS["critical"]
        arrow = "↓" if delta < 0 else "↑"
        delta_html = (f'<div class="dri-tile-delta" style="color:{color}">'
                      f'{arrow} {html.escape(delta_text)}</div>')
    unit_html = (f'<span class="dri-tile-unit">{html.escape(unit)}</span>'
                 if unit else "")
    st.markdown(
        f'<div class="dri-tile">'
        f'<div class="dri-tile-label">{html.escape(label)}</div>'
        f'<div class="dri-tile-value">{html.escape(value)}{unit_html}</div>'
        f'{delta_html}</div>', unsafe_allow_html=True)


def page_lead(question: str, detail: str = "") -> None:
    """The question this page answers. The second line is optional."""
    note = (f'<p class="dri-section-note">{html.escape(detail)}</p>'
            if detail else "")
    st.markdown(
        f'<p class="dri-lead-q">{html.escape(question)}</p>{note}',
        unsafe_allow_html=True)


def steps(items: list[tuple[str, str, str]]) -> None:
    """Three short instructions. Each item is a number, a title, and a sentence."""
    cards = []
    for number, title, detail in items:
        cards.append(
            f'<div class="dri-step">'
            f'<div class="dri-step-n">{html.escape(number)}</div>'
            f'<div class="dri-step-t">{html.escape(title)}</div>'
            f'<p class="dri-step-d">{html.escape(detail)}</p></div>')
    st.markdown(f'<div class="dri-steps">{"".join(cards)}</div>',
                unsafe_allow_html=True)


def side_heading(title: str, first: bool = False) -> None:
    css = "dri-side-h first" if first else "dri-side-h"
    st.sidebar.markdown(f'<p class="{css}">{html.escape(title)}</p>',
                        unsafe_allow_html=True)


def note(text: str) -> None:
    """One quiet line for caveats that should be visible but not shout."""
    st.markdown(f'<div class="dri-note">{html.escape(text)}</div>',
                unsafe_allow_html=True)


def section(title: str, note: str = "") -> None:
    note_html = (f'<p class="dri-section-note">{html.escape(note)}</p>'
                 if note else "")
    st.markdown(f'<div class="dri-section">{html.escape(title)}</div>{note_html}',
                unsafe_allow_html=True)
