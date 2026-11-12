"""Sidebar presets. The domestic coal figures are the unsourced dilution already
used by the dashboard. They are not a measured analysis.
"""
from __future__ import annotations

from src.data.coal import daf_rescale
from src.data.parameters import Parameters


def domestic_coal(params: Parameters | None = None) -> dict:
    params = params or Parameters()
    return {
        **daf_rescale(params, "coal_feed", 0.30, nhv_kj_kg=19500.0),
        **daf_rescale(params, "coal_inj", 0.28, nhv_kj_kg=20200.0),
    }


PRESET_NAMES = ("imported", "domestic")
