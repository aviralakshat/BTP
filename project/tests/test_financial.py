"""Hand checks for the project cash flow, and the scenario round trip.

The capital-recovery identity is the one that matters: with no tax, no debt
and no escalation, the cash-flow levelised cost is the annuity cost. The tax
line is checked against the arithmetic in the BEE 2011 annexure.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analysis.scenario_store import (
    diff_overrides, document, load_scenario, save_scenario,
)
from src.data.parameters import Parameters
from src.data.price_series import load_price_series
from src.economics.economics import capital_recovery_factor
from src.economics.financial import (
    book_depreciation, finance_project, levelised_cost, loan_schedule,
    reconciliation, wdv_depreciation,
)
from src.version import MODEL_VERSION, parameters_sha256


def test_annuity_identity_holds_when_the_cash_flow_is_pre_tax_and_all_equity():
    p = Parameters()
    cash, output, capex, opex = 7000.0, 30000.0, 5.0e7, 1.2e6
    row = levelised_cost(
        cash, output, capex, opex, p,
        tax_rate=0.0, debt_fraction=0.0, escalation=0.0,
        book_rate=0.0, wdv_rate=0.0, working_capital_frac=0.0)
    assert row["levelised_cost_inr_per_t"] == pytest.approx(
        row["annuity_cost_inr_per_t"], rel=1e-9)
    crf = capital_recovery_factor(p["econ.discount_rate"], p["econ.project_life_yr"])
    assert row["annuity_cost_inr_per_t"] == pytest.approx(
        cash + (capex * crf + opex) / output)


def test_the_financed_case_is_reported_separately_from_the_annuity():
    p = Parameters()
    row = reconciliation(7000.0, 30000.0, 5.0e7, 1.2e6, p)
    assert row["cash_flow_matching_annuity_inr_per_t"] == pytest.approx(
        row["annuity_cost_inr_per_t"], rel=1e-9)
    assert row["financed_levelised_cost_inr_per_t"] != pytest.approx(
        row["annuity_cost_inr_per_t"], rel=1e-3)


def test_simple_payback_of_a_flat_saving_is_equity_over_the_annual_cash():
    result = finance_project(
        200.0, 0.0, 1000.0, 10.0,
        life=20, discount_rate=0.08, tax_rate=0.0, book_rate=0.0, wdv_rate=0.0,
        debt_fraction=0.0, interest_rate=0.10, tenor=5, escalation=0.0,
        working_capital_frac=0.0)
    assert result["simple_payback_yr"] == pytest.approx(5.0)
    assert result["discounted_payback_yr"] > result["simple_payback_yr"]
    assert result["npv_inr"] > 0
    assert result["irr"] is not None
    at_irr = sum(cf / (1.0 + result["irr"]) ** t
                 for t, cf in enumerate(result["cash_flows_inr"]))
    assert at_irr == pytest.approx(0.0, abs=1.0)


def test_loan_principal_sums_to_the_debt_and_interest_is_on_the_opening_balance():
    rows = loan_schedule(750.0, 0.10, 5, 20)
    assert sum(row["principal"] for row in rows) == pytest.approx(750.0)
    assert rows[0]["interest"] == pytest.approx(75.0)
    assert rows[5]["principal"] == 0.0
    assert rows[0]["closing"] == pytest.approx(600.0)


def test_bee_taxable_profit_arithmetic():
    """Annexure 4, year 1: PBDIT 902.47, interest 84.05, WDV depreciation 75.32.

    Taxable profit is 743.10 and tax at 33.99% is 252.58. The interest figure
    is the report's, not a 10% opening-balance interest, so this checks the
    tax definition rather than the loan schedule.
    """
    ebitda, interest, wdv = 902.47, 84.05, 75.32
    taxable = ebitda - interest - wdv
    assert taxable == pytest.approx(743.10, abs=0.02)
    assert 0.3399 * taxable == pytest.approx(252.58, abs=0.02)
    assert book_depreciation(960.75, 0.0528, 6)[0] == pytest.approx(50.73, abs=0.01)
    assert wdv_depreciation(960.75, 0.0784, 6)[0] == pytest.approx(75.32, abs=0.02)


def test_a_loss_does_not_generate_a_tax_refund():
    result = finance_project(
        0.0, 100.0, 0.0, 10.0,
        life=5, discount_rate=0.08, tax_rate=0.3399, book_rate=0.05, wdv_rate=0.08,
        debt_fraction=0.0, interest_rate=0.10, tenor=5, escalation=0.0,
        working_capital_frac=0.0)
    assert all(row["tax_inr"] == 0.0 for row in result["years"])


def test_price_series_follow_the_parameter_file_and_name_carbon():
    bands = load_price_series()
    coal = next(row for row in bands["rows"] if row["id"] == "coal")
    assert coal["base"] == Parameters()["econ.coal_price_inr_per_t"]
    assert coal["has_range"] is False
    power = next(row for row in bands["rows"] if row["id"] == "power")
    assert power["has_range"] is True
    assert power["high"] > power["base"]
    carbon = next(row for row in bands["rows"] if row["id"] == "carbon")
    assert carbon["base"] == 0.0
    assert carbon["high"] == pytest.approx(82.32 * 104.8645)


def test_scenario_round_trip_and_diff(tmp_path):
    doc = document(
        "Imported baseline", {"econ.coal_price_inr_per_t": 2500},
        100, 0.9, {"whr": False, "biomass_frac": 0.0})
    path = save_scenario(doc, str(tmp_path))
    loaded = load_scenario(path)
    assert loaded["model_version"] == MODEL_VERSION
    assert loaded["parameters_sha256"] == parameters_sha256()
    assert loaded["overrides"] == doc["overrides"]
    other = {"econ.coal_price_inr_per_t": 2500, "econ.power_tariff_inr_per_kwh": 5.0}
    changes = diff_overrides(loaded["overrides"], other)
    assert changes == [{"parameter": "econ.power_tariff_inr_per_kwh",
                        "left": None, "right": 5.0}]
