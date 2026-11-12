"""Plant construction, including the coal-rate solver.

Kept separate from baseline.py because solving for the coal rate needs the energy
balance, and the energy balance needs a plant -- putting the solver here keeps
baseline.py free of a circular import.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.data.coal import InconsistentInputError
from src.data.parameters import Parameters
from src.models.baseline import BaselinePlant
from src.models.energy_balance import EnergyBalance
from src.version import stamp


class CoalRateNotSolvedError(ValueError):
    """The energy balance has no root in the coal-rate search range."""


def _residual(params: Parameters, coal_rate: float,
              capacity_tpd: float, utilization: float) -> float:
    try:
        plant = BaselinePlant(
            params.with_overrides({"coal.rate_t_per_t_dri": coal_rate}),
            capacity_tpd, utilization)
    except InconsistentInputError:
        raise
    except ValueError:
        # Too little coal to supply the carbon or the inert solids the rest of
        # the stream table demands. That is the far-negative end of the
        # residual curve, so report it as such and let the bisection move up.
        return -1e12
    return EnergyBalance(plant).calculate_balance()["residual_kj_per_t_dri"]


def solve_coal_rate(params: Parameters, capacity_tpd: float, utilization: float,
                    lo: float = 0.60, hi: float = 2.50,
                    tol: float = 1e-4) -> dict:
    """Find the coal rate at which the kiln energy balance closes.

    Raising the coal rate adds proportionally to both sides of the ledger, but
    the endothermic reduction duty and the DRI sensible heat are fixed per tonne
    of product, so the residual is monotonic in coal rate and a bisection is
    safe.

    Returns a dict rather than a bare float so callers can see whether the
    solve actually bracketed a root.
    """
    f_lo, f_hi = (_residual(params, lo, capacity_tpd, utilization),
                  _residual(params, hi, capacity_tpd, utilization))
    if f_lo * f_hi > 0:
        return {"converged": False, "coal_rate": params["coal.rate_t_per_t_dri"],
                "residual_kj": f_lo, "bracket": (lo, hi),
                "reason": "energy residual does not change sign over the search "
                          "range; coal quality or loss fractions are inconsistent"}
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = _residual(params, mid, capacity_tpd, utilization)
        if abs(f_mid) < 1.0 or (hi - lo) < tol:
            break
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    mid = 0.5 * (lo + hi)
    return {"converged": True, "coal_rate": mid,
            "residual_kj": _residual(params, mid, capacity_tpd, utilization),
            "bracket": (lo, hi)}


def build_plant(params: Parameters | None = None,
                capacity_tpd: float | None = None,
                utilization: float | None = None) -> BaselinePlant:
    """Build a plant, honouring coal.rate_mode.

    'solve'      -- coal rate is derived by closing the energy balance.
    'specified'  -- coal rate is taken from the config as given.
    """
    params = params or Parameters()
    capacity_tpd = (capacity_tpd if capacity_tpd is not None
                    else params["plant.capacity_tpd"])
    utilization = (utilization if utilization is not None
                   else params["plant.utilization"])

    if params["coal.rate_mode"] != "solve":
        plant = BaselinePlant(params, capacity_tpd, utilization)
        plant.coal_rate_solved = None
        return _identify(plant, params)

    sol = solve_coal_rate(params, capacity_tpd, utilization)
    if not sol["converged"]:
        raise CoalRateNotSolvedError(
            f"No coal rate between {sol['bracket'][0]} and {sol['bracket'][1]} "
            f"t/t closes the kiln energy balance: {sol['reason']}.")
    plant = BaselinePlant(
        params.with_overrides({"coal.rate_t_per_t_dri": sol["coal_rate"]}),
        capacity_tpd, utilization)
    plant.coal_rate_solved = sol
    return _identify(plant, params)


def _identify(plant: BaselinePlant, params: Parameters) -> BaselinePlant:
    meta = stamp(params.path)
    plant.model_version = meta["model_version"]
    plant.parameters_sha256 = meta["parameters_sha256"]
    return plant


if __name__ == "__main__":
    p = Parameters()
    plant = build_plant(p, 100, 0.9)
    eb = EnergyBalance(plant).calculate_balance()
    print(f"coal.rate_mode          = {p['coal.rate_mode']}")
    print(f"solved coal rate        = {plant.coal_rate:.4f} t-coal/t-DRI")
    print(f"config (TERI, imported) = {p['coal.rate_t_per_t_dri']:.4f}")
    print(f"energy closure error    = {eb['closure_error_percent']:.4f}%")
    print(f"SEC                     = {eb['sec_gcal_per_t_dri']:.3f} Gcal/t DRI")
    print(f"ore rate                = {plant.ore_rate:.4f} t-ore/t-DRI")
    print(f"reductant carbon ratio  = {plant.reductant_carbon_ratio:.3f}")
