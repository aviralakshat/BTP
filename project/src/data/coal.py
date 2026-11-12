"""Coal composition: closure checks and dry-ash-free rescaling.

A coal analysis is a set of mass fractions, so both the ultimate analysis
(C, H, O, N, S plus ash and moisture) and the proximate analysis (fixed carbon,
volatile matter, ash, moisture) must each sum to one. Changing the ash without
changing anything else breaks that, and the model then charges the kiln for
carbon the coal cannot contain.
"""
from __future__ import annotations

from src.data.parameters import LATENT_HEAT_WATER_KJ_KG, Parameters

COAL_STREAMS = ("coal_feed", "coal_inj")
ULTIMATE = ("total_carbon", "hydrogen", "oxygen", "nitrogen", "sulphur",
            "ash", "moisture")
PROXIMATE = ("fixed_carbon", "volatile_matter", "ash", "moisture")
#: Components that belong to the dry, ash-free coal substance.
DAF_COMPONENTS = ("total_carbon", "hydrogen", "oxygen", "nitrogen", "sulphur",
                  "fixed_carbon", "volatile_matter")

#: Laboratory analyses are reported to 0.01 wt%, so a closure miss beyond
#: half a percent is a data-entry error, not rounding.
CLOSURE_TOLERANCE = 0.005


class InconsistentInputError(ValueError):
    """An input set that cannot describe a physical material."""


def closure(params: Parameters, stream: str) -> dict:
    """Sum of the ultimate and proximate analyses of one coal stream."""
    return {
        "ultimate": sum(params[f"{stream}.{k}"] for k in ULTIMATE),
        "proximate": sum(params[f"{stream}.{k}"] for k in PROXIMATE),
    }


def check_composition(params: Parameters) -> None:
    """Raise if either coal analysis does not sum to one."""
    problems = []
    for stream in COAL_STREAMS:
        for basis, total in closure(params, stream).items():
            if abs(total - 1.0) > CLOSURE_TOLERANCE:
                problems.append(f"{stream} {basis} analysis sums to "
                                f"{total * 100:.2f}%")
        if params[f"{stream}.fixed_carbon"] > params[f"{stream}.total_carbon"]:
            problems.append(f"{stream} fixed carbon exceeds total carbon")
    if problems:
        raise InconsistentInputError(
            "Coal analysis is not a physical material: " + "; ".join(problems)
            + ". Rebuild it with coal.daf_rescale() rather than editing one "
            "component.")


def daf_rescale(params: Parameters, stream: str, ash: float,
                moisture: float | None = None,
                nhv_kj_kg: float | None = None) -> dict:
    """Overrides for a coal with new ash (and moisture) on the same organic basis.

    The dry, ash-free composition of the reference coal is held fixed and
    diluted by the new ash and moisture, so both analyses still close. The
    heating value is either supplied (when the new coal has a measured one) or
    scaled on the same dry, ash-free basis.
    """
    a0, m0 = params[f"{stream}.ash"], params[f"{stream}.moisture"]
    m = m0 if moisture is None else moisture
    if not 0.0 <= ash < 1.0 or not 0.0 <= m < 1.0 or ash + m >= 1.0:
        raise InconsistentInputError(
            f"Ash {ash} plus moisture {m} leaves no combustible coal.")
    factor = (1.0 - ash - m) / (1.0 - a0 - m0)
    out = {f"{stream}.{k}": params[f"{stream}.{k}"] * factor
           for k in DAF_COMPONENTS}
    out[f"{stream}.ash"] = ash
    out[f"{stream}.moisture"] = m
    if nhv_kj_kg is None:
        # Net heating value already carries the moisture's latent heat, so
        # add it back before diluting the organic part and take it off again.
        nhv_daf_part = (params[f"{stream}.nhv_kj_kg"]
                        + LATENT_HEAT_WATER_KJ_KG * m0)
        nhv_kj_kg = nhv_daf_part * factor - LATENT_HEAT_WATER_KJ_KG * m
    out[f"{stream}.nhv_kj_kg"] = nhv_kj_kg
    return out
