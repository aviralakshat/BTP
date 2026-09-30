"""Hydrogen substitution retrofit for an existing rotary kiln.

Hydrogen does two jobs at once, and the previous version only counted the first:

  1. Fuel. It displaces coal energy.
  2. Reductant. Fe2O3 + 3H2 -> 2Fe + 3H2O removes oxygen without carbon, so
     hydrogen spares reductant carbon instead of competing with it. That is what
     makes H2 a qualitatively different lever from biomass, which must supply
     carbon to keep the reduction going.

The stoichiometric hydrogen demand for the oxygen actually removed is reported
alongside, because it is directly checkable: Kamal et al. validate complete
H2 direct reduction against 53.5-59.6 kg H2/t DRI.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data.parameters import MW
from src.models.baseline import BaselinePlant


class Hydrogen:
    def __init__(self, plant: BaselinePlant, substitution_frac: float):
        self.plant = plant
        self.p = plant.p
        cap = plant.p["hydrogen.max_substitution_frac"]
        self.substitution_frac = min(substitution_frac, cap)
        self.capped = substitution_frac > cap

    def calculate_impact(self) -> dict:
        pl, p = self.plant, self.p
        frac = self.substitution_frac

        energy_displaced = pl.nhv_coal_kj * frac
        h2_kg = energy_displaced / p["hydrogen.nhv_kj_kg"]
        coal_saved_kg = (pl.coal_feed + pl.coal_inj) * frac

        fossil_gas_c = pl.c_gasified + pl.c_unburnt_vm
        fossil_c_removed = fossil_gas_c * frac

        # Hydrogen that reaches the reduction zone can carry oxygen out as H2O.
        # One mole of H2 removes one mole of O, capped by the oxygen actually
        # available to remove.
        o_removable_by_h2 = min(pl.o_removed,
                                h2_kg * MW["O"] / MW["H2"])
        carbon_spared = o_removable_by_h2 * MW["C"] / MW["O"]

        # Stoichiometric H2 for complete reduction, for cross-checking against
        # the 53.5-59.6 kg H2/t DRI reported for full H2-DR.
        h2_stoich_full_dr = pl.o_removed * MW["H2"] / MW["O"]

        reductant_c = fossil_gas_c - fossil_c_removed
        c_required = max(0.0, pl.c_stoich_reduction - carbon_spared)
        ratio = reductant_c / c_required if c_required > 0 else float("inf")

        cost_delta = (h2_kg * p["hydrogen.price_inr_per_kg"]
                      - coal_saved_kg / 1000.0 * p["econ.coal_price_inr_per_t"])
        h2_co2 = h2_kg / 1000.0 * p["hydrogen.ef_t_per_t"]

        return {
            "substitution_frac": frac,
            "capped_at_max": self.capped,
            "h2_required_kg_per_t_dri": h2_kg,
            "h2_required_tpd": h2_kg * pl.production_tpd / 1000.0,
            "h2_stoichiometric_full_dr_kg_per_t_dri": h2_stoich_full_dr,
            "coal_saved_kg_per_t_dri": coal_saved_kg,
            "fossil_carbon_removed_kg_per_t_dri": fossil_c_removed,
            "oxygen_removed_by_h2_kg_per_t_dri": o_removable_by_h2,
            "reductant_carbon_spared_kg_per_t_dri": carbon_spared,
            "reductant_carbon_ratio": ratio,
            "reductant_carbon_adequate": ratio >= 1.0,
            "h2_supply_co2_t_per_t_dri": h2_co2,
            "opex_delta_inr_per_t_dri": cost_delta,
            "capex_inr": 0.0,
        }
