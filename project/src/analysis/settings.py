"""Readers for the analysis settings and the distribution overrides.

The plant model does not import this module. Carbon-price cases are converted
here so the rupee figure is the product of the two cited inputs, not a third
number typed beside them.
"""
from __future__ import annotations

import json
import os

_CONFIG = os.path.join(os.path.dirname(__file__), "..", "..", "config")


def _load(name: str, path: str | None) -> dict:
    path = path or os.path.join(_CONFIG, name)
    with open(path) as fh:
        return json.load(fh)


def load_analysis(path: str | None = None) -> dict:
    return _load("analysis.json", path)


def load_distributions(path: str | None = None) -> dict:
    return _load("distributions.json", path)


def carbon_price_inr_per_t(case: dict) -> float:
    """Rupees per tonne of CO2 for one declared case."""
    if "eur_per_t" in case:
        return float(case["eur_per_t"]) * float(case["inr_per_eur"])
    return float(case["inr_per_t"])


def carbon_cases(cfg: dict | None = None) -> list[dict]:
    cfg = cfg or load_analysis()
    out = []
    for case in cfg["carbon_cases"]:
        row = dict(case)
        row["inr_per_t"] = carbon_price_inr_per_t(case)
        out.append(row)
    return out
