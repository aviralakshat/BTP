"""CO2 accounting from the carbon balance, with explicit scopes.

The previous version of this model multiplied coal tonnage by a single emission
factor of 2.4 t CO2/t coal. That factor implies a coal carbon content of
2.4 x 12/44 = 65.5%, whereas the coal analysis this model actually uses (Dey
et al. 2015, Table 6) measures 60.6-62.2% carbon. Deriving CO2 from the carbon
balance removes that contradiction, and as a by-product tells you the emission
factor the assumed coal really implies.

Boundary: the stack, i.e. kiln plus after-burner chamber. Every carbon atom that
reaches the gas phase is counted as CO2, because the ABC exists precisely to
post-combust the CO and volatiles before the gas reaches the ESP. Carbon that
leaves in a solid stream (dolochar, flue dust, DRI) is NOT a stack emission --
but dolochar is routinely burnt in AFBC captive boilers, so that downstream
release is reported as a separate line rather than silently dropped.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data.parameters import MW
from src.models.baseline import BaselinePlant

CO2_PER_C = MW["CO2"] / MW["C"]


class CO2Model:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_emissions(self, net_power_import_kwh_per_t: float | None = None,
                            biogenic_carbon_kg_per_t: float = 0.0,
                            fossil_carbon_offset_kg_per_t: float = 0.0,
                            extra_scope2_t_per_t: float = 0.0) -> dict:
        """Emissions per tonne of DRI.

        net_power_import_kwh_per_t
            Grid electricity drawn after any WHR self-generation. Negative means
            net export, which earns a negative (avoided) Scope 2 figure.
        biogenic_carbon_kg_per_t
            Carbon of biomass origin reaching the gas phase. Reported separately
            and, by the IPCC convention, excluded from the fossil total when
            biomass.biogenic_co2_zero_rated is set.
        fossil_carbon_offset_kg_per_t
            Fossil carbon displaced from the gas phase by a retrofit.
        """
        pl, p = self.plant, self.p
        if net_power_import_kwh_per_t is None:
            net_power_import_kwh_per_t = p["power.aux_kwh_per_t_dri"]

        # --- carbon reaching the gas phase ------------------------------
        c_gas_fossil = (pl.c_coal + pl.c_dolomite
                        - pl.c_char - pl.c_dust - pl.c_dri
                        - fossil_carbon_offset_kg_per_t)
        c_gas_fossil = max(0.0, c_gas_fossil)

        process_co2 = c_gas_fossil * CO2_PER_C / 1000.0          # t/t DRI
        calcination_co2 = pl.c_dolomite * CO2_PER_C / 1000.0
        biogenic_co2 = biogenic_carbon_kg_per_t * CO2_PER_C / 1000.0

        scope2 = (net_power_import_kwh_per_t / 1000.0
                  * p["power.grid_ef_t_per_mwh"]) + extra_scope2_t_per_t

        # Carbon that leaves as solids, and what it becomes if dolochar is
        # subsequently burnt for power (common practice in Indian clusters).
        downstream_char_co2 = pl.c_char * CO2_PER_C / 1000.0
        retained_in_solids = ((pl.c_char + pl.c_dust + pl.c_dri)
                              * CO2_PER_C / 1000.0)

        zero_rated = bool(p["biomass.biogenic_co2_zero_rated"])
        fossil_total = process_co2 + scope2
        reported_total = fossil_total + (0.0 if zero_rated else biogenic_co2)

        implied_coal_ef = (pl.c_coal * CO2_PER_C
                           / max(pl.coal_feed + pl.coal_inj, 1e-9))

        return {
            "co2_direct_t_per_t_dri": process_co2,
            "co2_scope2_t_per_t_dri": scope2,
            "co2_biogenic_t_per_t_dri": biogenic_co2,
            "co2_total_t_per_t_dri": reported_total,
            "co2_fossil_t_per_t_dri": fossil_total,
            "biogenic_zero_rated": zero_rated,
            "of_which_calcination_t_per_t_dri": calcination_co2,
            "co2_retained_in_solids_t_per_t_dri": retained_in_solids,
            "co2_downstream_dolochar_t_per_t_dri": downstream_char_co2,
            "co2_total_incl_dolochar_t_per_t_dri": reported_total + downstream_char_co2,
            "implied_coal_ef_t_per_t_coal": implied_coal_ef,
            "net_power_import_kwh_per_t_dri": net_power_import_kwh_per_t,
            "total_co2_tpd": pl.production_tpd * reported_total,
            "gas_phase_carbon_kg_per_t_dri": c_gas_fossil,
        }


if __name__ == "__main__":
    from src.models.plant import build_plant
    pl = build_plant(capacity_tpd=100, utilization=0.9)
    for k, v in CO2Model(pl).calculate_emissions().items():
        print(f"  {k:44s} {v:10.4f}" if isinstance(v, (int, float))
              else f"  {k:44s} {v}")
