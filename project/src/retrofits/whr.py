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
from src.economics.economics import scaled_cost
from src.models.baseline import BaselinePlant


class WHR:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_impact(self, energy_balance: dict,
                         aux_kwh_per_t: float | None = None,
                         coal_remaining_frac: float = 1.0) -> dict:
        """`coal_remaining_frac` scales the after-burner heat when another
        lever removes coal: the volatiles and CO it burns come from that coal.
        The waste-gas sensible heat is left on the baseline."""
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
                         * p["whr.abc_combustion_frac"] * coal_remaining_frac)
        heat_available = sensible_available + abc_available

        steam_kj = heat_available * p["whr.boiler_efficiency"]
        gross_kwh_per_t = steam_kj * p["whr.cycle_efficiency"] / KJ_PER_KWH
        auxiliary = gross_kwh_per_t * p["whr.auxiliary_frac"]
        delivered = gross_kwh_per_t - auxiliary

        aux = p["power.aux_kwh_per_t_dri"] if aux_kwh_per_t is None else aux_kwh_per_t
        self_used = min(delivered, aux)
        export = max(0.0, delivered - aux)
        net_import = max(0.0, aux - delivered)

        capacity_mw = gross_kwh_per_t * pl.production_tpd / 1000.0 / 24.0
        capex = scaled_cost(p["whr.capex_inr_per_mw"] * p["whr.capex_ref_mw"],
                            capacity_mw, p["whr.capex_ref_mw"],
                            p["econ.capex_scale_exponent"])
        annual_kwh = gross_kwh_per_t * pl.production_tpd * p["plant.operating_days"]

        return {
            "heat_available_kj_per_t_dri": heat_available,
            "from_waste_gas_sensible_kj": sensible_available,
            "from_abc_post_combustion_kj": abc_available,
            "sensible_recoverable_fraction": recoverable_fraction,
            "gross_generation_kwh_per_t_dri": gross_kwh_per_t,
            "auxiliary_kwh_per_t_dri": auxiliary,
            "delivered_kwh_per_t_dri": delivered,
            "self_consumed_kwh_per_t_dri": self_used,
            "export_kwh_per_t_dri": export,
            "net_import_kwh_per_t_dri": net_import,
            "capacity_mw": capacity_mw,
            "capex_inr": capex,
            "capex_inr_per_mw": capex / capacity_mw if capacity_mw else 0.0,
            "annual_opex_inr": annual_kwh * p["whr.maintenance_inr_per_kwh"],
            "gross_generation_mwh_d": gross_kwh_per_t * pl.production_tpd / 1000.0,
        }
