"""Chart builders for the dashboard.

Forms are chosen by the data's job, not by variety:

  Cost composition   polarity (cost added vs credit received) -> diverging bar
  CO2 composition    part-to-whole -> stacked bar, categorical slots
  Mass flow          flow between stages -> Sankey, single hue
  Energy ledger      magnitude by group -> grouped horizontal bar
  Validation         one ratio against a limit -> meter, band track + marker
  Scenario delta     before -> after per item -> dumbbell, one hue two shades

Every builder returns a Plotly figure and every chart in app.py ships a
table-view twin, which is how the palette's sub-3:1 contrast warning on the
aqua and yellow slots is relieved.
"""
from __future__ import annotations

import plotly.graph_objects as go

from src.ui import theme as T
from src.ui.labels import COST_LINES, ENERGY_GROUPS, stream, title_case


def _layout(fig: go.Figure, height: int, **kwargs) -> go.Figure:
    fig.update_layout(height=height, **kwargs)
    return fig


# ---------------------------------------------------------------------------
def cost_composition(econ: dict) -> go.Figure:
    """Diverging bar: what adds to the cost per tonne and what comes back."""
    items = [(COST_LINES.get(k, title_case(k)), v)
             for k, v in econ["breakdown_inr_per_t_dri"].items()
             if abs(v) > 0.5]
    items.sort(key=lambda kv: kv[1])
    labels = [k for k, _ in items]
    values = [v for _, v in items]
    colors = [T.DIVERGING_POS if v >= 0 else T.DIVERGING_NEG for v in values]

    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker=dict(color=colors, cornerradius=T.BAR_CORNER_RADIUS),
        text=[T.rupees(v) for v in values],
        textposition="outside", cliponaxis=False,
        textfont=dict(color=T.INK_SECONDARY, size=12),
        hovertemplate="<b>%{customdata}</b><br>%{y}<extra></extra>",
        customdata=[T.rupees(v) + " per tonne DRI" for v in values],
        showlegend=False,
    ))
    # Zero is the anchor, so the axis need not be symmetric -- forcing symmetry
    # left half the plot empty, since credits are far smaller than costs.
    lo, hi = min(values), max(values)
    pad = (hi - lo) * 0.18
    fig.update_xaxes(range=[min(lo - pad, -pad), hi + pad * 1.6],
                     title="INR per Tonne DRI", tickformat=",.0f")
    fig.add_vline(x=0, line_width=1, line_color=T.BASELINE)
    fig.update_layout(bargap=0.55)
    return _layout(fig, 34 * len(items) + 96)


# ---------------------------------------------------------------------------
def co2_composition(co2: dict, baseline: dict | None = None) -> go.Figure:
    """Stacked bar: the parts of the reported CO2 intensity.

    Rendered as Baseline against Scenario when a retrofit is active. A single
    stacked bar on its own is a one-bar bar chart, which the stat tiles above it
    already do better -- the comparison is what earns the stacked form.
    """
    # Plotly stacks the first category at the bottom, so the list is reversed
    # to make Baseline read first, top-down.
    cols = ([("Scenario", co2), ("Baseline", baseline)] if baseline
            else [("Baseline", co2)])
    parts = [("Direct (Stack)", "co2_direct_t_per_t_dri", T.SERIES[0]),
             ("Scope 2 (Power)", "co2_scope2_t_per_t_dri", T.SERIES[1]),
             ("Biogenic", "co2_biogenic_t_per_t_dri", T.SERIES[2])]

    totals = {name: sum(abs(d.get(k, 0.0)) for _, k, _ in parts)
              for name, d in cols}
    fig = go.Figure()
    for label, key, color in parts:
        values = [d.get(key, 0.0) for _, d in cols]
        if all(abs(v) < 5e-4 for v in values):
            continue                      # nothing to show, so no legend entry
        texts = []
        for (name, _), v in zip(cols, values):
            t = f"{v:.2f}"
            share = abs(v) / max(totals[name], 1e-9)
            # An interior segment has no free end, so a label that will not fit
            # goes to the legend and tooltip rather than being clipped.
            texts.append(t if T.fits_inside(t, share) else "")
        fig.add_trace(go.Bar(
            x=values, y=[name for name, _ in cols], orientation="h", name=label,
            marker=dict(color=color, cornerradius=T.BAR_CORNER_RADIUS,
                        line=dict(color=T.SURFACE, width=2)),
            text=texts, textposition="inside", insidetextanchor="middle",
            textfont=dict(color="#ffffff", size=12),
            hovertemplate=f"<b>%{{x:.3f}} t CO2/t DRI</b><br>{label}"
                          "<br>%{y}<extra></extra>",
        ))
    fig.update_layout(barmode="stack", bargap=0.68,
                      legend=dict(traceorder="normal"))
    fig.update_xaxes(title="Tonnes CO2 per Tonne DRI", tickformat=".1f")
    fig.update_yaxes(showgrid=False,
                     tickfont=dict(color=T.INK_SECONDARY, size=12))
    return _layout(fig, 74 * len(cols) + 110)


# ---------------------------------------------------------------------------
def mass_sankey(plant) -> go.Figure:
    """Sankey of the stream table, in kg per tonne of DRI.

    A single hue throughout: the flow's direction is already encoded by
    position, so hue would be decoration. Air and waste gas dominate the
    diagram, which is the honest picture of a kiln's mass flow.
    """
    ins = dict(plant.inputs)
    ore = ins.pop("iron ore (dry)", 0.0) + ins.pop("ore moisture", 0.0)
    inputs = [("Iron Ore", ore)] + [(stream(k), v) for k, v in ins.items()]
    outputs = [(stream(k), v) for k, v in plant.outputs.items()]

    hub = "Rotary Kiln"
    nodes = [n for n, _ in inputs] + [hub] + [n for n, _ in outputs]
    idx = {n: i for i, n in enumerate(nodes)}
    hub_i = idx[hub]

    src = [idx[n] for n, _ in inputs] + [hub_i] * len(outputs)
    tgt = [hub_i] * len(inputs) + [idx[n] for n, _ in outputs]
    val = [v for _, v in inputs] + [v for _, v in outputs]

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=nodes, pad=18, thickness=14,
            color=[T.BLUE[450]] * len(inputs) + [T.BLUE[650]]
                  + [T.BLUE[350]] * len(outputs),
            line=dict(color=T.SURFACE, width=2),
            hovertemplate="<b>%{value:,.0f} kg/t DRI</b><br>%{label}<extra></extra>",
        ),
        link=dict(
            source=src, target=tgt, value=val,
            color=T.rgba(T.BLUE[300], 0.34),
            hovertemplate="<b>%{value:,.0f} kg/t DRI</b><br>"
                          "%{source.label} to %{target.label}<extra></extra>",
        ),
        textfont=dict(color=T.INK_PRIMARY, size=12, family=T.FONT),
    ))
    # The smallest nodes land hard against the top and bottom edges, so the
    # container carries margin for their labels instead of cropping them.
    return _layout(fig, 470, margin=dict(l=8, r=8, t=26, b=26))


# ---------------------------------------------------------------------------
def energy_ledger(energy: dict, nhv_kj: float) -> go.Figure:
    """Where the coal's energy goes, grouped by the kind of destination."""
    from src.data.parameters import GCAL_PER_KJ

    rows = []
    for group, items in energy["items"].items():
        if group == "in":
            continue
        for name, kj in items.items():
            if kj <= 0:
                continue
            rows.append((ENERGY_GROUPS.get(group, title_case(group)),
                         title_case(name), kj * GCAL_PER_KJ, kj / nhv_kj * 100))
    rows.sort(key=lambda r: r[2])
    groups = list(dict.fromkeys(r[0] for r in rows))
    color_of = {g: T.SERIES[i] for i, g in enumerate(ENERGY_GROUPS.values())}

    fig = go.Figure()
    for g in groups:
        sel = [r for r in rows if r[0] == g]
        fig.add_trace(go.Bar(
            x=[r[2] for r in sel], y=[r[1] for r in sel], orientation="h",
            name=g,
            marker=dict(color=color_of.get(g, T.SERIES[0]),
                        cornerradius=T.BAR_CORNER_RADIUS),
            text=[f"{r[2]:.3f}" for r in sel],
            textposition="outside", cliponaxis=False,
            textfont=dict(color=T.INK_SECONDARY, size=11),
            customdata=[f"{r[3]:.1f}" for r in sel],
            hovertemplate="<b>%{x:.3f} Gcal/t DRI</b><br>%{y}<br>"
                          "%{customdata}% of coal NHV<extra></extra>",
        ))
    # Bars are plotted bottom-up, so the legend is reversed to read in the
    # same order as the chart.
    fig.update_layout(barmode="relative", bargap=0.5,
                      legend=dict(traceorder="reversed"))
    fig.update_xaxes(title="Gcal per Tonne DRI",
                     range=[0, max(r[2] for r in rows) * 1.22])
    return _layout(fig, 30 * len(rows) + 120)


# ---------------------------------------------------------------------------
def validation_meters(rows: list[dict]) -> go.Figure:
    """One ratio against a limit, per check.

    Each check has its own unit, so position is normalised to its own band: 0 is
    the band minimum, 1 the maximum. That puts every check on one comparable
    axis without inventing a second scale.

    Verdict is carried by marker SHAPE as well as colour, and the shapes are the
    same glyphs the table uses. A status colour never carries meaning on its own.
    """
    rows = list(reversed(rows))
    symbol = {"PASS": "circle", "WARN": "triangle-up",
              "FAIL": "square", "INFO": "circle-open"}

    fig = go.Figure()
    # The acceptance band as a recessive track, drawn once behind the markers.
    fig.add_shape(type="rect", x0=0, x1=1, y0=-0.5, y1=len(rows) - 0.5,
                  fillcolor=T.rgba(T.BLUE[100], 0.75), line_width=0,
                  layer="below")
    for x, name in ((0, "Band Minimum"), (1, "Band Maximum")):
        fig.add_vline(x=x, line_width=1, line_color=T.BASELINE,
                      annotation_text=name, annotation_position="top",
                      annotation_font=dict(color=T.INK_MUTED, size=11))

    # One trace per verdict so the legend names the shapes.
    for verdict in ("PASS", "WARN", "FAIL", "INFO"):
        sel = [r for r in rows if r["verdict"] == verdict]
        if not sel:
            continue
        style = T.VERDICT[verdict]
        positions, labels, texts, hovers = [], [], [], []
        for r in sel:
            lo, hi, v = r["min"], r["max"], r["model_value"]
            width = (hi - lo) or 1.0
            positions.append(max(-0.55, min(1.55, (v - lo) / width)))
            labels.append(title_case(r["label"]))
            texts.append(f"{v:,.4g}")
            hovers.append(f"<b>{v:,.4g} {r['unit']}</b><br>"
                          f"{title_case(r['label'])}<br>"
                          f"Band {lo:,.4g} to {hi:,.4g}<br>{style['label']}")
        fig.add_trace(go.Scatter(
            x=positions, y=labels, mode="markers+text", name=style["label"],
            marker=dict(size=13, color=style["color"], symbol=symbol[verdict],
                        line=dict(color=T.SURFACE, width=2)),
            text=texts, textposition="middle right",
            textfont=dict(color=T.INK_SECONDARY, size=11),
            hovertemplate="%{customdata}<extra></extra>", customdata=hovers,
        ))

    fig.update_xaxes(range=[-0.75, 1.9], showticklabels=False, showgrid=False,
                     title="Position Within Literature Band")
    fig.update_yaxes(showgrid=False,
                     categoryorder="array",
                     categoryarray=[title_case(r["label"]) for r in rows],
                     tickfont=dict(color=T.INK_SECONDARY, size=12))
    # Top margin carries the band annotations, which were being cropped.
    return _layout(fig, 34 * len(rows) + 130,
                   margin=dict(l=8, r=24, t=52, b=8))


# ---------------------------------------------------------------------------
def scenario_dumbbell(metrics: list[dict]) -> go.Figure:
    """Before -> after per metric, as a dumbbell in one hue and two shades.

    Each metric is normalised against its own baseline (baseline = 100) so that
    quantities in different units share a single axis.
    """
    metrics = list(reversed(metrics))
    fig = go.Figure()
    for m in metrics:
        base, now = m["baseline"], m["scenario"]
        idx = 100.0 * now / base if base else 100.0
        fig.add_trace(go.Scatter(
            x=[100, idx], y=[m["label"]] * 2, mode="lines",
            line=dict(color=T.BLUE[200], width=2),
            hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[100] * len(metrics), y=[m["label"] for m in metrics],
        mode="markers", name="Baseline",
        marker=dict(size=11, color=T.BLUE[250],
                    line=dict(color=T.SURFACE, width=2)),
        customdata=[f"{m['baseline']:,.4g} {m['unit']}" for m in metrics],
        hovertemplate="<b>%{customdata}</b><br>%{y}, Baseline<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[100.0 * m["scenario"] / m["baseline"] if m["baseline"] else 100.0
           for m in metrics],
        y=[m["label"] for m in metrics], mode="markers+text", name="Scenario",
        marker=dict(size=13, color=T.BLUE[650],
                    line=dict(color=T.SURFACE, width=2)),
        text=[f"{m['scenario']:,.4g}" for m in metrics],
        textposition="middle right",
        textfont=dict(color=T.INK_SECONDARY, size=11),
        customdata=[f"{m['scenario']:,.4g} {m['unit']}" for m in metrics],
        hovertemplate="<b>%{customdata}</b><br>%{y}, Scenario<extra></extra>"))
    fig.add_vline(x=100, line_width=1, line_color=T.BASELINE)
    fig.update_xaxes(title="Indexed to Baseline = 100", ticksuffix="")
    fig.update_yaxes(showgrid=False, tickfont=dict(color=T.INK_SECONDARY, size=12))
    return _layout(fig, 40 * len(metrics) + 120)
