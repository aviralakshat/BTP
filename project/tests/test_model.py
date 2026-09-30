"""Regression tests for the DRI digital twin.

These assert the properties that must hold for the model to be trustworthy:
balances close, streams stay physical, retrofits move results in the right
direction, and the headline outputs stay inside their literature bands.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.parameters import Parameters
from src.economics.economics import EconomicsModel, capital_recovery_factor
from src.emissions.co2_model import CO2Model
from src.models.baseline import BaselinePlant
from src.models.energy_balance import EnergyBalance
from src.models.mass_balance import MassBalance
from src.models.plant import build_plant, solve_coal_rate
from src.retrofits.biomass import Biomass
from src.retrofits.hydrogen import Hydrogen
from src.retrofits.whr import WHR
from src.validation.literature_check import run_checks


@pytest.fixture(scope="module")
def params():
    return Parameters()


@pytest.fixture(scope="module")
def plant(params):
    return build_plant(params, capacity_tpd=100, utilization=0.9)


@pytest.fixture(scope="module")
def energy(plant):
    return EnergyBalance(plant).calculate_balance()


# --------------------------------------------------------------------------
# Balances
# --------------------------------------------------------------------------
def test_total_mass_closes(plant):
    r = MassBalance(plant).calculate_balance()
    assert r["is_valid"], f"total mass closure {r['error_percent']:.2f}%"


def test_every_element_closes(plant):
    r = MassBalance(plant).calculate_balance()
    assert r["all_elements_valid"], f"failing: {r['elements_failing']}"


@pytest.mark.parametrize("element", ["Fe", "C", "H", "N", "S"])
def test_conserved_elements_close_exactly(plant, element):
    """Atom accounting for these should be exact, not merely within tolerance."""
    rows = {e["element"]: e for e in MassBalance(plant).elements()}
    assert rows[element]["error_percent"] < 1e-6


def test_energy_balance_closes_in_solve_mode(plant, energy):
    assert energy["is_valid"]
    assert energy["closure_error_percent"] < 0.01


def test_energy_balance_itemisation_sums_to_total(plant, energy):
    items = energy["items"]
    total_out = sum(sum(g.values()) for k, g in items.items() if k != "in")
    assert total_out == pytest.approx(energy["energy_out_kj_per_t_dri"], rel=1e-9)


# --------------------------------------------------------------------------
# Physical sanity
# --------------------------------------------------------------------------
def test_all_streams_non_negative(plant):
    for name, v in {**plant.inputs, **plant.outputs}.items():
        assert v >= 0, f"{name} is negative: {v}"


def test_waste_gas_composition_sums_to_stream(plant):
    assert sum(plant.waste_gas_composition.values()) == pytest.approx(
        plant.outputs["waste gas"], rel=1e-9)


def test_reductant_carbon_is_adequate(plant):
    assert plant.reductant_carbon_ratio > 1.0


def test_metallization_between_zero_and_one(plant):
    assert 0.0 < plant.metallization < 1.0
    assert plant.metallization == pytest.approx(0.9017, abs=5e-4)


def test_ore_rate_reproduces_calibration_plant(plant):
    """Dey et al. (2015) measured 30 t/h ore for 18.9 t/h DRI = 1.587 t/t."""
    assert plant.ore_rate == pytest.approx(1.587, abs=0.01)


def test_production_scales_with_capacity_and_utilization(params):
    a = build_plant(params, capacity_tpd=100, utilization=0.9)
    b = build_plant(params, capacity_tpd=350, utilization=0.9)
    assert b.production_tpd == pytest.approx(3.5 * a.production_tpd)
    # Intensities are per tonne of DRI and must not drift with scale.
    assert b.ore_rate == pytest.approx(a.ore_rate, rel=1e-9)
    assert b.coal_rate == pytest.approx(a.coal_rate, rel=1e-9)


def test_specified_mode_uses_config_coal_rate(params):
    p = params.with_overrides({"coal.rate_mode": "specified"})
    pl = BaselinePlant(p, 100, 0.9)
    assert pl.coal_rate == pytest.approx(p["coal.rate_t_per_t_dri"])


def test_coal_solver_brackets_a_root(params):
    sol = solve_coal_rate(params, 100, 0.9)
    assert sol["converged"]
    assert 0.6 < sol["coal_rate"] < 2.5


def test_inconsistent_iron_losses_are_rejected(params):
    p = params.with_overrides({"ore.fe_loss_to_dust_frac": 0.7,
                               "ore.fe_other_loss_frac": 0.7})
    with pytest.raises(ValueError):
        BaselinePlant(p, 100, 0.9)


# --------------------------------------------------------------------------
# Electricity, which used to be a capacity-independent constant
# --------------------------------------------------------------------------
def test_aux_power_scales_with_production(params):
    aux = params["power.aux_kwh_per_t_dri"]
    a = build_plant(params, capacity_tpd=100, utilization=0.9)
    b = build_plant(params, capacity_tpd=500, utilization=0.9)
    assert (aux * b.production_tpd) == pytest.approx(5.0 * aux * a.production_tpd)


# --------------------------------------------------------------------------
# Emissions
# --------------------------------------------------------------------------
def test_co2_is_consistent_with_the_carbon_balance(plant):
    r = CO2Model(plant).calculate_emissions(net_power_import_kwh_per_t=0.0)
    c_gas = r["gas_phase_carbon_kg_per_t_dri"]
    assert r["co2_direct_t_per_t_dri"] == pytest.approx(
        c_gas * 44.009 / 12.011 / 1000.0, rel=1e-9)


def test_implied_coal_ef_matches_assumed_carbon_content(plant):
    """The old hardcoded 2.4 t CO2/t coal implied 65.5% carbon; the coal used
    here measures 60.6-62.2%, so the implied factor must be below 2.4."""
    r = CO2Model(plant).calculate_emissions()
    assert 2.0 < r["implied_coal_ef_t_per_t_coal"] < 2.4


def test_net_export_gives_negative_scope2(plant):
    r = CO2Model(plant).calculate_emissions(net_power_import_kwh_per_t=-200.0)
    assert r["co2_scope2_t_per_t_dri"] < 0


def test_solid_carbon_is_not_counted_as_a_stack_emission(plant):
    r = CO2Model(plant).calculate_emissions()
    assert r["co2_retained_in_solids_t_per_t_dri"] > 0
    assert (r["co2_total_incl_dolochar_t_per_t_dri"]
            > r["co2_total_t_per_t_dri"])


# --------------------------------------------------------------------------
# Retrofits
# --------------------------------------------------------------------------
def test_whr_splits_generation_into_self_use_and_export(plant, energy, params):
    r = WHR(plant).calculate_impact(energy)
    assert r["gross_generation_kwh_per_t_dri"] == pytest.approx(
        r["self_consumed_kwh_per_t_dri"] + r["export_kwh_per_t_dri"], rel=1e-9)


def test_whr_export_revenue_is_not_discarded(plant, energy):
    """Regression guard: surplus generation used to be clamped away with
    max(0, ...), which threw out most of the WHR business case."""
    r = WHR(plant).calculate_impact(energy)
    assert r["export_kwh_per_t_dri"] > 0
    econ = EconomicsModel(plant)
    with_export = econ.calculate_economics(
        net_power_import_kwh_per_t=r["net_import_kwh_per_t_dri"],
        power_export_kwh_per_t=r["export_kwh_per_t_dri"])
    without = econ.calculate_economics(
        net_power_import_kwh_per_t=r["net_import_kwh_per_t_dri"],
        power_export_kwh_per_t=0.0)
    assert with_export["cost_per_t_dri"] < without["cost_per_t_dri"]


def test_whr_heat_sources_sum_to_total(plant, energy):
    r = WHR(plant).calculate_impact(energy)
    assert r["heat_available_kj_per_t_dri"] == pytest.approx(
        r["from_waste_gas_sensible_kj"] + r["from_abc_post_combustion_kj"],
        rel=1e-9)


@pytest.mark.parametrize("frac", [0.05, 0.15, 0.30])
def test_biomass_displaces_coal_monotonically(plant, frac):
    r = Biomass(plant, frac).calculate_impact()
    assert r["coal_saved_kg_per_t_dri"] > 0
    assert r["biomass_required_kg_per_t_dri"] > r["coal_saved_kg_per_t_dri"], (
        "biomass has a lower heating value than coal, so more of it is needed")


def test_biomass_substitution_is_capped(plant, params):
    cap = params["biomass.max_substitution_frac"]
    r = Biomass(plant, 0.95).calculate_impact()
    assert r["capped_at_max"]
    assert r["substitution_frac"] == pytest.approx(cap)


def test_biomass_erodes_reductant_carbon_margin(plant):
    """Substituting coal on a purely energetic basis removes reductant carbon;
    the check must register that even while staying feasible."""
    low = Biomass(plant, 0.05).calculate_impact()
    high = Biomass(plant, 0.30).calculate_impact()
    assert high["reductant_carbon_ratio"] != pytest.approx(
        low["reductant_carbon_ratio"])


def test_biomass_biogenic_carbon_reported_separately(plant):
    r = Biomass(plant, 0.30).calculate_impact()
    assert r["biogenic_carbon_to_gas_kg_per_t_dri"] > 0
    co2 = CO2Model(plant).calculate_emissions(
        biogenic_carbon_kg_per_t=r["biogenic_carbon_to_gas_kg_per_t_dri"],
        fossil_carbon_offset_kg_per_t=r["fossil_carbon_removed_kg_per_t_dri"])
    assert co2["co2_biogenic_t_per_t_dri"] > 0
    # Zero-rated by default, so the biogenic stream must not inflate the total.
    assert co2["co2_total_t_per_t_dri"] == pytest.approx(
        co2["co2_fossil_t_per_t_dri"])


def test_biogenic_counted_when_not_zero_rated(params, plant):
    p = params.with_overrides({"biomass.biogenic_co2_zero_rated": 0})
    pl = build_plant(p, 100, 0.9)
    r = Biomass(pl, 0.30).calculate_impact()
    co2 = CO2Model(pl).calculate_emissions(
        biogenic_carbon_kg_per_t=r["biogenic_carbon_to_gas_kg_per_t_dri"])
    assert co2["co2_total_t_per_t_dri"] > co2["co2_fossil_t_per_t_dri"]


def test_hydrogen_spares_reductant_carbon(plant):
    r = Hydrogen(plant, 0.30).calculate_impact()
    assert r["reductant_carbon_spared_kg_per_t_dri"] > 0
    assert r["oxygen_removed_by_h2_kg_per_t_dri"] <= plant.o_removed + 1e-9


def test_hydrogen_stoichiometry_is_physical(plant):
    """One mole of H2 carries one mole of O, so the stoichiometric requirement
    for the oxygen removed is fixed by the ore, not by the substitution rate."""
    a = Hydrogen(plant, 0.10).calculate_impact()
    b = Hydrogen(plant, 0.30).calculate_impact()
    assert (a["h2_stoichiometric_full_dr_kg_per_t_dri"]
            == pytest.approx(b["h2_stoichiometric_full_dr_kg_per_t_dri"]))
    assert 40.0 < a["h2_stoichiometric_full_dr_kg_per_t_dri"] < 60.0


def test_grey_hydrogen_adds_emissions(params, plant):
    p = params.with_overrides({"hydrogen.ef_t_per_t": 9.5})
    pl = build_plant(p, 100, 0.9)
    assert Hydrogen(pl, 0.30).calculate_impact()["h2_supply_co2_t_per_t_dri"] > 0
    assert Hydrogen(plant, 0.30).calculate_impact()["h2_supply_co2_t_per_t_dri"] == 0


# --------------------------------------------------------------------------
# Economics
# --------------------------------------------------------------------------
def test_capex_raises_cost_per_tonne(plant):
    """Regression guard: retrofit CAPEX used to be displayed but never costed,
    so a retrofit could only ever look cheaper than the baseline."""
    econ = EconomicsModel(plant)
    base = econ.calculate_economics()
    with_capex = econ.calculate_economics(capex_inr=2.0e8)
    assert with_capex["cost_per_t_dri"] > base["cost_per_t_dri"]
    assert with_capex["capex_charge_per_t_dri"] > 0


def test_capital_recovery_factor_is_sane():
    assert capital_recovery_factor(0.11, 20) == pytest.approx(0.12558, abs=1e-4)
    assert capital_recovery_factor(0.0, 20) == pytest.approx(0.05)


def test_cost_breakdown_sums_to_total(plant):
    r = EconomicsModel(plant).calculate_economics(capex_inr=1.0e8)
    assert sum(r["breakdown_inr_per_t_dri"].values()) == pytest.approx(
        r["cost_per_t_dri"], rel=1e-9)


def test_coal_dominates_baseline_cost(plant):
    b = EconomicsModel(plant).calculate_economics()["breakdown_inr_per_t_dri"]
    assert b["coal"] > b["purchased power"]
    assert b["coal"] > b["dolomite"]


# --------------------------------------------------------------------------
# Provenance and validation
# --------------------------------------------------------------------------
def test_no_parameter_lacks_a_source(params):
    for key in params.keys():
        assert params.meta(key).get("source"), f"{key} has no source"


def test_unknown_parameter_raises(params):
    with pytest.raises(KeyError):
        params["nonexistent.parameter"]
    with pytest.raises(KeyError):
        params.with_overrides({"nonexistent.parameter": 1.0})


def test_overrides_do_not_leak_between_copies(params):
    a = params.with_overrides({"plant.utilization": 0.5})
    assert a["plant.utilization"] == 0.5
    assert params["plant.utilization"] != 0.5


def test_headline_outputs_are_within_literature_bands():
    result = run_checks(capacity_tpd=100, utilization=0.9)
    failing = [r["label"] for r in result["rows"] if r["verdict"] == "FAIL"]
    # WHR generation is a known open gap, documented in validation_targets.json.
    assert failing == ["WHR gross generation", "WHR surplus export"], failing


def test_validation_targets_are_not_model_inputs(params):
    """A PASS must be evidence, so no target may also be a parameter."""
    from src.data.parameters import load_validation_targets
    keys = set(params.keys())
    for tgt in load_validation_targets():
        assert tgt["key"] not in keys
