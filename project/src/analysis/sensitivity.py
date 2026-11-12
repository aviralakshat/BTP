"""One-at-a-time tornado and Morris elementary effects.

The tornado moves each flagged parameter to its own minimum and its own
maximum and re-solves the plant. Where that minimum is not a physical coal,
the row says so and a separate closed-analysis row moves the ash with the
rest of the analysis rescaled.

Morris follows the trajectory design in Campolongo, Cariboni and Saltelli
(2007): r trajectories, p levels, a step of p / (2(p-1)) on the coded [0, 1]
factor. mu-star is the mean absolute elementary effect on that coded factor,
so a parameter moved across its whole cited band is comparable with another.
The convergence check is the Spearman rank correlation of mu-star between the
first half of the trajectories and the second half.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np

from src.analysis.plant_eval import (
    apply_factor_point, as_flags, closed_streams, coal_still_closes, headlines,
    label_of, scenario_for, solve, varying_factors,
)
from src.analysis.settings import load_analysis
from src.data.coal import InconsistentInputError, daf_rescale
from src.data.parameters import Parameters
from src.version import stamp


def _swing(low, high, floor: float):
    if low is None or high is None:
        return None
    change = abs(high - low)
    return 0.0 if change < floor else change


def _blank_row(parameter: str, unit: str, method: str, scenario: str,
               low, high, note: str) -> dict:
    return {
        "parameter": parameter, "unit": unit, "method": method,
        "scenario": scenario, "low": low, "high": high, "note": note,
        "low_ok": False, "high_ok": False,
        "baseline_cost_at_low": None, "baseline_cost_at_high": None,
        "baseline_co2_at_low": None, "baseline_co2_at_high": None,
        "abatement_at_low": None, "abatement_at_high": None,
        "co2_cut_at_low": None, "co2_cut_at_high": None,
        "scenario_cost_at_low": None, "scenario_cost_at_high": None,
        "cost_swing": None, "co2_swing": None,
        "abatement_swing": None, "co2_cut_swing": None,
    }


def _fill(row: dict, side: str, metrics: dict | None, reason: str):
    if metrics is None:
        row["note"] = (row["note"] + " " if row["note"] else "") + f"{side} end: {reason}"
        return
    row[f"{side}_ok"] = True
    row[f"baseline_cost_at_{side}"] = metrics["cost_inr_per_t"]
    row[f"baseline_co2_at_{side}"] = metrics["co2_total_t_per_t"]
    row[f"abatement_at_{side}"] = metrics["abatement_inr_per_t"]
    row[f"co2_cut_at_{side}"] = metrics["co2_cut_t_per_t"]
    row[f"scenario_cost_at_{side}"] = metrics["scenario_cost_inr_per_t"]


def _finish(row: dict, floor_cost: float, floor_co2: float) -> dict:
    row["cost_swing"] = _swing(row["baseline_cost_at_low"], row["baseline_cost_at_high"], floor_cost)
    row["co2_swing"] = _swing(row["baseline_co2_at_low"], row["baseline_co2_at_high"], floor_co2)
    row["abatement_swing"] = _swing(row["abatement_at_low"], row["abatement_at_high"], floor_cost)
    row["co2_cut_swing"] = _swing(row["co2_cut_at_low"], row["co2_cut_at_high"], floor_co2)
    if row["low_ok"] and row["high_ok"] and not any(
            row[name] for name in ("cost_swing", "co2_swing", "abatement_swing", "co2_cut_swing")):
        extra = "No effect above the reporting floor."
        row["note"] = (row["note"] + " " + extra).strip() if row["note"] else extra
    return row


def _ends_from_overrides(params: Parameters, flags: dict, low_over: dict, high_over: dict,
                         floor_cost, floor_co2, row: dict) -> dict:
    for side, overrides in (("low", low_over), ("high", high_over)):
        solved, reason = solve(params.with_overrides(overrides))
        if solved and not coal_still_closes(solved["plant"].p):
            solved, reason = None, "coal analysis does not sum to one"
        _fill(row, side, headlines(solved, flags) if solved else None, reason or "")
    return _finish(row, floor_cost, floor_co2)


def tornado(params: Parameters | None = None, cfg: dict | None = None) -> dict:
    """Every sensitivity-flagged parameter at its minimum and its maximum."""
    params = params or Parameters()
    cfg = cfg or load_analysis()
    floor_cost = cfg["noise"]["cost_inr_per_t"]
    floor_co2 = cfg["noise"]["co2_t_per_t"]
    reference = as_flags(cfg["reference_pathway"])
    rows = []

    for key in params.sensitivity_keys():
        meta = params.meta(key)
        flags = scenario_for(key, cfg)
        scenario = label_of(flags)
        if meta.get("unit") == "boolean":
            low, high, method = 0, 1, "scenario_switch"
            note = "Evaluated off and on. The stored band is not used, because both ends of it stay on."
        elif key == "coal.rate_t_per_t_dri" and params["coal.rate_mode"] == "solve":
            bounds = params.bounds(key)
            row = _blank_row(key, meta.get("unit", ""), "not_an_input", scenario,
                             bounds[0], bounds[1],
                             "While coal.rate_mode is solve this value is replaced by "
                             "the energy-balance solution, so the band does not change the plant.")
            row["low_ok"] = row["high_ok"] = True
            row["cost_swing"] = row["co2_swing"] = 0.0
            row["abatement_swing"] = row["co2_cut_swing"] = 0.0
            rows.append(row)
            continue
        else:
            low, high = params.bounds(key)
            if low is None or high is None or high == low:
                row = _blank_row(key, meta.get("unit", ""), "no_range", scenario,
                                 low, high,
                                 "The cited minimum and maximum are the same value, so there is nothing to vary.")
                rows.append(row)
                continue
            method = "one_at_a_time"
            note = ""
            if key.endswith("nhv_kj_kg"):
                note = ("Heating value moves on its own and the carbon analysis stays "
                        "at the base coal, so the two ends are not one consistent coal. "
                        "The closed-analysis row moves them together.")

        row = _blank_row(key, meta.get("unit", ""), method, scenario, low, high, note)
        rows.append(_ends_from_overrides(
            params, flags, {key: low}, {key: high}, floor_cost, floor_co2, row))

    for stream in closed_streams(params):
        ash_key = f"{stream}.ash"
        low, high = params.bounds(ash_key)
        meta = params.meta(ash_key)
        note = ("Ash is changed and the rest of the analysis, including the heating "
                "value, is rescaled on the dry ash-free coal, so the analysis still sums to one.")
        if meta.get("min") is None or meta.get("max") is None:
            note += " No minimum or maximum is set on this ash; the band is the store's default around the measured value."
        flags = reference
        row = _blank_row(f"{ash_key} (closed analysis)", meta.get("unit", ""),
                         "closed_analysis", label_of(flags), low, high, note)
        if low is None or high is None or not high > low:
            rows.append(row)
            continue
        try:
            low_over = daf_rescale(params, stream, low)
            high_over = daf_rescale(params, stream, high)
        except InconsistentInputError as exc:
            row["note"] = row["note"] + " " + str(exc)
            rows.append(row)
            continue
        rows.append(_ends_from_overrides(
            params, flags, low_over, high_over, floor_cost, floor_co2, row))

    base, reason = solve(params)
    base_metrics = headlines(base, reference) if base else None
    return {
        "rows": rows,
        "base": base_metrics,
        "base_error": reason,
        "reference_label": label_of(reference),
        "chart_bars": cfg["tornado_chart_bars"],
        **stamp(params.path),
    }


def coded_trajectories(k: int, r: int, p: int, seed: int) -> list[np.ndarray]:
    """r Morris trajectories on the coded unit interval. Each is (k+1, k)."""
    if p < 4 or p % 2:
        raise ValueError("Morris level count p must be an even integer of at least 4.")
    if r < 2 or r % 2:
        raise ValueError("Morris trajectory count r must be an even integer of at least 2, so the two halves can be compared.")
    rng = np.random.default_rng(seed)
    delta = p / (2.0 * (p - 1))
    grid = np.arange(p) / (p - 1)
    starts = grid[grid <= 1.0 - delta + 1e-12]
    out = []
    for _ in range(r):
        x_star = rng.choice(starts, size=k)
        signs = np.diag(rng.choice(np.array([-1.0, 1.0]), size=k))
        permute = np.eye(k)[:, rng.permutation(k)]
        step = np.tril(np.ones((k + 1, k)), -1)
        ones = np.ones((k + 1, k))
        trajectory = (ones * x_star + (delta / 2.0) * ((2.0 * step - ones) @ signs + ones)) @ permute
        out.append(trajectory)
    return out


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average = 0.5 * (i + j)
        for pos in range(i, j + 1):
            ranks[order[pos]] = average
        i = j + 1
    return ranks


def spearman(left: list[float], right: list[float]) -> float | None:
    """Spearman rank correlation, or None when either ranking has no spread."""
    a, b = _ranks(left), _ranks(right)
    mean_a, mean_b = sum(a) / len(a), sum(b) / len(b)
    num = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    den_a = sum((x - mean_a) ** 2 for x in a) ** 0.5
    den_b = sum((y - mean_b) ** 2 for y in b) ** 0.5
    if den_a == 0 or den_b == 0:
        return None
    return num / (den_a * den_b)


def morris(evaluate_at, factors: list[dict], output_names: list[str],
           r: int, p: int, seed: int) -> dict:
    """Elementary effects of `evaluate_at(values) -> {name: float | None}`.

    `values` is a list aligned with `factors`, on each factor's own [lo, hi].
    A None output, or a point the function rejects by raising, drops that step.
    """
    k = len(factors)
    delta = p / (2.0 * (p - 1))
    trajectories = coded_trajectories(k, r, p, seed)
    # Each entry is (trajectory index, elementary effect), so the two halves
    # of the sample can be separated even when a point is rejected.
    effects = {name: [[] for _ in range(k)] for name in output_names}
    failed = 0
    points = 0

    def at(coded_row):
        nonlocal failed, points
        points += 1
        values = [factor["lo"] + float(u) * (factor["hi"] - factor["lo"])
                  for factor, u in zip(factors, coded_row)]
        try:
            result = evaluate_at(values)
        except Exception:
            failed += 1
            return None
        if result is None:
            failed += 1
            return None
        return result

    for t_index, trajectory in enumerate(trajectories):
        outputs = [at(row) for row in trajectory]
        for step in range(k):
            before, after = outputs[step], outputs[step + 1]
            gap = trajectory[step + 1] - trajectory[step]
            changed = np.flatnonzero(np.abs(gap) > 1e-9)
            if before is None or after is None or len(changed) != 1:
                continue
            index = int(changed[0])
            du = float(gap[index])
            for name in output_names:
                y0, y1 = before.get(name), after.get(name)
                if y0 is None or y1 is None:
                    continue
                effects[name][index].append((t_index, (float(y1) - float(y0)) / du))

    def summarise(groups: list[list[tuple]]) -> dict:
        mu, sigma, count = [], [], []
        for samples in groups:
            count.append(len(samples))
            if not samples:
                mu.append(0.0)
                sigma.append(None)
                continue
            values = [ee for _i, ee in samples]
            absolute = [abs(v) for v in values]
            mu.append(sum(absolute) / len(absolute))
            if len(values) < 2:
                sigma.append(None)
            else:
                mean = sum(values) / len(values)
                sigma.append((sum((v - mean) ** 2 for v in values) / (len(values) - 1)) ** 0.5)
        return {"mu_star": mu, "sigma": sigma, "n": count}

    half = r // 2

    def subset(groups, predicate):
        return [[item for item in samples if predicate(item[0])] for samples in groups]

    agreement = {}
    summarised = {}
    for name in output_names:
        summarised[name] = summarise(effects[name])
        first = summarise(subset(effects[name], lambda i: i < half))
        second = summarise(subset(effects[name], lambda i: i >= half))
        agreement[name] = spearman(first["mu_star"], second["mu_star"])

    return {
        "factors": [factor["key"] + (" (closed analysis)" if factor["closed"] else "")
                    for factor in factors],
        "outputs": summarised,
        "rank_agreement": agreement,
        "r": r, "p": p, "delta": delta, "seed": seed,
        "n_points": points, "n_failed_points": failed,
    }


def morris_plant(params: Parameters | None = None, r: int | None = None,
                 p: int | None = None, seed: int | None = None,
                 cfg: dict | None = None) -> dict:
    """Morris on the bare-plant cost and CO2 and on the reference pathway."""
    params = params or Parameters()
    cfg = cfg or load_analysis()
    r = cfg["morris"]["r"] if r is None else r
    p = cfg["morris"]["p"] if p is None else p
    seed = cfg["seed"] if seed is None else seed
    factors, skipped = varying_factors(params, cfg=cfg)
    flags = as_flags(cfg["reference_pathway"])
    names = ["cost_inr_per_t", "co2_total_t_per_t",
             "scenario_cost_inr_per_t", "abatement_inr_per_t"]

    def evaluate_at(values):
        solved, _reason = solve(apply_factor_point(params, factors, values))
        if solved is None:
            return None
        return headlines(solved, flags)

    result = morris(evaluate_at, factors, names, r, p, seed)
    result["skipped"] = skipped
    result["reference_label"] = label_of(flags)
    result.update(stamp(params.path))
    return result
