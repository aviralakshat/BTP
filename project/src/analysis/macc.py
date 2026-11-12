"""Marginal abatement curve, carbon-price overlay and price break-evens.

The curve follows the dependent-option rule in Bhardwaj et al. (2024),
Section 5.1. Start from the bare plant. At each step, recompute every
remaining move against the package already chosen, and take the move with the
lowest marginal abatement cost that still cuts CO2. A move the reductant check
rejects is skipped. A move that does not cut CO2 is listed and is not drawn.

Bhardwaj treat char recycling as exclusive with gaseous reductants. This plant
model has no such exclusion. The reductant-carbon ratio is the constraint that
is enforced. Stacked coal-cutting studies were not measured as a package, and
the row carries that warning when the plant raises it.

The carbon price at which a pathway ties the baseline is the abatement cost.
That identity is used rather than a second calculation. Coal, power, export
and hydrogen prices are linear in the cost, so the break-even is the root of
that line, checked at a third price.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.analysis.plant_eval import PATHWAY_FLAGS, as_flags, label_of
from src.analysis.scenarios import (
    BIOMASS_LEVELS, H2_LEVELS, evaluate, h2_breakeven_price,
)
from src.analysis.settings import carbon_cases, load_analysis
from src.data.parameters import Parameters
from src.models.baseline import BaselinePlant
from src.models.energy_balance import EnergyBalance
from src.models.plant import build_plant
from src.version import stamp

_CO2_FLOOR = 1e-6


def _blank() -> dict:
    return {key: (0.0 if key.endswith("_frac") else False) for key in PATHWAY_FLAGS}


def _moves(state: dict, biomass_cap: float, hydrogen_cap: float) -> list[tuple[str, dict]]:
    moves = []
    if not state["whr"]:
        moves.append(("Waste heat recovery", {**state, "whr": True}))
    if not state["vfd"]:
        moves.append(("Variable frequency drives", {**state, "vfd": True}))
    if not state["kiln_control"]:
        moves.append(("Kiln control", {**state, "kiln_control": True}))
    if not state["char_recycle"]:
        moves.append(("Char recycling", {**state, "char_recycle": True}))
    if not state["oxygen"]:
        moves.append(("Oxygen enrichment", {**state, "oxygen": True}))
    if not state["producer_gas"]:
        moves.append(("Producer gas", {**state, "producer_gas": True}))
    biomass = state["biomass_frac"]
    hydrogen = state["h2_frac"]
    nxt_b = next((level for level in BIOMASS_LEVELS if level > biomass + 1e-12), None)
    if nxt_b is not None and nxt_b <= biomass_cap + 1e-12 and nxt_b + hydrogen < 1.0:
        moves.append((f"Biomass to {nxt_b:.0%}", {**state, "biomass_frac": nxt_b}))
    nxt_h = next((level for level in H2_LEVELS if level > hydrogen + 1e-12), None)
    if nxt_h is not None and nxt_h <= hydrogen_cap + 1e-12 and biomass + nxt_h < 1.0:
        moves.append((f"Hydrogen to {nxt_h:.0%}", {**state, "h2_frac": nxt_h}))
    return moves


def _package(plant: BaselinePlant, energy: dict, flags: dict, bare: dict) -> dict:
    return evaluate(plant, energy, baseline=bare, **flags)


def marginal_curve(plant: BaselinePlant, energy: dict) -> dict:
    """Greedy marginal abatement curve on one solved plant."""
    bare = evaluate(plant, energy)
    biomass_cap = plant.p["biomass.max_substitution_frac"]
    hydrogen_cap = plant.p["hydrogen.max_substitution_frac"]
    state = _blank()
    current = bare
    bars = []
    no_abatement = []
    warnings = []
    seen = 0
    limit = 2 + len(BIOMASS_LEVELS) + len(H2_LEVELS) + 6

    while seen < limit:
        seen += 1
        candidates = []
        for name, flags in _moves(state, biomass_cap, hydrogen_cap):
            result = _package(plant, energy, flags, bare)
            for warning in result["warnings"]:
                if warning not in warnings:
                    warnings.append(warning)
            if not result["feasible"]:
                continue
            d_cost = result["econ"]["cost_per_t_dri"] - current["econ"]["cost_per_t_dri"]
            d_co2 = (current["co2"]["co2_total_t_per_t_dri"]
                     - result["co2"]["co2_total_t_per_t_dri"])
            candidates.append({
                "measure": name, "flags": flags, "result": result,
                "marginal_cost_inr_per_t": d_cost,
                "marginal_co2_t_per_t": d_co2,
            })
        abating = [c for c in candidates if c["marginal_co2_t_per_t"] > _CO2_FLOOR]
        if not abating:
            for candidate in candidates:
                if candidate["marginal_cost_inr_per_t"] < -_CO2_FLOOR:
                    no_abatement.append({
                        "measure": candidate["measure"],
                        "cost_change_inr_per_t": candidate["marginal_cost_inr_per_t"],
                        "co2_change_t_per_t": -candidate["marginal_co2_t_per_t"],
                    })
            break
        pick = min(abating, key=lambda c: c["marginal_cost_inr_per_t"] / c["marginal_co2_t_per_t"])
        mac = pick["marginal_cost_inr_per_t"] / pick["marginal_co2_t_per_t"]
        cumulative = (bars[-1]["cumulative_co2_t_per_t"] if bars else 0.0) + pick["marginal_co2_t_per_t"]
        bars.append({
            "order": len(bars) + 1,
            "measure": pick["measure"],
            "marginal_cost_inr_per_t": pick["marginal_cost_inr_per_t"],
            "marginal_co2_t_per_t": pick["marginal_co2_t_per_t"],
            "abatement_cost_inr_per_t_co2": mac,
            "cumulative_co2_t_per_t": cumulative,
            "annual_co2_t": pick["marginal_co2_t_per_t"] * bare["econ"]["annual_output_t"],
            "package": label_of(pick["flags"]),
        })
        state = pick["flags"]
        current = pick["result"]

    standalone = []
    for name, flags in _moves(_blank(), biomass_cap, hydrogen_cap):
        result = _package(plant, energy, flags, bare)
        d_co2 = result.get("co2_reduction_t_per_t_dri")
        standalone.append({
            "measure": name,
            "feasible": result["feasible"],
            "cost_change_inr_per_t": result.get("cost_delta_inr_per_t_dri"),
            "co2_cut_t_per_t": d_co2,
            "abatement_cost_inr_per_t_co2": result.get("abatement_cost_inr_per_t_co2"),
        })

    return {
        "bars": bars,
        "no_abatement": no_abatement,
        "standalone": standalone,
        "warnings": warnings,
        "baseline_cost_inr_per_t": bare["econ"]["cost_per_t_dri"],
        "baseline_co2_t_per_t": bare["co2"]["co2_total_t_per_t_dri"],
        **stamp(plant.p.path),
    }


def _at_price(plant: BaselinePlant, energy: dict, flags: dict, key: str, price: float):
    """Cost of the bare plant and of one pathway at a price that does not affect the balance.

    The coal rate stays at the solved value. Re-solving would spend the search
    on a price the kiln physics does not use.
    """
    adjusted = plant.p.with_overrides({
        "coal.rate_mode": "specified",
        "coal.rate_t_per_t_dri": plant.coal_rate,
        key: price,
    })
    rebuilt = build_plant(adjusted)
    bare = evaluate(rebuilt, energy)
    scenario = evaluate(rebuilt, energy, baseline=bare, **flags)
    return bare["econ"]["cost_per_t_dri"], scenario["econ"]["cost_per_t_dri"]


def price_break_evens(plant: BaselinePlant, energy: dict,
                      pathways: list[dict] | None = None,
                      cfg: dict | None = None) -> list[dict]:
    """Price at which each pathway ties the bare plant."""
    cfg = cfg or load_analysis()
    pathways = pathways if pathways is not None else cfg["probability_pathways"]
    probe = cfg["prices"]["probe_frac"]
    tolerance = cfg["prices"]["linearity_tolerance_inr_per_t"]
    rows = []
    bare = evaluate(plant, energy)
    for spec in pathways:
        flags = as_flags(spec)
        scenario = evaluate(plant, energy, baseline=bare, **flags)
        carbon_root = scenario.get("abatement_cost_inr_per_t_co2")
        row = {
            "label": spec["label"],
            "feasible": scenario["feasible"],
            "cost_delta_inr_per_t": scenario.get("cost_delta_inr_per_t_dri"),
            "co2_cut_t_per_t": scenario.get("co2_reduction_t_per_t_dri"),
            "carbon_price_inr_per_t": carbon_root,
            "prices": [],
        }
        for key in cfg["prices"]["keys"]:
            base_price = float(plant.p[key])
            step = max(abs(base_price) * probe, 1.0)
            c0_b, c0_s = _at_price(plant, energy, flags, key, base_price)
            c1_b, c1_s = _at_price(plant, energy, flags, key, base_price + step)
            d0, d1 = c0_s - c0_b, c1_s - c1_b
            slope = (d1 - d0) / step
            check_b, check_s = _at_price(plant, energy, flags, key, base_price + 2 * step)
            predicted = d0 + slope * (2 * step)
            actual = check_s - check_b
            linear = abs(actual - predicted) <= tolerance
            if abs(d1 - d0) <= tolerance or not linear:
                root, depends = None, False
            else:
                root, depends = base_price - d0 / slope, True
            row["prices"].append({
                "parameter": key,
                "cited_value": base_price,
                "depends": depends and linear,
                "break_even": root if depends and linear else None,
                "linear": linear,
                "slope_inr_per_unit": slope,
            })
        rows.append(row)
    rows.append({
        "label": "Hydrogen, energy parity, operating cost only",
        "feasible": True,
        "cost_delta_inr_per_t": None,
        "co2_cut_t_per_t": None,
        "carbon_price_inr_per_t": None,
        "prices": [{
            "parameter": "hydrogen.price_inr_per_kg",
            "cited_value": float(plant.p["hydrogen.price_inr_per_kg"]),
            "depends": True,
            "break_even": h2_breakeven_price(plant),
            "linear": True,
            "slope_inr_per_unit": None,
            "note": "Coal displaced per kilogram of hydrogen on a heating-value basis. "
                    "Capital and the carbon account are not in this figure.",
        }],
    })
    return rows


def carbon_overlay(plant: BaselinePlant, energy: dict,
                   cfg: dict | None = None) -> dict:
    """Cost per tonne with a carbon charge added, for the baseline and each pathway."""
    cfg = cfg or load_analysis()
    cases = carbon_cases(cfg)
    bare = evaluate(plant, energy)
    series = [{"label": "Baseline", "flags": None,
               "cost": bare["econ"]["cost_per_t_dri"],
               "co2": bare["co2"]["co2_total_t_per_t_dri"]}]
    for spec in cfg["probability_pathways"]:
        result = evaluate(plant, energy, baseline=bare, **as_flags(spec))
        series.append({
            "label": spec["label"],
            "cost": result["econ"]["cost_per_t_dri"],
            "co2": result["co2"]["co2_total_t_per_t_dri"],
            "feasible": result["feasible"],
            "abatement_cost_inr_per_t_co2": result.get("abatement_cost_inr_per_t_co2"),
        })
    positive = [row["abatement_cost_inr_per_t_co2"] for row in series
                if row.get("abatement_cost_inr_per_t_co2") and row["abatement_cost_inr_per_t_co2"] > 0]
    cited = max(case["inr_per_t"] for case in cases)
    hi = max([cited, *positive, 1.0]) * cfg["carbon_axis_pad"]
    n = cfg["carbon_sweep_points"]
    prices = [hi * i / (n - 1) for i in range(n)]
    # Make sure each cited case sits on the sweep, so the table can be read off it.
    for case in cases:
        if case["inr_per_t"] not in prices and 0 <= case["inr_per_t"] <= hi:
            prices.append(case["inr_per_t"])
    prices = sorted(prices)
    lines = []
    for row in series:
        lines.append({
            "label": row["label"],
            "prices": prices,
            "costs": [row["cost"] + price * row["co2"] for price in prices],
            "co2_t_per_t": row["co2"],
            "cost_without_carbon_inr_per_t": row["cost"],
        })
    return {"cases": cases, "lines": lines, "axis_max_inr_per_t": hi,
            **stamp(plant.p.path)}


def decision_tables(params: Parameters | None = None, capacity_tpd: float | None = None,
                    utilization: float | None = None) -> dict:
    """Curve, break-evens and carbon overlay for one plant. One coal-rate solve."""
    params = params or Parameters()
    plant = build_plant(params, capacity_tpd, utilization)
    energy = EnergyBalance(plant).calculate_balance()
    return {
        "macc": marginal_curve(plant, energy),
        "break_evens": price_break_evens(plant, energy),
        "carbon": carbon_overlay(plant, energy),
    }
