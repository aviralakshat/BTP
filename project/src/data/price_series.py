"""Low, base and high prices.

Commodity bands are read from parameters.json, which already holds the cited
value and its bounds. This module only names the series and attaches the
carbon charges, which are not plant parameters.
"""
from __future__ import annotations

import json
import os

from src.analysis.settings import carbon_cases
from src.data.parameters import Parameters

_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data",
                     "price_series", "commodity_prices.json")


def load_price_series(path: str | None = None, params: Parameters | None = None) -> dict:
    path = path or _PATH
    with open(path) as fh:
        raw = json.load(fh)
    params = params or Parameters()
    rows = []
    for spec in raw["series"]:
        key = spec["parameter"]
        meta = params.meta(key)
        low, high = params.bounds(key)
        rows.append({
            "id": spec["id"],
            "parameter": key,
            "unit": meta.get("unit", ""),
            "low": low,
            "base": params[key],
            "high": high,
            "has_range": high is not None and low is not None and high > low,
            "source": meta.get("source", ""),
            "note": spec.get("note", ""),
        })
    cases = {case["id"]: case for case in carbon_cases()}
    carbon = raw["carbon"]
    rows.append({
        "id": carbon["id"],
        "parameter": None,
        "unit": carbon["unit"],
        "low": cases[carbon["low_case"]]["inr_per_t"],
        "base": cases[carbon["base_case"]]["inr_per_t"],
        "high": cases[carbon["high_case"]]["inr_per_t"],
        "has_range": True,
        "source": cases[carbon["high_case"]]["source"],
        "note": carbon.get("note", ""),
    })
    return {"retrieved": raw["retrieved"], "rows": rows}
