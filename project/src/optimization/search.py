"""Continuous search over biomass fraction, hydrogen fraction and WHR.

The grid in `pathway_grid` is the reference. The search evaluates every grid
cell, then a mesh from zero to each cap, then walks downhill from the best
point in steps that halve until the stop size. The reductant-carbon check and
the CO2 target are hard constraints. Because the grid cells are inside the
candidate set, the continuous result cannot be worse than the grid result by
more than the cost tolerance, and a point between cells can be better.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np

from src.analysis.scenarios import CO2_TARGETS, evaluate, least_cost, pathway_grid
from src.analysis.settings import load_analysis
from src.models.baseline import BaselinePlant
from src.version import stamp


def _ok(result: dict, target: float) -> bool:
    return (result["feasible"]
            and result.get("co2_reduction_frac", 0.0) >= target - 1e-9)


def _pack(result: dict) -> dict:
    return {
        "label": result["label"],
        "whr": result["whr"],
        "biomass_frac": result["biomass_frac"],
        "h2_frac": result["h2_frac"],
        "cost_inr_per_t": result["econ"]["cost_per_t_dri"],
        "co2_reduction_frac": result["co2_reduction_frac"],
        "co2_t_per_t": result["co2"]["co2_total_t_per_t_dri"],
        "feasible": result["feasible"],
        "abatement_cost_inr_per_t_co2": result.get("abatement_cost_inr_per_t_co2"),
    }


def _candidates(plant: BaselinePlant, energy: dict, cfg: dict):
    """Grid rows, plus every mesh point that is not already a grid cell."""
    base = evaluate(plant, energy)
    grid = pathway_grid(plant, energy)
    results = list(grid)
    seen = {(row["whr"], round(row["biomass_frac"], 6), round(row["h2_frac"], 6))
            for row in grid}
    biomass_cap = float(plant.p["biomass.max_substitution_frac"])
    hydrogen_cap = float(plant.p["hydrogen.max_substitution_frac"])
    for whr in (False, True):
        for biomass in np.linspace(0.0, biomass_cap, int(cfg["mesh_steps"])):
            for hydrogen in np.linspace(0.0, hydrogen_cap, int(cfg["mesh_steps"])):
                key = (bool(whr), round(float(biomass), 6), round(float(hydrogen), 6))
                if key in seen or key[1] + key[2] >= 1.0:
                    continue
                seen.add(key)
                results.append(evaluate(plant, energy, key[0], key[1], key[2], baseline=base))
    return base, grid, results


def search_all(plant: BaselinePlant, energy: dict,
               targets=CO2_TARGETS, cfg: dict | None = None) -> dict:
    full = cfg or load_analysis()
    opt = full["optimiser"]
    base, grid_rows, results = _candidates(plant, energy, opt)
    biomass_cap = float(plant.p["biomass.max_substitution_frac"])
    hydrogen_cap = float(plant.p["hydrogen.max_substitution_frac"])
    rows = []
    for target in targets:
        grid_best = least_cost(grid_rows, target)
        meeting = [row for row in results if _ok(row, target)]
        best = min(meeting, key=lambda row: row["econ"]["cost_per_t_dri"]) if meeting else None
        if best is not None:
            step = float(opt["refine_step"])
            for _ in range(40):
                if step < float(opt["refine_stop"]):
                    break
                improved = False
                whr = best["whr"]
                biomass = best["biomass_frac"]
                hydrogen = best["h2_frac"]
                before = best["econ"]["cost_per_t_dri"]
                for db, dh in ((step, 0.0), (-step, 0.0), (0.0, step), (0.0, -step)):
                    bb, hh = biomass + db, hydrogen + dh
                    if (bb < -1e-12 or hh < -1e-12 or bb > biomass_cap + 1e-12
                            or hh > hydrogen_cap + 1e-12 or bb + hh >= 1.0):
                        continue
                    trial = evaluate(plant, energy, whr, bb, hh, baseline=base)
                    if _ok(trial, target) and trial["econ"]["cost_per_t_dri"] < before - 1e-9:
                        best = trial
                        before = trial["econ"]["cost_per_t_dri"]
                        improved = True
                if not improved:
                    step *= 0.5
        continuous = _pack(best) if best is not None else None
        grid_pick = _pack(grid_best) if grid_best is not None else None
        gap = None
        if continuous and grid_pick:
            gap = grid_pick["cost_inr_per_t"] - continuous["cost_inr_per_t"]
        rows.append({
            "target_frac": target,
            "grid": grid_pick,
            "continuous": continuous,
            "continuous_saving_vs_grid_inr_per_t": gap,
        })
    return {"targets": rows,
            "tolerance_inr_per_t": opt["cost_tolerance_inr_per_t"],
            **stamp(plant.p.path)}
