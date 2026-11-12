"""Uncertainty tab: tornado, abatement curve, price break-evens, and the sample.

The plant is solved in src/. This module only chooses what to show and draws it.
Monte Carlo and Morris are behind a button because a few hundred plant solves
take longer than a tab change should.
"""
from __future__ import annotations

import hashlib
import os

import pandas as pd
import streamlit as st

from src.analysis.macc import decision_tables
from src.analysis.montecarlo import propagate
from src.analysis.sensitivity import morris_plant, tornado
from src.data.parameters import Parameters
from src.models.energy_balance import EnergyBalance
from src.models.plant import build_plant
from src.optimization.search import search_all
from src.ui import charts
from src.ui import components as ui
from src.ui import theme as T
from src.ui.labels import plain_parameter, plain_route

_CONFIG = os.path.join(os.path.dirname(__file__), "..", "..", "config")
PLOT = {"displayModeBar": False, "responsive": True}

_METRICS = (
    ("cost", "Cost of a tonne, kiln alone", "baseline_cost_at_low", "baseline_cost_at_high",
     "cost_swing", "Cost of one tonne (INR)", "cost_inr_per_t", True),
    ("co2", "Carbon dioxide, kiln alone", "baseline_co2_at_low", "baseline_co2_at_high",
     "co2_swing", "Carbon dioxide (t per tonne)", "co2_total_t_per_t", True),
    ("abatement", "Rupees per tonne of CO2 avoided", "abatement_at_low", "abatement_at_high",
     "abatement_swing", "Rupees per tonne of CO2 avoided", None, True),
    ("cut", "Carbon dioxide removed by the reference mix", "co2_cut_at_low", "co2_cut_at_high",
     "co2_cut_swing", "Carbon dioxide removed (t per tonne)", None, False),
)


def _token() -> str:
    digest = hashlib.sha256()
    for name in ("analysis.json", "distributions.json"):
        with open(os.path.join(_CONFIG, name), "rb") as fh:
            digest.update(fh.read())
    return digest.hexdigest()[:16]


def _params(overrides_key: tuple, capacity: float, utilization: float) -> Parameters:
    return Parameters().with_overrides({
        **dict(overrides_key),
        "plant.capacity_tpd": float(capacity),
        "plant.utilization": float(utilization),
    })


def _table(frame: pd.DataFrame, caption: str = "") -> None:
    with st.expander("Show Data Table"):
        st.dataframe(frame, width="stretch", hide_index=True)
        if caption:
            st.caption(caption)


def _num(value, digits: int = 1):
    if value is None:
        return "—"
    return f"{value:,.{digits}f}"


@st.cache_data(show_spinner="Pushing each assumption to its published ends")
def _cached_tornado(overrides_key: tuple, capacity: float, utilization: float,
                    token: str) -> dict:
    del token
    return tornado(_params(overrides_key, capacity, utilization))


@st.cache_data(show_spinner="Pricing the carbon cuts and the price breaks")
def _cached_decisions(overrides_key: tuple, capacity: float, utilization: float,
                      token: str) -> dict:
    del token
    params = _params(overrides_key, capacity, utilization)
    tables = decision_tables(params)
    plant = build_plant(params)
    energy = EnergyBalance(plant).calculate_balance()
    tables["search"] = search_all(plant, energy)
    return tables


@st.cache_data(show_spinner="Drawing the random sample")
def _cached_sample(overrides_key: tuple, capacity: float, utilization: float,
                   token: str) -> dict:
    del token
    params = _params(overrides_key, capacity, utilization)
    return {"monte_carlo": propagate(params), "morris": morris_plant(params)}


def _tornado_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame([{
        "Assumption": plain_parameter(r["parameter"]),
        "Code name": r["parameter"],
        "How it was moved": r["method"],
        "Mix it belongs to": plain_route(r["scenario"]),
        "Low": r["low"],
        "High": r["high"],
        "Cost at low": _num(r["baseline_cost_at_low"], 1),
        "Cost at high": _num(r["baseline_cost_at_high"], 1),
        "CO2 at low": _num(r["baseline_co2_at_low"], 4),
        "CO2 at high": _num(r["baseline_co2_at_high"], 4),
        "Abatement at low": _num(r["abatement_at_low"], 1),
        "Abatement at high": _num(r["abatement_at_high"], 1),
        "Note": r["note"],
    } for r in rows])


def _chart_rows(rows: list[dict], low_key: str, high_key: str, swing_key: str,
                reference: str, money: bool) -> list[dict]:
    usable = [r for r in rows
              if r.get(swing_key) and r[low_key] is not None and r[high_key] is not None]
    usable.sort(key=lambda r: r[swing_key], reverse=True)
    out = []
    for r in usable:
        label = plain_parameter(r["parameter"])
        if r["scenario"] != reference:
            label = f"{label}, with {plain_route(r['scenario'])}"
        swing = r[swing_key]
        text = T.rupees(swing) if money else f"{swing:.4f}"
        out.append({
            **r,
            "axis_label": label,
            "bar_label": text,
            "hover": f"{r[low_key]:,.4g} at the low end → {r[high_key]:,.4g} at the high end",
        })
    return out


def cached_tornado(overrides_key: tuple, capacity: float, utilization: float) -> dict:
    """The one-at-a-time sweep, shared with the Summary page."""
    return _cached_tornado(overrides_key, capacity, utilization, _token())


def render(overrides_key: tuple, capacity: float, utilization: float) -> None:
    token = _token()
    swept = _cached_tornado(overrides_key, capacity, utilization, token)
    decisions = _cached_decisions(overrides_key, capacity, utilization, token)
    base = swept["base"] or {}
    rows = swept["rows"]

    ui.section(
        "Pushed to the ends of its published range",
        "One assumption moves. The rest stay put. A line that does not move "
        "the kiln is a result: that assumption does not matter here.")
    if base:
        c = st.columns(3)
        with c[0]:
            ui.stat_tile("Baseline cost", T.rupees(base["cost_inr_per_t"]), "/ t DRI")
        with c[1]:
            ui.stat_tile("Baseline CO2", f"{base['co2_total_t_per_t']:.3f}", "t / t DRI")
        with c[2]:
            ui.stat_tile("Reference package", swept["reference_label"], "")

    no_range = [r["parameter"] for r in rows if r["method"] == "no_range"]
    illegal = [r["parameter"] for r in rows if r["method"] == "one_at_a_time" and not (r["low_ok"] and r["high_ok"])]
    closed = sorted(
        (r for r in rows if r["method"] == "closed_analysis" and r["cost_swing"]),
        key=lambda r: r["cost_swing"], reverse=True)
    if illegal or closed or no_range:
        st.caption(
            "Coal carbon and ash cannot be moved on their own, or the coal would "
            "no longer add up to 100%. Those rows fail on purpose. The closed "
            "rows raise the ash and rescale the rest of the coal, heating value "
            "included. "
            + (f"The ash change that moves cost the most is "
               f"{plain_parameter(closed[0]['parameter'])} "
               f"({T.rupees(closed[0]['cost_swing'])}). " if closed else "")
            + ("No published range, so they are left out: "
               + ", ".join(plain_parameter(name) for name in no_range) + "."
               if no_range else ""))

    choice = st.selectbox(
        "Rank by", [m[1] for m in _METRICS],
        help="Rupees per tonne of CO2 avoided, and the size of the cut, use "
             "the reference mix of changes. An assumption that belongs to a "
             "change that mix leaves off "
             "is solved with the lever switched on, and the bar name says so.")
    spec = next(m for m in _METRICS if m[1] == choice)
    _key, _title, low_key, high_key, swing_key, axis, base_key, money = spec
    plotted = _chart_rows(rows, low_key, high_key, swing_key,
                          swept["reference_label"], money)
    limit = swept["chart_bars"]
    shown = plotted[:limit]
    if shown:
        base_value = base.get(base_key) if base_key else None
        st.plotly_chart(charts.tornado_ranges(shown, low_key, high_key, axis, base_value),
                        config=PLOT)
        _table(_tornado_frame(shown), "The rows in the chart, largest swing first.")
    else:
        st.info("Nothing moves this metric above the reporting floor.")
    with st.expander(f"Every parameter ({len(rows)})"):
        st.dataframe(_tornado_frame(rows), width="stretch", hide_index=True)
        st.caption("Includes coal analyses the plant refused, parameters with no range, "
                   "and parameters that do not move the result.")

    # --- abatement curve ---------------------------------------------------
    curve = decisions["macc"]
    ui.section(
        "Marginal abatement curve",
        "Measures are added one at a time. At each step the cost and the CO2 of "
        "what remains are recomputed against the package already chosen, and the "
        "cheapest tonne is taken. Bar numbers match the table. Orange is a saving, "
        "blue is a cost. The height is the marginal cost when the measure was added, "
        "so a later bar can be cheaper than an earlier one when the measures interact.")
    if curve["warnings"]:
        with st.expander(f"Plant notes on this curve ({len(curve['warnings'])})"):
            for warning in curve["warnings"]:
                st.markdown(f"- {warning}")
    if curve["no_abatement"]:
        names = ", ".join(item["measure"] for item in curve["no_abatement"])
        st.caption(
            f"{names} still reduce cost once the plant is off the grid, but they no longer "
            "reduce CO2, because waste heat recovery has already removed the power purchase. "
            "They are not drawn.")
    if curve["bars"]:
        st.plotly_chart(charts.macc(curve["bars"]), config=PLOT)
        _table(pd.DataFrame([{
            "Order": b["order"], "Measure": b["measure"],
            "Marginal CO2 (t/t)": round(b["marginal_co2_t_per_t"], 4),
            "Marginal cost (INR/t)": round(b["marginal_cost_inr_per_t"], 1),
            "Abatement cost (INR/t CO2)": round(b["abatement_cost_inr_per_t_co2"], 1),
            "Cumulative CO2 (t/t)": round(b["cumulative_co2_t_per_t"], 4),
            "Annual CO2 (t/yr)": round(b["annual_co2_t"], 0),
            "Package": b["package"],
        } for b in curve["bars"]]))

    # --- optimiser ---------------------------------------------------------
    ui.section(
        "Continuous search against the pathway grid",
        "Biomass fraction, hydrogen fraction and waste heat recovery, with the "
        "reductant-carbon check and the CO2 target as hard constraints. The grid "
        "is the 5% steps. The continuous result can sit between those steps.")
    search_rows = []
    for row in decisions["search"]["targets"]:
        grid, cont = row["grid"], row["continuous"]
        search_rows.append({
            "CO2 target": f"{row['target_frac']:.0%}",
            "Grid": grid["label"] if grid else "Not reachable",
            "Grid cost (INR/t)": _num(grid["cost_inr_per_t"], 0) if grid else "—",
            "Continuous": cont["label"] if cont else "Not reachable",
            "Continuous cost (INR/t)": _num(cont["cost_inr_per_t"], 0) if cont else "—",
            "Continuous cut": f"{cont['co2_reduction_frac']:.1%}" if cont else "—",
            "Saving vs grid (INR/t)": _num(row["continuous_saving_vs_grid_inr_per_t"], 0),
        })
    st.dataframe(pd.DataFrame(search_rows), width="stretch", hide_index=True)

    # --- prices ------------------------------------------------------------
    ui.section(
        "Prices at which the ranking flips",
        "The carbon price at which a pathway ties the baseline is its abatement cost. "
        "Coal, power, export and hydrogen prices are linear in the cost, and the "
        "root is checked at a third price. A blank means the pathway does not use "
        "that price. The hydrogen energy-parity line ignores capital and carbon.")
    price_names = []
    for item in decisions["break_evens"]:
        for price in item["prices"]:
            if price["parameter"] not in price_names:
                price_names.append(price["parameter"])
    price_rows = []
    for item in decisions["break_evens"]:
        record = {
            "Pathway": item["label"],
            "Carbon price that ties the baseline (INR/t)": _num(item["carbon_price_inr_per_t"], 0),
        }
        found = {price["parameter"]: price for price in item["prices"]}
        for name in price_names:
            price = found.get(name)
            if price is None:
                record[name] = "—"
            elif price.get("note"):
                record[name] = _num(price["break_even"], 2)
            elif not price["depends"]:
                record[name] = "No effect"
            else:
                record[name] = _num(price["break_even"], 2)
        price_rows.append(record)
    st.dataframe(pd.DataFrame(price_rows), width="stretch", hide_index=True)

    carbon = decisions["carbon"]
    cases = ", ".join(
        f"{case['label']} at {T.rupees(case['inr_per_t'])}/t"
        + (f" ({case['eur_per_t']} EUR × {case['inr_per_eur']} INR/EUR on {case['fx_date']})"
           if "eur_per_t" in case else "")
        for case in carbon["cases"])
    st.caption("Carbon charges added on top of the plant-gate cost: " + cases + ". "
               "The Rs 400/t coal cess was removed on 11 September 2025 and is not applied. "
               "Which of these the report treats as official is still an open question.")
    st.plotly_chart(charts.carbon_price_lines(carbon["lines"]), config=PLOT)
    _table(pd.DataFrame([{
        "Pathway": line["label"],
        "Cost without a carbon charge": round(line["cost_without_carbon_inr_per_t"], 1),
        "CO2 (t/t)": round(line["co2_t_per_t"], 4),
        **{f"At {T.rupees(case['inr_per_t'])}/t": round(
            line["cost_without_carbon_inr_per_t"] + case["inr_per_t"] * line["co2_t_per_t"], 1)
           for case in carbon["cases"]}
    } for line in carbon["lines"]]),
        "Cost per tonne at each cited carbon price. The chart draws the line between them.")

    # --- probability sample ------------------------------------------------
    ui.section(
        "A random sample of the published ranges",
        "Each assumption is drawn inside its published range. Assumptions that "
        "are choices, such as which coal, are not drawn. Coal that has to add "
        "up to 100% is drawn as ash, then the rest of the coal is rescaled. "
        "The button solves the kiln a few hundred times.")
    if st.button("Run the sample"):
        st.session_state["uncertainty_sample"] = True
    if not st.session_state.get("uncertainty_sample"):
        st.caption("Not run yet.")
        return

    sample = _cached_sample(overrides_key, capacity, utilization, token)
    mc = sample["monte_carlo"]
    st.caption(
        f"{mc['n_accepted']} of {mc['n_requested']} draws solved "
        f"({mc['n_rejected']} rejected). Seed {mc['seed']}. "
        "Percentiles are over the draws that solved.")
    if mc["mode_clipped"]:
        st.caption("Base value outside the cited band, so the triangular mode was "
                   "pinned to the edge: " + ", ".join(mc["mode_clipped"]) + ".")
    summary = pd.DataFrame([{
        "Metric": row["metric"], "Unit": row["unit"],
        "P10": _num(row.get("p10"), 3), "P50": _num(row.get("p50"), 3),
        "P90": _num(row.get("p90"), 3), "Mean": _num(row.get("mean"), 3),
        "Draws": row.get("n", 0),
    } for row in mc["summary"]])
    st.dataframe(summary, width="stretch", hide_index=True)
    hist = mc["cost_histogram"]
    cost = next(row for row in mc["summary"] if row["key"] == "cost_inr_per_t")
    if hist and cost.get("p50") is not None:
        st.plotly_chart(charts.cost_distribution(
            hist["counts"], hist["edges"],
            [(cost["p10"], "P10"), (cost["p50"], "P50"), (cost["p90"], "P90")]),
            config=PLOT)
        edges = hist["edges"]
        _table(pd.DataFrame({
            "From (INR/t)": [round(v, 1) for v in edges[:-1]],
            "To (INR/t)": [round(v, 1) for v in edges[1:]],
            "Draws": hist["counts"],
        }), "The bins in the histogram.")

    st.dataframe(pd.DataFrame([{
        "Pathway": row["label"],
        "Feasible": _num(100 * row["p_feasible"], 1) + "%" if row["p_feasible"] is not None else "—",
        "Cheaper than baseline": _num(100 * row["p_cheaper"], 1) + "%" if row["p_cheaper"] is not None else "—",
        "Lower CO2": _num(100 * row["p_lower_co2"], 1) + "%" if row["p_lower_co2"] is not None else "—",
        "Both": _num(100 * row["p_cheaper_and_lower_co2"], 1) + "%" if row["p_cheaper_and_lower_co2"] is not None else "—",
    } for row in mc["probabilities"]]), width="stretch", hide_index=True)
    st.caption("Shares of the draws that solved, not of the draws in which the pathway "
               "was feasible. An infeasible draw counts as not cheaper and not lower CO2.")

    morris = sample["morris"]
    agreement = morris["rank_agreement"].get("cost_inr_per_t")
    agreement_text = "undefined (the two halves do not both have a spread)" if agreement is None else f"{agreement:.2f}"
    st.caption(
        f"Morris: {morris['r']} trajectories, {morris['p']} levels, "
        f"step {morris['delta']:.3f} of each factor's band. "
        f"{morris['n_failed_points']} of {morris['n_points']} points failed. "
        f"Spearman rank correlation of the cost mu-star between the two halves "
        f"of the trajectories: {agreement_text}.")
    output = morris["outputs"]["cost_inr_per_t"]
    co2_mu = dict(zip(morris["factors"], morris["outputs"]["co2_total_t_per_t"]["mu_star"]))
    n_effects = dict(zip(morris["factors"], output["n"]))
    paired = sorted(zip(morris["factors"], output["mu_star"]),
                    key=lambda item: item[1], reverse=True)
    top = [(name, value) for name, value in paired if value > 0][:16]
    if top:
        st.plotly_chart(charts.morris_mu(
            [name for name, _ in top], [value for _, value in top],
            "mu-star of bare-plant cost (INR per t, per full band)"), config=PLOT)
        _table(pd.DataFrame([{
            "Factor": name,
            "mu-star, cost": round(value, 2),
            "mu-star, CO2": round(co2_mu[name], 4),
            "Effects": n_effects[name],
        } for name, value in top]),
            "The factors drawn in the chart. mu-star is the effect of moving a factor "
            "across its whole cited band, so the factors can be compared.")
