"""Variable frequency drives on the kiln's motors.

Bhardwaj et al. (2024), Section 4.2: motors take 90% of the plant's
electricity, the unit runs at about 90% of rated capacity, and equipment at 90%
of rated speed draws 73% of rated power. The saving is applied to this plant's
own auxiliary load rather than copied from the paper's kWh per tonne of steel.
Table 3 gives the cost as an annualised charge per tonne of crude steel, which
is converted to a tonne of DRI and carried as an operating charge.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.baseline import BaselinePlant


class VariableFrequencyDrive:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_impact(self) -> dict:
        p = self.p
        aux = p["power.aux_kwh_per_t_dri"]
        saving_frac = (p["vfd.motor_share_frac"]
                       * (1.0 - p["vfd.power_at_reduced_speed_frac"]))
        return {
            "power_saving_frac": saving_frac,
            "power_saving_kwh_per_t_dri": aux * saving_frac,
            "aux_after_kwh_per_t_dri": aux * (1.0 - saving_frac),
            "annualised_cost_inr_per_t_dri": p["vfd.annualised_cost_inr_per_t_dri"],
            "capex_inr": 0.0,
        }
