"""Read-only tools the analyst may call.

Nothing here opens the parameter file or the validation file for writing.
Overrides live only in the returned plant, for that call.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.analysis.scenarios import evaluate, h2_breakeven_price, least_cost, pathway_grid
from src.data.parameters import Parameters
from src.data.presets import domestic_coal
from src.economics.financial import retrofit_project
from src.kiln.axial import axial_profile
from src.models.energy_balance import EnergyBalance
from src.models.mass_balance import MassBalance
from src.models.plant import build_plant
from src.validation.literature_check import run_checks
from src.version import MODEL_VERSION, stamp

_FORBIDDEN_PATHS = ("parameters.json", "validation_targets.json")


def protected_files() -> tuple[str, ...]:
    """Files the analyst is not allowed to write. The tools never open them for writing."""
    return _FORBIDDEN_PATHS


def _params(preset: str = "imported", overrides: dict | None = None) -> Parameters:
    base = Parameters()
    values = {}
    if preset == "domestic":
        values.update(domestic_coal(base))
    if overrides:
        values.update(overrides)
    return base.with_overrides(values) if values else base


def _plant(preset: str, capacity_tpd: float, utilization: float,
           overrides: dict | None):
    params = _params(preset, overrides)
    plant = build_plant(params, capacity_tpd, utilization)
    energy = EnergyBalance(plant).calculate_balance()
    mass = MassBalance(plant).calculate_balance()
    return plant, energy, mass


def run_scenario(capacity_tpd: float = 100, utilization: float = 0.9,
                 preset: str = "imported", whr: bool = False,
                 biomass_frac: float = 0.0, h2_frac: float = 0.0,
                 overrides: dict | None = None) -> dict:
    plant, energy, mass = _plant(preset, capacity_tpd, utilization, overrides)
    result = evaluate(plant, energy, whr=whr, biomass_frac=biomass_frac,
                      h2_frac=h2_frac)
    co2 = result["co2"]
    econ = result["econ"]
    return {
        "model_version": MODEL_VERSION,
        "parameters_sha256": stamp()["parameters_sha256"],
        "preset": preset,
        "capacity_tpd": capacity_tpd,
        "utilization": utilization,
        "coal_t_per_t": plant.coal_rate,
        "ore_t_per_t": plant.ore_rate,
        "metallisation_frac": plant.metallization,
        "metallisation_is_an_input": True,
        "sec_gcal_per_t": energy["sec_gcal_per_t_dri"],
        "mass_closure_percent": mass["error_percent"],
        "energy_closure_percent": energy["closure_error_percent"],
        "co2_direct_t_per_t": co2["co2_direct_t_per_t_dri"],
        "co2_total_t_per_t": co2["co2_total_t_per_t_dri"],
        "cost_inr_per_t": econ["cost_per_t_dri"],
        "cash_cost_inr_per_t": econ["cash_cost_per_t_dri"],
        "annual_output_t": econ["annual_output_t"],
        "capex_inr": result["capex_inr"],
        "feasible": result["feasible"],
        "reductant_carbon_ratio": result["reductant_carbon_ratio"],
        "label": result["label"],
        "unsourced": plant.p.unsourced_keys(),
    }


def find_least_cost(target_frac: float, capacity_tpd: float = 100,
                    utilization: float = 0.9, preset: str = "imported",
                    overrides: dict | None = None) -> dict:
    plant, energy, _mass = _plant(preset, capacity_tpd, utilization, overrides)
    rows = pathway_grid(plant, energy)
    chosen = least_cost(rows, target_frac)
    if chosen is None:
        return {
            "reachable": False,
            "target_frac": target_frac,
            "reason": "Not reachable within the substitution caps without "
                      "the reductant-carbon ratio falling below 1.",
            "model_version": MODEL_VERSION,
        }
    return {
        "reachable": True,
        "target_frac": target_frac,
        "label": chosen["label"],
        "co2_reduction_frac": chosen["co2_reduction_frac"],
        "cost_inr_per_t": chosen["econ"]["cost_per_t_dri"],
        "cost_delta_inr_per_t": chosen["cost_delta_inr_per_t_dri"],
        "abatement_cost_inr_per_t_co2": chosen["abatement_cost_inr_per_t_co2"],
        "capex_inr": chosen["capex_inr"],
        "payback_yr": chosen["payback_yr"],
        "feasible": chosen["feasible"],
        "model_version": MODEL_VERSION,
    }


def get_parameter(name: str) -> dict:
    params = Parameters()
    key = name if name in params else next(
        (k for k in params.keys() if name.lower() in k.lower()), None)
    if key is None:
        return {"found": False, "query": name}
    meta = params.meta(key)
    low, high = params.bounds(key)
    return {
        "found": True,
        "parameter": key,
        "value": params[key],
        "unit": meta.get("unit", ""),
        "min": low,
        "max": high,
        "status": meta.get("status", ""),
        "source": meta.get("source", ""),
    }


def list_unsourced() -> dict:
    params = Parameters()
    return {"parameters": params.unsourced_keys(), "count": len(params.unsourced_keys())}


def run_validation(capacity_tpd: float = 100, utilization: float = 0.9,
                   preset: str = "imported", overrides: dict | None = None) -> dict:
    result = run_checks(_params(preset, overrides), capacity_tpd, utilization)
    rows = [{"key": row["key"], "label": row["label"], "verdict": row["verdict"],
             "model_value": row["model_value"]} for row in result["rows"]]
    return {"counts": result["counts"], "rows": rows, "model_version": MODEL_VERSION}


def explain_closure(capacity_tpd: float = 100, utilization: float = 0.9,
                    preset: str = "imported", overrides: dict | None = None) -> dict:
    _plant_obj, energy, mass = _plant(preset, capacity_tpd, utilization, overrides)
    return {
        "mass_closure_percent": mass["error_percent"],
        "mass_valid": mass["is_valid"],
        "elements": [{"element": row["element"], "error_percent": row["error_percent"],
                      "valid": row["is_valid"]} for row in mass["element_balances"]],
        "energy_closure_percent": energy["closure_error_percent"],
        "energy_valid": energy["is_valid"],
        "sec_gcal_per_t": energy["sec_gcal_per_t_dri"],
    }


def hydrogen_breakeven(capacity_tpd: float = 100, utilization: float = 0.9,
                       preset: str = "imported", overrides: dict | None = None) -> dict:
    plant, _energy, _mass = _plant(preset, capacity_tpd, utilization, overrides)
    return {
        "breakeven_inr_per_kg": h2_breakeven_price(plant),
        "cited_price_inr_per_kg": plant.p["hydrogen.price_inr_per_kg"],
        "note": "Energy parity only. Capital and carbon are not in this price.",
    }


def compare_presets(capacity_tpd: float = 100, utilization: float = 0.9) -> dict:
    left = run_scenario(capacity_tpd, utilization, "imported")
    right = run_scenario(capacity_tpd, utilization, "domestic")
    return {"imported": left, "domestic": right}


def waste_heat_finance(capacity_tpd: float = 100, utilization: float = 0.9,
                       preset: str = "imported", overrides: dict | None = None) -> dict:
    plant, energy, _mass = _plant(preset, capacity_tpd, utilization, overrides)
    bare = evaluate(plant, energy)
    case = evaluate(plant, energy, whr=True, baseline=bare)
    opex = case["retrofits"]["Waste Heat Recovery"]["annual_opex_inr"]
    project = retrofit_project(
        bare["econ"]["cash_cost_per_t_dri"], bare["econ"]["annual_output_t"],
        case["econ"]["cash_cost_per_t_dri"], case["econ"]["annual_output_t"],
        case["capex_inr"], opex, plant.p)
    return {
        "capex_inr": case["capex_inr"],
        "npv_inr": project["npv_inr"],
        "irr": project["irr"],
        "irr_status": project["irr_status"],
        "project_npv_inr": project["project_npv_inr"],
        "project_irr": project["project_irr"],
        "simple_payback_yr": project["simple_payback_yr"],
        "discounted_payback_yr": project["discounted_payback_yr"],
        "equity_inr": project["equity_inr"],
        "debt_fraction": plant.p["econ.debt_fraction"],
        "note": "Equity cash flow after debt service. Not a return on the whole capital.",
    }


def kiln_summary() -> dict:
    plant, energy, _mass = _plant("imported", 100, 0.9, None)
    profile = axial_profile(plant, energy)
    return {
        "length_m": profile["length_m"],
        "internal_diameter_m": profile["internal_diameter_m"],
        "inclination_deg": profile["inclination_deg"],
        "mode": profile["mode"],
        "metallisation_is_prescribed": profile["metallisation_is_prescribed"],
        "discharge_metallisation_frac": profile["discharge_metallisation_frac"],
        "residual_kj": profile["residual_kj"],
        "note": "Geometry is Dey's 80 m kiln. Metallisation is not predicted.",
    }
