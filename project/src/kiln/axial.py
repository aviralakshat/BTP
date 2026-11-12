"""Axial reconstruction of the kiln energy balance. Not a kinetic model.

Dey et al. (2015) give the kiln that this balance was built on: 80 m long,
4.55 m inside, inclined at 2.5°, the first half a preheating zone and the
second half a reduction zone, solids held at 1020 °C, waste gas 1170 °C at
the discharge end and 900 °C at the feed end. They plot gas temperature, bed
temperature and metallisation along the kiln in Figure 4. The figure is not
a table, the rotation speed is not stated, and no rate constant is given.
Residence time and metallisation are therefore not predicted.

What this module does is place the terms of the already-closed kiln ledger
onto that geometry.

  * Feed coal enters at the feed end. Injection coal enters at the discharge
    end, which is where Dey says it is blown in.
  * Moisture and devolatilisation sit in the preheating half. Dey describes
    that half as the section where the charge is heated, and the volatile
    matter leaves with the gas toward the feed end.
  * Reduction sits in the reduction half. Dey says reduction starts there.
  * Dolomite calcination sits in the reduction half. Dey lists it among the
    duties of the heat, and does not name the zone. It is placed where the
    bed is at the reaction temperature.
  * Solids leave at the discharge end. Waste gas, flue dust and the unburnt
    volatiles leave at the feed end.
  * Shell loss is spread evenly along the length. Dey does not give a
    distribution.

Gas temperature is a straight line between the two measured ends. Solids
temperature is the 1020 °C Dey says is maintained. Metallisation is zero in
the preheating half and a straight line up to the measured product value at
the discharge. That line is a drawing rule, not a rate.

Cells do not pass heat to their neighbours. A cell residual is the heat that
would have to move along the kiln for that cell to close. It is reported, not
cancelled. The residuals of all the cells sum to the kiln residual.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.baseline import BaselinePlant


def _cells(p) -> list[dict]:
    n = int(p["kiln.n_cells"])
    length = p["kiln.length_m"]
    dz = length / n
    preheat_end = p["kiln.preheat_length_frac"] * length
    gas_feed = p["kiln.waste_gas_temp_c"]
    gas_discharge = p["kiln.gas_temp_discharge_c"]
    solid = p["dri.discharge_temp_c"]
    rows = []
    for i in range(n):
        z_up = i * dz
        z_down = (i + 1) * dz
        z_mid = 0.5 * (z_up + z_down)
        zone = "preheat" if z_down <= preheat_end + 1e-9 else "reduction"
        # Gas flows from the discharge toward the feed, so the hot end is z = L.
        gas = gas_feed + (gas_discharge - gas_feed) * (z_mid / length)
        rows.append({
            "index": i,
            "z_mid_m": z_mid,
            "z_down_m": z_down,
            "zone": zone,
            "gas_temp_c": gas,
            "solid_temp_c": solid,
            "in": {},
            "out": {},
        })
    return rows


def _add(cells: list[dict], side: str, indexes: list[int], name: str, total: float) -> None:
    if not indexes:
        return
    share = total / len(indexes)
    for i in indexes:
        cells[i][side][name] = cells[i][side].get(name, 0.0) + share


def axial_profile(plant: BaselinePlant, energy: dict) -> dict:
    """Place the kiln ledger on Dey's geometry. `energy` is the kiln balance."""
    p = plant.p
    cells = _cells(p)
    preheat = [c["index"] for c in cells if c["zone"] == "preheat"]
    reduction = [c["index"] for c in cells if c["zone"] == "reduction"]
    feed, discharge = [0], [len(cells) - 1]
    every = [c["index"] for c in cells]

    feed_nhv = plant.coal_feed * p["coal_feed.nhv_kj_kg"]
    inj_nhv = plant.coal_inj * p["coal_inj.nhv_kj_kg"]
    coal_mass = plant.coal_feed + plant.coal_inj
    feed_share = plant.coal_feed / coal_mass if coal_mass else 0.0
    coal_sensible = energy["items"]["in"]["sensible heat in coal"]

    items = energy["items"]
    _add(cells, "in", feed, "feed coal", feed_nhv)
    _add(cells, "in", discharge, "injection coal", inj_nhv)
    _add(cells, "in", feed, "sensible heat in ore", items["in"]["sensible heat in ore"])
    _add(cells, "in", feed, "sensible heat in feed coal", coal_sensible * feed_share)
    _add(cells, "in", discharge, "sensible heat in injection coal",
         coal_sensible * (1.0 - feed_share))

    chemical = items["chemical energy out (unburnt)"]
    process = items["endothermic process demand"]
    sensible = items["sensible heat out"]

    _add(cells, "out", preheat, "evaporation of feed moisture",
         process["evaporation of feed moisture"])
    _add(cells, "out", preheat, "coal devolatilisation", process["coal devolatilisation"])
    _add(cells, "out", feed, "volatile carbon to ABC", chemical["volatile carbon to ABC"])
    _add(cells, "out", feed, "volatile hydrogen to ABC", chemical["volatile hydrogen to ABC"])
    _add(cells, "out", feed, "CO slip to ABC", chemical["CO slip to ABC"])
    _add(cells, "out", feed, "waste gas", sensible["waste gas"])
    _add(cells, "out", feed, "flue dust", sensible["flue dust"])
    _add(cells, "out", feed, "carbon in flue dust (lost)", chemical["carbon in flue dust (lost)"])

    _add(cells, "out", reduction, "reduction of iron oxides", process["reduction of iron oxides"])
    _add(cells, "out", reduction, "dolomite calcination", process["dolomite calcination"])
    for name in ("DRI", "char (dolochar)", "free ash to cooler",
                 "unreduced fines", "calcined flux"):
        _add(cells, "out", discharge, name, sensible[name])
    _add(cells, "out", discharge, "carbon in char (lost)", chemical["carbon in char (lost)"])
    _add(cells, "out", discharge, "carbon in DRI (lost)", chemical["carbon in DRI (lost)"])
    _add(cells, "out", every, "radiation and shell loss",
         items["losses"]["radiation and shell loss"])

    length = p["kiln.length_m"]
    preheat_end = p["kiln.preheat_length_frac"] * length
    met_end = plant.metallization
    total_in = 0.0
    total_out = 0.0
    for cell in cells:
        cin = sum(cell["in"].values())
        cout = sum(cell["out"].values())
        cell["energy_in_kj"] = cin
        cell["energy_out_kj"] = cout
        cell["residual_kj"] = cin - cout
        total_in += cin
        total_out += cout
        if cell["z_down_m"] <= preheat_end + 1e-9:
            cell["metallisation_frac"] = 0.0
        else:
            cell["metallisation_frac"] = met_end * (
                (cell["z_down_m"] - preheat_end) / (length - preheat_end))

    return {
        "cells": cells,
        "length_m": length,
        "internal_diameter_m": p["kiln.internal_diameter_m"],
        "external_diameter_m": p["kiln.external_diameter_m"],
        "inclination_deg": p["kiln.inclination_deg"],
        "preheat_length_frac": p["kiln.preheat_length_frac"],
        "energy_in_kj": total_in,
        "energy_out_kj": total_out,
        "residual_kj": total_in - total_out,
        "kiln_residual_kj": energy["residual_kj_per_t_dri"],
        "metallisation_is_prescribed": True,
        "discharge_metallisation_frac": cells[-1]["metallisation_frac"],
        "mode": "planning",
    }
