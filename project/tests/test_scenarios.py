"""Retrofit pathway search: combined evaluation, frontier and break-even."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analysis.scenarios import (evaluate, h2_breakeven_price, least_cost,
                                    pareto_front, pathway_grid)
from src.models.energy_balance import EnergyBalance
from src.models.plant import build_plant
from src.retrofits.hydrogen import Hydrogen


@pytest.fixture(scope="module")
def solved():
    pl = build_plant(capacity_tpd=100, utilization=0.9)
    return pl, EnergyBalance(pl).calculate_balance()


@pytest.fixture(scope="module")
def grid(solved):
    return pathway_grid(*solved)


def test_baseline_scenario_has_no_reduction(solved):
    base = evaluate(*solved)
    r = evaluate(*solved, baseline=base)
    assert r["co2_reduction_frac"] == pytest.approx(0.0, abs=1e-12)
    assert r["cost_delta_inr_per_t_dri"] == pytest.approx(0.0, abs=1e-9)


def test_single_retrofit_ratio_matches_its_module(solved):
    pl, eb = solved
    r = evaluate(pl, eb, biomass_frac=0.2)
    assert r["reductant_carbon_ratio"] == pytest.approx(
        r["retrofits"]["Biomass Substitution"]["reductant_carbon_ratio"])


def test_frontier_is_monotone_in_cost_and_co2(grid):
    front = pareto_front(grid)
    assert front
    cuts = [r["co2_reduction_frac"] for r in front]
    costs = [r["econ"]["cost_per_t_dri"] for r in front]
    assert cuts == sorted(cuts) and costs == sorted(costs)
    assert all(r["feasible"] for r in front)


def test_least_cost_meets_its_target(grid):
    for t in (0.1, 0.2, 0.4):
        r = least_cost(grid, t)
        if r is not None:
            assert r["co2_reduction_frac"] >= t - 1e-9 and r["feasible"]


def test_unreachable_target_returns_none(grid):
    assert least_cost(grid, 0.99) is None


def test_h2_breakeven_zeroes_the_cost_delta(solved):
    pl, _ = solved
    be = h2_breakeven_price(pl)
    p = pl.p.with_overrides({"hydrogen.price_inr_per_kg": be})
    pl2 = build_plant(p, 100, 0.9)
    r = Hydrogen(pl2, 0.2).calculate_impact()
    assert r["opex_delta_inr_per_t_dri"] == pytest.approx(0.0, abs=1e-6)


def test_grid_factor_is_the_cea_average(solved):
    assert solved[0].p["power.grid_ef_t_per_mwh"] == 0.727


def test_oxygen_uses_the_table_not_the_six_percent_claim(solved):
    pl, energy = solved
    r = evaluate(pl, energy, oxygen=True)
    ox = r["retrofits"]["Oxygen Enrichment"]
    hourly = 4.15 / 4.29
    specific = 1.0 - hourly / 1.06
    assert ox["coal_reduction_frac"] == pytest.approx(specific, rel=1e-9)
    assert ox["coal_reduction_frac"] != pytest.approx(0.06, abs=1e-3)
    assert ox["authors_specific_coal_claim_frac"] == 0.06
    assert r["econ"]["annual_output_t"] == pytest.approx(
        pl.production_tpd * 1.06 * pl.p["plant.operating_days"])
    assert any("no oxygen price" in w for w in r["warnings"])


def test_kiln_control_is_capped_at_five_percent(solved):
    pl, energy = solved
    raised = build_plant(pl.p.with_overrides({"kiln_control.coal_saving_frac": 0.20}), 100, 0.9)
    r = evaluate(raised, EnergyBalance(raised).calculate_balance(), kiln_control=True)
    assert r["retrofits"]["Kiln Control"]["coal_reduction_frac"] == 0.05
    assert r["retrofits"]["Kiln Control"]["capped"]
    assert r["capex_inr"] == 5_000_000


def test_producer_gas_applies_the_energy_saving_without_a_capital_cost(solved):
    pl, energy = solved
    r = evaluate(pl, energy, producer_gas=True)
    pg = r["retrofits"]["Producer Gas"]
    assert pg["coal_reduction_frac"] == 0.20
    assert pg["capex_inr"] == 0.0
    assert pg["reference_coal_saving_t_per_year"] == 4200
    assert r["capex_inr"] == 0.0
    assert any("no sourced capital cost" in w for w in r["warnings"])


def test_biomass_and_hydrogen_capital_costs_add_up_in_the_pathway(solved):
    pl, energy = solved
    r = evaluate(pl, energy, biomass_frac=0.1, h2_frac=0.1)
    bio = r["retrofits"]["Biomass Substitution"]["capex_inr"]
    h2 = r["retrofits"]["Hydrogen Substitution"]["capex_inr"]
    assert bio > 0 and h2 > 0
    assert r["capex_inr"] == pytest.approx(bio + h2)
