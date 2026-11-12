"""Streamlit dashboard for the coal-based rotary-kiln DRI digital twin.

UI only. Every number shown here is computed in src/ and every assumption
behind it is declared in config/parameters.json, rendered on the Evidence tab.
Presentation lives in src/ui/ (palette, chart builders, components).

Each chart ships a table-view twin. That is deliberate: the validated palette
carries a sub-3:1 contrast warning on two of its slots, and the documented
relief for that is visible direct labels plus a table view.

Only the open tab is computed (st.tabs with on_change="rerun"), so the slow
analyses on Options and What if do not run until someone opens them.
"""
from __future__ import annotations

import json
import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from src.agent.tools import run_scenario
from src.analysis.scenario_store import diff_overrides, document
from src.analysis.scenarios import (CO2_TARGETS, evaluate, h2_breakeven_price,
                                    least_cost, pareto_front, pathway_grid)
from src.data.parameters import GCAL_PER_KJ, Parameters
from src.data.presets import domestic_coal
from src.data.price_series import load_price_series
from src.economics.economics import EconomicsModel
from src.economics.financial import reconciliation, retrofit_project
from src.emissions.co2_model import CO2Model
from src.kiln.axial import axial_profile
from src.models.energy_balance import EnergyBalance
from src.models.mass_balance import MassBalance
from src.models.plant import build_plant
from src.retrofits.hydrogen import Hydrogen
from src.ui import charts
from src.ui import components as ui
from src.ui import summary
from src.ui import theme as T
from src.reporting.export import html_brief, plant_workbook
from src.ui.analyst_panel import render as render_analyst
from src.ui.compare import render as render_compare
from src.ui.uncertainty import cached_tornado, render as render_uncertainty
from src.ui.labels import (COST_LINES, ENERGY_GROUPS, plain_parameter, plain_route,
                          stream, title_case)
from src.validation.literature_check import run_checks
from src.version import stamp

st.set_page_config(page_title="Kiln planner", layout="wide",
                   page_icon="◉", initial_sidebar_state="expanded")
T.register_template()
ui.inject_css()

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}


def _cell(value) -> str:
    """Render any result value as text, so a column never mixes Arrow types."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:,.4f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def table(df: pd.DataFrame, caption: str = "") -> None:
    """The table-view twin that sits under every chart."""
    with st.expander("Show Data Table"):
        st.dataframe(df, width="stretch", hide_index=True)
        if caption:
            st.caption(caption)


def is_open(tab) -> bool:
    """True for the selected tab. If Streamlit cannot tell, render it anyway."""
    return tab.open is not False


# ===========================================================================
# Control panel
# ===========================================================================
defaults = Parameters()
overrides: dict = {}


def _reset() -> None:
    for key in [k for k in st.session_state if str(k).startswith("w_")]:
        del st.session_state[key]


st.sidebar.markdown("### Kiln planner")
st.sidebar.caption("Every tab recalculates from these settings.")

ui.side_heading("Plant")
_PRESET_LABEL = {"imported": "Imported coal (published kiln)",
                 "domestic": "Domestic coal, higher ash"}
coal_preset = st.sidebar.selectbox(
    "Coal", list(_PRESET_LABEL), key="w_coal",
    format_func=_PRESET_LABEL.get,
    help="Imported coal is the published kiln. Domestic coal is that same coal "
         "with the ash raised. It is not a sample from an Indian mine.")
if coal_preset == "domestic":
    overrides.update(domestic_coal(defaults))
capacity = st.sidebar.select_slider(
    "Nameplate", [50, 100, 175, 200, 350, 500, 600], value=100, key="w_capacity",
    format_func=lambda v: f"{v} t/day")
_util_pct = st.sidebar.slider(
    "Share of the year it runs", 50, 95,
    int(round(float(defaults["plant.utilization"]) * 100)), 5, format="%d%%",
    key="w_util")
utilization = _util_pct / 100.0
st.sidebar.caption(
    f"About {capacity * utilization:,.0f} t of sponge iron a day, on average.")

coal_mode = st.sidebar.radio(
    "Coal rate", ["solve", "specified"], key="w_coal_mode",
    format_func=lambda m: {
        "solve": "Solve it from the heat balance",
        "specified": "I will type it",
    }[m],
    help="Solving makes coal a result. Typing it makes coal an input, "
         "and the heat balance then shows whatever is left over.")
overrides["coal.rate_mode"] = coal_mode
if coal_mode == "specified":
    lo, hi = defaults.bounds("coal.rate_t_per_t_dri")
    overrides["coal.rate_t_per_t_dri"] = st.sidebar.slider(
        "Coal per tonne of sponge iron", float(lo), float(hi),
        float(defaults["coal.rate_t_per_t_dri"]), 0.01, format="%.2f t",
        key="w_coal_rate",
        help="Published surveys: imported about 0.9 to 1.1, domestic about 1.4 to 1.6.")

ui.side_heading("Retrofits")
whr_on = st.sidebar.toggle(
    "Waste heat to power", key="w_whr",
    help="A boiler on the after-burner gas making electricity for the plant and the grid.")
biomass_pct = st.sidebar.slider(
    "Rice husk in place of coal", 0,
    int(defaults["biomass.max_substitution_frac"] * 100),
    0, 5, format="%d%%", key="w_biomass") / 100.0
h2_pct = st.sidebar.slider(
    "Hydrogen in place of coal", 0,
    int(defaults["hydrogen.max_substitution_frac"] * 100), 0, 5,
    format="%d%%", key="w_h2") / 100.0
oxygen_on = st.sidebar.toggle(
    "Oxygen-enriched air", key="w_oxygen",
    help="One published trial on a 100 t/day kiln. The oxygen price is a supplier quote.")
kiln_control_on = st.sidebar.toggle(
    "Tighter kiln control", key="w_control",
    help="About 3% less coal from better air control. Capital is the low end of a published range.")
producer_gas_on = st.sidebar.toggle(
    "Producer gas at the discharge end", key="w_pgas",
    help="About 20% less energy. No published cost for the gasifier, so capital stays at zero.")
char_recycle_on = st.sidebar.toggle(
    "Recycle the char", key="w_char",
    help="Most of the char goes back in place of feed coal. The char you no longer sell is charged.")
vfd_on = st.sidebar.toggle(
    "Variable-speed motor drives", key="w_vfd",
    help="The fans and drives draw less power at lower speed.")

ui.side_heading("Carbon accounting")
overrides["biomass.biogenic_co2_zero_rated"] = int(st.sidebar.toggle(
    "Count rice-husk carbon as zero", key="w_biogenic",
    value=bool(defaults["biomass.biogenic_co2_zero_rated"]),
    help="The usual reporting rule. Switch off to see all of the carbon dioxide in the stack."))
overrides["hydrogen.ef_t_per_t"] = st.sidebar.selectbox(
    "Hydrogen source", key="w_h2_source",
    options=[0.0, float(defaults["hydrogen.grey_ef_t_per_t"])],
    format_func=lambda x: "Electrolysis on renewable power" if x == 0
    else "Made from natural gas")

st.sidebar.button("Reset to the published kiln", on_click=_reset, width="stretch")

# ===========================================================================
# Model run
# ===========================================================================
# The coal-rate solve bisects the energy balance a few hundred times, and the
# validation pass runs the whole model again. Caching on the control values
# means switching tabs re-renders rather than re-solves.
@st.cache_data(show_spinner="Working out this kiln", max_entries=24)
def solve(overrides_key: tuple, capacity_tpd: int, util: float) -> dict:
    p = Parameters().with_overrides(dict(overrides_key))
    pl = build_plant(p, capacity_tpd, util)
    return {"plant": pl,
            "energy": EnergyBalance(pl).calculate_balance(),
            "mass": MassBalance(pl).calculate_balance()}


@st.cache_data(show_spinner=False, max_entries=24)
def validate(overrides_key: tuple, capacity_tpd: int, util: float) -> dict:
    p = Parameters().with_overrides(dict(overrides_key))
    result = run_checks(p, capacity_tpd, util)
    result.pop("outputs", None)          # drop the model objects before caching
    return result


def _row(r: dict) -> dict:
    """Flatten one evaluated scenario into a cacheable table row."""
    return {"label": r["label"], "whr": r["whr"],
            "biomass_frac": r["biomass_frac"], "h2_frac": r["h2_frac"],
            "feasible": r["feasible"],
            "reductant_carbon_ratio": r["reductant_carbon_ratio"],
            "co2_t_per_t_dri": r["co2"]["co2_total_t_per_t_dri"],
            "co2_reduction_frac": r["co2_reduction_frac"],
            "cost_per_t_dri": r["econ"]["cost_per_t_dri"],
            "cost_delta_inr_per_t_dri": r["cost_delta_inr_per_t_dri"],
            "abatement_cost_inr_per_t_co2": r["abatement_cost_inr_per_t_co2"],
            "capex_inr": r["capex_inr"], "payback_yr": r["payback_yr"],
            "econ": {"cost_per_t_dri": r["econ"]["cost_per_t_dri"]}}


@st.cache_data(show_spinner="Pricing every mix of retrofits", max_entries=24)
def pathways(overrides_key: tuple, capacity_tpd: int, util: float) -> dict:
    p = Parameters().with_overrides(dict(overrides_key))
    pl = build_plant(p, capacity_tpd, util)
    e = EnergyBalance(pl).calculate_balance()
    rows = [_row(r) for r in pathway_grid(pl, e)]
    h2_kg = {f: Hydrogen(pl, f).calculate_impact()["h2_required_kg_per_t_dri"]
             for f in sorted({r["h2_frac"] for r in rows if r["h2_frac"] > 0})}
    return {"rows": rows, "h2_kg": h2_kg,
            "h2_breakeven": h2_breakeven_price(pl),
            "h2_price": p["hydrogen.price_inr_per_kg"]}


@st.cache_data(show_spinner=False, max_entries=8)
def preset_snapshot(name: str, capacity_tpd: int, util: float) -> dict:
    """Imported or domestic coal with retrofits off, for the compare tab."""
    row = run_scenario(capacity_tpd, util, name)
    keep = ("preset", "coal_t_per_t", "co2_total_t_per_t", "cost_inr_per_t",
            "mass_closure_percent", "energy_closure_percent")
    return {key: row[key] for key in keep}


params = defaults.with_overrides(overrides)
_key = tuple(sorted(overrides.items()))
_solved = solve(_key, capacity, utilization)
plant, eb, mb = _solved["plant"], _solved["energy"], _solved["mass"]

aux = params["power.aux_kwh_per_t_dri"]
scenario_result = evaluate(plant, eb, whr_on, biomass_pct, h2_pct,
                           oxygen=oxygen_on, kiln_control=kiln_control_on,
                           producer_gas=producer_gas_on,
                           char_recycle=char_recycle_on, vfd=vfd_on)
co2, econ = scenario_result["co2"], scenario_result["econ"]
retrofits, warnings = scenario_result["retrofits"], scenario_result["warnings"]
net_import, capex = scenario_result["net_import_kwh_per_t_dri"], scenario_result["capex_inr"]

# Retrofit-free reference for every delta shown.
base_key = tuple(sorted(
    (k, v) for k, v in overrides.items()
    if k not in ("biomass.biogenic_co2_zero_rated", "hydrogen.ef_t_per_t")))
base_plant = solve(base_key, capacity, utilization)["plant"]
base_co2 = CO2Model(base_plant).calculate_emissions()
base_econ = EconomicsModel(base_plant).calculate_economics()
validation = validate(_key, capacity, utilization)
has_retrofit = bool(retrofits)

# ===========================================================================
# Header
# ===========================================================================
counts = validation["counts"]
_on = []
if whr_on:
    _on.append("waste heat to power")
if biomass_pct:
    _on.append(f"rice husk {biomass_pct:.0%}")
if h2_pct:
    _on.append(f"hydrogen {h2_pct:.0%}")
if oxygen_on:
    _on.append("oxygen")
if kiln_control_on:
    _on.append("tighter control")
if producer_gas_on:
    _on.append("producer gas")
if char_recycle_on:
    _on.append("char recycle")
if vfd_on:
    _on.append("motor drives")
_changes = ", ".join(_on) if _on else "no retrofits"
_scored = counts["PASS"] + counts["FAIL"] + counts["WARN"]
ui.header(
    "Kiln planner",
    f"{_PRESET_LABEL[coal_preset]}  ·  {capacity} t/day  ·  "
    f"runs {utilization:.0%} of the year  ·  {_changes}",
    [(f"{counts['PASS']} of {_scored} literature checks pass",
      T.STATUS["good"] if counts["FAIL"] == 0 else T.STATUS["warning"]),
     (f"Mass balance {mb['error_percent']:.2f}% open",
      T.STATUS["good"] if mb["is_valid"] else T.STATUS["critical"]),
     (f"Heat balance {eb['closure_error_percent']:.2f}% open",
      T.STATUS["good"] if eb["is_valid"] else T.STATUS["critical"])])

if not mb["is_valid"]:
    st.error(f"The materials do not add up: {mb['error_percent']:.2f}% is "
             f"unaccounted for. Read the Plant tab before trusting a cost.",
             icon="■")
if not eb["is_valid"]:
    st.error(f"The heat does not add up: {eb['closure_error_percent']:.2f}% "
             f"is unaccounted for.", icon="■")
_alerts = list(warnings) + [
    f"{plain_parameter(r['parameter'])} is {r['value']:g}, outside the "
    f"published range of {r['min']:g} to {r['max']:g}."
    for r in params.out_of_range()]
if _alerts:
    st.warning("\n".join(f"- {a}" for a in _alerts), icon="⚠")
_notes = []
open_citations = [
    plain_parameter(key) for key in params.unsourced_keys()
    if not (key.startswith("biomass.") and biomass_pct == 0)
    and not (key.startswith("hydrogen.") and h2_pct == 0)]
if open_citations:
    _notes.append("Engineering default, no published source yet: "
                  + "; ".join(open_citations) + ".")
if coal_preset == "domestic":
    _notes.append("Domestic coal is the published coal with the ash raised, "
                  "not a sample from an Indian mine.")
if _notes:
    ui.note("  ".join(_notes))

TAB_NAMES = ["Decision", "Plant", "Options", "Carbon & cost", "What if",
             "Evidence", "Compare", "Ask"]
tabs = st.tabs(TAB_NAMES, key="page", on_change="rerun")

# ===========================================================================
# Decision
# ===========================================================================
with tabs[0]:
    if is_open(tabs[0]):
        ui.page_lead(
            "What should this kiln do?",
            "Pick a carbon cut. Every mix of waste heat, rice husk and hydrogen "
            "is priced, and the cheapest one that still reduces the ore is shown.")
        grid = pathways(_key, capacity, utilization)["rows"]
        target_frac = st.select_slider(
            "Carbon dioxide to cut",
            options=list(CO2_TARGETS), value=0.20, key="w_target", persist_state="page",
            format_func=lambda frac: f"{frac:.0%}")
        target = f"{target_frac:.0%}"
        chosen = least_cost(grid, target_frac)
        recommendation = None
        if chosen is not None:
            recommendation = {
                "label": plain_route(chosen["label"]),
                "cost_per_t": chosen["cost_per_t_dri"],
                "cost_text": T.rupees(chosen["cost_per_t_dri"]),
                "co2_t": chosen["co2_t_per_t_dri"],
                "annual_cost": chosen["cost_per_t_dri"] * base_econ["annual_output_t"],
                "co2_cut_frac": chosen["co2_reduction_frac"],
                "cut_text": f"{chosen['co2_reduction_frac']:.0%} lower",
                "payback_yr": chosen["payback_yr"],
            }
        summary.recommendation(
            recommendation, target,
            "That cut cannot be reached. The ore would not be fully reduced.")
        if recommendation is not None:
            cost_chart, co2_chart = st.columns(2, gap="large")
            with cost_chart:
                st.plotly_chart(charts.labeled_bars(
                    [{"label": "This kiln", "value": econ["cost_per_t_dri"],
                      "text": T.rupees(econ["cost_per_t_dri"])},
                     {"label": "Recommended", "value": recommendation["cost_per_t"],
                      "text": T.rupees(recommendation["cost_per_t"])}],
                    "Rupees per tonne"), config=PLOT_CONFIG)
            with co2_chart:
                st.plotly_chart(charts.labeled_bars(
                    [{"label": "This kiln", "value": co2["co2_total_t_per_t_dri"],
                      "text": f"{co2['co2_total_t_per_t_dri']:.2f}"},
                     {"label": "Recommended", "value": recommendation["co2_t"],
                      "text": f"{recommendation['co2_t']:.2f}"}],
                    "Tonnes of CO2 per tonne"), config=PLOT_CONFIG)
            table(pd.DataFrame([
                {"Case": "This kiln, as set in the sidebar",
                 "Cost, INR per tonne": round(econ["cost_per_t_dri"]),
                 "CO2, t per tonne of iron": round(co2["co2_total_t_per_t_dri"], 3)},
                {"Case": f"Cheapest workable mix for a {target} cut",
                 "Cost, INR per tonne": round(recommendation["cost_per_t"]),
                 "CO2, t per tonne of iron": round(recommendation["co2_t"], 3)},
            ]))

        summary.headlines([
            {"label": "A tonne costs", "value": T.rupees(econ["cost_per_t_dri"]),
             "unit": ""},
            {"label": "Carbon dioxide", "value": f"{co2['co2_total_t_per_t_dri']:.2f}",
             "unit": "t per tonne of iron"},
            {"label": "Coal used", "value": f"{plant.coal_rate:.3f}",
             "unit": "t per tonne of iron"}])

        ident = stamp()
        snap = {
            "preset": coal_preset,
            "capacity_tpd": capacity,
            "coal_t_per_t": plant.coal_rate,
            "co2_total_t_per_t": co2["co2_total_t_per_t_dri"],
            "cost_inr_per_t": econ["cost_per_t_dri"],
            "mass_closure_percent": mb["error_percent"],
            "energy_closure_percent": eb["closure_error_percent"],
        }
        book = plant_workbook(
            snap,
            [{"label": row["label"], "feasible": row["feasible"],
              "co2_reduction_frac": row.get("co2_reduction_frac"),
              "cost_per_t_dri": row.get("cost_per_t_dri"),
              "payback_yr": row.get("payback_yr")} for row in grid],
            [{"key": row["key"], "verdict": row["verdict"],
              "model_value": row["model_value"]} for row in validation["rows"]],
            ident["model_version"], ident["parameters_sha256"])
        brief = html_brief(snap, recommendation, ident["model_version"])
        file_left, file_right, _ = st.columns([1, 1, 1.2])
        with file_left:
            st.download_button(
                "Download the tables (.xlsx)", book, "dri_report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch")
        with file_right:
            st.download_button("Download the one-page brief", brief, "dri_brief.html",
                               "text/html", width="stretch")
        st.caption(f"Model {ident['model_version']}. "
                   f"Assumption-file fingerprint {ident['parameters_sha256'][:12]}.")

        # Last on the page: the sweep is the slowest step, so everything above
        # is already on screen while it runs.
        swept = cached_tornado(_key, capacity, utilization)
        top = sorted((row for row in swept["rows"] if row.get("cost_swing")),
                     key=lambda row: row["cost_swing"], reverse=True)[:3]
        summary.swings([
            {"Assumption": plain_parameter(row["parameter"]),
             "Cost if low": T.rupees(row["baseline_cost_at_low"]),
             "Cost if high": T.rupees(row["baseline_cost_at_high"]),
             "Swing": T.rupees(row["cost_swing"])}
            for row in top])

# ===========================================================================
# Plant: the kiln, its flows and both balances
# ===========================================================================
with tabs[1]:
    if is_open(tabs[1]):
        ui.page_lead(
            "This kiln, per tonne of sponge iron.",
            "Ore rate, air rate, waste gas and coal are solved from the balances, "
            "not typed in. Any leftover is reported, not hidden.")
        ui.kiln_schematic(
            [("Ore", f"{plant.ore_rate:.2f} t"),
             ("Coal", f"{plant.coal_rate:.2f} t"),
             ("Air", f"{plant.air / 1000:.2f} t"),
             ("Dolomite", f"{plant.dolomite_mass / 1000:.3f} t")],
            [("Sponge iron", "1.00 t"),
             ("Waste gas", f"{plant.outputs['waste gas'] / 1000:.2f} t"),
             ("Char", f"{plant.outputs['char (dolochar)'] / 1000:.3f} t"),
             ("Carbon dioxide", f"{co2['co2_total_t_per_t_dri']:.2f} t")])

        left, right = st.columns([1, 2.1], gap="large")
        with left:
            d_co2 = co2["co2_total_t_per_t_dri"] - base_co2["co2_total_t_per_t_dri"]
            ui.hero("Carbon dioxide", f"{co2['co2_total_t_per_t_dri']:.2f}",
                    "t per tonne of iron",
                    (f"{d_co2:+.2f} t against the same kiln with the retrofits off"
                     if has_retrofit else
                     "No retrofits are switched on. This is the kiln on its own."))
        with right:
            c = st.columns(3)
            with c[0]:
                ui.stat_tile("Output", T.compact(plant.production_tpd), "t/day")
            with c[1]:
                ui.stat_tile("A tonne costs",
                             T.rupees(econ["cost_per_t_dri"]), "",
                             delta=econ["cost_per_t_dri"] - base_econ["cost_per_t_dri"],
                             delta_text=(
                                 T.rupees(abs(econ["cost_per_t_dri"]
                                              - base_econ["cost_per_t_dri"]))
                                 + " vs baseline") if has_retrofit else "",
                             lower_is_better=True)
            with c[2]:
                ui.stat_tile("Retrofit equipment",
                             T.rupees(capex, compact_form=True) if capex else "None", "")
            c = st.columns(3)
            with c[0]:
                ui.stat_tile("Coal", f"{plant.coal_rate:.3f}", "t per tonne of iron")
            with c[1]:
                ui.stat_tile("Heat in the coal",
                             f"{eb['sec_gcal_per_t_dri']:.2f}", "Gcal per tonne")
            with c[2]:
                ui.stat_tile("Carbon left to reduce the ore",
                             f"{plant.reductant_carbon_ratio:.2f}", "× the minimum")
        st.caption(
            "Below 1× on the last tile there is not enough carbon left to take the "
            "oxygen out of the ore, and the case is marked unworkable."
            + (f" Coal is solved from the heat balance at {plant.coal_rate:.3f} t/t; "
               "published surveys put imported coal at 0.9 to 1.1 and domestic at 1.4 to 1.6."
               if plant.coal_rate_solved else ""))

        if has_retrofit:
            ui.section("Against the same kiln with the retrofits off",
                       "The hollow end of each line is the kiln alone. The solid "
                       "end is the kiln with your retrofits.")
            metrics = [
                {"label": "Carbon dioxide", "unit": "t CO2/t iron",
                 "baseline": base_co2["co2_total_t_per_t_dri"],
                 "scenario": co2["co2_total_t_per_t_dri"]},
                {"label": "Cost of one tonne", "unit": "INR/t iron",
                 "baseline": base_econ["cost_per_t_dri"],
                 "scenario": econ["cost_per_t_dri"]},
                {"label": "Power bought from the grid", "unit": "kWh/t iron",
                 "baseline": aux, "scenario": net_import},
            ]
            st.plotly_chart(charts.scenario_dumbbell(metrics), config=PLOT_CONFIG)
            table(pd.DataFrame([
                {"Metric": m["label"], "Unit": m["unit"],
                 "Baseline": round(m["baseline"], 4),
                 "Scenario": round(m["scenario"], 4),
                 "Change": round(m["scenario"] - m["baseline"], 4)}
                for m in metrics]))
            with st.expander("What each retrofit did"):
                for name, r in retrofits.items():
                    st.markdown(f"**{name}**")
                    st.dataframe(pd.DataFrame([
                        {"Quantity": title_case(k), "Value": _cell(v)}
                        for k, v in r.items()]), width="stretch", hide_index=True)

        ui.section("Inside the kiln")
        view = st.radio(
            "View", ["Material flows", "Where the heat goes", "Along the kiln",
                     "Element check"],
            horizontal=True, key="w_plant_view", persist_state="page", label_visibility="collapsed")

        if view == "Material flows":
            st.caption("Kilograms per tonne of sponge iron. Air and waste gas are "
                       "most of the mass, as they are on a real kiln.")
            st.plotly_chart(charts.mass_sankey(plant), config=PLOT_CONFIG)
            table(pd.DataFrame([
                {"Stream": stream(r["stream"]),
                 "Direction": r["direction"].title(),
                 "kg per t DRI": round(r["kg_per_t_dri"], 2),
                 "t per day": round(r["tpd"], 3)} for r in plant.stream_table()]))

        elif view == "Where the heat goes":
            st.caption(
                f"Counted at the kiln, on the coal's heating value of "
                f"{eb['sec_gcal_per_t_dri']:.2f} Gcal per tonne. "
                f"{eb['closure_error_percent']:.2f}% is left over. “To the "
                "afterburner” is volatile matter that burns after the kiln; waste "
                "heat recovery can use it.")
            st.plotly_chart(charts.energy_ledger(eb, plant.nhv_coal_kj),
                            config=PLOT_CONFIG)
            table(pd.DataFrame([
                {"Group": ENERGY_GROUPS.get(g, title_case(g)), "Item": title_case(k),
                 "Gcal per t DRI": round(v * GCAL_PER_KJ, 4),
                 "% of coal NHV": round(v / plant.nhv_coal_kj * 100, 2)}
                for g, items in eb["items"].items() for k, v in items.items()]))

        elif view == "Along the kiln":
            kiln = axial_profile(plant, eb)
            st.caption(
                f"The published kiln: {kiln['length_m']:.0f} m long, "
                f"{kiln['internal_diameter_m']:.2f} m inside, sloping "
                f"{kiln['inclination_deg']:.1f}°. The first half heats the charge, "
                "the second reduces it. Gas temperature is a straight line between "
                "the two measured ends and the bed is held at its measured "
                "temperature. Metallisation is the measured product placed along "
                "the reducing half; this view does not predict it.")
            st.plotly_chart(charts.kiln_temperatures(kiln["cells"]), config=PLOT_CONFIG)
            table(pd.DataFrame([
                {"Distance (m)": round(c["z_mid_m"], 2), "Zone": c["zone"],
                 "Gas (°C)": round(c["gas_temp_c"], 1),
                 "Solids (°C)": round(c["solid_temp_c"], 1),
                 "In (GJ/t)": round(c["energy_in_kj"] / 1e6, 3),
                 "Out (GJ/t)": round(c["energy_out_kj"] / 1e6, 3),
                 "Residual (GJ/t)": round(c["residual_kj"] / 1e6, 3)}
                for c in kiln["cells"]]),
                "A leftover in one slice is heat that would have to move along the "
                "kiln. The slices together leave the same leftover as the whole "
                f"kiln, {kiln['residual_kj'] / 1e6:.3f} GJ per tonne.")
            st.plotly_chart(charts.kiln_metallisation(kiln["cells"]), config=PLOT_CONFIG)
            table(pd.DataFrame([
                {"Downstream face (m)": round(c["z_down_m"], 2), "Zone": c["zone"],
                 "Metallisation (%)": round(100 * c["metallisation_frac"], 2)}
                for c in kiln["cells"]]))

        else:
            c1, c2 = st.columns([1.15, 1], gap="large")
            with c1:
                st.caption(
                    f"All mass together leaves {mb['error_percent']:.2f}% unaccounted "
                    f"for, against a limit of {mb['tolerance_percent']:.0f}%.")
                st.dataframe(pd.DataFrame([
                    {"Element": title_case(e["element"]),
                     "In (kg/t)": round(e["in_kg_per_t_dri"], 2),
                     "Out (kg/t)": round(e["out_kg_per_t_dri"], 2),
                     "Error %": round(e["error_percent"], 4),
                     "Status": "● Pass" if e["is_valid"] else "■ Fail"}
                    for e in mb["element_balances"]]), width="stretch", hide_index=True)
            with c2:
                st.caption("What is in the waste gas.")
                st.dataframe(pd.DataFrame([
                    {"Species": title_case(k), "kg per t DRI": round(v, 2)}
                    for k, v in plant.waste_gas_composition.items()]),
                    width="stretch", hide_index=True)

# ===========================================================================
# Options: retrofit pathways
# ===========================================================================
with tabs[2]:
    if is_open(tabs[2]):
        ui.page_lead(
            "Which mix of retrofits hits a carbon cut, and what does it cost?",
            "Every combination of waste heat, rice husk and hydrogen is solved "
            "together. A mix that runs out of carbon is marked unworkable.")
        pw = pathways(_key, capacity, utilization)
        grid = pw["rows"]
        front = pareto_front(grid)
        feasible = [r for r in grid if r["feasible"]]
        max_cut = max((r["co2_reduction_frac"] for r in feasible), default=0.0)

        c = st.columns(4)
        with c[0]:
            ui.stat_tile("Mixes priced", str(len(grid)))
        with c[1]:
            ui.stat_tile("Workable", str(len(feasible)), "enough carbon left")
        with c[2]:
            ui.stat_tile("Deepest workable cut", f"{max_cut:.0%}", "of the kiln's CO2")
        with c[3]:
            ui.stat_tile("Hydrogen matches coal at", T.rupees(pw["h2_breakeven"]),
                         "per kg", delta=0.0,
                         delta_text=f"priced at {T.rupees(pw['h2_price'])}/kg")

        ui.section("Cheapest workable mix for each cut",
                   "Each row is solved with the retrofits acting together. "
                   "The savings are not added up from separate studies.")
        roadmap = []
        for t in CO2_TARGETS:
            r = least_cost(grid, t)
            roadmap.append({
                "Cut asked for": f"{t:.0%}",
                "Cheapest workable mix": plain_route(r["label"]) if r else "Cannot be reached",
                "Cut achieved": f"{r['co2_reduction_frac']:.1%}" if r else "",
                "Cost change, INR/t": f"{r['cost_delta_inr_per_t_dri']:+,.0f}" if r else "",
                "INR per t CO2 avoided": (
                    f"{r['abatement_cost_inr_per_t_co2']:+,.0f}"
                    if r and r["abatement_cost_inr_per_t_co2"] is not None else ""),
                "Equipment": (T.rupees(r["capex_inr"], compact_form=True)
                              if r and r["capex_inr"] else ""),
                "Payback, years": (f"{r['payback_yr']:.1f}" if r and r["payback_yr"]
                                   and r["payback_yr"] < 50 else ""),
            })
        st.dataframe(pd.DataFrame(roadmap), width="stretch", hide_index=True)
        if max_cut < max(CO2_TARGETS):
            st.caption(
                f"A cut past {max_cut:.0%} cannot be reached. Rice husk and hydrogen "
                f"are capped, and past that cap the ore would not be reduced.")

        ui.section("Cost against the carbon cut",
                   "Every mix of waste heat, rice husk up to 20% and hydrogen up "
                   "to 30%. The line is the cheapest mix at each cut.")
        st.plotly_chart(charts.abatement_curve(grid, front), config=PLOT_CONFIG)
        table(pd.DataFrame([{
            "Mix": plain_route(r["label"]),
            "Workable": "Yes" if r["feasible"] else "No",
            "Reductant carbon ratio": round(min(r["reductant_carbon_ratio"], 99), 2),
            "CO2, t/t DRI": round(r["co2_t_per_t_dri"], 3),
            "CO2 cut, %": round(r["co2_reduction_frac"] * 100, 1),
            "Cost, INR/t DRI": round(r["cost_per_t_dri"]),
            "Change, INR/t DRI": round(r["cost_delta_inr_per_t_dri"]),
            "Abatement, INR/t CO2": (None if r["abatement_cost_inr_per_t_co2"] is None
                                     else round(r["abatement_cost_inr_per_t_co2"])),
            "Equipment, INR": round(r["capex_inr"]),
        } for r in sorted(grid, key=lambda r: r["co2_reduction_frac"])]))

        ui.section("What if hydrogen costs something else",
                   f"Hydrogen replaces coal on heating value, so it matches coal at "
                   f"{T.rupees(pw['h2_breakeven'])} per kg at any share. A higher "
                   "share only makes the line steeper. The assumption file prices "
                   f"hydrogen at {T.rupees(pw['h2_price'])} per kg.")
        be = pw["h2_breakeven"]
        prices = list(range(25, 425, 25))
        levels = [f for f in pw["h2_kg"] if f in (0.10, 0.20, 0.30)]
        h2_rows = [{"level": f, "price": P, "delta": pw["h2_kg"][f] * (P - be)}
                   for f in levels for P in prices]
        st.plotly_chart(charts.h2_price_lines(h2_rows), config=PLOT_CONFIG)
        table(pd.DataFrame([{"Hydrogen share": f"{r['level']:.0%}",
                             "Hydrogen price, INR/kg": r["price"],
                             "Change, INR/t DRI": round(r["delta"])}
                            for r in h2_rows]))

        ui.section("The same question at a bigger kiln",
                   "Same search at the running time set in the sidebar. A bigger "
                   "kiln spreads the equipment over more tonnes.")
        if st.toggle("Solve at 100, 200, 350 and 500 t/day", key="w_scale", persist_state="page"):
            scale_rows = []
            for cap in (100, 200, 350, 500):
                g = pathways(_key, cap, utilization)["rows"]
                row = {"Nameplate": f"{cap} t/day"}
                for t in (0.20, 0.40, 0.60):
                    r = least_cost(g, t)
                    row[f"{t:.0%} cut"] = (
                        f"{plain_route(r['label'])} ({r['cost_delta_inr_per_t_dri']:+,.0f} INR/t)"
                        if r else "Not reachable")
                scale_rows.append(row)
            st.dataframe(pd.DataFrame(scale_rows), width="stretch", hide_index=True)
        else:
            st.caption("Off by default: it solves the whole search four more times.")

        st.caption(
            "Coal is 2,500 rupees a tonne and ore is 2,600, both from the 2024 papers. "
            "Waste-heat equipment and the fixed daily cost get cheaper per tonne as "
            "the kiln gets bigger. Rice-husk handling and the hydrogen compressor are "
            "included. Producer gas has no published equipment cost, so that case "
            "saves energy and adds no capital.")

# ===========================================================================
# Carbon & cost
# ===========================================================================
with tabs[3]:
    if is_open(tabs[3]):
        money_view = st.radio(
            "View", ["Carbon dioxide", "Cost per tonne", "Retrofit finance"],
            horizontal=True, key="w_money_view", persist_state="page", label_visibility="collapsed")

        if money_view == "Carbon dioxide":
            ui.page_lead(
                "Where does the carbon dioxide come from?",
                "The stack is the kiln and the chamber after it. Power bought from "
                "the grid is counted separately. Rice-husk carbon is left out of the "
                "total while that sidebar switch is on.")
            c = st.columns(4)
            with c[0]:
                ui.stat_tile("From the stack", f"{co2['co2_direct_t_per_t_dri']:.3f}",
                             "t per tonne")
            with c[1]:
                ui.stat_tile("From bought power", f"{co2['co2_scope2_t_per_t_dri']:.3f}",
                             "t per tonne")
            with c[2]:
                ui.stat_tile("Reported total", f"{co2['co2_total_t_per_t_dri']:.3f}",
                             "t per tonne",
                             delta=co2["co2_total_t_per_t_dri"]
                                   - base_co2["co2_total_t_per_t_dri"],
                             delta_text=f"{abs(co2['co2_total_t_per_t_dri'] - base_co2['co2_total_t_per_t_dri']):.3f} vs baseline"
                             if has_retrofit else "", lower_is_better=True)
            with c[3]:
                ui.stat_tile("CO2 per tonne of coal",
                             f"{co2['implied_coal_ef_t_per_t_coal']:.3f}", "t")

            ui.section("What the total is made of",
                       "Counted from the carbon in and the carbon out, not from a "
                       "single handbook factor.")
            st.plotly_chart(
                charts.co2_composition(co2, base_co2 if has_retrofit else None),
                config=PLOT_CONFIG)
            table(pd.DataFrame([
                {"Quantity": title_case(k), "Value": _cell(v)}
                for k, v in co2.items()]),
                "A rule of thumb of 2.4 t CO2 per t coal would need coal that is "
                "65.5% carbon. The coal measured on this kiln is 60.6 to 62.2%.")

        elif money_view == "Cost per tonne":
            ui.page_lead(
                "What does a tonne cost?",
                f"Equipment is spread at {params['econ.discount_rate']:.0%} over "
                f"{params['econ.project_life_yr']:.0f} years, before tax and with "
                "no loan, so it can sit next to coal and power.")
            c = st.columns(4)
            with c[0]:
                ui.stat_tile("A tonne costs", T.rupees(econ["cost_per_t_dri"]), "")
            with c[1]:
                ui.stat_tile("Cash, before equipment",
                             T.rupees(econ["cash_cost_per_t_dri"]), "")
            with c[2]:
                ui.stat_tile("Equipment, per tonne",
                             T.rupees(econ["capex_charge_per_t_dri"]), "")
            with c[3]:
                ui.stat_tile("Made in a year", T.compact(econ["annual_output_t"]),
                             "tonnes")
            ui.section("Where a rupee goes",
                       "Costs point right. Credits, such as power sold, point left.")
            st.plotly_chart(charts.cost_composition(econ), config=PLOT_CONFIG)
            table(pd.DataFrame([
                {"Line item": COST_LINES.get(k, title_case(k)),
                 "INR per t DRI": round(v, 2)}
                for k, v in econ["breakdown_inr_per_t_dri"].items()]))

            prices = load_price_series(params=params)
            ui.section("Prices this kiln can be stressed with",
                       "Low and high are the published bounds. A price with one "
                       "figure has no bound in the papers. Carbon dioxide is not in "
                       "the tonne cost above; its high case is the published "
                       "European certificate price.")
            st.dataframe(pd.DataFrame([
                {"Series": row["id"], "Unit": row["unit"],
                 "Low": None if row["low"] is None else round(row["low"], 2),
                 "Base": round(row["base"], 2),
                 "High": None if row["high"] is None else round(row["high"], 2),
                 "Range": "Yes" if row["has_range"] else "No"}
                for row in prices["rows"]
            ]), width="stretch", hide_index=True)

        else:
            ui.page_lead(
                "Does the retrofit pay for itself with a loan?",
                "75% borrowed at 10% for 5 years, tax at 33.99%, and operating cost "
                "rising at 5% a year, from a 2011 waste-heat project on a 100 t/day "
                f"kiln. The discount rate stays {params['econ.discount_rate']:.0%}. "
                "This values the retrofits switched on, not the whole plant: the "
                "kiln has no purchase price here and sponge iron no selling price.")
            if not has_retrofit:
                st.info("Switch on a retrofit in the sidebar to value it here.")
            opex_yr = sum(item.get("annual_opex_inr", 0.0) for item in retrofits.values())
            project = retrofit_project(
                base_econ["cash_cost_per_t_dri"], base_econ["annual_output_t"],
                econ["cash_cost_per_t_dri"], econ["annual_output_t"],
                capex, opex_yr, params)
            compared = reconciliation(
                econ["cash_cost_per_t_dri"], econ["annual_output_t"], capex, opex_yr,
                params)
            c = st.columns(4)
            with c[0]:
                ui.stat_tile("Value of the retrofit",
                             T.rupees(project["npv_inr"], compact_form=True),
                             "on the equity cheque", lower_is_better=False)
            with c[1]:
                ui.stat_tile("Return on equity",
                             "—" if project["irr"] is None else f"{project['irr']:.1%}", "")
            with c[2]:
                ui.stat_tile("Equity back in",
                             "—" if project["simple_payback_yr"] is None
                             else f"{project['simple_payback_yr']:.1f}", "years")
            with c[3]:
                ui.stat_tile("Back, discounted",
                             "—" if project["discounted_payback_yr"] is None
                             else f"{project['discounted_payback_yr']:.1f}", "years")
            ui.section("Three ways to charge the equipment")
            st.dataframe(pd.DataFrame([
                {"Cost": "Equipment spread over the years, no loan, no tax",
                 "Rupees per tonne": round(compared["annuity_cost_inr_per_t"], 1)},
                {"Cost": "Same case, written as a cash flow",
                 "Rupees per tonne": round(compared["cash_flow_matching_annuity_inr_per_t"], 1)},
                {"Cost": "Cash flow with the loan, the tax and rising costs",
                 "Rupees per tonne": round(compared["financed_levelised_cost_inr_per_t"], 1)},
            ]), width="stretch", hide_index=True)
            st.caption(
                "The first two rows match: the cash flow and the simple equipment "
                "charge are the same sum when the loan and tax are off. The third is "
                "higher because the loan costs 10% against the 8% discount rate, and "
                "a cost with no selling price has no profit for depreciation to "
                "shelter. Payback here is on the equity cheque after the loan; the "
                "payback on Decision is total equipment over the yearly saving.")
            with st.expander("Equity cash flow by year"):
                st.dataframe(pd.DataFrame([
                    {"Year": 0, "Equity cash flow": round(-project["equity_inr"], 0)}
                ] + [
                    {"Year": row["year"],
                     "Operating surplus": round(row["ebitda_inr"], 0),
                     "Interest": round(row["interest_inr"], 0),
                     "Principal": round(row["principal_inr"], 0),
                     "Tax": round(row["tax_inr"], 0),
                     "Equity cash flow": round(row["equity_cash_flow_inr"], 0)}
                    for row in project["years"]
                ]), width="stretch", hide_index=True)

# ===========================================================================
# What if: uncertainty
# ===========================================================================
with tabs[4]:
    if is_open(tabs[4]):
        ui.page_lead(
            "Which assumption, if it moved, would change the answer?",
            "One assumption at a time is pushed to the ends of its published range. "
            "The random sample further down runs on request; it takes a minute.")
        render_uncertainty(_key, capacity, utilization)

# ===========================================================================
# Evidence: literature checks and the parameter register
# ===========================================================================
with tabs[5]:
    if is_open(tabs[5]):
        evidence_view = st.radio(
            "View", ["Published ranges", "Where every number comes from"],
            horizontal=True, key="w_evidence_view", persist_state="page", label_visibility="collapsed")

        if evidence_view == "Published ranges":
            ui.page_lead(
                "Does this kiln land inside the published ranges?",
                "These ranges test the answers and are never fed back in as inputs, "
                "so a pass is evidence rather than a tautology.")
            c = st.columns(4)
            for col, key in zip(c, ("PASS", "WARN", "FAIL", "INFO")):
                style = T.VERDICT[key]
                with col:
                    ui.stat_tile(f"{style['icon']} {style['label']}", str(counts[key]))
            ui.section("Each published range",
                       "Metallisation passing is weaker evidence: it is typed in, so "
                       "it cannot fail. The waste-heat electricity is a design figure, "
                       "not a measured boiler test.")
            st.plotly_chart(charts.validation_meters(validation["rows"]),
                            config=PLOT_CONFIG)
            st.dataframe(pd.DataFrame([
                {"Status": f"{T.VERDICT[r['verdict']]['icon']} "
                           f"{T.VERDICT[r['verdict']]['label']}",
                 "Check": title_case(r["label"]), "Unit": r["unit"],
                 "Model": round(r["model_value"], 4),
                 "Minimum": r["min"], "Maximum": r["max"],
                 "Outside %": round(r["deviation_percent"], 1),
                 "Source": r["source"]} for r in validation["rows"]]),
                width="stretch", hide_index=True)

        else:
            ui.page_lead(
                "Where does every number come from?",
                "Every number the kiln is allowed to use, who published it, and the "
                "range it is plausible over.")
            prov = params.provenance_summary()
            c = st.columns(4)
            with c[0]:
                ui.stat_tile("Assumptions", str(prov["total"]))
            with c[1]:
                ui.stat_tile("Tied to a paper", str(prov.get("verified", 0)))
            with c[2]:
                ui.stat_tile("Still need a source", str(prov.get("needs_citation", 0)))
            with c[3]:
                ui.stat_tile("Used in the stress test", str(len(params.sensitivity_keys())))

            f1, f2 = st.columns([1, 2])
            status_filter = f1.selectbox(
                "Show", ["All", *T.PROVENANCE], key="w_prov_filter", persist_state="page",
                format_func=lambda s: s if s == "All" else
                f"{T.PROVENANCE[s]['icon']} {T.PROVENANCE[s]['label']}")
            search = f2.text_input("Search", placeholder="coal, hydrogen, waste heat",
                                   key="w_prov_search", persist_state="page")
            rows = params.provenance_rows()
            if status_filter != "All":
                rows = [r for r in rows if r["status"] == status_filter]
            if search:
                q = search.lower()
                rows = [r for r in rows
                        if q in r["parameter"].lower() or q in r["source"].lower()
                        or q in plain_parameter(r["parameter"]).lower()]
            st.dataframe(pd.DataFrame([{
                "Assumption": plain_parameter(r["parameter"]),
                "Figure used": ("" if r["value"] is None else
                                f"{r['value']:,.6g}" if isinstance(r["value"], (int, float))
                                else str(r["value"])),
                "Unit": r["unit"],
                "Lowest published": "" if r["min"] is None else f"{r['min']:,.6g}",
                "Highest published": "" if r["max"] is None else f"{r['max']:,.6g}",
                "Standing": (f"{T.PROVENANCE.get(r['status'], {}).get('icon', '')} "
                             f"{T.PROVENANCE.get(r['status'], {}).get('label', r['status'])}"),
                "Source": r["source"],
                "Code name": r["parameter"],
            } for r in rows]), width="stretch", hide_index=True, height=520)
            st.caption(f"Showing {len(rows)} of {prov['total']} parameters. "
                       f"Calibration plant: {params.calibration_plant}")
            st.download_button(
                "Download the register (.csv)",
                pd.DataFrame(params.provenance_rows()).to_csv(index=False),
                "parameter_provenance.csv", "text/csv")

# ===========================================================================
# Compare
# ===========================================================================
with tabs[6]:
    if is_open(tabs[6]):
        ui.page_lead(
            "Imported coal or the higher-ash coal?",
            "The first row is the kiln in the sidebar, including any retrofit. "
            "The other two are the coals alone, with every retrofit off.")

        def _case(label: str, assumption: str, coal: float, co2_t: float, cost: float,
                  mass: float, energy: float) -> dict:
            return {
                "Case": label,
                "What is assumed": assumption,
                "Coal, t per t iron": f"{coal:.3f}",
                "CO2, t per t iron": f"{co2_t:.3f}",
                "Cost, INR per t": f"{cost:,.0f}",
                "Mass balance open, %": f"{mass:.2f}",
                "Heat balance open, %": f"{energy:.4f}",
            }

        imported = preset_snapshot("imported", capacity, utilization)
        domestic = preset_snapshot("domestic", capacity, utilization)
        render_compare([
            _case("This kiln",
                  "As set in the sidebar, including any retrofit",
                  plant.coal_rate, co2["co2_total_t_per_t_dri"],
                  econ["cost_per_t_dri"], mb["error_percent"],
                  eb["closure_error_percent"]),
            _case("Imported coal",
                  "The published imported coal, every retrofit off",
                  imported["coal_t_per_t"],
                  imported["co2_total_t_per_t"], imported["cost_inr_per_t"],
                  imported["mass_closure_percent"], imported["energy_closure_percent"]),
            _case("Higher-ash coal",
                  "The published coal with the ash raised, every retrofit off",
                  domestic["coal_t_per_t"],
                  domestic["co2_total_t_per_t"], domestic["cost_inr_per_t"],
                  domestic["mass_closure_percent"], domestic["energy_closure_percent"]),
        ], diff_overrides({}, overrides))
        saved = document("sidebar", overrides, capacity, utilization, {
            "waste_heat_recovery": whr_on,
            "biomass_frac": biomass_pct,
            "hydrogen_frac": h2_pct,
            "oxygen": oxygen_on,
            "kiln_control": kiln_control_on,
            "producer_gas": producer_gas_on,
            "char_recycle": char_recycle_on,
            "vfd": vfd_on,
        })
        st.download_button(
            "Download this scenario (.json)",
            json.dumps(saved, indent=2) + "\n",
            "sidebar_scenario.json", "application/json")

# ===========================================================================
# Ask
# ===========================================================================
with tabs[7]:
    if is_open(tabs[7]):
        ui.page_lead(
            "Ask the kiln.",
            "Answers are quoted from the calculation. A number that is not in the "
            "calculation is withheld. Nothing here can edit the assumption file.")
        render_analyst(capacity_tpd=capacity, utilization=utilization,
                       preset=coal_preset, overrides=overrides)
