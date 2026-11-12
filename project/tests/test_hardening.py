"""Phase 1 hardening: inputs that cannot describe a real plant are refused,
the solids partition holds across the coal-quality range, cost scales with size,
and the kiln and stack boundaries reconcile.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.coal import (COAL_STREAMS, InconsistentInputError, closure,
                           daf_rescale)
from src.data.parameters import MW, Parameters
from src.economics.economics import EconomicsModel, fixed_opex_inr_per_day
from src.emissions.co2_model import CO2Model
from src.models.energy_balance import EnergyBalance
from src.models.mass_balance import MassBalance
from src.models.plant import CoalRateNotSolvedError, build_plant
from src.retrofits.whr import WHR

# Dey et al. (2015) Table 10 flows, kg/h.
DEY_COAL_KG_H = 13_990 + 7_730
DEY_DRI_KG_H = 18_900
DEY_ORE_KG_H = 30_000
DEY_CHAR_KG_H = 2_900
DEY_DUST_KG_H = 3_159


@pytest.fixture(scope="module")
def params():
    return Parameters()


@pytest.fixture(scope="module")
def plant(params):
    return build_plant(params, capacity_tpd=100, utilization=0.9)


@pytest.fixture(scope="module")
def dey_plant(params):
    """The model run at Dey's own measured coal rate."""
    return build_plant(params.with_overrides({
        "coal.rate_mode": "specified",
        "coal.rate_t_per_t_dri": DEY_COAL_KG_H / DEY_DRI_KG_H}), 100, 0.9)


def _coal(params, ash, nhv=None):
    return {k: v for s in COAL_STREAMS
            for k, v in daf_rescale(params, s, ash, nhv_kj_kg=nhv).items()}


# --- parameter set ----------------------------------------------------------
def test_every_configured_value_is_inside_its_own_range(params):
    assert params.out_of_range() == []


def test_out_of_range_override_is_flagged(params):
    rows = params.with_overrides({"whr.boiler_efficiency": 0.95}).out_of_range()
    assert [r["parameter"] for r in rows] == ["whr.boiler_efficiency"]
    assert rows[0]["overridden"]


# --- coal composition ---------------------------------------------------------
def test_configured_coal_analyses_sum_to_one(params):
    for s in COAL_STREAMS:
        for total in closure(params, s).values():
            assert total == pytest.approx(1.0, abs=1e-6)


def test_raising_ash_alone_is_refused(params):
    """The old Domestic Coal preset did this and described 106% coal."""
    bad = params.with_overrides({"coal_feed.ash": 0.30})
    with pytest.raises(InconsistentInputError):
        build_plant(bad, 100, 0.9)


@pytest.mark.parametrize("ash", [0.05, 0.30, 0.45])
def test_daf_rescale_closes_and_keeps_the_organic_ratios(params, ash):
    q = params.with_overrides(_coal(params, ash))
    for s in COAL_STREAMS:
        for total in closure(q, s).values():
            assert total == pytest.approx(1.0, abs=1e-9)
        assert q[f"{s}.ash"] == ash
        assert (q[f"{s}.total_carbon"] / q[f"{s}.hydrogen"]
                == pytest.approx(params[f"{s}.total_carbon"]
                                 / params[f"{s}.hydrogen"]))


def test_daf_rescale_at_the_reference_ash_is_the_identity(params):
    for s in COAL_STREAMS:
        same = daf_rescale(params, s, params[f"{s}.ash"])
        for k, v in same.items():
            assert v == pytest.approx(params[k], rel=1e-9), k


# --- solids partition ---------------------------------------------------------
def test_char_partition_reproduces_dey_char(dey_plant):
    c = dey_plant
    assert c.char_rate_t_per_t_coal == pytest.approx(
        DEY_CHAR_KG_H / DEY_COAL_KG_H, rel=2e-3)
    assert c.c_char / c.char_mass == pytest.approx(c.p["char.fixed_carbon"], rel=2e-3)
    assert c.char_ash / c.char_mass == pytest.approx(c.p["char.ash"], rel=2e-3)


def test_dust_partition_reproduces_dey_dust(dey_plant):
    c = dey_plant
    assert c.dust_mass / c.ore_dry == pytest.approx(
        DEY_DUST_KG_H / DEY_ORE_KG_H, rel=1e-2)


@pytest.mark.parametrize("ash", [0.05, 0.10, 0.15, 0.20, 0.30, 0.35, 0.40, 0.45])
def test_plant_solves_and_closes_across_the_ash_range(params, ash):
    pl = build_plant(params.with_overrides(_coal(params, ash)), 100, 0.9)
    assert EnergyBalance(pl).calculate_balance()["is_valid"]
    mb = MassBalance(pl).calculate_balance()
    assert mb["is_valid"] and mb["all_elements_valid"]
    assert pl.free_ash > 0 and pl.char_mass > 0 and pl.dust_mass > 0


def test_coal_rate_rises_smoothly_with_ash(params):
    rates = [build_plant(params.with_overrides(_coal(params, a)), 100, 0.9).coal_rate
             for a in (0.10, 0.20, 0.30, 0.40)]
    steps = [b - a for a, b in zip(rates, rates[1:])]
    assert all(s > 0 for s in steps)
    # Convex but not explosive: no 10-point ash step more than doubles the last.
    assert all(b < 2.0 * a for a, b in zip(steps, steps[1:]))


def test_unsolvable_coal_raises_rather_than_returning_a_default(params):
    with pytest.raises(CoalRateNotSolvedError):
        build_plant(params.with_overrides(_coal(params, 0.70)), 100, 0.9)


# --- scale --------------------------------------------------------------------
def test_fixed_opex_equals_the_configured_value_at_its_reference_size(params):
    assert fixed_opex_inr_per_day(params, params["econ.fixed_opex_ref_tpd"]) \
        == pytest.approx(params["econ.fixed_opex_inr_per_day"])


def test_fixed_cost_per_tonne_falls_with_capacity(params):
    per_t = [EconomicsModel(build_plant(params, cap, 0.9)).calculate_economics()
             ["breakdown_inr_per_t_dri"]["fixed OPEX"] for cap in (100, 200, 350, 500)]
    assert per_t == sorted(per_t, reverse=True)
    x = params["econ.fixed_opex_scale_exponent"]
    assert per_t[-1] / per_t[0] == pytest.approx(5.0 ** (x - 1.0), rel=1e-6)


def test_whr_unit_cost_falls_with_size_and_matches_gaurav_at_reference(params):
    def unit_cost(cap):
        pl = build_plant(params, cap, 0.9)
        return WHR(pl).calculate_impact(EnergyBalance(pl).calculate_balance())
    small, large = unit_cost(100), unit_cost(500)
    assert large["capex_inr_per_mw"] < small["capex_inr_per_mw"]
    x = params["econ.capex_scale_exponent"]
    ratio = (large["capacity_mw"] / small["capacity_mw"]) ** (x - 1.0)
    assert large["capex_inr_per_mw"] / small["capex_inr_per_mw"] \
        == pytest.approx(ratio, rel=1e-6)
    ref = params["whr.capex_ref_mw"]
    at_ref = small["capex_inr"] * (ref / small["capacity_mw"]) ** x / ref
    assert at_ref == pytest.approx(params["whr.capex_inr_per_mw"], rel=1e-9)


# --- boundary audit -----------------------------------------------------------
def test_carbon_partition_is_exhaustive(plant):
    c_in = plant.c_coal + plant.c_dolomite
    c_out = (plant.c_char + plant.c_dust + plant.c_dri + plant.c_unburnt_vm
             + plant.c_gasified)
    # Dolomite carbon leaves in the waste gas outside c_gasified.
    assert c_out + plant.c_dolomite == pytest.approx(c_in, rel=1e-12)


def test_stack_co2_is_every_gas_phase_carbon_atom(plant):
    """Stack boundary: unburnt volatiles leave the kiln but burn in the ABC."""
    co2 = CO2Model(plant).calculate_emissions()
    gas_c = plant.c_gasified + plant.c_unburnt_vm + plant.c_dolomite
    assert co2["co2_direct_t_per_t_dri"] * 1000 == pytest.approx(
        gas_c * MW["CO2"] / MW["C"], rel=1e-9)


def test_every_unburnt_energy_term_is_labelled_lost_or_to_abc(plant):
    eb = EnergyBalance(plant).calculate_balance()
    items = eb["items"]["chemical energy out (unburnt)"]
    for name in items:
        assert name.endswith("(lost)") or name.endswith("to ABC"), name
    to_abc = sum(v for k, v in items.items() if k.endswith("to ABC"))
    lost = sum(v for k, v in items.items() if k.endswith("(lost)"))
    assert to_abc == pytest.approx(eb["recoverable_chemical_kj"], rel=1e-12)
    assert lost == pytest.approx(eb["solid_carbon_loss_kj"], rel=1e-12)


def test_scope2_is_net_import_times_the_grid_factor(plant):
    co2 = CO2Model(plant).calculate_emissions(net_power_import_kwh_per_t=100.0)
    assert co2["co2_scope2_t_per_t_dri"] == pytest.approx(
        0.1 * plant.p["power.grid_ef_t_per_mwh"])
