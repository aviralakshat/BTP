"""Rebuild baseline_100tpd_imported.json from the current model.

Run only in a model phase, after bumping MODEL_VERSION, and record the reason
in CHANGELOG.md:

    ./venv/bin/python tests/golden/regenerate.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.analysis.scenarios import (CO2_TARGETS, h2_breakeven_price,
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
CAPACITY, UTILIZATION = 100, 0.9


def build() -> dict:
    params = Parameters()
    plant = build_plant(params, CAPACITY, UTILIZATION)
    energy = EnergyBalance(plant).calculate_balance()
    mass = MassBalance(plant).calculate_balance()
    co2 = CO2Model(plant).calculate_emissions()
    cost = EconomicsModel(plant).calculate_economics()
    whr = WHR(plant).calculate_impact(energy)
    grid = pathway_grid(plant, energy)

    pathways = []
    for target in CO2_TARGETS:
        r = least_cost(grid, target)
        pathways.append({
            "target_frac": target,
            "reachable": r is not None,
            "label": r["label"] if r else None,
            "co2_reduction_frac": r["co2_reduction_frac"] if r else None,
            "cost_delta_inr_per_t_dri": r["cost_delta_inr_per_t_dri"] if r else None,
            "abatement_cost_inr_per_t_co2": (r["abatement_cost_inr_per_t_co2"]
                                             if r else None),
            "payback_yr": r["payback_yr"] if r else None,
        })

    return {
        "description": (f"Imported-coal preset, {CAPACITY} TPD at "
                        f"{UTILIZATION:.0%} utilisation, model {MODEL_VERSION}. "
                        "Prices, heating values and the waste-heat figures are "
                        "the values printed in the papers. Dollar figures use "
                        "95 INR per USD."),
        "model_version": MODEL_VERSION,
        "parameters_sha256": parameters_sha256(),
        "case": {"capacity_tpd": CAPACITY, "utilization": UTILIZATION,
                 "coal_rate_mode": params["coal.rate_mode"]},
        "baseline": {
            "coal_rate_t_per_t_dri": plant.coal_rate,
            "ore_rate_t_per_t_dri": plant.ore_rate,
            "metallization_frac": plant.metallization,
            "sec_gcal_per_t_dri": energy["sec_gcal_per_t_dri"],
            "mass_closure_percent": mass["error_percent"],
            "energy_closure_percent": energy["closure_error_percent"],
            "co2_direct_t_per_t_dri": co2["co2_direct_t_per_t_dri"],
            "co2_total_t_per_t_dri": co2["co2_total_t_per_t_dri"],
            "cost_inr_per_t_dri": cost["cost_per_t_dri"],
            "h2_breakeven_inr_per_kg": h2_breakeven_price(plant),
            "whr_gross_kwh_per_t_dri": whr["gross_generation_kwh_per_t_dri"],
            "whr_export_kwh_per_t_dri": whr["export_kwh_per_t_dri"],
        },
        "validation": [{"key": r["key"], "verdict": r["verdict"],
                        "model_value": r["model_value"]}
                       for r in run_checks(params, CAPACITY, UTILIZATION)["rows"]],
        "pathways": pathways,
    }


if __name__ == "__main__":
    data = build()
    with open(_GOLDEN, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
    print(f"Wrote {_GOLDEN} for model {MODEL_VERSION}")
