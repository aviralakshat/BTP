"""Plant economics: daily OPEX, annualised retrofit CAPEX and cost per tonne.

Two things the previous version left out matter a lot to the retrofit cases:

  * Surplus WHR power. Generation above in-plant demand was clamped away with
    max(0, ...), which silently discarded the export revenue that is most of the
    WHR business case.
  * CAPEX. Retrofit capital was displayed but never entered the cost per tonne,
    so a retrofit could only ever look cheaper than the baseline.

CAPEX is annualised with a capital recovery factor so that CAPEX and OPEX can be
added on the same basis.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.baseline import BaselinePlant


def capital_recovery_factor(rate: float, years: int | float) -> float:
    """Annuity factor converting a lump-sum CAPEX into an equal annual charge."""
    if rate <= 0:
        return 1.0 / years
    return rate * (1 + rate) ** years / ((1 + rate) ** years - 1)


class EconomicsModel:
    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    def calculate_economics(self, net_power_import_kwh_per_t: float | None = None,
                            power_export_kwh_per_t: float = 0.0,
                            extra_opex_inr_per_t: float = 0.0,
                            capex_inr: float = 0.0,
                            capex_opex_inr_per_yr: float = 0.0) -> dict:
        pl, p = self.plant, self.p
        prod = pl.production_tpd
        if net_power_import_kwh_per_t is None:
            net_power_import_kwh_per_t = p["power.aux_kwh_per_t_dri"]

        # --- per tonne of DRI -------------------------------------------
        ore_cost = pl.ore_wet / 1000.0 * p["econ.ore_price_inr_per_t"]
        coal_cost = ((pl.coal_feed + pl.coal_inj) / 1000.0
                     * p["econ.coal_price_inr_per_t"])
        dolomite_cost = (pl.dolomite_mass / 1000.0
                         * p["econ.dolomite_price_inr_per_t"])
        power_cost = (net_power_import_kwh_per_t
                      * p["econ.power_tariff_inr_per_kwh"])
        fixed_cost = p["econ.fixed_opex_inr_per_day"] / prod if prod else 0.0
        char_credit = (pl.char_mass / 1000.0 * p["econ.char_credit_inr_per_t"])
        export_revenue = (power_export_kwh_per_t
                          * p["econ.export_tariff_inr_per_kwh"])

        crf = capital_recovery_factor(p["econ.discount_rate"],
                                      p["econ.project_life_yr"])
        annual_output_t = prod * p["plant.operating_days"]
        capex_charge = ((capex_inr * crf + capex_opex_inr_per_yr)
                        / annual_output_t) if annual_output_t else 0.0

        variable = (ore_cost + coal_cost + dolomite_cost + power_cost
                    + extra_opex_inr_per_t)
        cash_cost = variable + fixed_cost - char_credit - export_revenue
        total_cost = cash_cost + capex_charge

        return {
            "cost_per_t_dri": total_cost,
            "cash_cost_per_t_dri": cash_cost,
            "capex_charge_per_t_dri": capex_charge,
            "capex_inr": capex_inr,
            "capital_recovery_factor": crf,
            "breakdown_inr_per_t_dri": {
                "iron ore": ore_cost,
                "coal": coal_cost,
                "dolomite": dolomite_cost,
                "purchased power": power_cost,
                "other retrofit OPEX": extra_opex_inr_per_t,
                "fixed OPEX": fixed_cost,
                "dolochar credit": -char_credit,
                "power export revenue": -export_revenue,
                "annualised CAPEX": capex_charge,
            },
            "total_daily_opex_inr": cash_cost * prod,
            "annual_cost_inr": total_cost * annual_output_t,
            "annual_output_t": annual_output_t,
        }


if __name__ == "__main__":
    from src.models.plant import build_plant
    pl = build_plant(capacity_tpd=100, utilization=0.9)
    r = EconomicsModel(pl).calculate_economics()
    print(f"  cost per t DRI  INR {r['cost_per_t_dri']:,.0f}")
    for k, v in r["breakdown_inr_per_t_dri"].items():
        print(f"    {k:24s} {v:10,.0f}")
