"""Baseline coal-based rotary-kiln DRI plant: elemental stream model.

Everything is computed on a basis of 1 tonne of DRI product and then scaled to
plant throughput. The design rule is that only *independent* quantities are read
from the config -- the rest are derived, so that the mass balance closes by
construction rather than by assumption.

Independent inputs:  ore composition, DRI composition, Fe losses, coal rate and
                     composition, dolomite rate, char and dust rates, excess air.
Derived outputs:     ore rate, air rate, waste-gas composition, oxygen removed,
                     reductant-carbon adequacy.

Two system boundaries are modelled, because they give different answers and the
literature uses both:

  KILN  -- the rotary kiln itself. A large share of coal volatile-matter carbon
           and hydrogen leaves unburnt. This is the boundary of Dey et al. (2015)
           and is what the energy balance is validated against.
  STACK -- kiln plus after-burner chamber, where those volatiles and CO are
           post-combusted. This is the boundary for CO2 accounting and for the
           heat available to a waste-heat recovery boiler.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data.parameters import MW, Parameters

#: Mass fraction of O2 in dry air, and the matching N2 fraction.
O2_MASS_FRAC_AIR = 0.232
N2_MASS_FRAC_AIR = 1.0 - O2_MASS_FRAC_AIR

_EXTRA_MW = {"CH4": 16.043, "SO2": 64.058, "S": 32.060, "H": 1.008}


class BaselinePlant:
    """Steady-state baseline plant on a 1 t DRI basis."""

    def __init__(self, params: Parameters | None = None,
                 capacity_tpd: float | None = None,
                 utilization: float | None = None):
        self.p = params or Parameters()
        self.capacity_tpd = (capacity_tpd if capacity_tpd is not None
                             else self.p["plant.capacity_tpd"])
        self.utilization = (utilization if utilization is not None
                            else self.p["plant.utilization"])
        self.production_tpd = self.capacity_tpd * self.utilization
        self._solve()

    # ------------------------------------------------------------------
    # Solver
    # ------------------------------------------------------------------
    def _solve(self) -> None:
        p = self.p
        # ---- product side: fix the 1000 kg DRI basis ------------------
        fe_m = 1000.0 * p["dri.fe_metallic_frac"]
        feo = 1000.0 * p["dri.feo_frac"]
        gangue_dri = 1000.0 * p["dri.gangue_frac"]
        c_dri = 1000.0 * p["dri.carbon_frac"]
        fe_in_feo = feo * MW["Fe"] / MW["FeO"]
        fe_total_dri = fe_m + fe_in_feo

        self.dri_fe_total_frac = fe_total_dri / 1000.0
        self.metallization = fe_m / fe_total_dri

        # ---- ore: derived from the iron requirement and the Fe yield ---
        fe_yield = 1.0 - p["ore.fe_loss_to_dust_frac"] - p["ore.fe_other_loss_frac"]
        if fe_yield <= 0:
            raise ValueError("Iron losses exceed 100%; check ore.fe_*_loss params.")
        ore_dry = fe_total_dri / (p["ore.fe_total_frac"] * fe_yield)
        ore_moisture = ore_dry * p["ore.moisture_frac"] / (1 - p["ore.moisture_frac"])
        fe_in = ore_dry * p["ore.fe_total_frac"]
        gangue_in = ore_dry * p["ore.gangue_frac"]

        # ---- coal ------------------------------------------------------
        coal_total = 1000.0 * p["coal.rate_t_per_t_dri"]
        coal_inj = coal_total * p["coal.injection_share"]
        coal_feed = coal_total - coal_inj

        def _coal(attr: str) -> float:
            return coal_feed * p[f"coal_feed.{attr}"] + coal_inj * p[f"coal_inj.{attr}"]

        c_coal = _coal("total_carbon")
        h_coal = _coal("hydrogen")
        o_coal = _coal("oxygen")
        n_coal = _coal("nitrogen")
        ash_coal = _coal("ash")
        moist_coal = _coal("moisture")
        s_coal = _coal("sulphur")
        nhv_coal = (coal_feed * p["coal_feed.nhv_kj_kg"]
                    + coal_inj * p["coal_inj.nhv_kj_kg"])

        # ---- flux, char, dust -----------------------------------------
        dolomite = 1000.0 * p["dolomite.rate_t_per_t_dri"]
        # Char is a coal residue and dust is mostly entrained ore fines, so
        # each is scaled on its own parent stream rather than on DRI output.
        char = coal_total * p["char.rate_t_per_t_coal"]
        dust = ore_dry * p["dust.rate_t_per_t_ore"]

        # Dolomite calcination releases CO2 from both the Ca and Mg carbonates.
        # Dey's Table 10 counts only the CaO-bound carbon; including MgO roughly
        # doubles this (small) term, so the two are reported separately.
        c_dolomite_ca = dolomite * p["dolomite.cao_frac"] * MW["C"] / MW["CaO"]
        c_dolomite_mg = dolomite * p["dolomite.mgo_frac"] * MW["C"] / MW["MgO"]
        c_dolomite = c_dolomite_ca + c_dolomite_mg
        cao_mass = dolomite * p["dolomite.cao_frac"]
        mgo_mass = dolomite * p["dolomite.mgo_frac"]
        dolomite_inerts = dolomite * (1.0 - p["dolomite.cao_frac"]
                                      - p["dolomite.mgo_frac"]) - c_dolomite \
            - c_dolomite * (2 * MW["O"]) / MW["C"]
        dolomite_inerts = max(0.0, dolomite_inerts)
        cao_out = cao_mass + mgo_mass

        # ---- carbon partition -----------------------------------------
        c_char = char * p["char.fixed_carbon"]
        c_dust = dust * p["dust.carbon_frac"]
        c_unburnt_vm = c_coal * p["kiln.unburnt_vm_carbon_frac"]
        c_gasified = c_coal - c_char - c_dust - c_dri - c_unburnt_vm
        if c_gasified <= 0:
            raise ValueError(
                "No carbon left for gasification. Coal rate is too low, or the "
                "char/dust/unburnt-VM fractions are too high.")

        # ---- oxygen removed from the ore ------------------------------
        # All iron reporting to DRI entered as Fe2O3; the FeO in the product
        # still holds one oxygen per iron.
        o_bound_as_fe2o3 = fe_total_dri * (3 * MW["O"]) / (2 * MW["Fe"])
        o_in_feo = feo * MW["O"] / MW["FeO"]
        o_removed = o_bound_as_fe2o3 - o_in_feo

        # ---- reductant carbon adequacy --------------------------------
        # Worst case: every removed oxygen leaves on a separate CO molecule.
        c_stoich_reduction = o_removed * MW["C"] / MW["O"]
        self.reductant_carbon_ratio = c_gasified / c_stoich_reduction

        # ---- combustion air (global oxygen atom balance) ---------------
        h_burnt_kiln = h_coal * p["kiln.h2_burnt_in_kiln_frac"]
        co_frac = p["kiln.co_in_waste_gas_frac"]
        c_to_co2 = c_gasified * (1.0 - co_frac)
        c_to_co = c_gasified * co_frac

        o_for_co2 = c_to_co2 * (2 * MW["O"]) / MW["C"]
        o_for_co = c_to_co * MW["O"] / MW["C"]
        o_for_h2o = h_burnt_kiln * MW["O"] / MW["H2"]
        o_demand = o_for_co2 + o_for_co + o_for_h2o
        o2_stoich = max(0.0, o_demand - o_removed - o_coal)
        o2_actual = o2_stoich * (1.0 + p["kiln.excess_air_frac"])
        air = o2_actual / O2_MASS_FRAC_AIR

        # ---- waste gas constituents (kiln boundary) --------------------
        wg_co2 = c_to_co2 * MW["CO2"] / MW["C"] + c_dolomite * MW["CO2"] / MW["C"]
        wg_co = c_to_co * MW["CO"] / MW["C"]
        wg_h2o = (moist_coal + ore_moisture
                  + h_burnt_kiln * MW["H2O"] / MW["H2"])
        wg_n2 = air * N2_MASS_FRAC_AIR + n_coal
        wg_o2 = o2_actual - o2_stoich
        wg_so2 = s_coal * _EXTRA_MW["SO2"] / _EXTRA_MW["S"]
        # Unburnt volatiles leave as a carbon + hydrogen stream. No single
        # molecular formula is assumed; Dey models the V.M. as phenol.
        h_unburnt = h_coal - h_burnt_kiln
        wg_volatiles = c_unburnt_vm + h_unburnt
        waste_gas = (wg_co2 + wg_co + wg_h2o + wg_n2 + wg_o2 + wg_so2
                     + wg_volatiles)

        # ---- solid loss streams ----------------------------------------
        # Iron lost other than in the flue dust leaves as unreduced fines.
        fe_other_loss = fe_in * p["ore.fe_other_loss_frac"]
        other_fines = fe_other_loss * MW["Fe2O3"] / (2 * MW["Fe"])
        # "Free ash to cooler" is the coal ash and ore gangue that neither
        # binds into char nor leaves up the stack. Dey et al. (2015) Table 10
        # obtain this stream by difference as well.
        inerts_in = ash_coal + gangue_in + dolomite_inerts
        inerts_accounted = (char * p["char.ash"] + gangue_dri
                            + dust * (1 - p["dust.fe2o3_frac"]
                                      - p["dust.carbon_frac"]))
        free_ash = inerts_in - inerts_accounted
        if free_ash < 0:
            raise ValueError(
                "Inert solids out exceed inerts in by "
                f"{-free_ash:.1f} kg/t DRI. Check char.ash, dust composition "
                "and coal ash against each other.")

        # ---- assemble the per-tonne-DRI ledger -------------------------
        self.inputs = {
            "iron ore (dry)": ore_dry,
            "ore moisture": ore_moisture,
            "feed coal": coal_feed,
            "injection coal": coal_inj,
            "dolomite": dolomite,
            "combustion air": air,
        }
        self.outputs = {
            "DRI": 1000.0,
            "char (dolochar)": char,
            "flue dust": dust,
            "calcined flux (CaO+MgO)": cao_out,
            "free ash to cooler": free_ash,
            "other unreduced fines": other_fines,
            "waste gas": waste_gas,
        }
        self.waste_gas_composition = {
            "CO2": wg_co2, "CO": wg_co, "H2O": wg_h2o, "N2": wg_n2,
            "O2": wg_o2, "SO2": wg_so2, "unburnt volatiles": wg_volatiles,
        }
        self.carbon = {
            "in: coal": c_coal,
            "in: dolomite (Ca)": c_dolomite_ca,
            "in: dolomite (Mg)": c_dolomite_mg,
            "out: char": c_char,
            "out: flue dust": c_dust,
            "out: DRI": c_dri,
            "out: unburnt volatiles": c_unburnt_vm,
            "out: gasified (to CO/CO2)": c_gasified,
        }
        self.elements = {
            "Fe": {"in": fe_in,
                   "out": fe_total_dri
                          + fe_in * p["ore.fe_loss_to_dust_frac"]
                          + fe_in * p["ore.fe_other_loss_frac"]},
            "gangue": {"in": gangue_in, "out": gangue_dri,
                       "to_dust_or_loss": gangue_in - gangue_dri},
            "ash": {"in": ash_coal,
                    "out": char * p["char.ash"] + (dust - c_dust)},
        }
        # Scalars other modules need.
        self.ore_rate = ore_dry / 1000.0
        self.coal_rate = coal_total / 1000.0
        self.o_removed = o_removed
        self.c_gasified = c_gasified
        self.c_unburnt_vm = c_unburnt_vm
        self.c_char = c_char
        self.c_dust = c_dust
        self.c_dri = c_dri
        self.c_coal = c_coal
        self.c_dolomite = c_dolomite
        self.c_stoich_reduction = c_stoich_reduction
        self.h_coal = h_coal
        self.h_burnt_kiln = h_burnt_kiln
        self.nhv_coal_kj = nhv_coal
        self.air = air
        self.o2_stoich = o2_stoich
        self.waste_gas = waste_gas
        self.char_mass = char
        self.dust_mass = dust
        self.cao_out = cao_out
        self.cao_mass = cao_mass
        self.mgo_mass = mgo_mass
        self.dolomite_inerts = dolomite_inerts
        self.free_ash = free_ash
        self.other_fines = other_fines
        self.moisture_total = moist_coal + ore_moisture
        self.dolomite_mass = dolomite
        self.coal_feed = coal_feed
        self.coal_inj = coal_inj
        self.ore_dry = ore_dry
        self.ore_wet = ore_dry + ore_moisture

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    @property
    def sec_gcal_per_t_dri(self) -> float:
        """Specific energy consumption on a coal net-heating-value basis."""
        from src.data.parameters import GCAL_PER_KJ
        return self.nhv_coal_kj * GCAL_PER_KJ

    def to_tpd(self, kg_per_t_dri: float) -> float:
        """Scale a per-tonne-DRI intensity to plant tonnes per day."""
        return kg_per_t_dri * self.production_tpd / 1000.0

    def stream_table(self) -> list[dict]:
        rows = []
        for name, v in self.inputs.items():
            rows.append({"stream": name, "direction": "in",
                         "kg_per_t_dri": v, "tpd": self.to_tpd(v)})
        for name, v in self.outputs.items():
            rows.append({"stream": name, "direction": "out",
                         "kg_per_t_dri": v, "tpd": self.to_tpd(v)})
        return rows

    def summary(self) -> dict:
        return {
            "capacity_tpd": self.capacity_tpd,
            "utilization": self.utilization,
            "production_tpd": self.production_tpd,
            "ore_rate_t_per_t_dri": self.ore_rate,
            "coal_rate_t_per_t_dri": self.coal_rate,
            "dolomite_rate_t_per_t_dri": self.dolomite_mass / 1000.0,
            "air_rate_t_per_t_dri": self.air / 1000.0,
            "dri_fe_total_frac": self.dri_fe_total_frac,
            "metallization_frac": self.metallization,
            "oxygen_removed_kg_per_t_dri": self.o_removed,
            "reductant_carbon_ratio": self.reductant_carbon_ratio,
            "sec_gcal_per_t_dri": self.sec_gcal_per_t_dri,
            "ore_tpd": self.to_tpd(self.ore_wet),
            "coal_tpd": self.to_tpd(self.coal_feed + self.coal_inj),
            "dolomite_tpd": self.to_tpd(self.dolomite_mass),
        }


if __name__ == "__main__":
    plant = BaselinePlant(capacity_tpd=100, utilization=0.9)
    for k, v in plant.summary().items():
        print(f"  {k:36s} {v:12.4f}" if isinstance(v, float) else f"  {k:36s} {v}")
