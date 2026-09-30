"""Check model outputs against independent literature bands.

The bands in config/validation_targets.json are acceptance criteria, not inputs:
nothing in the model reads them. That separation is the point -- it means a PASS
is evidence and not a tautology.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data.parameters import Parameters, load_validation_targets
from src.economics.economics import EconomicsModel
from src.emissions.co2_model import CO2Model
from src.models.energy_balance import EnergyBalance
from src.models.mass_balance import MassBalance
from src.models.plant import build_plant
from src.retrofits.hydrogen import Hydrogen
from src.retrofits.whr import WHR


def collect_outputs(params: Parameters | None = None,
                    capacity_tpd: float | None = None,
                    utilization: float | None = None) -> dict:
    """Run the whole model and return the values the targets refer to."""
    params = params or Parameters()
    plant = build_plant(params, capacity_tpd, utilization)
    eb = EnergyBalance(plant).calculate_balance()
    mb = MassBalance(plant).calculate_balance()
    whr = WHR(plant).calculate_impact(eb)
    co2 = CO2Model(plant).calculate_emissions()
    h2 = Hydrogen(plant, params["hydrogen.max_substitution_frac"]).calculate_impact()
    return {
        "plant": plant, "energy": eb, "mass": mb, "whr": whr, "co2": co2,
        "values": {
            "ore_rate_t_per_t_dri": plant.ore_rate,
            "coal_rate_t_per_t_dri": plant.coal_rate,
            "sec_gcal_per_t_dri": eb["sec_gcal_per_t_dri"],
            "dri_fe_total_frac": plant.dri_fe_total_frac,
            "metallization_frac": plant.metallization,
            "co2_direct_t_per_t_dri": co2["co2_direct_t_per_t_dri"],
            "aux_power_kwh_per_t_dri": params["power.aux_kwh_per_t_dri"],
            "whr_gross_kwh_per_t_dri": whr["gross_generation_kwh_per_t_dri"],
            "whr_export_kwh_per_t_dri": whr["export_kwh_per_t_dri"],
            "waste_gas_sensible_frac": eb["waste_gas_sensible_frac_of_nhv"],
            "h2_full_dr_kg_per_t_dri": h2["h2_stoichiometric_full_dr_kg_per_t_dri"],
        },
    }


def run_checks(params: Parameters | None = None,
               capacity_tpd: float | None = None,
               utilization: float | None = None) -> dict:
    out = collect_outputs(params, capacity_tpd, utilization)
    values = out["values"]
    rows = []
    for tgt in load_validation_targets():
        v = values.get(tgt["key"])
        if v is None:
            continue
        lo, hi = tgt["min"], tgt["max"]
        deviation = 0.0
        if lo <= v <= hi:
            verdict = "PASS"
        else:
            nearest = lo if v < lo else hi
            deviation = (v - nearest) / nearest * 100.0
            # Within a tenth of the band edge is a warning, not a failure.
            verdict = "WARN" if abs(deviation) <= 10.0 else "FAIL"
        # Some targets compare related-but-not-identical quantities and are
        # carried for context only; they must not gate the model.
        if tgt.get("informational"):
            verdict = "INFO"
        rows.append({
            "key": tgt["key"], "label": tgt["label"], "unit": tgt["unit"],
            "model_value": v, "min": lo, "max": hi,
            "verdict": verdict, "deviation_percent": deviation,
            "source": tgt["source"], "source_file": tgt.get("source_file", ""),
            "note": tgt.get("note", ""),
        })

    counts = {k: sum(1 for r in rows if r["verdict"] == k)
              for k in ("PASS", "WARN", "FAIL", "INFO")}
    return {
        "rows": rows,
        "counts": counts,
        "mass_closure_percent": out["mass"]["error_percent"],
        "mass_closure_valid": out["mass"]["is_valid"],
        "mass_elements_failing": out["mass"]["elements_failing"],
        "energy_closure_percent": out["energy"]["closure_error_percent"],
        "energy_closure_valid": out["energy"]["is_valid"],
        "all_passed": counts["FAIL"] == 0,
        "outputs": out,
    }


def format_report(result: dict) -> str:
    lines = ["MODEL VALIDATION AGAINST LITERATURE", "=" * 96,
             f"{'check':34s} {'model':>10s} {'band':>19s}  verdict"]
    lines.append("-" * 96)
    for r in result["rows"]:
        band = f"{r['min']:.3g} - {r['max']:.3g}"
        extra = ("" if r["verdict"] in ("PASS", "INFO")
                 else f"  ({r['deviation_percent']:+.1f}% outside)")
        lines.append(f"{r['label'][:34]:34s} {r['model_value']:10.4g} "
                     f"{band:>19s}  {r['verdict']}{extra}")
    lines += ["-" * 96,
              f"PASS {result['counts']['PASS']}   "
              f"WARN {result['counts']['WARN']}   "
              f"FAIL {result['counts']['FAIL']}   "
              f"INFO {result['counts']['INFO']}",
              f"mass balance closure   {result['mass_closure_percent']:.2f}%  "
              f"(valid={result['mass_closure_valid']}, "
              f"failing elements={result['mass_elements_failing'] or 'none'})",
              f"energy balance closure {result['energy_closure_percent']:.2f}%  "
              f"(valid={result['energy_closure_valid']})"]
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_report(run_checks(capacity_tpd=100, utilization=0.9)))
