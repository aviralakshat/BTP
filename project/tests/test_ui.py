"""Tests for the presentation layer: formatters, labels, chart construction."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.economics.economics import EconomicsModel
from src.emissions.co2_model import CO2Model
from src.models.energy_balance import EnergyBalance
from src.models.plant import build_plant
from src.retrofits.whr import WHR
from src.ui import charts
from src.ui import theme as T
from src.ui.labels import title_case
from src.validation.literature_check import run_checks


@pytest.fixture(scope="module")
def model():
    plant = build_plant(capacity_tpd=100, utilization=0.9)
    eb = EnergyBalance(plant).calculate_balance()
    whr = WHR(plant).calculate_impact(eb)
    return {
        "plant": plant, "energy": eb, "whr": whr,
        "co2": CO2Model(plant).calculate_emissions(),
        "econ": EconomicsModel(plant).calculate_economics(capex_inr=2e8),
        "validation": run_checks(capacity_tpd=100, utilization=0.9),
    }


# --- formatters ------------------------------------------------------------
@pytest.mark.parametrize("value,expected", [
    (5.773, "5.77"), (60, "60.0"), (1284, "1,284"), (12900, "12.9K"),
    (4.2e6, "4.2M"),
])
def test_compact_abbreviates_above_ten_thousand(value, expected):
    assert T.compact(value) == expected


def test_rupee_sign_precedes_the_symbol():
    """INR -170 reads as a malformed amount; -INR 170 reads as a credit."""
    assert T.rupees(-170) == "-₹170"
    assert T.rupees(9729) == "₹9,729"
    assert T.rupees(219311904, compact_form=True) == "₹21.93 Cr"


def test_label_fit_check_rejects_undersized_marks():
    assert T.fits_inside("2.15", 0.5)
    assert not T.fits_inside("Power Export Revenue", 0.02)


# --- labels ----------------------------------------------------------------
@pytest.mark.parametrize("raw,expected", [
    ("iron ore consumption", "Iron Ore Consumption"),
    ("volatile carbon to ABC", "Volatile Carbon to ABC"),
    ("reduction of iron oxides", "Reduction of Iron Oxides"),
    ("waste-gas sensible heat share", "Waste-Gas Sensible Heat Share"),
    ("calcined flux (CaO+MgO)", "Calcined Flux (CaO+MgO)"),
    ("CO slip to ABC", "CO Slip to ABC"),
])
def test_title_case(raw, expected):
    assert title_case(raw) == expected


# --- palette contract ------------------------------------------------------
def test_categorical_slots_are_fixed_and_never_cycled():
    assert len(T.SERIES) == 8
    assert len(set(T.SERIES)) == 8
    assert T.SERIES[0] == "#2a78d6"


def test_status_colours_are_not_reused_as_series_colours():
    assert not set(T.STATUS.values()) & set(T.SERIES)


def test_every_verdict_ships_an_icon_and_a_label():
    for style in T.VERDICT.values():
        assert style["icon"] and style["label"]


def test_diverging_pair_is_warm_against_cool():
    assert T.DIVERGING_POS != T.DIVERGING_NEG
    assert T.DIVERGING_MID not in (T.DIVERGING_POS, T.DIVERGING_NEG)


# --- chart construction ----------------------------------------------------
def test_every_chart_builds(model):
    figs = [
        charts.cost_composition(model["econ"]),
        charts.co2_composition(model["co2"]),
        charts.co2_composition(model["co2"], model["co2"]),
        charts.mass_sankey(model["plant"]),
        charts.energy_ledger(model["energy"], model["plant"].nhv_coal_kj),
        charts.validation_meters(model["validation"]["rows"]),
        charts.scenario_dumbbell([
            {"label": "Carbon Intensity", "unit": "t/t", "baseline": 2.2,
             "scenario": 1.7}]),
    ]
    for fig in figs:
        assert fig.data
        assert fig.layout.height > 0


def test_sankey_links_conserve_the_stream_table(model):
    fig = charts.mass_sankey(model["plant"])
    link_total = sum(fig.data[0].link.value)
    expected = (sum(model["plant"].inputs.values())
                + sum(model["plant"].outputs.values()))
    assert link_total == pytest.approx(expected, rel=1e-9)


def test_zero_segments_do_not_create_legend_entries(model):
    """With WHR covering all in-plant demand, Scope 2 is zero and must not
    appear as an invisible legend entry."""
    co2 = CO2Model(model["plant"]).calculate_emissions(
        net_power_import_kwh_per_t=0.0)
    names = {t.name for t in charts.co2_composition(co2).data}
    assert "Scope 2 (Power)" not in names


def test_validation_marker_shape_varies_with_verdict(model):
    fig = charts.validation_meters(model["validation"]["rows"])
    symbols = {t.marker.symbol for t in fig.data}
    assert len(symbols) > 1, "verdict must not be carried by colour alone"


def test_cost_axis_includes_zero(model):
    fig = charts.cost_composition(model["econ"])
    lo, hi = fig.layout.xaxis.range
    assert lo <= 0 <= hi
