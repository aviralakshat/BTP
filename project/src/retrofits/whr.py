"""Waste heat recovery retrofit.

Sizing is derived from the kiln's own energy balance rather than from a blanket
"35% of input energy" rule. Two heat sources feed the boiler:

  1. Sensible heat in the waste gas, recoverable between the gas temperature and
     the WHRB stack temperature.
  2. Chemical energy released when the after-burner chamber post-combusts the
     volatiles and CO that leave the kiln unburnt. On this plant that is the
     larger of the two, which is why sponge-iron WHR plants generate as much
     power as they do.

Validation: Nduagu et al. report 450-451 kWh/t-DRI generated and 351 kWh/t-DRI
exported for a rotary-kiln plant, so the computed figures are directly checkable.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data.parameters import KJ_PER_KWH
from src.models.baseline import BaselinePlant


class WHR:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_impact(self, energy_balance: dict) -> dict:
        pl, p = self.plant, self.p
        t_gas = p["kiln.waste_gas_temp_c"]
        t_stack = p["whr.stack_temp_c"]
        t_amb = p["kiln.ambient_temp_c"]

        # Only the part of the gas sensible heat above the stack temperature can
        # be taken out; the rest leaves up the chimney regardless.
        sensible_total = energy_balance["waste_gas_sensible_kj"]
        recoverable_fraction = max(0.0, (t_gas - t_stack) / (t_gas - t_amb))
        sensible_available = sensible_total * recoverable_fraction

        abc_available = (energy_balance["recoverable_chemical_kj"]
                         * p["whr.abc_combustion_frac"])
        heat_available = sensible_available + abc_available

        steam_kj = heat_available * p["whr.boiler_efficiency"]
        gross_kwh_per_t = steam_kj * p["whr.cycle_efficiency"] / KJ_PER_KWH

        aux = p["power.aux_kwh_per_t_dri"]
        self_used = min(gross_kwh_per_t, aux)
        export = max(0.0, gross_kwh_per_t - aux)
        net_import = max(0.0, aux - gross_kwh_per_t)

        capacity_mw = gross_kwh_per_t * pl.production_tpd / 1000.0 / 24.0
        capex = capacity_mw * p["whr.capex_inr_per_mw"]

        return {
            "heat_available_kj_per_t_dri": heat_available,
            "from_waste_gas_sensible_kj": sensible_available,
            "from_abc_post_combustion_kj": abc_available,
            "sensible_recoverable_fraction": recoverable_fraction,
            "gross_generation_kwh_per_t_dri": gross_kwh_per_t,
            "self_consumed_kwh_per_t_dri": self_used,
            "export_kwh_per_t_dri": export,
            "net_import_kwh_per_t_dri": net_import,
            "capacity_mw": capacity_mw,
            "capex_inr": capex,
            "annual_opex_inr": capex * p["whr.opex_frac_of_capex"],
            "gross_generation_mwh_d": gross_kwh_per_t * pl.production_tpd / 1000.0,
        }
