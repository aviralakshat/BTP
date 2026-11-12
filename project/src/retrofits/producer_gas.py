"""Producer gas in place of discharge-end coal injection.

TERI (2021) describes gasifying coal fines and returning the gas to the kiln.
The applied effect is the stated energy saving of about 20%. The same section's
4,200 t/year of coal, INR 260 lakh/year and 7,500 t CO2/year belong to one
100 TPD reference kiln and are reported, not added to the 20%. No capital cost
is stated, so none is charged.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.baseline import BaselinePlant


class ProducerGas:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_impact(self) -> dict:
        p = self.p
        return {
            "coal_reduction_frac": p["producer_gas.energy_saving_frac"],
            "reference_coal_saving_t_per_year": p["producer_gas.reference_coal_saving_t_per_year"],
            "reference_benefit_inr_per_year": p["producer_gas.reference_benefit_inr_per_year"],
            "reference_co2_saving_t_per_year": p["producer_gas.reference_co2_saving_t_per_year"],
            "capex_inr": 0.0,
        }
