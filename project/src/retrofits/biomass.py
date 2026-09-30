"""Biomass (agri-residue / biochar) substitution retrofit.

Modelled as an energy-for-energy swap against coal, expressed as a delta on the
validated baseline rather than by rebuilding the stream table.

Two checks the previous version did not make:

  * Reductant carbon. Coal in a rotary kiln is not only fuel, it supplies the
    carbon that strips oxygen from the ore. Substituting on a purely energetic
    basis can leave too little carbon to reduce the burden. The adequacy ratio is
    recomputed here, with biomass carbon credited at a reactivity factor because
    biochar gasifies to CO more readily than coal char.
  * Biogenic accounting. Biomass CO2 is reported separately from fossil CO2 and
    zero-rated in the fossil total only if that accounting choice is switched on,
    instead of being credited as an unconditional reduction at coal's emission
    factor.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.baseline import BaselinePlant


class Biomass:
    def __init__(self, plant: BaselinePlant, substitution_frac: float):
        self.plant = plant
        self.p = plant.p
        cap = plant.p["biomass.max_substitution_frac"]
        self.substitution_frac = min(substitution_frac, cap)
        self.capped = substitution_frac > cap

    def calculate_impact(self) -> dict:
        pl, p = self.plant, self.p
        frac = self.substitution_frac

        energy_displaced = pl.nhv_coal_kj * frac
        biomass_kg = energy_displaced / p["biomass.nhv_kj_kg"]
        coal_saved_kg = (pl.coal_feed + pl.coal_inj) * frac

        # Fossil gas-phase carbon removed, in proportion to the coal displaced.
        fossil_gas_c = pl.c_gasified + pl.c_unburnt_vm
        fossil_c_removed = fossil_gas_c * frac

        biomass_c = biomass_kg * p["biomass.carbon_frac"]
        # Biomass carbon follows the same fate split as coal carbon: most
        # gasifies, a little leaves with the char.
        char_retention = pl.c_char / max(pl.c_coal, 1e-9)
        biogenic_c_to_gas = biomass_c * (1.0 - char_retention)

        # --- reductant carbon adequacy ----------------------------------
        reductant_c = ((fossil_gas_c - fossil_c_removed)
                       + biomass_c * p["biomass.char_reactivity"])
        ratio = reductant_c / pl.c_stoich_reduction

        cost_delta = (biomass_kg / 1000.0 * p["biomass.price_inr_per_t"]
                      - coal_saved_kg / 1000.0 * p["econ.coal_price_inr_per_t"])

        return {
            "substitution_frac": frac,
            "capped_at_max": self.capped,
            "biomass_required_kg_per_t_dri": biomass_kg,
            "coal_saved_kg_per_t_dri": coal_saved_kg,
            "biomass_required_tpd": biomass_kg * pl.production_tpd / 1000.0,
            "fossil_carbon_removed_kg_per_t_dri": fossil_c_removed,
            "biogenic_carbon_to_gas_kg_per_t_dri": biogenic_c_to_gas,
            "extra_ash_kg_per_t_dri": biomass_kg * p["biomass.ash_frac"],
            "reductant_carbon_ratio": ratio,
            "reductant_carbon_adequate": ratio >= 1.0,
            "opex_delta_inr_per_t_dri": cost_delta,
            "capex_inr": 0.0,
        }
