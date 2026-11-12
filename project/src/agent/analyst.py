"""Answers assembled from tool results. No language-model API is called.

The question picks a tool. The sentences quote that tool. A number that is
not in the tool result, and not in the question, fails the grounding check
and the answer is marked unverified.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.agent import tools
from src.agent.grounding import ungrounded
from src.agent.prompts import SYSTEM_PROMPT

_MESSAGE_CAP = 12


def _money(value: float) -> str:
    return f"{value:,.0f}"


def _pct(fraction: float) -> str:
    return f"{100.0 * fraction:.0f}"


def answer(question: str, *, capacity_tpd: float = 100,
           utilization: float = 0.9, preset: str = "imported",
           overrides: dict | None = None, turns_so_far: int = 0) -> dict:
    if turns_so_far >= _MESSAGE_CAP:
        return {
            "text": "This session has reached its question limit. Start a new one to continue.",
            "tools": [],
            "grounded": True,
            "ungrounded": [],
            "refused": False,
        }
    text, calls = _route(question, capacity_tpd, utilization, preset, overrides)
    missing = ungrounded(text, [item["result"] for item in calls], question)
    return {
        "text": text,
        "tools": calls,
        "grounded": not missing,
        "ungrounded": missing,
        "refused": any(item["name"] == "refuse" for item in calls),
        "system_prompt": SYSTEM_PROMPT,
    }


def _route(question: str, capacity: float, utilization: float, preset: str,
           overrides: dict | None):
    q = question.lower()
    if any(phrase in q for phrase in ("change the parameter", "edit parameter",
                                      "set the coal price", "overwrite parameters",
                                      "update parameters.json")):
        result = {"refused": True, "wrote_files": False}
        text = ("I cannot change the parameter file. "
                "A change stays in this session only, and only from the sidebar.")
        return text, [{"name": "refuse", "result": result}]
    if any(phrase in q for phrase in ("invent a citation", "make up a source",
                                      "fake a reference")):
        result = {"refused": True}
        text = "I will not invent a citation. A number without a source stays marked as needing one."
        return text, [{"name": "refuse", "result": result}]
    if "60" in q and ("cut" in q or "target" in q or "reach" in q or "%" in q):
        result = tools.find_least_cost(0.60, capacity, utilization, preset, overrides)
        if result["reachable"]:
            text = (f"The cheapest route to a 60% cut is {result['label']}. "
                    f"It cuts {_pct(result['co2_reduction_frac'])}% of CO2 and costs "
                    f"INR {_money(result['cost_inr_per_t'])} per tonne. "
                    f"Model {result['model_version']}.")
        else:
            text = (f"A 60% CO2 cut is not reachable. {result['reason']} "
                    f"Model {result['model_version']}.")
        return text, [{"name": "find_least_cost", "result": result}]
    if "least cost" in q or "cheapest" in q:
        target = 0.20
        for value, label in ((0.50, "50%"), (0.40, "40%"), (0.30, "30%"),
                             (0.20, "20%"), (0.10, "10%")):
            if label in q:
                target = value
                break
        result = tools.find_least_cost(target, capacity, utilization, preset, overrides)
        if not result["reachable"]:
            text = f"A {_pct(target)}% cut is not reachable. {result['reason']}"
        else:
            text = (f"The cheapest route to a {_pct(target)}% cut is {result['label']}. "
                    f"It cuts {_pct(result['co2_reduction_frac'])}% of CO2 and costs "
                    f"INR {_money(result['cost_inr_per_t'])} per tonne. "
                    f"Model {result['model_version']}.")
        return text, [{"name": "find_least_cost", "result": result}]
    if ("break-even" in q or "breakeven" in q
            or ("break" in q and "hydrogen" in q)):
        result = tools.hydrogen_breakeven(capacity, utilization, preset, overrides)
        text = (f"Hydrogen breaks even with coal, on heating value alone, at "
                f"INR {_money(result['breakeven_inr_per_kg'])} per kg. "
                f"The cited price is INR {_money(result['cited_price_inr_per_kg'])} per kg. "
                f"{result['note']}")
        return text, [{"name": "hydrogen_breakeven", "result": result}]
    if "domestic" in q:
        result = tools.compare_presets(capacity, utilization)
        domestic = result["domestic"]
        text = (f"Domestic coal solves at {domestic['coal_t_per_t']:.3f} t per t DRI "
                f"and INR {_money(domestic['cost_inr_per_t'])} per tonne. "
                f"It is Dey's analysis diluted to higher ash, not a measured domestic coal. "
                f"It is not a validation pass.")
        return text, [{"name": "compare_presets", "result": result}]
    if "validation" in q or "literature check" in q or "how many checks" in q:
        result = tools.run_validation(capacity, utilization, preset, overrides)
        counts = result["counts"]
        text = (f"{counts['PASS']} checks pass, {counts['FAIL']} fail, "
                f"{counts['WARN']} warn and {counts['INFO']} are informational. "
                f"Metallisation is an input, so a pass on it is not evidence. "
                f"Model {result['model_version']}.")
        return text, [{"name": "run_validation", "result": result}]
    if ("closure" in q or "mass balance" in q or "energy balance" in q
            or "specific energy" in q):
        result = tools.explain_closure(capacity, utilization, preset, overrides)
        text = (f"Mass closure is {result['mass_closure_percent']:.2f}%. "
                f"Energy closure is {result['energy_closure_percent']:.4f}%. "
                f"Specific energy is {result['sec_gcal_per_t']:.3f} Gcal per tonne.")
        return text, [{"name": "explain_closure", "result": result}]
    if "parameter" in q or "citation" in q or "source of" in q or "unsourced" in q:
        if "unsourced" in q or "need a citation" in q or "needs a citation" in q:
            result = tools.list_unsourced()
            text = (f"{result['count']} parameters still need a citation: "
                    + ", ".join(result["parameters"]) + ".")
            return text, [{"name": "list_unsourced", "result": result}]
        query = "econ.coal_price_inr_per_t"
        for token in ("coal price", "hydrogen price", "discount", "kiln length", "tax"):
            if token in q:
                query = {"coal price": "coal_price", "hydrogen price": "hydrogen.price",
                         "discount": "discount_rate", "kiln length": "kiln.length",
                         "tax": "tax_rate"}[token]
        result = tools.get_parameter(query)
        if not result["found"]:
            text = f"No parameter matches {result['query']}."
        else:
            text = (f"{result['parameter']} is {result['value']} {result['unit']}. "
                    f"Status: {result['status']}. Source: {result['source']}")
        return text, [{"name": "get_parameter", "result": result}]
    if "kiln" in q or "metallisation" in q or "metallization" in q:
        result = tools.kiln_summary()
        text = (f"The kiln in the axial view is {result['length_m']:.0f} m long and "
                f"{result['internal_diameter_m']:.2f} m inside, inclined at "
                f"{result['inclination_deg']:.1f} degrees. "
                f"Discharge metallisation is {_pct(result['discharge_metallisation_frac'])}%. "
                f"Metallisation is an input. {result['note']}")
        return text, [{"name": "kiln_summary", "result": result}]
    if "npv" in q or "irr" in q or "equity" in q or "payback" in q:
        result = tools.waste_heat_finance(capacity, utilization, preset, overrides)
        if result["irr"] is not None:
            irr_text = f"The equity IRR is {_pct(result['irr'])}%. "
        elif result["irr_status"] == "multiple":
            irr_text = "The equity cash flow has more than one IRR, so none is quoted. "
        elif result["irr_status"] == "no_investment":
            irr_text = "There is no equity outlay, so a rate of return does not apply. "
        else:
            irr_text = "The equity cash flow never recovers its outlay, so there is no IRR. "
        if result["simple_payback_yr"] is not None:
            payback_text = f"Equity payback is {result['simple_payback_yr']:.1f} years. "
        else:
            payback_text = "Equity does not pay back within the project life. "
        text = (f"Waste heat recovery has an equity NPV of INR {_money(result['npv_inr'])}. "
                f"{irr_text}{payback_text}"
                f"This is the equity cheque, after debt service. {result['note']}")
        return text, [{"name": "waste_heat_finance", "result": result}]
    if any(phrase in q for phrase in ("tornado", "sensitive", "monte carlo",
                                      "what moves the cost")):
        result = {"computed_here": False}
        text = ("That ranking is on the Uncertainty tab. "
                "This chat does not recompute the sweep.")
        return text, [{"name": "uncertainty_tab", "result": result}]
    result = tools.run_scenario(capacity, utilization, preset, overrides=overrides)
    text = (f"At {result['capacity_tpd']:.0f} TPD, {result['preset']} coal, "
            f"the plant uses {result['coal_t_per_t']:.3f} t coal and "
            f"{result['ore_t_per_t']:.3f} t ore per t DRI, "
            f"emits {result['co2_total_t_per_t']:.3f} t CO2 per t, and costs "
            f"INR {_money(result['cost_inr_per_t'])} per tonne. "
            f"Mass closure is {result['mass_closure_percent']:.2f}%. "
            f"Model {result['model_version']}.")
    if result["unsourced"]:
        text += " Still without a citation: " + ", ".join(result["unsourced"][:5]) + "."
    return text, [{"name": "run_scenario", "result": result}]
