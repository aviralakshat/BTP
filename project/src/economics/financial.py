"""Project cash flow beside the capital-recovery cost per tonne.

The cost per tonne annualises capital with a recovery factor and stops there.
This module writes the same project as a cash flow: equity cheque, term loan,
interest, book depreciation, tax depreciation, and tax. The terms are the
Bureau of Energy Efficiency 2011 waste-heat project on a 100 TPD kiln
(Annexure 4), and the discount rate is the 8% weighted average cost of capital
already used for the annuity (Hall et al. 2025).

Two results are deliberately different, and the reconciliation says why.

  * Annuity cost. Pre-tax, all equity, no escalation. Capital becomes
    CRF × capex. This is the number on the Economics tab.
  * Financed cost. After tax, 75% debt, operating cost escalated at 5%.
    The equity cheque is what is discounted.

A retrofit is valued on its incremental cash flow (what the plant stops
spending, minus the new operating cost). The kiln itself has no capital cost
in this model, so there is no whole-plant net present value and none is
reported. Levelised cost without a selling price does not generate a tax
bill, so the depreciation shield appears only in the incremental project,
where the saving is the income.

Each project is reported twice: the equity view (after debt service, the
BEE structure) and the unlevered project view (full capital at year 0, no
debt). Tax losses are carried forward, not refunded and not lost. An IRR is
quoted only when the cash flow has exactly one; otherwise `irr_status` says
whether there is none or several.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.economics.economics import capital_recovery_factor


def loan_schedule(principal: float, interest_rate: float, tenor: int,
                  life: int) -> list[dict]:
    """Equal annual principal. A tenor longer than the project life is repaid
    with the balance in the last year."""
    if principal <= 0 or tenor <= 0:
        return [{"year": year, "opening": 0.0, "interest": 0.0,
                 "principal": 0.0, "closing": 0.0} for year in range(1, life + 1)]
    instalment = principal / tenor
    balance = principal
    rows = []
    for year in range(1, life + 1):
        opening = balance
        interest = opening * interest_rate
        if year < min(tenor, life):
            paid = min(instalment, balance)
        else:
            paid = balance if year == min(tenor, life) else 0.0
        balance = max(0.0, balance - paid)
        rows.append({"year": year, "opening": opening, "interest": interest,
                     "principal": paid, "closing": balance})
    return rows


def book_depreciation(capex: float, rate: float, life: int) -> list[float]:
    """Straight line at `rate` of original cost, and not past the cost."""
    remaining = capex
    charges = []
    for _ in range(life):
        charge = min(max(capex * rate, 0.0), remaining)
        charges.append(charge)
        remaining -= charge
    return charges


def wdv_depreciation(capex: float, rate: float, life: int) -> list[float]:
    """Written-down value: `rate` of the opening balance each year."""
    opening = capex
    charges = []
    for _ in range(life):
        charge = max(opening * rate, 0.0)
        charges.append(charge)
        opening -= charge
    return charges


def _npv(cashflows: list[float], rate: float) -> float:
    factor = 1.0 / (1.0 + rate)
    total = 0.0
    for cf in reversed(cashflows):
        total = total * factor + cf
    return total


def _irr_grid() -> list[float]:
    """Rates from -90% to 100% in 1% steps, then geometric to 100,000%.

    A small equity cheque against a large saving has an equity IRR far above
    any fixed bracket, so the upper end is open rather than capped at 500%.
    """
    fine = [-0.9 + 0.01 * i for i in range(191)]
    coarse = [1.0 * 1.25 ** k for k in range(1, 32)]
    return fine + coarse


def _irr_roots(cashflows: list[float]) -> list[float]:
    """Every rate on the grid where the net present value changes sign,
    each refined by bisection."""
    if not any(cashflows):
        return []

    def value(rate: float) -> float:
        return _npv(cashflows, rate)

    grid = _irr_grid()
    values = [value(r) for r in grid]
    roots = []
    for (lo, flo), (hi, fhi) in zip(zip(grid, values), zip(grid[1:], values[1:])):
        if flo == 0.0:
            roots.append(lo)
            continue
        if flo * fhi > 0.0:
            continue
        while hi - lo > 1e-9 * (1.0 + abs(lo)):
            mid = 0.5 * (lo + hi)
            fmid = value(mid)
            if flo * fmid <= 0.0:
                hi, fhi = mid, fmid
            else:
                lo, flo = mid, fmid
        roots.append(0.5 * (lo + hi))
    return roots


def _irr_result(cashflows: list[float]) -> tuple[float | None, str]:
    """The IRR and why it is or is not reported.

    `unique` is the only status with a number. `no_investment` means there is
    no outlay at year 0, so a rate of return is undefined. `none` means the
    cash flow never recovers its outlay at any rate. `multiple` means the
    series changes sign more than once and has several IRRs, so none of them
    is quoted and the net present value is the decision measure.
    """
    if cashflows and cashflows[0] == 0.0:
        return None, "no_investment"
    roots = _irr_roots(cashflows)
    if len(roots) == 1:
        return roots[0], "unique"
    if not roots:
        return None, "none"
    return None, "multiple"


def _irr(cashflows: list[float]) -> float | None:
    return _irr_result(cashflows)[0]


def _payback(cashflows: list[float]) -> float | None:
    """Years from the cheque until the cumulative cash flow turns non-negative.

    The crossing year is interpolated. Year 0 is the cheque, so a recovery
    during year 3 is a payback of between 2 and 3 years.
    """
    cumulative = 0.0
    for t, cf in enumerate(cashflows):
        previous = cumulative
        cumulative += cf
        if t > 0 and previous < 0.0 <= cumulative:
            step = cumulative - previous
            return (t - 1) + ((-previous) / step if step else 0.0)
    return None


def _tax_with_carry_forward(taxable: float, losses: float,
                            tax_rate: float) -> tuple[float, float]:
    """Tax for one year and the loss pool carried into the next.

    A loss is not refunded. It is set off against later profit with no
    expiry: the losses here come from tax depreciation, and unabsorbed
    depreciation carries forward without limit under s.32(2) of the Income
    Tax Act, 1961.
    """
    if taxable <= 0.0:
        return 0.0, losses - taxable
    set_off = min(losses, taxable)
    return tax_rate * (taxable - set_off), losses - set_off


def _discounted(cashflows: list[float], rate: float) -> list[float]:
    return [cf / (1.0 + rate) ** t for t, cf in enumerate(cashflows)]


def finance_project(flat_income_inr: float, escalating_cost_inr: float,
                    capex_inr: float, annual_output_t: float, *,
                    life: int, discount_rate: float, tax_rate: float,
                    book_rate: float, wdv_rate: float, debt_fraction: float,
                    interest_rate: float, tenor: int,
                    escalation: float, working_capital_frac: float,
                    flat_cost_inr: float = 0.0) -> dict:
    """Equity cash flow of one project.

    Income and the ordinary operating cost are not escalated. Only
    `escalating_cost_inr` grows, which is how the BEE report treats
    maintenance against a power saving that stays put. Levelised cost is
    filled in when income is zero, so the stream is a cost and not a mix.
    """
    if not 0.0 <= debt_fraction <= 1.0:
        raise ValueError(f"Debt fraction {debt_fraction} is outside 0 to 1.")
    if not 0.0 <= tax_rate < 1.0:
        raise ValueError(f"Tax rate {tax_rate} is outside 0 to 1.")
    if discount_rate <= -1.0 or interest_rate < 0.0:
        raise ValueError("Discount rate must exceed -100% and interest must be non-negative.")
    if capex_inr < 0.0:
        raise ValueError(f"Capital cost {capex_inr} is negative.")
    life = int(life)
    tenor = int(tenor)
    if life < 1:
        raise ValueError(f"Project life {life} must be at least one year.")
    debt = capex_inr * debt_fraction
    equity = capex_inr - debt
    working = working_capital_frac * escalating_cost_inr
    schedule = loan_schedule(debt, interest_rate, tenor, life)
    books = book_depreciation(capex_inr, book_rate, life)
    wdvs = wdv_depreciation(capex_inr, wdv_rate, life)

    rows = []
    equity_cf = [-(equity + working)]
    project_cf = [-(capex_inr + working)]
    losses = 0.0
    project_losses = 0.0
    for year in range(1, life + 1):
        opex = escalating_cost_inr * (1.0 + escalation) ** (year - 1)
        ebitda = flat_income_inr - flat_cost_inr - opex
        interest = schedule[year - 1]["interest"]
        principal = schedule[year - 1]["principal"]
        book = books[year - 1]
        wdv = wdvs[year - 1]
        tax, losses = _tax_with_carry_forward(ebitda - interest - wdv, losses, tax_rate)
        project_tax, project_losses = _tax_with_carry_forward(
            ebitda - wdv, project_losses, tax_rate)
        cash = ebitda - interest - tax - principal
        project_cash = ebitda - project_tax
        if year == life:
            cash += working
            project_cash += working
        equity_cf.append(cash)
        project_cf.append(project_cash)
        rows.append({
            "year": year,
            "ebitda_inr": ebitda,
            "interest_inr": interest,
            "principal_inr": principal,
            "book_depreciation_inr": book,
            "tax_depreciation_inr": wdv,
            "tax_inr": tax,
            "tax_losses_carried_inr": losses,
            "equity_cash_flow_inr": cash,
            "project_cash_flow_inr": project_cash,
        })

    present_output = sum(annual_output_t / (1.0 + discount_rate) ** t
                         for t in range(1, life + 1))
    levelised = None
    if flat_income_inr == 0.0 and present_output:
        cost_cf = [-cf for cf in equity_cf]
        cost_cf[0] = equity + working
        levelised = _npv(cost_cf, discount_rate) / present_output

    irr, irr_status = _irr_result(equity_cf)
    project_irr, project_irr_status = _irr_result(project_cf)
    return {
        "equity_inr": equity,
        "debt_inr": debt,
        "working_capital_inr": working,
        "cash_flows_inr": equity_cf,
        "project_cash_flows_inr": project_cf,
        "years": rows,
        "npv_inr": _npv(equity_cf, discount_rate),
        "irr": irr,
        "irr_status": irr_status,
        "project_npv_inr": _npv(project_cf, discount_rate),
        "project_irr": project_irr,
        "project_irr_status": project_irr_status,
        "simple_payback_yr": _payback(equity_cf),
        "discounted_payback_yr": _payback(_discounted(equity_cf, discount_rate)),
        "levelised_cost_inr_per_t": levelised,
        "discount_rate": discount_rate,
        "life_yr": life,
    }


def financing_terms(p, **overrides) -> dict:
    values = {
        "life": int(p["econ.project_life_yr"]),
        "discount_rate": p["econ.discount_rate"],
        "tax_rate": p["econ.tax_rate"],
        "book_rate": p["econ.book_depreciation_rate"],
        "wdv_rate": p["econ.it_depreciation_rate"],
        "debt_fraction": p["econ.debt_fraction"],
        "interest_rate": p["econ.interest_rate"],
        "tenor": int(p["econ.loan_tenor_yr"]),
        "escalation": p["econ.opex_escalation_rate"],
        "working_capital_frac": p["econ.working_capital_frac_of_opex"],
    }
    values.update(overrides)
    return values


def retrofit_project(base_cash_per_t: float, base_output_t: float,
                     scenario_cash_per_t: float, scenario_output_t: float,
                     capex_inr: float, annual_opex_inr: float, p,
                     **overrides) -> dict:
    """Incremental project: the per-tonne operating saving on the scenario's output.

    Totals at two different outputs are not compared. With no selling price,
    a retrofit that raises output (oxygen enrichment) would otherwise be
    charged for the extra tonnes it makes as if they were a cost overrun.
    `base_output_t` is kept for the call signature and is not used.
    """
    saving = (base_cash_per_t - scenario_cash_per_t) * scenario_output_t
    result = finance_project(saving, annual_opex_inr, capex_inr,
                             scenario_output_t, **financing_terms(p, **overrides))
    result["annual_saving_inr"] = saving
    result["annual_opex_inr"] = annual_opex_inr
    result["capex_inr"] = capex_inr
    return result


def levelised_cost(cash_cost_per_t: float, annual_output_t: float,
                   capex_inr: float, annual_opex_inr: float, p,
                   **overrides) -> dict:
    """Levelised operating and capital cost per tonne, with no selling price.

    Tax is zero in the result whenever the project has only costs, because a
    loss is not modelled as a refund. Pass tax_rate=0, debt_fraction=0 and
    escalation=0 to recover the capital-recovery annuity.
    """
    result = finance_project(
        0.0, annual_opex_inr, capex_inr, annual_output_t,
        flat_cost_inr=cash_cost_per_t * annual_output_t,
        **financing_terms(p, **overrides))
    crf = capital_recovery_factor(p["econ.discount_rate"], p["econ.project_life_yr"])
    annuity = ((capex_inr * crf + annual_opex_inr) / annual_output_t
               if annual_output_t else None)
    result["annuity_capital_inr_per_t"] = annuity
    result["cash_cost_inr_per_t"] = cash_cost_per_t
    result["annuity_cost_inr_per_t"] = (
        cash_cost_per_t + annuity if annuity is not None else None)
    return result


def reconciliation(cash_cost_per_t: float, annual_output_t: float,
                   capex_inr: float, annual_opex_inr: float, p) -> dict:
    """Annuity cost, the same case with the annuity's own assumptions, and
    the financed case. The first two match. The third is the BEE structure."""
    annuity = levelised_cost(
        cash_cost_per_t, annual_output_t, capex_inr, annual_opex_inr, p,
        tax_rate=0.0, debt_fraction=0.0, escalation=0.0,
        book_rate=0.0, wdv_rate=0.0, working_capital_frac=0.0)
    financed = levelised_cost(
        cash_cost_per_t, annual_output_t, capex_inr, annual_opex_inr, p)
    return {
        "annuity_cost_inr_per_t": annuity["annuity_cost_inr_per_t"],
        "cash_flow_matching_annuity_inr_per_t": annuity["levelised_cost_inr_per_t"],
        "financed_levelised_cost_inr_per_t": financed["levelised_cost_inr_per_t"],
        "gap_inr_per_t": (None if financed["levelised_cost_inr_per_t"] is None
                          else financed["levelised_cost_inr_per_t"]
                          - annuity["annuity_cost_inr_per_t"]),
    }
