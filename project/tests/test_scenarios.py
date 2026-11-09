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
