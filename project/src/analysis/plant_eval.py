"""One plant solve, and the overrides a sample is allowed to make.

Coal ultimate and proximate analyses have to sum to one. A Monte Carlo draw
that moves carbon or ash on its own is not a coal, so those components are not
sampled independently. Ash is drawn instead, and the rest of the analysis is
rescaled on the dry, ash-free basis. A heating value that is itself a factor
is applied after that rescaling, so the two uncertainties stay separate: one
is dilution, the other is the heating value of the coal in front of us.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.analysis.scenarios import _label, evaluate
from src.analysis.settings import load_analysis, load_distributions
from src.data.coal import (
    COAL_STREAMS, PROXIMATE, ULTIMATE, InconsistentInputError, closure, daf_rescale,
)
from src.data.parameters import Parameters
from src.models.energy_balance import EnergyBalance
from src.models.mass_balance import MassBalance
from src.models.plant import CoalRateNotSolvedError, build_plant

PATHWAY_FLAGS = ("whr", "biomass_frac", "h2_frac", "oxygen", "kiln_control",
                 "producer_gas", "char_recycle", "vfd")

_LEVER_PREFIX = (
    ("whr.", "whr"),
    ("biomass.", "biomass"),
    ("hydrogen.", "hydrogen"),
    ("oxygen.", "oxygen"),
    ("kiln_control.", "kiln_control"),
    ("producer_gas.", "producer_gas"),
    ("char_recycle.", "char_recycle"),
    ("vfd.", "vfd"),
)

LOCKED = {f"{stream}.{part}"
          for stream in COAL_STREAMS
          for part in (*ULTIMATE, *PROXIMATE)}


def as_flags(spec: dict) -> dict:
    return {key: spec[key] for key in PATHWAY_FLAGS}


def label_of(flags: dict) -> str:
    return _label(flags["whr"], flags["biomass_frac"], flags["h2_frac"],
                  flags["oxygen"], flags["kiln_control"], flags["producer_gas"],
                  flags["char_recycle"], flags["vfd"])


def scenario_for(parameter: str, cfg: dict) -> dict:
    """Flags for the abatement-cost tornado of one parameter.

    Plant parameters are varied on the reference package. A parameter that
    belongs to a lever is varied with that lever on, so a boiler efficiency
    is not reported as having no effect just because the lever was off.
    """
    flags = as_flags(cfg["reference_pathway"])
    for prefix, lever in _LEVER_PREFIX:
        if parameter.startswith(prefix):
            flags.update(cfg["lever_on"][lever])
            break
    return flags


def solve(params: Parameters):
    """Return (solved, None) or (None, reason). The reason is one line."""
    try:
        plant = build_plant(params)
        energy = EnergyBalance(plant).calculate_balance()
        mass = MassBalance(plant).calculate_balance()
    except (InconsistentInputError, CoalRateNotSolvedError, ValueError) as exc:
        text = f"{type(exc).__name__}: {exc}".split("\n")[0]
        return None, text[:300]
    return {"plant": plant, "energy": energy, "mass": mass}, None


def headlines(solved: dict, flags: dict) -> dict:
    """Bare-plant metrics plus the named pathway measured against that plant."""
    plant, energy = solved["plant"], solved["energy"]
    base = evaluate(plant, energy)
    scenario = evaluate(plant, energy, baseline=base, **flags)
    return {
        "coal_t_per_t": plant.coal_rate,
        "sec_gcal_per_t": energy["sec_gcal_per_t_dri"],
        "co2_direct_t_per_t": base["co2"]["co2_direct_t_per_t_dri"],
        "co2_scope2_t_per_t": base["co2"]["co2_scope2_t_per_t_dri"],
        "co2_total_t_per_t": base["co2"]["co2_total_t_per_t_dri"],
        "cost_inr_per_t": base["econ"]["cost_per_t_dri"],
        "mass_closure_percent": solved["mass"]["error_percent"],
        "energy_closure_percent": energy["closure_error_percent"],
        "scenario_cost_inr_per_t": scenario["econ"]["cost_per_t_dri"],
        "scenario_co2_t_per_t": scenario["co2"]["co2_total_t_per_t_dri"],
        "co2_cut_t_per_t": scenario.get("co2_reduction_t_per_t_dri"),
        "abatement_inr_per_t": scenario.get("abatement_cost_inr_per_t_co2"),
        "cost_delta_inr_per_t": scenario.get("cost_delta_inr_per_t_dri"),
        "feasible": bool(scenario["feasible"]),
        "annual_output_t": scenario["econ"]["annual_output_t"],
    }


def compose(base: Parameters, draws: dict, closed_ash: dict) -> Parameters:
    """Apply independent draws, then a closed coal analysis, then heating value.

    The heating value is put back after the rescaling so an independent heating
    value is not overwritten by the dilution.
    """
    overrides = dict(draws)
    for stream, ash in closed_ash.items():
        scaled = daf_rescale(base, stream, ash)
        heating = f"{stream}.nhv_kj_kg"
        keep = draws.get(heating)
        overrides.update(scaled)
        if keep is not None:
            overrides[heating] = keep
    return base.with_overrides(overrides)


def _authored_range(params: Parameters, key: str, overrides: dict):
    """(lo, hi, mode, clipped) or None when the parameter is a point."""
    spec = overrides.get(key)
    if spec and spec.get("distribution") == "point":
        return None
    if spec and "min" in spec and "max" in spec:
        lo, hi = float(spec["min"]), float(spec["max"])
        mode = float(spec.get("mode", params[key]))
    else:
        lo, hi = params.bounds(key)
        mode = float(params[key])
    if lo is None or hi is None or not hi > lo:
        return None
    used = min(max(mode, lo), hi)
    return lo, hi, used, used != mode


def closed_streams(params: Parameters) -> list[str]:
    """Streams whose flagged composition cannot be moved one component at a time."""
    flagged = set(params.sensitivity_keys())
    return [stream for stream in COAL_STREAMS
            if any(f"{stream}.{part}" in flagged for part in (*ULTIMATE, *PROXIMATE))]


def varying_factors(params: Parameters, distributions: dict | None = None,
                    cfg: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Factors for Morris and Monte Carlo, and the parameters left out.

    Scenario choices are left out of the probability sample. They are switches,
    and a triangular draw between them would pretend a decision is a random
    variable. The tornado still evaluates them at both positions.
    """
    cfg = cfg or load_analysis()
    distributions = distributions if distributions is not None else load_distributions()
    overrides = distributions.get("overrides", {})
    excluded = set(cfg["exclude_status_from_probability"])
    factors, skipped = [], []

    for key in params.sensitivity_keys():
        meta = params.meta(key)
        if meta.get("status") in excluded or meta.get("unit") == "boolean":
            skipped.append({
                "parameter": key,
                "reason": "scenario choice; the tornado evaluates it as a switch",
            })
            continue
        if key in LOCKED:
            skipped.append({
                "parameter": key,
                "reason": "part of a coal analysis that must sum to one; "
                          "ash is drawn and the analysis is rescaled",
            })
            continue
        if key == "coal.rate_t_per_t_dri" and params["coal.rate_mode"] == "solve":
            skipped.append({
                "parameter": key,
                "reason": "replaced by the energy-balance solution while "
                          "coal.rate_mode is solve",
            })
            continue
        span = _authored_range(params, key, overrides)
        if span is None:
            skipped.append({"parameter": key, "reason": "minimum and maximum are equal"})
            continue
        lo, hi, mode, clipped = span
        factors.append({
            "key": key, "lo": lo, "hi": hi, "mode": mode,
            "closed": False, "mode_clipped": clipped,
        })

    for stream in closed_streams(params):
        key = f"{stream}.ash"
        span = _authored_range(params, key, overrides)
        if span is None:
            continue
        lo, hi, mode, clipped = span
        note = ""
        entry = params.meta(key)
        if entry.get("min") is None or entry.get("max") is None:
            note = ("No minimum or maximum is set on this ash. The band is the "
                    "store's default around the measured value.")
        factors.append({
            "key": key, "stream": stream, "lo": lo, "hi": hi, "mode": mode,
            "closed": True, "mode_clipped": clipped, "note": note,
        })
    return factors, skipped


def apply_factor_point(base: Parameters, factors: list[dict], values: list[float]) -> Parameters:
    """Map one coded or drawn point onto a parameter set."""
    draws, closed = {}, {}
    for factor, value in zip(factors, values):
        if factor["closed"]:
            closed[factor["stream"]] = float(value)
        else:
            draws[factor["key"]] = float(value)
    return compose(base, draws, closed)


def coal_still_closes(params: Parameters) -> bool:
    for stream in COAL_STREAMS:
        totals = closure(params, stream)
        if abs(totals["ultimate"] - 1.0) > 0.005 or abs(totals["proximate"] - 1.0) > 0.005:
            return False
    return True
