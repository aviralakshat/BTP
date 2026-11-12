"""Monte Carlo on the cited bands.

Each varying factor is drawn from a triangular distribution on its minimum,
its base value and its maximum, independently. The triangular shape is the
default set in the plan: the cited ends are possible and the base value is the
mode. Correlations are not applied, because none are documented. A draw that
the plant refuses is counted as rejected and left out of the percentiles, and
the rejection count is part of the result.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np

from src.analysis.plant_eval import (
    apply_factor_point, as_flags, headlines, solve, varying_factors,
)
from src.analysis.scenarios import evaluate
from src.analysis.settings import load_analysis
from src.data.parameters import Parameters
from src.version import stamp

HEADLINES = (
    ("coal_t_per_t", "Coal rate", "t/t DRI"),
    ("sec_gcal_per_t", "Specific energy", "Gcal/t DRI"),
    ("co2_direct_t_per_t", "Direct CO2", "t/t DRI"),
    ("co2_total_t_per_t", "Total CO2", "t/t DRI"),
    ("cost_inr_per_t", "Cost of production", "INR/t DRI"),
    ("mass_closure_percent", "Mass closure", "%"),
    ("scenario_cost_inr_per_t", "Reference pathway cost", "INR/t DRI"),
    ("co2_cut_t_per_t", "Reference CO2 cut", "t/t DRI"),
    ("abatement_inr_per_t", "Reference abatement cost", "INR/t CO2"),
)


def _percentiles(values: list[float]) -> dict | None:
    if not values:
        return None
    p10, p50, p90 = np.percentile(np.asarray(values, dtype=float), [10, 50, 90])
    return {"p10": float(p10), "p50": float(p50), "p90": float(p90),
            "mean": float(sum(values) / len(values)), "n": len(values)}


def _histogram(values: list[float], bins: int) -> dict:
    counts, edges = np.histogram(np.asarray(values, dtype=float), bins=bins)
    return {"counts": [int(c) for c in counts],
            "edges": [float(e) for e in edges]}


def propagate(params: Parameters | None = None, n: int | None = None,
              seed: int | None = None, bins: int | None = None,
              cfg: dict | None = None, distributions: dict | None = None) -> dict:
    params = params or Parameters()
    cfg = cfg or load_analysis()
    n = cfg["monte_carlo"]["n"] if n is None else n
    bins = cfg["monte_carlo"]["histogram_bins"] if bins is None else bins
    seed = cfg["seed"] if seed is None else seed
    factors, skipped = varying_factors(params, distributions, cfg)
    flags = as_flags(cfg["reference_pathway"])
    pathways = [(spec["label"], as_flags(spec)) for spec in cfg["probability_pathways"]]
    rng = np.random.default_rng(seed)

    columns = {key: [] for key, _label, _unit in HEADLINES}
    beats = {label: {"cheaper": 0, "lower_co2": 0, "both": 0, "feasible": 0}
             for label, _flags in pathways}
    rejected = 0
    clipped = [factor["key"] for factor in factors if factor["mode_clipped"]]

    for _ in range(n):
        values = [float(rng.triangular(factor["lo"], factor["mode"], factor["hi"]))
                  for factor in factors]
        solved, _reason = solve(apply_factor_point(params, factors, values))
        if solved is None:
            rejected += 1
            continue
        metrics = headlines(solved, flags)
        for key, _label, _unit in HEADLINES:
            if metrics[key] is not None:
                columns[key].append(metrics[key])
        plant, energy = solved["plant"], solved["energy"]
        bare = evaluate(plant, energy)
        for label, pathway_flags in pathways:
            scenario = evaluate(plant, energy, baseline=bare, **pathway_flags)
            slot = beats[label]
            if not scenario["feasible"]:
                continue
            slot["feasible"] += 1
            cheaper = scenario["econ"]["cost_per_t_dri"] < bare["econ"]["cost_per_t_dri"]
            cleaner = scenario["co2"]["co2_total_t_per_t_dri"] < bare["co2"]["co2_total_t_per_t_dri"]
            slot["cheaper"] += int(cheaper)
            slot["lower_co2"] += int(cleaner)
            slot["both"] += int(cheaper and cleaner)

    accepted = n - rejected
    summary = []
    for key, label, unit in HEADLINES:
        row = {"metric": label, "unit": unit, "key": key}
        row.update(_percentiles(columns[key]) or {})
        summary.append(row)

    probabilities = []
    for label, _flags in pathways:
        slot = beats[label]
        probabilities.append({
            "label": label,
            "p_feasible": slot["feasible"] / accepted if accepted else None,
            "p_cheaper": slot["cheaper"] / accepted if accepted else None,
            "p_lower_co2": slot["lower_co2"] / accepted if accepted else None,
            "p_cheaper_and_lower_co2": slot["both"] / accepted if accepted else None,
            "n_feasible": slot["feasible"],
        })

    cost_values = columns["cost_inr_per_t"]
    return {
        "n_requested": n, "n_accepted": accepted, "n_rejected": rejected,
        "seed": seed, "summary": summary, "probabilities": probabilities,
        "cost_histogram": _histogram(cost_values, bins) if cost_values else None,
        "cost_values_note": "Histogram is the bare-plant cost per tonne.",
        "skipped": skipped,
        "mode_clipped": clipped,
        "reference_label": cfg["reference_pathway"]["label"],
        **stamp(params.path),
    }
