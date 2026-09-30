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
  .block-container {{ padding-top: 2.2rem; max-width: 1500px; }}
  #MainMenu, footer {{ visibility: hidden; }}

  .dri-head {{ display:flex; align-items:baseline; gap:.75rem; flex-wrap:wrap;
               margin-bottom:.2rem; }}
  .dri-head h1 {{ font-family:{T.FONT}; font-size:1.65rem; font-weight:650;
                  color:{T.INK_PRIMARY}; margin:0; letter-spacing:-.015em; }}
  .dri-sub {{ font-family:{T.FONT}; font-size:.9rem; color:{T.INK_MUTED};
              margin:0 0 1.1rem 0; }}

  .dri-hero-label {{ font-family:{T.FONT}; font-size:.78rem; font-weight:600;
                     letter-spacing:.07em; text-transform:uppercase;
                     color:{T.INK_MUTED}; margin-bottom:.15rem; }}
  .dri-hero-value {{ font-family:{T.FONT}; font-size:3.4rem; font-weight:650;
                     line-height:1.02; color:{T.INK_PRIMARY};
                     letter-spacing:-.03em; }}
  .dri-hero-unit {{ font-size:1.05rem; font-weight:500; color:{T.INK_SECONDARY};
                    margin-left:.35rem; letter-spacing:0; }}
  .dri-hero-note {{ font-family:{T.FONT}; font-size:.84rem;
                    color:{T.INK_SECONDARY}; margin-top:.35rem; }}

  .dri-tile {{ background:{T.SURFACE}; border:1px solid {T.BORDER};
               border-radius:10px; padding:.85rem .95rem; height:100%; }}
  .dri-tile-label {{ font-family:{T.FONT}; font-size:.76rem; font-weight:600;
                     letter-spacing:.05em; text-transform:uppercase;
                     color:{T.INK_MUTED}; margin-bottom:.3rem; }}
  .dri-tile-value {{ font-family:{T.FONT}; font-size:1.45rem; font-weight:650;
                     color:{T.INK_PRIMARY}; line-height:1.15;
                     letter-spacing:-.02em; }}
  .dri-tile-unit {{ font-size:.8rem; font-weight:500; color:{T.INK_MUTED};
                    margin-left:.28rem; letter-spacing:0; }}
  .dri-tile-delta {{ font-family:{T.FONT}; font-size:.8rem; font-weight:550;
                     margin-top:.22rem; }}
  .dri-tile-flat {{ color:{T.INK_MUTED}; }}

  .dri-chip {{ display:inline-flex; align-items:center; gap:.4rem;
               font-family:{T.FONT}; font-size:.78rem; font-weight:600;
               padding:.2rem .55rem; border-radius:999px;
               border:1px solid {T.BORDER}; background:{T.SURFACE};
               color:{T.INK_SECONDARY}; }}
  .dri-chip-dot {{ font-size:.72rem; line-height:1; }}

  .dri-section {{ font-family:{T.FONT}; font-size:1.02rem; font-weight:620;
                  color:{T.INK_PRIMARY}; margin:1.5rem 0 .1rem 0; }}
  .dri-section-note {{ font-family:{T.FONT}; font-size:.84rem;
                       color:{T.INK_MUTED}; margin:0 0 .7rem 0; }}

  div[data-testid="stMetricValue"] {{ font-family:{T.FONT}; }}
  .stTabs [data-baseweb="tab"] {{ font-family:{T.FONT}; font-weight:550; }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str, chips: list[tuple[str, str]]) -> None:
    """Product header with a row of status chips."""
    chip_html = "".join(
        f'<span class="dri-chip"><span class="dri-chip-dot" '
        f'style="color:{color}">●</span>{html.escape(text)}</span>'
        for text, color in chips)
    st.markdown(
        f'<div class="dri-head"><h1>{html.escape(title)}</h1>{chip_html}</div>'
        f'<p class="dri-sub">{html.escape(subtitle)}</p>',
        unsafe_allow_html=True)


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


def section(title: str, note: str = "") -> None:
    note_html = (f'<p class="dri-section-note">{html.escape(note)}</p>'
                 if note else "")
    st.markdown(f'<div class="dri-section">{html.escape(title)}</div>{note_html}',
                unsafe_allow_html=True)
