"""Mass balance verification for the baseline plant.

This module does not *size* anything -- BaselinePlant already derives the stream
table. Its job is to audit that table: total mass in versus out, plus an
element-by-element closure for Fe, C, O, H, N, S and inert solids.

Closure is reported, never forced. A residual term is printed explicitly so the
size of what the model fails to account for is always visible, which is how
Dey et al. (2015) present their own balance ("other losses by difference").
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data.parameters import MW
from src.models.baseline import N2_MASS_FRAC_AIR, O2_MASS_FRAC_AIR, BaselinePlant

_S_MW, _SO2_MW = 32.060, 64.058


class MassBalance:
    #: Total-mass closure tolerance. 5% is the usual engineering acceptance
    #: band for a plant-scale solids balance built from proximate/ultimate data.
    TOTAL_TOLERANCE = 0.05
    #: Element balances are built from atom accounting and should be tighter.
    ELEMENT_TOLERANCE = 0.02

    def __init__(self, plant: BaselinePlant):
        self.plant = plant
        self.p = plant.p

    # ------------------------------------------------------------------
    def total(self) -> dict:
        pl = self.plant
        mass_in = sum(pl.inputs.values())
        mass_out = sum(pl.outputs.values())
        residual = mass_in - mass_out
        return {
            "mass_in_kg_per_t_dri": mass_in,
            "mass_out_kg_per_t_dri": mass_out,
            "residual_kg_per_t_dri": residual,
            "error_percent": abs(residual) / mass_in * 100.0,
            "is_valid": abs(residual) / mass_in <= self.TOTAL_TOLERANCE,
            "tolerance_percent": self.TOTAL_TOLERANCE * 100.0,
            "mass_in_tpd": pl.to_tpd(mass_in),
            "mass_out_tpd": pl.to_tpd(mass_out),
        }

    # ------------------------------------------------------------------
    def elements(self) -> list[dict]:
        pl, p = self.plant, self.p
        wg = pl.waste_gas_composition
        rows = []

        def add(el, ins, outs):
            tin, tout = sum(ins.values()), sum(outs.values())
            denom = tin if tin else 1.0
            rows.append({
                "element": el,
                "in_kg_per_t_dri": tin,
                "out_kg_per_t_dri": tout,
                "residual": tin - tout,
                "error_percent": abs(tin - tout) / denom * 100.0,
                "is_valid": abs(tin - tout) / denom <= self.ELEMENT_TOLERANCE,
                "in_detail": ins,
                "out_detail": outs,
            })

        # --- iron -------------------------------------------------------
        fe_in = pl.ore_dry * p["ore.fe_total_frac"]
        add("Fe",
            {"iron ore": fe_in},
            {"DRI": pl.dri_fe_total_frac * 1000.0,
             "flue dust": fe_in * p["ore.fe_loss_to_dust_frac"],
             "unreduced fines": fe_in * p["ore.fe_other_loss_frac"]})

        # --- carbon -----------------------------------------------------
        add("C",
            {"coal": pl.c_coal, "dolomite": pl.c_dolomite},
            {"char": pl.c_char, "flue dust": pl.c_dust, "DRI": pl.c_dri,
             "unburnt volatiles": pl.c_unburnt_vm,
             "CO2 in waste gas": (wg["CO2"] * MW["C"] / MW["CO2"]),
             "CO in waste gas": (wg["CO"] * MW["C"] / MW["CO"])})

        # --- hydrogen ---------------------------------------------------
        h_moisture = pl.moisture_total * (2 * 1.008) / MW["H2O"]
        add("H",
            {"coal (as H2)": pl.h_coal, "moisture in feed": h_moisture},
            {"H2O in waste gas": wg["H2O"] * (2 * 1.008) / MW["H2O"],
             "unburnt volatiles": pl.h_coal - pl.h_burnt_kiln})

        # --- oxygen -----------------------------------------------------
        # Reacting oxygen only. Oxygen locked in unreduced Fe2O3, in gangue
        # and in the CaO/MgO surviving calcination passes straight through
        # and appears on neither side.
        def _coal(a):
            return (pl.coal_feed * p[f"coal_feed.{a}"]
                    + pl.coal_inj * p[f"coal_inj.{a}"])

        o_moisture = pl.moisture_total * MW["O"] / MW["H2O"]
        add("O",
            {"combustion air": pl.air * O2_MASS_FRAC_AIR,
             "iron ore (removed from Fe2O3)": pl.o_removed,
             "coal": _coal("oxygen"),
             "feed moisture": o_moisture,
             "dolomite carbonate": pl.c_dolomite * (2 * MW["O"]) / MW["C"]},
            {"CO2": wg["CO2"] * (2 * MW["O"]) / MW["CO2"],
             "CO": wg["CO"] * MW["O"] / MW["CO"],
             "H2O": wg["H2O"] * MW["O"] / MW["H2O"],
             "excess O2": wg["O2"],
             "SO2": wg["SO2"] * (2 * MW["O"]) / _SO2_MW})

        # --- nitrogen ---------------------------------------------------
        add("N",
            {"combustion air": pl.air * N2_MASS_FRAC_AIR, "coal": _coal("nitrogen")},
            {"N2 in waste gas": wg["N2"]})

        # --- sulphur ----------------------------------------------------
        add("S",
            {"coal": _coal("sulphur")},
            {"SO2 in waste gas": wg["SO2"] * _S_MW / _SO2_MW})

        # --- inert solids ------------------------------------------------
        add("inert solids (ash + gangue)",
            {"coal ash": _coal("ash"),
             "ore gangue": pl.ore_dry * p["ore.gangue_frac"],
             "dolomite inerts": pl.dolomite_inerts},
            {"char ash": pl.char_mass * p["char.ash"],
             "DRI gangue": 1000.0 * p["dri.gangue_frac"],
             "flue dust (non-Fe, non-C)": pl.dust_mass * (
                 1 - p["dust.fe2o3_frac"] - p["dust.carbon_frac"]),
             "free ash to cooler (by difference)": pl.free_ash})
        return rows

    # ------------------------------------------------------------------
    def calculate_balance(self) -> dict:
        t = self.total()
        els = self.elements()
        t["element_balances"] = els
        t["elements_failing"] = [e["element"] for e in els if not e["is_valid"]]
        t["all_elements_valid"] = not t["elements_failing"]
        return t


if __name__ == "__main__":
    plant = BaselinePlant(capacity_tpd=100, utilization=0.9)
    mb = MassBalance(plant)
    t = mb.calculate_balance()
    print(f"TOTAL  in {t['mass_in_kg_per_t_dri']:9.1f}  out {t['mass_out_kg_per_t_dri']:9.1f}"
          f"  err {t['error_percent']:6.2f}%  valid={t['is_valid']}")
    print(f"{'element':30s} {'in':>10s} {'out':>10s} {'err %':>8s}  ok")
    for e in t["element_balances"]:
        print(f"{e['element']:30s} {e['in_kg_per_t_dri']:10.2f} {e['out_kg_per_t_dri']:10.2f}"
              f" {e['error_percent']:8.2f}  {e['is_valid']}")
