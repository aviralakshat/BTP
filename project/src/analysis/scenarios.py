"""Retrofit scenarios assembled on one solved baseline plant.

A scenario is any combination of waste heat recovery (on/off), a biomass
substitution fraction and a hydrogen substitution fraction. `evaluate` applies
the retrofit deltas to the plant and returns CO2, cost and the derived
decision metrics; `pathway_grid` runs every combination on a grid, and
`least_cost` picks the cheapest feasible one that meets a CO2 target.

Combined biomass and hydrogen are checked for reductant carbon *together*: each
can pass on its own and still starve the bed when both remove coal carbon.
"""
from __future__ import annotations

import os
import sys
from itertools import product

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.economics.economics import EconomicsModel
from src.emissions.co2_model import CO2Model
from src.models.baseline import BaselinePlant
from src.retrofits.biomass import Biomass
from src.retrofits.char_recycle import CharRecycle
from src.retrofits.hydrogen import Hydrogen
from src.retrofits.kiln_control import KilnControl
from src.retrofits.oxygen import Oxygen
from src.retrofits.producer_gas import ProducerGas
from src.retrofits.vfd import VariableFrequencyDrive
from src.retrofits.whr import WHR
from src.version import stamp

BIOMASS_LEVELS = (0.0, 0.05, 0.10, 0.15, 0.20)
H2_LEVELS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30)
CO2_TARGETS = (0.10, 0.20, 0.30, 0.40, 0.50, 0.60)


def _label(whr: bool, biomass: float, h2: float, oxygen: bool = False,
           kiln_control: bool = False, producer_gas: bool = False,
           char_recycle: bool = False, vfd: bool = False) -> str:
    parts = (["WHR"] if whr else []) \
        + ([f"Biomass {biomass:.0%}"] if biomass > 0 else []) \
        + ([f"H2 {h2:.0%}"] if h2 > 0 else []) \
        + (["Oxygen"] if oxygen else []) \
        + (["Kiln control"] if kiln_control else []) \
        + (["Producer gas"] if producer_gas else []) \
        + (["Char recycle"] if char_recycle else []) \
        + (["VFD"] if vfd else [])
    return " + ".join(parts) or "Baseline"


def evaluate(plant: BaselinePlant, energy: dict, whr: bool = False,
             biomass_frac: float = 0.0, h2_frac: float = 0.0,
             baseline: dict | None = None, *, oxygen: bool = False,
             kiln_control: bool = False, producer_gas: bool = False,
             char_recycle: bool = False, vfd: bool = False) -> dict:
    """CO2, cost and decision metrics for one retrofit combination."""
    p = plant.p
    aux = p["power.aux_kwh_per_t_dri"]
    capex, capex_opex = 0.0, 0.0
    extra_opex, fossil_offset, biogenic_c, extra_scope2 = 0.0, 0.0, 0.0, 0.0
    retrofits: dict[str, dict] = {}
    warnings: list[str] = []

    if vfd:
        v = VariableFrequencyDrive(plant).calculate_impact()
        retrofits["Variable Frequency Drives"] = v
        aux = v["aux_after_kwh_per_t_dri"]
        extra_opex += v["annualised_cost_inr_per_t_dri"]
    net_import, export = aux, 0.0

    bio = h2 = None
    if biomass_frac > 0:
        bio = Biomass(plant, biomass_frac).calculate_impact()
        retrofits["Biomass Substitution"] = bio
        extra_opex += bio["opex_delta_inr_per_t_dri"]
        fossil_offset += bio["fossil_carbon_removed_kg_per_t_dri"]
        biogenic_c += bio["biogenic_carbon_to_gas_kg_per_t_dri"]
    if h2_frac > 0:
        h2 = Hydrogen(plant, h2_frac).calculate_impact()
        retrofits["Hydrogen Substitution"] = h2
        extra_opex += h2["opex_delta_inr_per_t_dri"]
        fossil_offset += h2["fossil_carbon_removed_kg_per_t_dri"]
        extra_scope2 += h2["h2_supply_co2_t_per_t_dri"]
        capex += h2["capex_inr"]
    if biomass_frac > 0 and bio is not None:
        capex += bio["capex_inr"]

    # Coal-cutting studies. Each fraction applies to the coal still left, so
    # two studies cannot each remove their full share of the original coal.
    # They were not measured as a package.
    coal_cuts = []
    if producer_gas:
        pg = ProducerGas(plant).calculate_impact()
        retrofits["Producer Gas"] = pg
        coal_cuts.append(pg)
        capex += pg["capex_inr"]
        warnings.append(
            "Producer gas: 20% fuel energy saving applied (TERI). Capital cost "
            "excluded, as no sourced capital cost is available. The reference "
            "plant's absolute savings are not added on top.")
    if kiln_control:
        kc = KilnControl(plant).calculate_impact()
        retrofits["Kiln Control"] = kc
        coal_cuts.append(kc)
        capex += kc["capex_inr"]
    if oxygen:
        ox = Oxygen(plant).calculate_impact()
        retrofits["Oxygen Enrichment"] = ox
        coal_cuts.append(ox)
        extra_opex += ox["oxygen_cost_inr_per_t_dri"]
        if not ox["oxygen_price_known"]:
            warnings.append(
                "Oxygen enrichment: coal and output changes from the Rajesh et al. "
                "plant trial. The trial reports no oxygen price, so oxygen is "
                f"costed at an indicative supplier quote of INR "
                f"{p['oxygen.price_inr_per_nm3']:g}/Nm3.")
    if char_recycle:
        cr = CharRecycle(plant).calculate_impact()
        retrofits["Char Recycling"] = cr
        coal_cuts.append(cr)
        extra_opex += cr["annualised_cost_inr_per_t_dri"]
        warnings.append(
            "Char recycling: single-pass return of 90% of the char to the feed, "
            "replacing coal on equal fixed carbon (Bhardwaj et al. 2024). "
            "Separation power is not reported and is excluded.")
    if len(coal_cuts) > 1:
        warnings.append(
            "Combined coal savings: each measure is applied to the coal remaining "
            "after the previous one, so savings compound rather than add. The "
            "combination has not been trialled on one plant.")

    remaining = 1.0
    coal_kg = plant.coal_feed + plant.coal_inj
    fossil_gas_c = plant.c_gasified + plant.c_unburnt_vm
    for cut in coal_cuts:
        # Char-linked terms shrink with the coal earlier studies already removed.
        before = remaining
        take = remaining * cut["coal_reduction_frac"]
        remaining -= take
        fossil_offset += (fossil_gas_c * take
                          - before * cut.get("carbon_returned_kg_per_t_dri", 0.0))
        extra_opex -= (coal_kg * take / 1000.0) * p["econ.coal_price_inr_per_t"]
        extra_opex += before * cut.get("lost_char_sales_inr_per_t_dri", 0.0)
        cut["coal_reduction_applied_frac"] = take

    if whr:
        r = WHR(plant).calculate_impact(energy, aux_kwh_per_t=aux,
                                        coal_remaining_frac=remaining)
        retrofits["Waste Heat Recovery"] = r
        net_import, export = r["net_import_kwh_per_t_dri"], r["export_kwh_per_t_dri"]
        capex += r["capex_inr"]
        capex_opex += r["annual_opex_inr"]
        if remaining < 1.0:
            warnings.append(
                f"Waste-heat power: after-burner heat is scaled to the {remaining:.1%} "
                "of coal that remains after the coal-saving measures. Waste-gas "
                "sensible heat is held at baseline.")

    production_factor = (1.0 + retrofits["Oxygen Enrichment"]["production_increase_frac"]
                         if oxygen else 1.0)

    # Reductant carbon with every substitution acting on the bed at once.
    reductant_c = fossil_gas_c - fossil_offset
    if bio:
        reductant_c += (bio["biomass_required_kg_per_t_dri"]
                        * p["biomass.carbon_frac"] * p["biomass.char_reactivity"])
    c_required = plant.c_stoich_reduction
    if h2:
        c_required = max(0.0, c_required
                         - h2["reductant_carbon_spared_kg_per_t_dri"])
    reductant_ratio = reductant_c / c_required if c_required > 0 else float("inf")
    feasible = reductant_ratio >= 1.0
    if not feasible:
        warnings.append(
            f"Reductant carbon ratio {reductant_ratio:.2f}: below 1.0 there is "
            "not enough carbon left to strip the oxygen from the burden.")

    co2 = CO2Model(plant).calculate_emissions(
        net_power_import_kwh_per_t=net_import, biogenic_carbon_kg_per_t=biogenic_c,
        fossil_carbon_offset_kg_per_t=fossil_offset,
        extra_scope2_t_per_t=extra_scope2)
    econ = EconomicsModel(plant).calculate_economics(
        net_power_import_kwh_per_t=net_import, power_export_kwh_per_t=export,
        extra_opex_inr_per_t=extra_opex, capex_inr=capex,
        capex_opex_inr_per_yr=capex_opex, production_factor=production_factor)

    result = {
        "label": _label(whr, biomass_frac, h2_frac, oxygen, kiln_control,
                        producer_gas, char_recycle, vfd),
        "whr": whr, "biomass_frac": biomass_frac, "h2_frac": h2_frac,
        "co2": co2, "econ": econ, "retrofits": retrofits, "warnings": warnings,
        "net_import_kwh_per_t_dri": net_import, "export_kwh_per_t_dri": export,
        "capex_inr": capex, "reductant_carbon_ratio": reductant_ratio,
        "feasible": feasible,
    }
    if baseline is not None:
        result.update(_decision_metrics(result, baseline))
    result.update(stamp(plant.p.path))
    return result


def _decision_metrics(s: dict, base: dict) -> dict:
    """Deltas against the baseline, abatement cost and simple payback."""
    co2_s = s["co2"]["co2_total_t_per_t_dri"]
    co2_b = base["co2"]["co2_total_t_per_t_dri"]
    d_co2 = co2_b - co2_s                                   # t avoided per t DRI
    d_cost = s["econ"]["cost_per_t_dri"] - base["econ"]["cost_per_t_dri"]
    annual_t = s["econ"]["annual_output_t"]
    capex = s["capex_inr"]
    # Operating saving excludes the annualised capital, so payback is not
    # counted against itself; retrofit O&M is charged against the saving.
    capex_opex_per_t = (s["econ"]["capex_charge_per_t_dri"]
                        - capex * s["econ"]["capital_recovery_factor"] / annual_t
                        if annual_t else 0.0)
    op_saving = (base["econ"]["cash_cost_per_t_dri"]
                 - s["econ"]["cash_cost_per_t_dri"] - capex_opex_per_t) * annual_t
    payback = capex / op_saving if capex > 0 and op_saving > 0 else None
    return {
        "co2_reduction_t_per_t_dri": d_co2,
        "co2_reduction_frac": d_co2 / co2_b if co2_b else 0.0,
        "cost_delta_inr_per_t_dri": d_cost,
        "abatement_cost_inr_per_t_co2": d_cost / d_co2 if d_co2 > 1e-6 else None,
        "annual_operating_saving_inr": op_saving,
        "payback_yr": payback,
    }


def pathway_grid(plant: BaselinePlant, energy: dict,
                 biomass_levels=BIOMASS_LEVELS, h2_levels=H2_LEVELS) -> list[dict]:
    """Every WHR x biomass x hydrogen combination, re-evaluated together."""
    base = evaluate(plant, energy)
    b_cap = plant.p["biomass.max_substitution_frac"]
    h_cap = plant.p["hydrogen.max_substitution_frac"]
    rows = []
    for whr, b, h in product((False, True), biomass_levels, h2_levels):
        if b > b_cap or h > h_cap or b + h >= 1.0:
            continue
        rows.append(evaluate(plant, energy, whr, b, h, baseline=base))
    return rows


def least_cost(rows: list[dict], target_frac: float) -> dict | None:
    """Cheapest feasible scenario reaching at least `target_frac` CO2 reduction."""
    ok = [r for r in rows
          if r["feasible"] and r["co2_reduction_frac"] >= target_frac - 1e-9]
    return min(ok, key=lambda r: r["econ"]["cost_per_t_dri"]) if ok else None


def pareto_front(rows: list[dict]) -> list[dict]:
    """Feasible scenarios no other scenario beats on both cost and CO2."""
    ok = sorted((r for r in rows if r["feasible"]),
                key=lambda r: (r["econ"]["cost_per_t_dri"],
                               -r["co2_reduction_frac"]))
    front, best = [], float("-inf")
    for r in ok:
        if r["co2_reduction_frac"] > best + 1e-9:
            front.append(r)
            best = r["co2_reduction_frac"]
    return front


def h2_breakeven_price(plant: BaselinePlant) -> float:
    """H2 price (INR/kg) at which substitution adds no operating cost.

    Substitution is energy-for-energy against coal, so the coal bought per kg
    of H2 is fixed and the break-even is the same at every substitution level.
    """
    p = plant.p
    coal_kg = plant.coal_feed + plant.coal_inj
    coal_kj_per_kg = plant.nhv_coal_kj / coal_kg
    return (p["hydrogen.nhv_kj_kg"] / coal_kj_per_kg
            * p["econ.coal_price_inr_per_t"] / 1000.0)


if __name__ == "__main__":
    from src.models.energy_balance import EnergyBalance
    from src.models.plant import build_plant
    pl = build_plant(capacity_tpd=100, utilization=0.9)
    eb = EnergyBalance(pl).calculate_balance()
    grid = pathway_grid(pl, eb)
    print(f"H2 break-even: INR {h2_breakeven_price(pl):,.0f}/kg")
    for t in CO2_TARGETS:
        r = least_cost(grid, t)
        print(f"{t:4.0%}  " + (f"{r['label']:32s} {r['co2_reduction_frac']:6.1%} "
                              f"INR {r['cost_delta_inr_per_t_dri']:+8,.0f}/t"
                              if r else "not reachable"))
