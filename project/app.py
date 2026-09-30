"""Streamlit dashboard for the coal-based rotary-kiln DRI digital twin.

UI only. Every number shown here is computed in src/ and every assumption
behind it is declared in config/parameters.json, rendered in the Parameters tab.
Presentation lives in src/ui/ (palette, chart builders, components).

Each chart ships a table-view twin. That is deliberate: the validated palette
carries a sub-3:1 contrast warning on two of its slots, and the documented
relief for that is visible direct labels plus a table view.
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))

from src.data.parameters import GCAL_PER_KJ, Parameters
from src.economics.economics import EconomicsModel
from src.emissions.co2_model import CO2Model
from src.models.energy_balance import EnergyBalance
from src.models.mass_balance import MassBalance
from src.models.plant import build_plant
from src.retrofits.biomass import Biomass
from src.retrofits.hydrogen import Hydrogen
from src.retrofits.whr import WHR
from src.ui import charts
from src.ui import components as ui
from src.ui import theme as T
from src.ui.labels import COST_LINES, ENERGY_GROUPS, stream, title_case
from src.validation.literature_check import run_checks

st.set_page_config(page_title="DRI Digital Twin", layout="wide",
                   page_icon="◉")
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


# ===========================================================================
# Control panel
# ===========================================================================
defaults = Parameters()
overrides: dict = {}

st.sidebar.markdown("### Scenario")
SCENARIOS = {
    "Baseline, Imported Coal": {},
    "Baseline, Domestic Coal": {"coal_feed.ash": 0.30, "coal_inj.ash": 0.28,
                                "coal_feed.nhv_kj_kg": 19500.0,
                                "coal_inj.nhv_kj_kg": 20200.0},
    "Custom": {},
}
scenario = st.sidebar.selectbox(
    "Preset", list(SCENARIOS), index=0,
    help="Domestic Coal uses a realistic Indian G12-G14 analysis, 30% ash at "
         "about 4,660 kcal/kg. Be aware that it currently solves to roughly "
         "2.05 t-coal/t-DRI, above CEEW's surveyed 1.4 to 1.6, so the Coal "
         "Consumption check will fail. That is a known model gap at high ash, "
         "kept visible rather than tuned away.")
overrides.update(SCENARIOS[scenario])

st.sidebar.markdown("### Plant Configuration")
capacity = st.sidebar.select_slider(
    "Rated Capacity", [50, 100, 175, 350, 500, 600], value=100,
    format_func=lambda v: f"{v} TPD")
utilization = st.sidebar.slider(
    "Capacity Utilisation", 0.50, 0.95, float(defaults["plant.utilization"]),
    0.05, format="%.2f")

st.sidebar.markdown("### Coal")
coal_mode = st.sidebar.radio(
    "Coal Rate Basis", ["solve", "specified"],
    format_func=lambda m: {"solve": "Solve From Energy Balance",
                           "specified": "Specify Directly"}[m],
    help="In Solve mode the coal rate is whatever closes the kiln energy "
         "balance, then validated against CEEW's surveyed band. Recommended: "
         "it makes coal consumption a result rather than an input.")
overrides["coal.rate_mode"] = coal_mode
if coal_mode == "specified":
    lo, hi = defaults.bounds("coal.rate_t_per_t_dri")
    overrides["coal.rate_t_per_t_dri"] = st.sidebar.slider(
        "Coal Rate", float(lo), float(hi),
        float(defaults["coal.rate_t_per_t_dri"]), 0.01,
        format="%.2f t/t",
        help="CEEW survey: imported coal 0.9 to 1.1, domestic 1.4 to 1.6.")

st.sidebar.markdown("### Retrofits")
whr_on = st.sidebar.toggle("Waste Heat Recovery")
biomass_pct = st.sidebar.slider(
    "Biomass Substitution", 0, int(defaults["biomass.max_substitution_frac"] * 100),
    0, 5, format="%d%%") / 100.0
h2_pct = st.sidebar.slider(
    "Hydrogen Substitution", 0,
    int(defaults["hydrogen.max_substitution_frac"] * 100), 0, 5,
    format="%d%%") / 100.0

st.sidebar.markdown("### Accounting Conventions")
overrides["biomass.biogenic_co2_zero_rated"] = int(st.sidebar.toggle(
    "Zero-Rate Biogenic CO2",
    value=bool(defaults["biomass.biogenic_co2_zero_rated"]),
    help="IPCC convention. Switch off to see gross stack CO2 including the "
         "biomass carbon."))
overrides["hydrogen.ef_t_per_t"] = st.sidebar.selectbox(
    "Hydrogen Supply Route", [0.0, 9.5],
    format_func=lambda x: "Green, Electrolytic" if x == 0 else "Grey, SMR")

# ===========================================================================
# Model run
# ===========================================================================
# The coal-rate solve bisects the energy balance a few hundred times, and the
# validation pass runs the whole model again. Caching on the control values
# means switching tabs re-renders rather than re-solves.
@st.cache_data(show_spinner="Solving Plant Model", max_entries=24)
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


params = defaults.with_overrides(overrides)
_key = tuple(sorted(overrides.items()))
_solved = solve(_key, capacity, utilization)
plant, eb, mb = _solved["plant"], _solved["energy"], _solved["mass"]

aux = params["power.aux_kwh_per_t_dri"]
net_import, export, capex, capex_opex = aux, 0.0, 0.0, 0.0
extra_opex, fossil_offset, biogenic_c, extra_scope2 = 0.0, 0.0, 0.0, 0.0
retrofits: dict[str, dict] = {}
warnings: list[str] = []

if whr_on:
    r = WHR(plant).calculate_impact(eb)
    retrofits["Waste Heat Recovery"] = r
    net_import, export = r["net_import_kwh_per_t_dri"], r["export_kwh_per_t_dri"]
    capex += r["capex_inr"]
    capex_opex += r["annual_opex_inr"]
if biomass_pct > 0:
    r = Biomass(plant, biomass_pct).calculate_impact()
    retrofits["Biomass Substitution"] = r
    extra_opex += r["opex_delta_inr_per_t_dri"]
    fossil_offset += r["fossil_carbon_removed_kg_per_t_dri"]
    biogenic_c += r["biogenic_carbon_to_gas_kg_per_t_dri"]
    if not r["reductant_carbon_adequate"]:
        warnings.append(
            f"Biomass at {biomass_pct:.0%} leaves a reductant carbon ratio of "
            f"{r['reductant_carbon_ratio']:.2f}. Below 1.0 there is not enough "
            "carbon to strip the oxygen from the burden.")
if h2_pct > 0:
    r = Hydrogen(plant, h2_pct).calculate_impact()
    retrofits["Hydrogen Substitution"] = r
    extra_opex += r["opex_delta_inr_per_t_dri"]
    fossil_offset += r["fossil_carbon_removed_kg_per_t_dri"]
    extra_scope2 += r["h2_supply_co2_t_per_t_dri"]
    if not r["reductant_carbon_adequate"]:
        warnings.append(
            f"Hydrogen at {h2_pct:.0%} leaves a reductant carbon ratio of "
            f"{r['reductant_carbon_ratio']:.2f}.")

co2 = CO2Model(plant).calculate_emissions(
    net_power_import_kwh_per_t=net_import, biogenic_carbon_kg_per_t=biogenic_c,
    fossil_carbon_offset_kg_per_t=fossil_offset,
    extra_scope2_t_per_t=extra_scope2)
econ = EconomicsModel(plant).calculate_economics(
    net_power_import_kwh_per_t=net_import, power_export_kwh_per_t=export,
    extra_opex_inr_per_t=extra_opex, capex_inr=capex,
    capex_opex_inr_per_yr=capex_opex)

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
ui.header(
    "Rotary-Kiln DRI Digital Twin",
    f"{scenario} · {capacity} TPD rated · "
    f"{plant.production_tpd:,.0f} TPD produced at {utilization:.0%} utilisation",
    [(f"{counts['PASS']} of {counts['PASS'] + counts['FAIL'] + counts['WARN']} "
      f"Checks Pass",
      T.STATUS["good"] if counts["FAIL"] == 0 else T.STATUS["warning"]),
     (f"Mass Closure {mb['error_percent']:.2f}%",
      T.STATUS["good"] if mb["is_valid"] else T.STATUS["critical"]),
     (f"Energy Closure {eb['closure_error_percent']:.2f}%",
      T.STATUS["good"] if eb["is_valid"] else T.STATUS["critical"])])

for w in warnings:
    st.warning(w, icon="⚠")
if not mb["is_valid"]:
    st.error(f"Mass balance does not close: {mb['error_percent']:.2f}%.",
             icon="■")
if not eb["is_valid"]:
    st.error(f"Energy balance does not close: "
             f"{eb['closure_error_percent']:.2f}%.", icon="■")

tabs = st.tabs(["Overview", "Mass & Energy", "Emissions", "Economics",
                "Validation", "Parameters"])

# ===========================================================================
# Overview
# ===========================================================================
with tabs[0]:
    left, right = st.columns([1, 2.1], gap="large")
    with left:
        d_co2 = co2["co2_total_t_per_t_dri"] - base_co2["co2_total_t_per_t_dri"]
        ui.hero("Carbon Intensity", f"{co2['co2_total_t_per_t_dri']:.2f}",
                "t CO2 / t DRI",
                (f"{d_co2:+.2f} against the retrofit-free baseline"
                 if has_retrofit else
                 "No retrofits applied. This is the baseline plant."))
    with right:
        c = st.columns(3)
        with c[0]:
            ui.stat_tile("Production", T.compact(plant.production_tpd), "TPD")
        with c[1]:
            ui.stat_tile("Cost of Production",
                         T.rupees(econ["cost_per_t_dri"]), "/ t DRI",
                         delta=econ["cost_per_t_dri"] - base_econ["cost_per_t_dri"],
                         delta_text=(
                             T.rupees(abs(econ["cost_per_t_dri"]
                                          - base_econ["cost_per_t_dri"]))
                             + " vs baseline") if has_retrofit else "",
                         lower_is_better=True)
        with c[2]:
            ui.stat_tile("Retrofit Capital",
                         T.rupees(capex, compact_form=True) if capex else "None",
                         "" if capex else "")
        c = st.columns(3)
        with c[0]:
            ui.stat_tile("Coal Rate", f"{plant.coal_rate:.3f}", "t / t DRI")
        with c[1]:
            ui.stat_tile("Specific Energy",
                         f"{eb['sec_gcal_per_t_dri']:.2f}", "Gcal / t DRI")
        with c[2]:
            ui.stat_tile("Reductant Carbon Ratio",
                         f"{plant.reductant_carbon_ratio:.2f}", "× minimum")

    if plant.coal_rate_solved:
        st.caption(
            f"Coal rate solved from the energy balance to "
            f"{plant.coal_rate:.4f} t per t DRI. CEEW surveyed 0.9 to 1.1 for "
            f"imported coal and 1.4 to 1.6 for domestic coal.")

    if has_retrofit:
        ui.section("Scenario Against Baseline",
                   "Each metric indexed to its own retrofit-free baseline, so "
                   "quantities in different units share one axis.")
        metrics = [
            {"label": "Carbon Intensity", "unit": "t CO2/t DRI",
             "baseline": base_co2["co2_total_t_per_t_dri"],
             "scenario": co2["co2_total_t_per_t_dri"]},
            {"label": "Cost of Production", "unit": "INR/t DRI",
             "baseline": base_econ["cost_per_t_dri"],
             "scenario": econ["cost_per_t_dri"]},
            {"label": "Grid Power Import", "unit": "kWh/t DRI",
             "baseline": aux, "scenario": net_import},
        ]
        st.plotly_chart(charts.scenario_dumbbell(metrics), config=PLOT_CONFIG)
        table(pd.DataFrame([
            {"Metric": m["label"], "Unit": m["unit"],
             "Baseline": round(m["baseline"], 4),
             "Scenario": round(m["scenario"], 4),
             "Change": round(m["scenario"] - m["baseline"], 4)}
            for m in metrics]))

        ui.section("Retrofit Detail")
        for name, r in retrofits.items():
            with st.expander(name, expanded=len(retrofits) == 1):
                st.dataframe(pd.DataFrame([
                    {"Quantity": title_case(k), "Value": _cell(v)}
                    for k, v in r.items()]), width="stretch", hide_index=True)
    else:
        ui.section("No Retrofit Selected",
                   "Enable Waste Heat Recovery, Biomass or Hydrogen "
                   "substitution in the control panel to compare a scenario "
                   "against this baseline.")

# ===========================================================================
# Mass & Energy
# ===========================================================================
with tabs[1]:
    ui.section("Mass Flow", "Kilograms per tonne of DRI. Combustion air and "
                            "waste gas dominate the flow, as they do in a real "
                            "kiln.")
    st.plotly_chart(charts.mass_sankey(plant), config=PLOT_CONFIG)
    table(pd.DataFrame([
        {"Stream": stream(r["stream"]),
         "Direction": r["direction"].title(),
         "kg / t DRI": round(r["kg_per_t_dri"], 2),
         "TPD": round(r["tpd"], 3)} for r in plant.stream_table()]))

    c1, c2 = st.columns([1.15, 1], gap="large")
    with c1:
        ui.section("Element Closure",
                   f"Total mass closes to {mb['error_percent']:.2f}% against a "
                   f"{mb['tolerance_percent']:.0f}% tolerance.")
        st.dataframe(pd.DataFrame([
            {"Element": title_case(e["element"]),
             "In (kg/t)": round(e["in_kg_per_t_dri"], 2),
             "Out (kg/t)": round(e["out_kg_per_t_dri"], 2),
             "Error %": round(e["error_percent"], 4),
             "Status": "Pass" if e["is_valid"] else "Fail"}
            for e in mb["element_balances"]]), width="stretch", hide_index=True)
    with c2:
        ui.section("Waste Gas Composition")
        st.dataframe(pd.DataFrame([
            {"Species": title_case(k), "kg / t DRI": round(v, 2)}
            for k, v in plant.waste_gas_composition.items()]),
            width="stretch", hide_index=True)

    ui.section("Energy Ledger",
               f"Kiln boundary, on a coal net-heating-value basis of "
               f"{eb['sec_gcal_per_t_dri']:.2f} Gcal per tonne of DRI. "
               f"Closes to {eb['closure_error_percent']:.2f}%.")
    st.plotly_chart(charts.energy_ledger(eb, plant.nhv_coal_kj),
                    config=PLOT_CONFIG)
    table(pd.DataFrame([
        {"Group": ENERGY_GROUPS.get(g, title_case(g)), "Item": title_case(k),
         "Gcal / t DRI": round(v * GCAL_PER_KJ, 4),
         "% of Coal NHV": round(v / plant.nhv_coal_kj * 100, 2)}
        for g, items in eb["items"].items() for k, v in items.items()]),
        "Volatile terms are labelled To ABC because they leave the kiln "
        "unburnt but are post-combusted downstream, where waste heat recovery "
        "can claim them.")

# ===========================================================================
# Emissions
# ===========================================================================
with tabs[2]:
    c = st.columns(4)
    with c[0]:
        ui.stat_tile("Direct, Stack", f"{co2['co2_direct_t_per_t_dri']:.3f}",
                     "t / t DRI")
    with c[1]:
        ui.stat_tile("Scope 2, Power", f"{co2['co2_scope2_t_per_t_dri']:.3f}",
                     "t / t DRI")
    with c[2]:
        ui.stat_tile("Reported Total", f"{co2['co2_total_t_per_t_dri']:.3f}",
                     "t / t DRI",
                     delta=co2["co2_total_t_per_t_dri"]
                           - base_co2["co2_total_t_per_t_dri"],
                     delta_text=f"{abs(co2['co2_total_t_per_t_dri'] - base_co2['co2_total_t_per_t_dri']):.3f} vs baseline"
                     if has_retrofit else "", lower_is_better=True)
    with c[3]:
        ui.stat_tile("Implied Coal Factor",
                     f"{co2['implied_coal_ef_t_per_t_coal']:.3f}",
                     "t CO2 / t coal")

    ui.section("Composition of Reported Intensity",
               "Derived from the carbon balance, not from a blanket emission "
               "factor.")
    st.plotly_chart(
        charts.co2_composition(co2, base_co2 if has_retrofit else None),
        config=PLOT_CONFIG)
    table(pd.DataFrame([
        {"Quantity": title_case(k), "Value": _cell(v)}
        for k, v in co2.items()]),
        "The 2.4 t CO2 per t coal used previously would require 65.5% carbon "
        "coal, against the 60.6 to 62.2% measured by Dey et al.")

# ===========================================================================
# Economics
# ===========================================================================
with tabs[3]:
    c = st.columns(4)
    with c[0]:
        ui.stat_tile("Total Cost", T.rupees(econ["cost_per_t_dri"]), "/ t DRI")
    with c[1]:
        ui.stat_tile("Cash Cost", T.rupees(econ["cash_cost_per_t_dri"]),
                     "/ t DRI")
    with c[2]:
        ui.stat_tile("Annualised Capital",
                     T.rupees(econ["capex_charge_per_t_dri"]), "/ t DRI")
    with c[3]:
        ui.stat_tile("Annual Output", T.compact(econ["annual_output_t"]),
                     "t / yr")

    ui.section("Cost Composition",
               "Costs to the right, credits to the left. Capital is annualised "
               f"at a recovery factor of {econ['capital_recovery_factor']:.4f}, "
               f"{params['econ.discount_rate']:.0%} over "
               f"{params['econ.project_life_yr']:.0f} years, so it is "
               "comparable with operating cost.")
    st.plotly_chart(charts.cost_composition(econ), config=PLOT_CONFIG)
    table(pd.DataFrame([
        {"Line Item": COST_LINES.get(k, title_case(k)),
         "INR / t DRI": round(v, 2)}
        for k, v in econ["breakdown_inr_per_t_dri"].items()]))

# ===========================================================================
# Validation
# ===========================================================================
with tabs[4]:
    c = st.columns(4)
    for col, key in zip(c, ("PASS", "WARN", "FAIL", "INFO")):
        style = T.VERDICT[key]
        with col:
            ui.stat_tile(style["label"], str(counts[key]))

    ui.section("Model Outputs Against Literature Bands",
               "These bands are acceptance criteria, never model inputs. No "
               "parameter in the configuration appears here, so a pass is "
               "evidence rather than a tautology.")
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
    st.caption("Waste heat recovery generation is a known open gap, documented "
               "in config/validation_targets.json. It is reported rather than "
               "tuned away.")

# ===========================================================================
# Parameters
# ===========================================================================
with tabs[5]:
    summary = params.provenance_summary()
    c = st.columns(4)
    with c[0]:
        ui.stat_tile("Parameters", str(summary["total"]))
    with c[1]:
        ui.stat_tile("Traced to a Source", str(summary.get("verified", 0)))
    with c[2]:
        ui.stat_tile("Need a Citation", str(summary.get("needs_citation", 0)))
    with c[3]:
        ui.stat_tile("Sensitivity Flagged", str(len(params.sensitivity_keys())))

    ui.section("Parameter Provenance",
               "Every numeric assumption the model uses, with its source and "
               "the range it is plausible over.")
    f1, f2 = st.columns([1, 2])
    status_filter = f1.selectbox(
        "Provenance Status",
        ["All", "Verified", "Needs Citation", "Physical Constant"])
    search = f2.text_input("Search Parameters", placeholder="coal, whr, co2")

    rows = params.provenance_rows()
    if status_filter != "All":
        wanted = status_filter.lower().replace(" ", "_")
        rows = [r for r in rows if r["status"] == wanted]
    if search:
        q = search.lower()
        rows = [r for r in rows
                if q in r["parameter"].lower() or q in r["source"].lower()]

    st.dataframe(pd.DataFrame([{
        "Status": f"{T.PROVENANCE.get(r['status'], {}).get('icon', '')} "
                  f"{T.PROVENANCE.get(r['status'], {}).get('label', r['status'])}",
        "Parameter": r["parameter"],
        "Value": ("" if r["value"] is None else
                  f"{r['value']:,.6g}" if isinstance(r["value"], (int, float))
                  else str(r["value"])),
        "Unit": r["unit"],
        "Minimum": "" if r["min"] is None else f"{r['min']:,.6g}",
        "Maximum": "" if r["max"] is None else f"{r['max']:,.6g}",
        "Sensitivity": "Yes" if r["sensitivity_required"] else "No",
        "Source": r["source"],
    } for r in rows]), width="stretch", hide_index=True)
    st.caption(f"Showing {len(rows)} of {summary['total']} parameters. "
               f"Calibration plant: {params.calibration_plant}")
    st.download_button(
        "Download Provenance as CSV",
        pd.DataFrame(params.provenance_rows()).to_csv(index=False),
        "parameter_provenance.csv", "text/csv")
