"""Oxygen enrichment, as measured on one 100 TPD kiln.

Rajesh, Nandi and Pabi (2016), Table 8, is one industrial trial. This module
applies that trial's coal and output changes. It does not rebuild the air
stream: the table's air figures are reported so they can be compared with the
solved air rate, and the abstract's 2,609 Nm3/t is not used.

The coal change applied per tonne of product comes from the table. Hourly solid
coal falls from 4.29 to 4.15 t/h while output rises 6%, so specific coal falls
by more than the authors' stated 6%. Both numbers are returned.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.baseline import BaselinePlant


class Oxygen:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_impact(self) -> dict:
        p = self.p
        hourly_remaining = (p["oxygen.table_coal_tph_case"]
                            / p["oxygen.table_coal_tph_base"])
        specific_remaining = hourly_remaining / (1.0 + p["oxygen.production_increase_frac"])
        specific_reduction = 1.0 - specific_remaining
        price_known = p.meta("oxygen.price_inr_per_nm3")["status"] == "verified"
        return {
            "coal_reduction_frac": specific_reduction,
            "rate_nm3_per_t": p["oxygen.rate_nm3_per_t"],
            "coal_hourly_remaining_frac": hourly_remaining,
            "authors_specific_coal_claim_frac": p["oxygen.authors_specific_coal_claim_frac"],
            "production_increase_frac": p["oxygen.production_increase_frac"],
            "air_nm3_per_t_base": p["oxygen.air_nm3_per_t_base"],
            "air_nm3_per_t_case": p["oxygen.air_nm3_per_t_case"],
            "campaign_days_base": p["oxygen.campaign_days_base"],
            "campaign_days_case": p["oxygen.campaign_days_case"],
            "oxygen_cost_inr_per_t_dri": (p["oxygen.rate_nm3_per_t"]
                                          * p["oxygen.price_inr_per_nm3"]),
            "oxygen_price_known": price_known,
            "capex_inr": 0.0,
        }
