"""HTTP layer over the plant model for the web console in project/web.

No calculation lives here. Every number is computed by src/ exactly as the
Streamlit app computes it; this module only selects fields and serialises them.

    cd project && ./venv/bin/uvicorn api.server:app --port 8000
"""
from __future__ import annotations

import json
import math
import os
import sys
from functools import lru_cache
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analysis.scenarios import (CO2_TARGETS, evaluate, h2_breakeven_price,  # noqa: E402
                                    least_cost, pareto_front, pathway_grid)
from src.data.parameters import GCAL_PER_KJ, Parameters  # noqa: E402
from src.data.presets import domestic_coal  # noqa: E402
from src.economics.economics import EconomicsModel  # noqa: E402
from src.economics.financial import (financing_terms, finance_project,  # noqa: E402
                                     reconciliation, retrofit_project)
from src.emissions.co2_model import CO2Model  # noqa: E402
from src.kiln.axial import axial_profile  # noqa: E402
from src.models.energy_balance import EnergyBalance  # noqa: E402
from src.models.mass_balance import MassBalance  # noqa: E402
from src.models.plant import build_plant  # noqa: E402
from src.ui.labels import (COST_LINES, ENERGY_GROUPS, plain_parameter,  # noqa: E402
                           plain_route, stream, title_case)
from src.validation.literature_check import run_checks  # noqa: E402
from src.version import stamp  # noqa: E402

app = FastAPI(title="Kiln planner API")
CAPACITIES = [50, 100, 175, 200, 350, 500, 600]
_ACCOUNTING = ("biomass.biogenic_co2_zero_rated", "hydrogen.ef_t_per_t")
with open(os.path.join(os.path.dirname(__file__), "..", "config", "analysis.json")) as _fh:
    _STRESS = json.load(_fh)["finance_stress"]


class Controls(BaseModel):
    preset: Literal["imported", "domestic"] = "imported"
    capacity: int = 100
    utilization: float = Field(0.9, ge=0.5, le=0.95)
    coal_mode: Literal["solve", "specified"] = "solve"
    coal_rate: float | None = None
    whr: bool = False
    biomass: float = Field(0.0, ge=0.0, le=1.0)
    h2: float = Field(0.0, ge=0.0, le=1.0)
    oxygen: bool = False
    kiln_control: bool = False
    producer_gas: bool = False
    char_recycle: bool = False
    vfd: bool = False
    biogenic_zero: bool = True
    h2_source: Literal["green", "grey"] = "green"


def _clean(value):
    """JSON-safe copy: numpy scalars to Python, NaN and infinity to null."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (TypeError, ValueError):
            return str(value)
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return str(value)


def _overrides(c: Controls) -> tuple:
    defaults = Parameters()
    o: dict = {}
    if c.preset == "domestic":
        o.update(domestic_coal(defaults))
    o["coal.rate_mode"] = c.coal_mode
    if c.coal_mode == "specified":
        o["coal.rate_t_per_t_dri"] = float(
            c.coal_rate if c.coal_rate is not None else defaults["coal.rate_t_per_t_dri"])
    o["biomass.biogenic_co2_zero_rated"] = int(c.biogenic_zero)
    o["hydrogen.ef_t_per_t"] = (0.0 if c.h2_source == "green"
                                else float(defaults["hydrogen.grey_ef_t_per_t"]))
    return tuple(sorted(o.items()))


@lru_cache(maxsize=64)
def _solve(key: tuple, capacity: int, util: float):
    p = Parameters().with_overrides(dict(key))
    plant = build_plant(p, capacity, util)
    return p, plant, EnergyBalance(plant).calculate_balance(), MassBalance(plant).calculate_balance()


@lru_cache(maxsize=64)
def _checks(key: tuple, capacity: int, util: float) -> dict:
    result = run_checks(Parameters().with_overrides(dict(key)), capacity, util)
    result.pop("outputs", None)
    return result


@lru_cache(maxsize=32)
def _pathways(key: tuple, capacity: int, util: float) -> dict:
    _, plant, eb, _ = _solve(key, capacity, util)
    rows = []
    for r in pathway_grid(plant, eb):
        rows.append({
            "label": plain_route(r["label"]), "feasible": r["feasible"],
            "whr": r["whr"], "biomass": r["biomass_frac"], "h2": r["h2_frac"],
            "co2": r["co2"]["co2_total_t_per_t_dri"],
            "co2_cut": r["co2_reduction_frac"],
            "cost": r["econ"]["cost_per_t_dri"],
            "cost_delta": r["cost_delta_inr_per_t_dri"],
            "abatement": r["abatement_cost_inr_per_t_co2"],
            "capex": r["capex_inr"], "payback": r["payback_yr"],
            "co2_reduction_frac": r["co2_reduction_frac"],
            "cost_per_t_dri": r["econ"]["cost_per_t_dri"],
            "cost_delta_inr_per_t_dri": r["cost_delta_inr_per_t_dri"],
            "econ": {"cost_per_t_dri": r["econ"]["cost_per_t_dri"]},
            "_key": r["label"],
        })
    front = {r["_key"] for r in pareto_front(rows)}
    roadmap = []
    for t in CO2_TARGETS:
        best = least_cost(rows, t)
        roadmap.append({"target": t, **({k: best[k] for k in (
            "label", "co2_cut", "cost", "cost_delta", "abatement", "capex",
            "payback", "co2", "whr", "biomass", "h2")} if best else {"label": None})})
    feasible = [r for r in rows if r["feasible"]]
    p = Parameters().with_overrides(dict(key))
    out = [{k: v for k, v in r.items()
            if k in ("label", "feasible", "co2", "co2_cut", "cost", "cost_delta",
                     "abatement", "capex", "payback", "whr", "biomass", "h2")}
           | {"frontier": r["_key"] in front} for r in rows]
    return _clean({
        "rows": out, "roadmap": roadmap,
        "max_cut": max((r["co2_cut"] for r in feasible), default=0.0),
        "h2_breakeven": h2_breakeven_price(plant),
        "h2_price": p["hydrogen.price_inr_per_kg"],
    })


@app.get("/api/meta")
def meta() -> dict:
    d = Parameters()
    lo, hi = d.bounds("coal.rate_t_per_t_dri")
    ident = stamp()
    return _clean({
        "version": ident["model_version"],
        "fingerprint": ident["parameters_sha256"][:12],
        "capacities": CAPACITIES,
        "utilization": d["plant.utilization"],
        "biomass_max": d["biomass.max_substitution_frac"],
        "h2_max": d["hydrogen.max_substitution_frac"],
        "coal_rate": {"default": d["coal.rate_t_per_t_dri"], "min": lo, "max": hi},
        "targets": list(CO2_TARGETS),
        "calibration": d.calibration_plant,
    })


def _finance(p, base_econ: dict, econ: dict, capex: float, opex: float) -> dict | None:
    if capex <= 0 and opex <= 0 and abs(base_econ["cash_cost_per_t_dri"]
                                        - econ["cash_cost_per_t_dri"]) < 1e-9:
        return None
    project = retrofit_project(base_econ["cash_cost_per_t_dri"], base_econ["annual_output_t"],
                               econ["cash_cost_per_t_dri"], econ["annual_output_t"],
                               capex, opex, p)
    rates = financing_terms(p)
    saving = project["annual_saving_inr"]

    def stressed(label: str, capex_x: float = 1.0, saving_x: float = 1.0,
                 interest_add: float = 0.0) -> dict:
        shocked = saving - abs(saving) * (1.0 - saving_x)
        r = finance_project(shocked, opex, capex * capex_x, econ["annual_output_t"],
                            **(rates | {"interest_rate": rates["interest_rate"] + interest_add}))
        return {"case": label, "npv": r["npv_inr"], "irr": r["irr"],
                "irr_status": r["irr_status"], "payback": r["simple_payback_yr"]}

    cumulative, rows = 0.0, []
    for year, cf in zip(range(0, rates["life"] + 1), project["cash_flows_inr"]):
        cumulative += cf
        row = project["years"][year - 1] if year else {}
        rows.append({"year": year, "equity_cf": cf, "cumulative": cumulative,
                     "project_cf": project["project_cash_flows_inr"][year],
                     "ebitda": row.get("ebitda_inr", 0.0), "interest": row.get("interest_inr", 0.0),
                     "principal": row.get("principal_inr", 0.0), "tax": row.get("tax_inr", 0.0)})
    recon = reconciliation(econ["cash_cost_per_t_dri"], econ["annual_output_t"], capex, opex, p)
    return {
        "capex": capex, "annual_opex": opex, "annual_saving": saving,
        "equity": project["equity_inr"], "debt": project["debt_inr"],
        "npv": project["npv_inr"], "irr": project["irr"], "irr_status": project["irr_status"],
        "project_npv": project["project_npv_inr"], "project_irr": project["project_irr"],
        "project_irr_status": project["project_irr_status"],
        "payback": project["simple_payback_yr"],
        "discounted_payback": project["discounted_payback_yr"],
        "years": rows,
        "terms": {"debt_fraction": rates["debt_fraction"], "interest": rates["interest_rate"],
                  "tenor": rates["tenor"], "tax": rates["tax_rate"],
                  "escalation": rates["escalation"], "discount": rates["discount_rate"],
                  "life": rates["life"]},
        "stress": [stressed("As planned")] + [
            stressed(case["label"], case["capex_x"], case["saving_x"], case["interest_add"])
            for case in _STRESS["cases"]],
        "levelised": {"annuity": recon["annuity_cost_inr_per_t"],
                      "financed": recon["financed_levelised_cost_inr_per_t"]},
    }


@app.post("/api/scenario")
def scenario(c: Controls) -> dict:
    key = _overrides(c)
    p, plant, eb, mb = _solve(key, c.capacity, c.utilization)
    res = evaluate(plant, eb, c.whr, c.biomass, c.h2, oxygen=c.oxygen,
                   kiln_control=c.kiln_control, producer_gas=c.producer_gas,
                   char_recycle=c.char_recycle, vfd=c.vfd)
    co2, econ = res["co2"], res["econ"]
    base_key = tuple((k, v) for k, v in key if k not in _ACCOUNTING)
    base_plant = _solve(base_key, c.capacity, c.utilization)[1]
    base_co2 = CO2Model(base_plant).calculate_emissions()
    base_econ = EconomicsModel(base_plant).calculate_economics()
    checks = _checks(key, c.capacity, c.utilization)
    counts = checks["counts"]
    kiln = axial_profile(plant, eb)
    nhv = plant.nhv_coal_kj

    return _clean({
        "status": {
            "checks_pass": counts["PASS"],
            "checks_scored": counts["PASS"] + counts["FAIL"] + counts["WARN"],
            "checks_fail": counts["FAIL"],
            "mass_closure": mb["error_percent"], "mass_ok": mb["is_valid"],
            "mass_tolerance": mb["tolerance_percent"],
            "energy_closure": eb["closure_error_percent"], "energy_ok": eb["is_valid"],
            "feasible": res["feasible"],
            "reductant_ratio": res["reductant_carbon_ratio"],
            "coal_solved": bool(plant.coal_rate_solved),
        },
        "kpi": {
            "cost": econ["cost_per_t_dri"],
            "cash_cost": econ["cash_cost_per_t_dri"],
            "capex_charge": econ["capex_charge_per_t_dri"],
            "annual_output": econ["annual_output_t"],
            "output_tpd": plant.production_tpd,
            "co2_total": co2["co2_total_t_per_t_dri"],
            "co2_direct": co2["co2_direct_t_per_t_dri"],
            "co2_scope2": co2["co2_scope2_t_per_t_dri"],
            "co2_biogenic": co2.get("co2_biogenic_t_per_t_dri", 0.0),
            "coal_ef": co2["implied_coal_ef_t_per_t_coal"],
            "coal_rate": plant.coal_rate,
            "sec_gcal": eb["sec_gcal_per_t_dri"],
            "capex": res["capex_inr"],
            "grid_kwh": res["net_import_kwh_per_t_dri"],
            "export_kwh": res["export_kwh_per_t_dri"],
            "ore_rate": plant.ore_rate,
        },
        "base": {
            "cost": base_econ["cost_per_t_dri"],
            "co2_total": base_co2["co2_total_t_per_t_dri"],
            "co2_direct": base_co2["co2_direct_t_per_t_dri"],
            "co2_scope2": base_co2["co2_scope2_t_per_t_dri"],
            "co2_biogenic": base_co2.get("co2_biogenic_t_per_t_dri", 0.0),
            "coal_rate": base_plant.coal_rate,
            "grid_kwh": p["power.aux_kwh_per_t_dri"],
        },
        "flows": {
            "ore_t": plant.ore_rate, "coal_t": plant.coal_rate,
            "air_t": plant.air / 1000, "dolomite_t": plant.dolomite_mass / 1000,
            "waste_gas_t": plant.outputs["waste gas"] / 1000,
            "char_t": plant.outputs["char (dolochar)"] / 1000,
        },
        "streams": [{"name": stream(r["stream"]), "direction": r["direction"],
                     "kg": r["kg_per_t_dri"], "tpd": r["tpd"]}
                    for r in plant.stream_table()],
        "energy": [{"group": ENERGY_GROUPS.get(g, title_case(g)), "item": title_case(k),
                    "gcal": v * GCAL_PER_KJ, "pct": v / nhv * 100, "is_input": g == "in"}
                   for g, items in eb["items"].items() for k, v in items.items()],
        "elements": [{"element": title_case(e["element"]), "in": e["in_kg_per_t_dri"],
                      "out": e["out_kg_per_t_dri"], "error": e["error_percent"],
                      "ok": e["is_valid"]} for e in mb["element_balances"]],
        "waste_gas": [{"species": title_case(k), "kg": v}
                      for k, v in plant.waste_gas_composition.items()],
        "kiln": {
            "length_m": kiln["length_m"], "diameter_m": kiln["internal_diameter_m"],
            "incline_deg": kiln["inclination_deg"],
            "cells": [{"z": cell["z_mid_m"], "zone": cell["zone"],
                       "gas": cell["gas_temp_c"], "solid": cell["solid_temp_c"],
                       "met": 100 * cell["metallisation_frac"]} for cell in kiln["cells"]],
        },
        "cost_lines": [{"item": COST_LINES.get(k, title_case(k)), "inr": v}
                       for k, v in econ["breakdown_inr_per_t_dri"].items() if abs(v) > 0.5],
        "retrofits": [{"name": name,
                       "metrics": [{"label": title_case(k), "value": v}
                                   for k, v in r.items()
                                   if isinstance(v, (int, float, bool)) or hasattr(v, "item")]}
                      for name, r in res["retrofits"].items()],
        "finance": _finance(p, base_econ, econ, res["capex_inr"],
                            sum(r.get("annual_opex_inr", 0.0) for r in res["retrofits"].values())),
        "basis": res["warnings"],
        "checks": [{"key": r["key"], "label": title_case(r["label"]), "unit": r["unit"],
                    "model": r["model_value"], "min": r["min"], "max": r["max"],
                    "verdict": r["verdict"], "deviation": r["deviation_percent"],
                    "source": r["source"]} for r in checks["rows"]],
        "open_citations": [plain_parameter(k) for k in p.unsourced_keys()],
        "out_of_range": [{"parameter": plain_parameter(r["parameter"]), "value": r["value"],
                          "min": r["min"], "max": r["max"]} for r in p.out_of_range()],
    })


@app.post("/api/pathways")
def pathways(c: Controls) -> dict:
    return _pathways(_overrides(c), c.capacity, c.utilization)


@app.get("/api/parameters")
def parameters() -> dict:
    d = Parameters()
    return _clean({
        "summary": d.provenance_summary(),
        "rows": [{"name": plain_parameter(r["parameter"]), "key": r["parameter"],
                  "value": r["value"], "unit": r["unit"], "min": r["min"], "max": r["max"],
                  "status": r["status"], "source": r["source"]}
                 for r in d.provenance_rows()],
    })
