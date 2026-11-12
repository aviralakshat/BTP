"""Named scenarios: save, load, and the difference in their overrides.

A saved scenario is the sidebar, not a second set of plant results. It stores
the model version and the parameter-file hash so a file written by one model
is not silently read as another.
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.version import MODEL_VERSION, parameters_sha256

_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "config", "scenarios")


def document(name: str, overrides: dict, capacity_tpd: float,
             utilization: float, retrofits: dict) -> dict:
    return {
        "name": name,
        "model_version": MODEL_VERSION,
        "parameters_sha256": parameters_sha256(),
        "capacity_tpd": capacity_tpd,
        "utilization": utilization,
        "overrides": {key: overrides[key] for key in sorted(overrides)},
        "retrofits": {key: retrofits[key] for key in sorted(retrofits)},
    }


def save_scenario(doc: dict, directory: str | None = None) -> str:
    directory = directory or _DIR
    os.makedirs(directory, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in doc["name"])
    path = os.path.join(directory, safe + ".json")
    with open(path, "w") as fh:
        json.dump(doc, fh, indent=2)
        fh.write("\n")
    return path


def load_scenario(path: str) -> dict:
    with open(path) as fh:
        doc = json.load(fh)
    missing = [key for key in ("name", "model_version", "parameters_sha256",
                               "overrides", "retrofits") if key not in doc]
    if missing:
        raise ValueError(f"Scenario file is missing {missing}.")
    return doc


def diff_overrides(left: dict, right: dict) -> list[dict]:
    """Keys whose override differs, including a key present on only one side."""
    keys = sorted(set(left) | set(right))
    rows = []
    for key in keys:
        a = left.get(key)
        b = right.get(key)
        if a != b:
            rows.append({"parameter": key, "left": a, "right": b})
    return rows
