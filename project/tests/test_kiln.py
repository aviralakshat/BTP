"""The axial reconstruction places the kiln ledger on Dey's geometry.

It does not predict metallisation. The discharge value is the measured
product, and the integrated residual is the kiln residual at any cell count.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.data.parameters import Parameters
from src.kiln.axial import axial_profile
from src.models.energy_balance import EnergyBalance
from src.models.plant import build_plant


@pytest.fixture(scope="module")
def solved():
    params = Parameters()
    plant = build_plant(params)
    energy = EnergyBalance(plant).calculate_balance()
    return plant, energy, axial_profile(plant, energy)


def test_cell_residuals_sum_to_the_kiln_residual(solved):
    _plant, energy, profile = solved
    assert profile["residual_kj"] == pytest.approx(energy["residual_kj_per_t_dri"], rel=1e-9, abs=1.0)
    assert sum(c["residual_kj"] for c in profile["cells"]) == pytest.approx(profile["residual_kj"])


def test_feed_coal_enters_at_the_feed_end_and_injection_at_the_discharge(solved):
    plant, _energy, profile = solved
    cells = profile["cells"]
    assert cells[0]["in"]["feed coal"] == pytest.approx(
        plant.coal_feed * plant.p["coal_feed.nhv_kj_kg"])
    assert cells[-1]["in"]["injection coal"] == pytest.approx(
        plant.coal_inj * plant.p["coal_inj.nhv_kj_kg"])
    assert "injection coal" not in cells[0]["in"]
    assert "feed coal" not in cells[-1]["in"]


def test_reduction_is_only_in_the_second_half_and_moisture_only_in_the_first(solved):
    _plant, energy, profile = solved
    preheat = [c for c in profile["cells"] if c["zone"] == "preheat"]
    reduction = [c for c in profile["cells"] if c["zone"] == "reduction"]
    assert preheat and reduction
    assert all("reduction of iron oxides" not in c["out"] for c in preheat)
    assert all("evaporation of feed moisture" not in c["out"] for c in reduction)
    reduction_heat = sum(c["out"].get("reduction of iron oxides", 0.0) for c in reduction)
    assert reduction_heat == pytest.approx(
        energy["items"]["endothermic process demand"]["reduction of iron oxides"])


def test_metallisation_is_the_measured_product_drawn_along_the_reduction_zone(solved):
    plant, _energy, profile = solved
    assert profile["metallisation_is_prescribed"] is True
    assert profile["mode"] == "planning"
    assert profile["discharge_metallisation_frac"] == pytest.approx(plant.metallization)
    assert all(c["metallisation_frac"] == 0.0
               for c in profile["cells"] if c["zone"] == "preheat")
    reduction = [c["metallisation_frac"] for c in profile["cells"] if c["zone"] == "reduction"]
    assert reduction == sorted(reduction)
    assert reduction[-1] == pytest.approx(plant.metallization)


def test_gas_temperature_runs_from_the_hot_discharge_end_to_the_feed_end(solved):
    profile = solved[2]
    gas = [c["gas_temp_c"] for c in profile["cells"]]
    assert gas[-1] > gas[0]
    assert profile["cells"][0]["solid_temp_c"] == profile["cells"][-1]["solid_temp_c"]


def test_a_finer_grid_does_not_change_the_integrated_balance(solved):
    plant, energy = solved[0], solved[1]
    coarse = axial_profile(
        build_plant(plant.p.with_overrides({"kiln.n_cells": 10})), energy)
    fine = axial_profile(
        build_plant(plant.p.with_overrides({"kiln.n_cells": 40})), energy)
    assert coarse["residual_kj"] == pytest.approx(fine["residual_kj"], abs=1.0)
    assert coarse["residual_kj"] == pytest.approx(energy["residual_kj_per_t_dri"], abs=1.0)


def test_geometry_is_deys_kiln(solved):
    profile = solved[2]
    assert profile["length_m"] == 80
    assert profile["internal_diameter_m"] == 4.55
    assert profile["inclination_deg"] == 2.5
    assert profile["preheat_length_frac"] == 0.5
