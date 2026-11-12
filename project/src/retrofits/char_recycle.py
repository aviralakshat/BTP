"""Char recycling to the kiln feed.

Bhardwaj et al. (2024), Section 4.6: the char in the dolo-char is separated
(90% recovery) and fed back with the ore, replacing feed coal on equal fixed
carbon. The coal it displaces is a coal cut like the other studies; what
differs is that the recycled char carbon now leaves as gas instead of with the
solids, and the plant stops selling that char as dolochar.

The method is single-pass, as in the source: the char that the recycled char
would itself leave behind is not iterated.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.baseline import BaselinePlant


class CharRecycle:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_impact(self) -> dict:
        pl, p = self.plant, self.p
        sep = p["char_recycle.separation_frac"]
        char_kg = pl.char_mass * sep
        char_c = pl.c_char * sep

        feed_coal_replaced = char_c / p["coal_feed.fixed_carbon"]
        coal_kg = pl.coal_feed + pl.coal_inj
        frac = feed_coal_replaced / coal_kg if coal_kg else 0.0

        return {
            "coal_reduction_frac": frac,
            "recycled_char_kg_per_t_dri": char_kg,
            "feed_coal_replaced_kg_per_t_dri": feed_coal_replaced,
            "carbon_returned_kg_per_t_dri": char_c,
            "lost_char_sales_inr_per_t_dri": (char_kg / 1000.0
                                              * p["econ.char_credit_inr_per_t"]),
            "annualised_cost_inr_per_t_dri": p["char_recycle.annualised_cost_inr_per_t_dri"],
            "capex_inr": 0.0,
        }
