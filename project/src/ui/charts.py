"""Chart builders for the dashboard.

Forms are chosen by the data's job, not by variety:

  Cost composition   polarity (cost added vs credit received) -> diverging bar
  CO2 composition    part-to-whole -> stacked bar, categorical slots
  Mass flow          flow between stages -> Sankey, single hue
  Energy ledger      magnitude by group -> grouped horizontal bar
  Validation         one ratio against a limit -> meter, band track + marker
  Scenario delta     before -> after per item -> dumbbell, one hue two shades
  Pathways           cost against CO2 cut -> scatter + Pareto frontier line
  H2 price           cost delta against H2 price, per level -> lines, fixed slots
  Tornado            one parameter's range -> horizontal bar, one hue
  Abatement curve    marginal cost against cumulative CO2 -> bars, cost polarity
  Carbon price       cost against a carbon price, per pathway -> lines, fixed slots
  Cost sample        draws of cost per tonne -> histogram, one hue, P10/P50/P90 markers

Every builder returns a Plotly figure and every chart in app.py ships a
table-view twin, which is how the palette's sub-3:1 contrast warning on the
aqua and yellow slots is relieved.
"""
from __future__ import annotations

import plotly.graph_objects as go

from src.ui import theme as T
from src.ui.labels import plain_route
from src.ui.labels import COST_LINES, ENERGY_GROUPS, stream, title_case


def _layout(fig: go.Figure, height: int, **kwargs) -> go.Figure:
    fig.update_layout(height=height, **kwargs)
    return fig


def labeled_bars(rows: list[dict], axis_title: str) -> go.Figure:
    """Two or three bars, one colour, one axis. The label sits on the bar."""
    fig = go.Figure(go.Bar(
        x=[row["label"] for row in rows],
        y=[row["value"] for row in rows],
        marker=dict(color=T.SERIES[0], cornerradius=T.BAR_CORNER_RADIUS),
        text=[row["text"] for row in rows],
        textposition="outside", cliponaxis=False,
        textfont=dict(color=T.INK_PRIMARY, size=13, family=T.FONT),
        showlegend=False,
        hovertemplate="%{x}<br>%{text}<extra></extra>",
    ))
    top = max(row["value"] for row in rows)
    fig.update_yaxes(title=axis_title, rangemode="tozero", range=[0, top * 1.28])
    fig.update_xaxes(title="")
    return _layout(fig, 300, margin=dict(l=8, r=12, t=24, b=4))


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
        customdata=[T.rupees(v) + " per tonne" for v in values],
        showlegend=False,
    ))
    # Zero is the anchor, so the axis need not be symmetric -- forcing symmetry
    # left half the plot empty, since credits are far smaller than costs.
    lo, hi = min(values), max(values)
    pad = (hi - lo) * 0.18
    fig.update_xaxes(range=[min(lo - pad, -pad), hi + pad * 1.6],
                     title="Rupees per tonne of sponge iron", tickformat=",.0f")
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
    cols = ([("With the changes", co2), ("Kiln alone", baseline)] if baseline
            else [("This kiln", co2)])
    parts = [("From the stack", "co2_direct_t_per_t_dri", T.SERIES[0]),
             ("From bought power", "co2_scope2_t_per_t_dri", T.SERIES[1]),
             ("Rice-husk carbon, reported separately", "co2_biogenic_t_per_t_dri", T.SERIES[2])]

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
    fig.update_xaxes(title="Tonnes of CO2 per tonne of sponge iron", tickformat=".1f")
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
    fig.update_xaxes(title="Heat, Gcal per tonne of sponge iron",
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
                     title="Where the answer sits in the published range")
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
        mode="markers", name="Kiln alone",
        marker=dict(size=11, color=T.BLUE[250],
                    line=dict(color=T.SURFACE, width=2)),
        customdata=[f"{m['baseline']:,.4g} {m['unit']}" for m in metrics],
        hovertemplate="<b>%{customdata}</b><br>%{y}, Baseline<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[100.0 * m["scenario"] / m["baseline"] if m["baseline"] else 100.0
           for m in metrics],
        y=[m["label"] for m in metrics], mode="markers+text", name="With the changes",
        marker=dict(size=13, color=T.BLUE[650],
                    line=dict(color=T.SURFACE, width=2)),
        text=[f"{m['scenario']:,.4g}" for m in metrics],
        textposition="middle right",
        textfont=dict(color=T.INK_SECONDARY, size=11),
        customdata=[f"{m['scenario']:,.4g} {m['unit']}" for m in metrics],
        hovertemplate="<b>%{customdata}</b><br>%{y}, Scenario<extra></extra>"))
    fig.add_vline(x=100, line_width=1, line_color=T.BASELINE)
    fig.update_xaxes(title="Kiln alone = 100", ticksuffix="")
    fig.update_yaxes(showgrid=False, tickfont=dict(color=T.INK_SECONDARY, size=12))
    return _layout(fig, 40 * len(metrics) + 120)


# ---------------------------------------------------------------------------
def abatement_curve(rows: list[dict], front: list[dict]) -> go.Figure:
    """Every retrofit combination, cost change against CO2 cut.

    Feasibility is carried by marker shape as well as shade: an open square is a
    combination that starves the bed of reductant carbon. The Pareto frontier
    is drawn as a line and labelled directly.
    """
    fig = go.Figure()
    for feasible, name, symbol, color in (
            (True, "Workable", "circle", T.BLUE[250]),
            (False, "Not enough carbon", "square-open", T.INK_MUTED)):
        sel = [r for r in rows if r["feasible"] is feasible]
        if not sel:
            continue
        fig.add_trace(go.Scatter(
            x=[r["co2_reduction_frac"] * 100 for r in sel],
            y=[r["cost_delta_inr_per_t_dri"] for r in sel],
            mode="markers", name=name,
            marker=dict(size=9, symbol=symbol, color=color,
                        line=dict(color=T.SURFACE if feasible else color,
                                  width=1)),
            customdata=[plain_route(r["label"]) for r in sel],
            hovertemplate="<b>%{customdata}</b><br>%{x:.1f}% CO2 cut<br>"
                          "INR %{y:+,.0f} per t DRI<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=[r["co2_reduction_frac"] * 100 for r in front],
        y=[r["cost_delta_inr_per_t_dri"] for r in front],
        mode="lines+markers+text", name="Cheapest mix",
        line=dict(color=T.BLUE[650], width=2),
        marker=dict(size=11, color=T.BLUE[650],
                    line=dict(color=T.SURFACE, width=2)),
        text=[plain_route(r["label"]) for r in front], textposition="top left",
        textfont=dict(color=T.INK_SECONDARY, size=11),
        customdata=[plain_route(r["label"]) for r in front],
        hovertemplate="<b>%{customdata}</b><br>%{x:.1f}% CO2 cut<br>"
                      "INR %{y:+,.0f} per t DRI<extra></extra>"))
    fig.add_hline(y=0, line_width=1, line_color=T.BASELINE)
    fig.update_xaxes(title="Carbon dioxide removed (%)", rangemode="tozero")
    fig.update_yaxes(title="Change in cost (rupees per tonne)", tickformat=",.0f")
    return _layout(fig, 480)


def h2_price_lines(rows: list[dict]) -> go.Figure:
    """Cost change against hydrogen price, one line per substitution level."""
    levels = sorted({r["level"] for r in rows})
    fig = go.Figure()
    for i, lvl in enumerate(levels):
        sel = [r for r in rows if r["level"] == lvl]
        fig.add_trace(go.Scatter(
            x=[r["price"] for r in sel], y=[r["delta"] for r in sel],
            mode="lines", name=f"H2 {lvl:.0%}",
            line=dict(color=T.SERIES[i % 4], width=2.5),
            hovertemplate=f"<b>H2 {lvl:.0%}</b><br>INR %{{x:,.0f}}/kg<br>"
                          "INR %{y:+,.0f} per t DRI<extra></extra>"))
        last = sel[-1]
        fig.add_annotation(x=last["price"], y=last["delta"],
                           text=f"H2 {lvl:.0%}", showarrow=False,
                           xanchor="left", xshift=6,
                           font=dict(color=T.INK_SECONDARY, size=11))
    fig.add_hline(y=0, line_width=1, line_color=T.BASELINE)
    fig.update_xaxes(title="Hydrogen price (rupees per kg)", tickformat=",.0f")
    fig.update_yaxes(title="Change in cost (rupees per tonne)", tickformat=",.0f")
    return _layout(fig, 400, margin=dict(l=8, r=64, t=8, b=8))


# ---------------------------------------------------------------------------
def tornado_ranges(rows: list[dict], low_key: str, high_key: str,
                   axis_title: str, base: float | None = None) -> go.Figure:
    """Horizontal range from the low case to the high case. Largest swing on top."""
    shown = list(reversed(rows))
    labels = [r["axis_label"] for r in shown]
    bases = [min(r[low_key], r[high_key]) for r in shown]
    spans = [abs(r[high_key] - r[low_key]) for r in shown]
    fig = go.Figure(go.Bar(
        y=labels, x=spans, base=bases, orientation="h",
        marker=dict(color=T.SERIES[0], cornerradius=T.BAR_CORNER_RADIUS),
        text=[r["bar_label"] for r in shown],
        textposition="outside", cliponaxis=False,
        textfont=dict(color=T.INK_SECONDARY, size=11),
        hovertemplate="<b>%{y}</b><br>%{customdata}<extra></extra>",
        customdata=[r["hover"] for r in shown],
        showlegend=False,
    ))
    if base is not None:
        fig.add_vline(x=base, line_width=1, line_color=T.BASELINE)
    fig.update_xaxes(title=axis_title)
    fig.update_layout(yaxis=dict(title=""), bargap=0.45)
    return _layout(fig, 32 * len(rows) + 96, margin=dict(l=8, r=88, t=8, b=8))


def macc(bars: list[dict]) -> go.Figure:
    """Marginal abatement cost in the order the measures were added."""
    centers, widths, heights, colors, names = [], [], [], [], []
    start = 0.0
    for bar in bars:
        width = bar["marginal_co2_t_per_t"]
        centers.append(start + width / 2.0)
        widths.append(width)
        heights.append(bar["abatement_cost_inr_per_t_co2"])
        colors.append(T.DIVERGING_NEG if bar["abatement_cost_inr_per_t_co2"] < 0
                      else T.DIVERGING_POS)
        names.append(bar["measure"])
        start += width
    fig = go.Figure(go.Bar(
        x=centers, y=heights, width=widths,
        marker=dict(color=colors, line=dict(color=T.SURFACE, width=1)),
        text=[str(bar["order"]) for bar in bars],
        textposition="outside", cliponaxis=False,
        textfont=dict(color=T.INK_PRIMARY, size=12),
        customdata=names,
        hovertemplate="<b>%{customdata}</b><br>INR %{y:,.0f} per t CO2<extra></extra>",
        showlegend=False,
    ))
    fig.add_hline(y=0, line_width=1, line_color=T.BASELINE)
    fig.update_xaxes(title="Carbon dioxide avoided, running total (t per tonne)", rangemode="tozero")
    fig.update_yaxes(title="Rupees per extra tonne of CO2 avoided", tickformat=",.0f")
    return _layout(fig, 480, margin=dict(l=8, r=16, t=28, b=28))


def carbon_price_lines(lines: list[dict]) -> go.Figure:
    """Cost per tonne against a carbon price. One colour per pathway, in fixed order."""
    fig = go.Figure()
    shown = lines[:len(T.SERIES)]
    for i, line in enumerate(shown):
        fig.add_trace(go.Scatter(
            x=line["prices"], y=line["costs"], mode="lines",
            name=line["label"],
            line=dict(color=T.SERIES[i], width=2.5),
            hovertemplate=f"<b>{line['label']}</b><br>INR %{{x:,.0f}}/t CO2<br>"
                          "INR %{y:,.0f} per t DRI<extra></extra>",
        ))
        fig.add_annotation(
            x=line["prices"][-1], y=line["costs"][-1], text=line["label"],
            showarrow=False, xanchor="left", xshift=6,
            font=dict(color=T.INK_SECONDARY, size=11))
    fig.update_xaxes(title="Carbon price (rupees per tonne of CO2)", tickformat=",.0f",
                     rangemode="tozero")
    fig.update_yaxes(title="Cost of one tonne (rupees)", tickformat=",.0f")
    return _layout(fig, 440, margin=dict(l=8, r=168, t=8, b=8))


def cost_distribution(counts: list[int], edges: list[float],
                      markers: list[tuple[float, str]]) -> go.Figure:
    """Histogram of bare-plant cost. Markers carry P10, P50 and P90."""
    centers = [(edges[i] + edges[i + 1]) / 2.0 for i in range(len(counts))]
    width = edges[1] - edges[0]
    fig = go.Figure(go.Bar(
        x=centers, y=counts, width=width * 0.96,
        marker=dict(color=T.SERIES[0], cornerradius=2),
        showlegend=False,
        hovertemplate="INR %{x:,.0f} per t<br>%{y} draws<extra></extra>",
    ))
    for x, name in markers:
        fig.add_vline(x=x, line_width=1, line_dash="dot", line_color=T.INK_PRIMARY,
                      annotation_text=name, annotation_position="top")
    fig.update_xaxes(title="Cost of one tonne (rupees)", tickformat=",.0f")
    fig.update_yaxes(title="How many draws landed here", rangemode="tozero")
    return _layout(fig, 380)


def morris_mu(names: list[str], mu: list[float], axis_title: str) -> go.Figure:
    """Mean absolute elementary effect. Largest at the top. One hue."""
    order = list(reversed(list(zip(names, mu))))
    fig = go.Figure(go.Bar(
        y=[name for name, _ in order],
        x=[value for _, value in order],
        orientation="h",
        marker=dict(color=T.SERIES[0], cornerradius=T.BAR_CORNER_RADIUS),
        text=[f"{value:,.3g}" for _, value in order],
        textposition="outside", cliponaxis=False,
        textfont=dict(color=T.INK_SECONDARY, size=11),
        showlegend=False,
    ))
    fig.update_xaxes(title=axis_title, rangemode="tozero")
    fig.update_layout(yaxis=dict(title=""), bargap=0.45)
    return _layout(fig, 32 * len(names) + 96, margin=dict(l=8, r=72, t=8, b=8))


def kiln_temperatures(cells: list[dict]) -> go.Figure:
    """Gas and solids temperature on one axis. Both are degrees Celsius."""
    z = [c["z_mid_m"] for c in cells]
    gas = [c["gas_temp_c"] for c in cells]
    solid = [c["solid_temp_c"] for c in cells]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=z, y=gas, mode="lines", name="Waste gas",
        line=dict(color=T.SERIES[0], width=2.5)))
    fig.add_trace(go.Scatter(
        x=z, y=solid, mode="lines", name="Solids",
        line=dict(color=T.SERIES[1], width=2.5)))
    fig.add_annotation(x=z[0], y=gas[0], text=f"Gas {gas[0]:.0f} °C",
                       showarrow=False, yshift=12, font=dict(color=T.INK_SECONDARY, size=11))
    fig.add_annotation(x=z[-1], y=gas[-1], text=f"Gas {gas[-1]:.0f} °C",
                       showarrow=False, yshift=12, font=dict(color=T.INK_SECONDARY, size=11))
    fig.add_annotation(x=z[-1], y=solid[-1], text=f"Solids {solid[-1]:.0f} °C",
                       showarrow=False, yshift=-14, font=dict(color=T.INK_SECONDARY, size=11))
    fig.update_xaxes(title="Distance from the Feed End (m)")
    fig.update_yaxes(title="Temperature (°C)")
    return _layout(fig, 380)


def kiln_metallisation(cells: list[dict]) -> go.Figure:
    """Prescribed metallisation. One series, one axis."""
    z = [c["z_down_m"] for c in cells]
    met = [100.0 * c["metallisation_frac"] for c in cells]
    fig = go.Figure(go.Scatter(
        x=z, y=met, mode="lines", name="Metallisation",
        line=dict(color=T.SERIES[0], width=2.5), showlegend=False))
    fig.add_annotation(x=z[-1], y=met[-1], text=f"{met[-1]:.1f}%",
                       showarrow=False, xanchor="left", xshift=6,
                       font=dict(color=T.INK_SECONDARY, size=12))
    fig.update_xaxes(title="Distance from the Feed End (m)", rangemode="tozero")
    fig.update_yaxes(title="Metallisation at the Downstream Face (%)", rangemode="tozero")
    return _layout(fig, 320, margin=dict(l=8, r=48, t=8, b=8))
