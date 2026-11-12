"""Freeze the imported-coal baseline so later phases cannot move a number silently.

Regenerate tests/golden/baseline_100tpd_imported.json only in a model phase,
and record why in CHANGELOG.md. UI and documentation phases must leave it alone.
"""
from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.analysis.scenarios import (CO2_TARGETS, evaluate, h2_breakeven_price,
                                    least_cost, pathway_grid)
from src.data.parameters import Parameters
from src.economics.economics import EconomicsModel
from src.emissions.co2_model import CO2Model
from src.models.energy_balance import EnergyBalance
from src.models.mass_balance import MassBalance
from src.models.plant import build_plant
from src.retrofits.whr import WHR
from src.validation.literature_check import run_checks
from src.version import MODEL_VERSION, parameters_sha256

_GOLDEN = os.path.join(os.path.dirname(__file__), "baseline_100tpd_imported.json")
_PHYSICAL = 1e-6
_COST = 1e-4


@pytest.fixture(scope="module")
def golden():
    with open(_GOLDEN) as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def solved():
    params = Parameters()
    plant = build_plant(params)
    energy = EnergyBalance(plant).calculate_balance()
    return params, plant, energy


def test_parameter_file_is_the_frozen_one(golden):
    assert parameters_sha256() == golden["parameters_sha256"]
    assert MODEL_VERSION == golden["model_version"]


def test_plant_carries_the_stamp(solved):
    _, plant, energy = solved
    assert plant.model_version == MODEL_VERSION
    assert plant.parameters_sha256 == parameters_sha256()
    stamped = evaluate(plant, energy)
    assert stamped["model_version"] == MODEL_VERSION
    assert stamped["parameters_sha256"] == parameters_sha256()


def test_baseline_numbers(golden, solved):
    params, plant, energy = solved
    mass = MassBalance(plant).calculate_balance()
    co2 = CO2Model(plant).calculate_emissions()
    cost = EconomicsModel(plant).calculate_economics()
    whr = WHR(plant).calculate_impact(energy)
    expected = golden["baseline"]
    assert plant.coal_rate == pytest.approx(expected["coal_rate_t_per_t_dri"], rel=_PHYSICAL)
    assert plant.ore_rate == pytest.approx(expected["ore_rate_t_per_t_dri"], rel=_PHYSICAL)
    assert plant.metallization == pytest.approx(expected["metallization_frac"], rel=_PHYSICAL)
    assert energy["sec_gcal_per_t_dri"] == pytest.approx(expected["sec_gcal_per_t_dri"], rel=_PHYSICAL)
    assert mass["error_percent"] == pytest.approx(expected["mass_closure_percent"], rel=_PHYSICAL)
    assert energy["closure_error_percent"] == pytest.approx(
        expected["energy_closure_percent"], rel=_PHYSICAL)
    assert co2["co2_direct_t_per_t_dri"] == pytest.approx(
        expected["co2_direct_t_per_t_dri"], rel=_PHYSICAL)
    assert co2["co2_total_t_per_t_dri"] == pytest.approx(
        expected["co2_total_t_per_t_dri"], rel=_PHYSICAL)
    assert whr["gross_generation_kwh_per_t_dri"] == pytest.approx(
        expected["whr_gross_kwh_per_t_dri"], rel=_PHYSICAL)
    assert whr["export_kwh_per_t_dri"] == pytest.approx(
        expected["whr_export_kwh_per_t_dri"], rel=_PHYSICAL)
    assert h2_breakeven_price(plant) == pytest.approx(
        expected["h2_breakeven_inr_per_kg"], rel=_COST)
    assert cost["cost_per_t_dri"] == pytest.approx(expected["cost_inr_per_t_dri"], rel=_COST)
    assert params["coal.rate_mode"] == golden["case"]["coal_rate_mode"]


def test_validation_verdicts(golden):
    live = {r["key"]: r for r in run_checks()["rows"]}
    frozen = {r["key"]: r for r in golden["validation"]}
    assert set(live) == set(frozen)
    for key, row in frozen.items():
        assert live[key]["verdict"] == row["verdict"]
        assert live[key]["model_value"] == pytest.approx(row["model_value"], rel=_PHYSICAL)


def test_pathway_table(golden, solved):
    _, plant, energy = solved
    grid = pathway_grid(plant, energy)
    frozen = {row["target_frac"]: row for row in golden["pathways"]}
    assert set(frozen) == set(CO2_TARGETS)
    for target, row in frozen.items():
        live = least_cost(grid, target)
        if not row["reachable"]:
            assert live is None
            continue
        assert live["label"] == row["label"]
        assert live["co2_reduction_frac"] == pytest.approx(row["co2_reduction_frac"], rel=_PHYSICAL)
        assert live["cost_delta_inr_per_t_dri"] == pytest.approx(
            row["cost_delta_inr_per_t_dri"], rel=_COST)
        assert live["payback_yr"] == pytest.approx(row["payback_yr"], rel=_COST)
