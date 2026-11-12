"""Edge cases and invariants of the project cash flow.

The hand checks in test_financial.py fix the arithmetic on one project. These
cases are the ones a plant sweep turns up: an equity IRR far above any fixed
bracket, a cash flow that never recovers, a series with two IRRs, and a tax
loss in the early years.
"""
from __future__ import annotations

import itertools
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analysis.scenarios import evaluate
from src.data.parameters import Parameters
from src.economics.economics import EconomicsModel
from src.economics.financial import (
    _irr_result, _npv, finance_project, loan_schedule, reconciliation,
    retrofit_project, wdv_depreciation,
)
from src.models.energy_balance import EnergyBalance
from src.models.plant import build_plant

PLAIN = dict(life=20, discount_rate=0.08, tax_rate=0.0, book_rate=0.0, wdv_rate=0.0,
             debt_fraction=0.0, interest_rate=0.10, tenor=5, escalation=0.0,
             working_capital_frac=0.0)


def test_an_equity_irr_above_500_percent_is_found_not_dropped():
    irr, status = _irr_result([-12.5] + [110.0] * 20)
    assert status == "unique"
    assert irr > 5.0
    assert _npv([-12.5] + [110.0] * 20, irr) == pytest.approx(0.0, abs=1e-6)


def test_a_cash_flow_that_never_recovers_has_no_irr():
    assert _irr_result([-100.0] + [-5.0] * 10) == (None, "none")


def test_a_project_with_no_outlay_has_no_rate_of_return():
    assert _irr_result([0.0] + [50.0] * 10) == (None, "no_investment")
    result = finance_project(100.0, 0.0, 0.0, 10.0, **PLAIN)
    assert result["irr_status"] == "no_investment"
    assert result["npv_inr"] > 0.0


def test_a_retrofit_that_raises_output_is_valued_on_its_per_tonne_saving():
    p = Parameters()
    # Cheaper per tonne, 6% more tonnes: the extra tonnes are not a cost.
    project = retrofit_project(7000.0, 30000.0, 6900.0, 31800.0, 0.0, 0.0, p)
    assert project["annual_saving_inr"] == pytest.approx(100.0 * 31800.0)
    assert project["npv_inr"] > 0.0


def test_two_sign_changes_with_two_roots_are_reported_as_multiple():
    # -100 + 230/(1+r) - 132/(1+r)^2 = 0 at r = 10% and r = 20%.
    assert _irr_result([-100.0, 230.0, -132.0]) == (None, "multiple")


def test_an_early_tax_loss_is_set_off_against_later_profit():
    result = finance_project(
        300.0, 0.0, 1000.0, 10.0,
        **(PLAIN | {"life": 6, "tax_rate": 0.3, "wdv_rate": 0.4}))
    years = result["years"]
    taxable = [row["ebitda_inr"] - row["interest_inr"] - row["tax_depreciation_inr"]
               for row in years]
    assert taxable[0] < 0.0
    assert years[0]["tax_inr"] == 0.0
    assert years[0]["tax_losses_carried_inr"] == pytest.approx(-taxable[0])
    # Once the pool is used up, cumulative tax is the rate on cumulative profit.
    assert years[-1]["tax_losses_carried_inr"] == pytest.approx(0.0)
    assert sum(row["tax_inr"] for row in years) == pytest.approx(0.3 * sum(taxable))


def test_without_debt_the_equity_and_project_cash_flows_are_the_same():
    result = finance_project(300.0, 20.0, 1000.0, 10.0,
                             **(PLAIN | {"tax_rate": 0.3, "wdv_rate": 0.15}))
    assert result["cash_flows_inr"] == pytest.approx(result["project_cash_flows_inr"])
    assert result["npv_inr"] == pytest.approx(result["project_npv_inr"])


def test_leverage_raises_the_equity_irr_when_the_project_beats_the_loan_rate():
    terms = PLAIN | {"tax_rate": 0.3, "wdv_rate": 0.15}
    levered = finance_project(400.0, 0.0, 1000.0, 10.0, **(terms | {"debt_fraction": 0.75}))
    assert levered["project_irr"] > terms["interest_rate"]
    assert levered["irr"] > levered["project_irr"]


@pytest.mark.parametrize("field,lower,higher", [
    ("discount_rate", 0.06, 0.12),
    ("interest_rate", 0.08, 0.14),
])
def test_npv_falls_as_money_gets_dearer(field, lower, higher):
    terms = PLAIN | {"debt_fraction": 0.75, "tax_rate": 0.3, "wdv_rate": 0.15}
    cheap = finance_project(250.0, 10.0, 1000.0, 10.0, **(terms | {field: lower}))
    dear = finance_project(250.0, 10.0, 1000.0, 10.0, **(terms | {field: higher}))
    assert dear["npv_inr"] < cheap["npv_inr"]


def test_more_capital_for_the_same_saving_lowers_npv_and_lengthens_payback():
    small = finance_project(250.0, 0.0, 1000.0, 10.0, **PLAIN)
    large = finance_project(250.0, 0.0, 1500.0, 10.0, **PLAIN)
    assert large["npv_inr"] < small["npv_inr"]
    assert large["simple_payback_yr"] > small["simple_payback_yr"]


def test_a_tenor_longer_than_the_life_is_repaid_in_the_last_year():
    rows = loan_schedule(900.0, 0.10, 10, 4)
    assert sum(row["principal"] for row in rows) == pytest.approx(900.0)
    assert rows[-1]["closing"] == 0.0


def test_tax_depreciation_never_exceeds_the_cost():
    assert sum(wdv_depreciation(1000.0, 0.4, 30)) <= 1000.0


@pytest.mark.parametrize("bad", [
    {"debt_fraction": 1.2}, {"tax_rate": 1.0}, {"discount_rate": -1.0},
    {"interest_rate": -0.01}, {"life": 0},
])
def test_impossible_terms_are_refused(bad):
    with pytest.raises(ValueError):
        finance_project(100.0, 0.0, 1000.0, 10.0, **(PLAIN | bad))


def test_negative_capital_is_refused():
    with pytest.raises(ValueError):
        finance_project(100.0, 0.0, -1.0, 10.0, **PLAIN)


@pytest.mark.parametrize("levers", [
    {"whr": True},
    {"h2": 0.2},
    {"whr": True, "biomass": 0.2, "h2": 0.2, "oxygen": True, "kiln_control": True,
     "producer_gas": True, "char_recycle": True, "vfd": True},
])
def test_no_downside_case_beats_the_plan_even_when_the_retrofit_loses_money(levers):
    from api.server import Controls, scenario
    finance = scenario(Controls(**levers))["finance"]
    planned = finance["stress"][0]["npv"]
    for case in finance["stress"][1:]:
        assert case["npv"] <= planned + 1e-6, case["case"]


def _plant(capacity, utilization):
    plant = build_plant(Parameters(), capacity, utilization)
    return plant, EnergyBalance(plant).calculate_balance()


LEVERS = ("whr", "oxygen", "kiln_control", "producer_gas", "char_recycle", "vfd")


@pytest.mark.parametrize("capacity,utilization", [(50, 0.5), (100, 0.9), (600, 0.95)])
def test_every_lever_combination_gives_a_sound_project(capacity, utilization):
    plant, energy = _plant(capacity, utilization)
    p = plant.p
    base = EconomicsModel(plant).calculate_economics()
    for bits in itertools.product((False, True), repeat=len(LEVERS)):
        on = dict(zip(LEVERS, bits))
        case = evaluate(plant, energy, on.pop("whr"), 0.1, 0.1, **on)
        econ = case["econ"]
        opex = sum(r.get("annual_opex_inr", 0.0) for r in case["retrofits"].values())
        assert econ["cost_per_t_dri"] > 0.0
        assert case["co2"]["co2_total_t_per_t_dri"] >= 0.0
        assert case["capex_inr"] >= 0.0
        project = retrofit_project(base["cash_cost_per_t_dri"], base["annual_output_t"],
                                   econ["cash_cost_per_t_dri"], econ["annual_output_t"],
                                   case["capex_inr"], opex, p)
        assert math.isfinite(project["npv_inr"])
        assert math.isfinite(project["project_npv_inr"])
        for irr, flows in ((project["irr"], project["cash_flows_inr"]),
                           (project["project_irr"], project["project_cash_flows_inr"])):
            if irr is not None:
                assert _npv(flows, irr) == pytest.approx(0.0, abs=max(1.0, 1e-6 * abs(flows[0])))
        if project["npv_inr"] > 0.0 and project["irr_status"] == "none":
            pytest.fail(f"Positive NPV with no IRR: {bits}")
        if project["simple_payback_yr"] is not None and project["discounted_payback_yr"]:
            assert project["discounted_payback_yr"] >= project["simple_payback_yr"] - 1e-9
        rec = reconciliation(econ["cash_cost_per_t_dri"], econ["annual_output_t"],
                             case["capex_inr"], opex, p)
        assert rec["cash_flow_matching_annuity_inr_per_t"] == pytest.approx(
            rec["annuity_cost_inr_per_t"], rel=1e-9)
