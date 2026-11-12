"""Phase 3: tornado, Morris, Monte Carlo, the abatement curve and the search.

The plant solve is the slow part, so the tornado, the curve and the search are
built once per test session and reused. The probability sample in the tests is
a small seeded draw, not the 400-draw run the dashboard button starts.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analysis.macc import carbon_overlay, marginal_curve, price_break_evens
from src.analysis.montecarlo import propagate
from src.analysis.plant_eval import (
    apply_factor_point, as_flags, headlines, label_of, solve, varying_factors,
)
from src.analysis.scenarios import CO2_TARGETS, evaluate, least_cost, pathway_grid
from src.analysis.sensitivity import coded_trajectories, morris, tornado
from src.analysis.settings import carbon_cases, load_analysis
from src.data.coal import closure
from src.data.parameters import Parameters
from src.models.energy_balance import EnergyBalance
from src.models.plant import build_plant
from src.optimization.search import search_all
from src.ui import charts
from src.ui import theme as T

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


@pytest.fixture(scope="module")
def solved():
    params = Parameters()
    plant = build_plant(params)
    energy = EnergyBalance(plant).calculate_balance()
    return params, plant, energy


@pytest.fixture(scope="module")
def swept(solved):
    return tornado(solved[0])


@pytest.fixture(scope="module")
def decided(solved):
    _params, plant, energy = solved
    return {
        "macc": marginal_curve(plant, energy),
        "breaks": price_break_evens(plant, energy),
        "search": search_all(plant, energy),
        "carbon": carbon_overlay(plant, energy),
        "grid": pathway_grid(plant, energy),
    }


def _row(swept, name):
    return next(row for row in swept["rows"] if row["parameter"] == name)


# --- tornado ---------------------------------------------------------------
def test_tornado_covers_every_flagged_parameter_and_the_closed_coals(solved, swept):
    flagged = set(solved[0].sensitivity_keys())
    named = {row["parameter"] for row in swept["rows"]}
    assert flagged <= named
    assert "coal_feed.ash (closed analysis)" in named
    assert "coal_inj.ash (closed analysis)" in named
    assert swept["reference_label"] == load_analysis()["reference_pathway"]["label"]


def test_reference_label_matches_the_pathway_formatter():
    cfg = load_analysis()
    assert label_of(as_flags(cfg["reference_pathway"])) == cfg["reference_pathway"]["label"]


def test_coal_components_cannot_move_alone_and_the_closed_analysis_can(solved, swept):
    carbon = _row(swept, "coal_feed.total_carbon")
    assert not carbon["low_ok"] and not carbon["high_ok"]
    assert "not a physical material" in carbon["note"]
    closed = _row(swept, "coal_feed.ash (closed analysis)")
    assert closed["low_ok"] and closed["high_ok"]
    assert closed["cost_swing"] > 100
    for ash in solved[0].bounds("coal_feed.ash"):
        from src.data.coal import daf_rescale
        totals = closure(solved[0].with_overrides(daf_rescale(solved[0], "coal_feed", ash)),
                         "coal_feed")
        assert totals["ultimate"] == pytest.approx(1.0)
        assert totals["proximate"] == pytest.approx(1.0)


def test_heating_value_is_the_largest_bare_plant_cost_swing(swept):
    ranked = sorted((row for row in swept["rows"] if row["cost_swing"]),
                    key=lambda row: row["cost_swing"], reverse=True)
    assert ranked[0]["parameter"] == "coal_feed.nhv_kj_kg"
    assert "not one consistent coal" in ranked[0]["note"]


def test_solved_coal_rate_is_not_treated_as_an_input(swept):
    row = _row(swept, "coal.rate_t_per_t_dri")
    assert row["method"] == "not_an_input"
    assert row["cost_swing"] == 0.0
    assert row["co2_swing"] == 0.0


def test_biogenic_accounting_is_a_switch_and_it_moves_the_co2_cut(swept):
    row = _row(swept, "biomass.biogenic_co2_zero_rated")
    assert row["method"] == "scenario_switch"
    assert (row["low"], row["high"]) == (0, 1)
    assert row["co2_cut_at_low"] != pytest.approx(row["co2_cut_at_high"])


def test_a_parameter_with_no_cited_range_is_reported_and_not_given_a_swing(swept):
    row = _row(swept, "econ.coal_price_inr_per_t")
    assert row["method"] == "no_range"
    assert row["cost_swing"] is None


# --- Morris and Monte Carlo ------------------------------------------------
def test_morris_trajectories_stay_in_the_unit_interval_and_change_one_factor():
    delta = 4 / (2 * 3)
    for trajectory in coded_trajectories(6, 4, 4, seed=11):
        assert np.all(trajectory >= -1e-9)
        assert np.all(trajectory <= 1 + 1e-9)
        for step in range(trajectory.shape[0] - 1):
            gap = np.abs(trajectory[step + 1] - trajectory[step])
            changed = np.flatnonzero(gap > 1e-8)
            assert len(changed) == 1
            assert gap[changed[0]] == pytest.approx(delta)


def test_morris_recovers_the_slopes_of_a_linear_model_and_repeats():
    factors = [{"key": "a", "lo": 0.0, "hi": 1.0, "closed": False},
               {"key": "b", "lo": 0.0, "hi": 1.0, "closed": False}]

    def evaluate_at(values):
        return {"y": values[0] + 3.0 * values[1]}

    first = morris(evaluate_at, factors, ["y"], r=4, p=4, seed=5)
    second = morris(evaluate_at, factors, ["y"], r=4, p=4, seed=5)
    assert first["outputs"]["y"]["mu_star"] == pytest.approx([1.0, 3.0])
    assert second["outputs"]["y"]["mu_star"] == first["outputs"]["y"]["mu_star"]
    assert first["rank_agreement"]["y"] == pytest.approx(1.0)


def test_a_two_factor_plant_sample_is_seeded(solved):
    params = solved[0]
    wanted = {"ore.fe_total_frac", "kiln.radiation_loss_frac"}
    factors = [factor for factor in varying_factors(params)[0]
               if factor["key"] in wanted]
    flags = as_flags(load_analysis()["reference_pathway"])

    def evaluate_at(values):
        solved_run, reason = solve(apply_factor_point(params, factors, values))
        assert solved_run is not None, reason
        return {"cost": headlines(solved_run, flags)["cost_inr_per_t"]}

    first = morris(evaluate_at, factors, ["cost"], r=2, p=4, seed=9)
    second = morris(evaluate_at, factors, ["cost"], r=2, p=4, seed=9)
    assert first["n_failed_points"] == 0
    assert first["outputs"]["cost"]["mu_star"] == second["outputs"]["cost"]["mu_star"]
    assert max(first["outputs"]["cost"]["mu_star"]) > 0


def test_probability_sample_skips_scenario_choices_and_locked_coal(solved):
    factors, skipped = varying_factors(solved[0])
    keys = {factor["key"] for factor in factors if not factor["closed"]}
    assert "hydrogen.ef_t_per_t" not in keys
    assert "biomass.biogenic_co2_zero_rated" not in keys
    assert "coal_feed.total_carbon" not in keys
    assert any(factor["closed"] and factor["key"] == "coal_feed.ash" for factor in factors)
    assert any(row["parameter"] == "coal.rate_t_per_t_dri" for row in skipped)


def test_a_point_distribution_removes_the_factor(solved):
    distributions = {"overrides": {
        "econ.dolomite_price_inr_per_t": {"distribution": "point", "value": 750}}}
    factors, _skipped = varying_factors(solved[0], distributions)
    assert all(factor["key"] != "econ.dolomite_price_inr_per_t" for factor in factors)


def test_monte_carlo_percentiles_repeat_for_a_seed(solved):
    first = propagate(solved[0], n=12, seed=21)
    second = propagate(solved[0], n=12, seed=21)
    assert first["n_rejected"] == 0
    for left, right in zip(first["summary"], second["summary"]):
        assert left["p50"] == pytest.approx(right["p50"])
        assert left["p10"] <= left["p50"] <= left["p90"]


# --- curve, prices, search -------------------------------------------------
def test_macc_marginals_add_up_and_the_first_bar_is_the_cheapest_standalone(decided):
    curve = decided["macc"]
    cumulative = 0.0
    for bar in curve["bars"]:
        assert bar["marginal_co2_t_per_t"] > 0
        assert bar["abatement_cost_inr_per_t_co2"] == pytest.approx(
            bar["marginal_cost_inr_per_t"] / bar["marginal_co2_t_per_t"])
        cumulative += bar["marginal_co2_t_per_t"]
        assert bar["cumulative_co2_t_per_t"] == pytest.approx(cumulative)
    standalone = [row["abatement_cost_inr_per_t_co2"]
                  for row in curve["standalone"]
                  if row["feasible"] and row["abatement_cost_inr_per_t_co2"] is not None]
    assert curve["bars"][0]["abatement_cost_inr_per_t_co2"] == pytest.approx(min(standalone))


def test_carbon_price_that_ties_the_baseline_is_the_abatement_cost(solved, decided):
    _params, plant, energy = solved
    bare = evaluate(plant, energy)
    scenario = evaluate(plant, energy, whr=True, baseline=bare)
    whr = next(row for row in decided["breaks"] if row["label"] == "WHR")
    assert whr["carbon_price_inr_per_t"] == pytest.approx(
        scenario["abatement_cost_inr_per_t_co2"])
    coal = next(price for price in whr["prices"]
                if price["parameter"] == "econ.coal_price_inr_per_t")
    power = next(price for price in whr["prices"]
                 if price["parameter"] == "econ.power_tariff_inr_per_kwh")
    export = next(price for price in whr["prices"]
                  if price["parameter"] == "econ.export_tariff_inr_per_kwh")
    assert coal["depends"] is False
    assert power["depends"] is True and power["linear"] is True
    assert export["depends"] is True and export["break_even"] is not None


def test_hydrogen_price_break_even_is_linear(decided):
    row = next(item for item in decided["breaks"]
               if item["label"] == "WHR + Biomass 10% + H2 10%")
    price = next(item for item in row["prices"]
                 if item["parameter"] == "hydrogen.price_inr_per_kg")
    assert price["depends"] is True
    assert price["linear"] is True
    assert price["break_even"] > 0


def test_continuous_search_meets_the_target_and_does_not_lose_to_the_grid(decided):
    tol = decided["search"]["tolerance_inr_per_t"]
    for target, row in zip(CO2_TARGETS, decided["search"]["targets"]):
        best = least_cost(decided["grid"], target)
        if best is None:
            assert row["grid"] is None
        else:
            assert row["grid"]["label"] == best["label"]
            assert row["grid"]["cost_inr_per_t"] == pytest.approx(best["econ"]["cost_per_t_dri"])
            assert row["continuous"]["co2_reduction_frac"] >= target - 1e-9
            assert row["continuous"]["cost_inr_per_t"] <= row["grid"]["cost_inr_per_t"] + tol
            assert row["continuous_saving_vs_grid_inr_per_t"] >= -tol


def test_cbam_price_is_the_product_of_the_two_archived_figures():
    case = next(item for item in carbon_cases() if item["id"] == "cbam_q3_2026")
    assert case["inr_per_t"] == pytest.approx(case["eur_per_t"] * case["inr_per_eur"])
    assert case["eur_per_t"] == 82.32
    assert case["inr_per_eur"] == 104.8645
    text = open(os.path.join(ROOT, "data", "web", "2026_EC_CBAM-certificate-prices.txt")).read()
    rate = open(os.path.join(ROOT, "data", "web", "2026_ECB_Euro-reference-INR.txt")).read()
    cess = open(os.path.join(ROOT, "data", "web", "2025_PIB_Coal-GST-cess-removed.txt")).read()
    assert "82.32" in text
    assert "104.8645" in rate
    assert "removal of GST Compensation cess" in cess


def test_every_analysis_source_file_exists():
    missing = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key.endswith("source_file") and isinstance(value, str):
                    path = (os.path.join(ROOT, "data", value + ".txt")
                            if value.startswith("web/")
                            else os.path.join(ROOT, "data", "text", value + ".txt"))
                    if not os.path.exists(path):
                        missing.append(value)
                else:
                    walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(json.load(open(os.path.join(ROOT, "project", "config", "analysis.json"))))
    assert missing == []


def test_new_charts_use_the_fixed_colours_and_do_not_cycle():
    fig = charts.carbon_price_lines([
        {"label": "Baseline", "prices": [0, 1000], "costs": [7000, 9000]},
        {"label": "WHR", "prices": [0, 1000], "costs": [6400, 8200]},
    ])
    assert fig.data[0].line.color == T.SERIES[0]
    assert fig.data[1].line.color == T.SERIES[1]
    ranges = charts.tornado_ranges(
        [{"axis_label": "ore grade", "bar_label": "₹471", "hover": "0.60 → 0.67",
          "baseline_cost_at_low": 7449, "baseline_cost_at_high": 6978}],
        "baseline_cost_at_low", "baseline_cost_at_high",
        "Cost of Production (INR per t DRI)", base=7234)
    assert ranges.data[0].marker.color == T.SERIES[0]
    curve = charts.macc([{
        "order": 1, "measure": "Waste heat recovery",
        "marginal_co2_t_per_t": 0.04,
        "abatement_cost_inr_per_t_co2": -19000,
    }])
    assert curve.data
