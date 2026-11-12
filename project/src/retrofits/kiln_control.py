"""Sensor-based kiln control.

CSE (Kumar and Haldar 2026), Table 4, gives a coal saving of 3-5% and an
indicative capital cost of INR 0.5-1 crore. The applied saving cannot exceed
the 5% cap. The capital cost is the low end of that range and is not scaled,
because the table does not state a kiln size.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.baseline import BaselinePlant


class KilnControl:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_impact(self) -> dict:
        p = self.p
        cap = p.bounds("kiln_control.coal_saving_frac")[1]
        requested = p["kiln_control.coal_saving_frac"]
        frac = min(requested, cap)
        return {
            "coal_reduction_frac": frac,
            "requested_frac": requested,
            "capped": requested > cap,
            "capex_inr": p["kiln_control.capex_inr"],
        }
