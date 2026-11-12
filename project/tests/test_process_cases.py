"""Process-optimisation cases, sourced retrofit capital and the provenance register."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.analysis.scenarios import evaluate
from src.data.parameters import MW, Parameters
from src.economics.economics import scaled_cost
from src.models.energy_balance import EnergyBalance
from src.models.plant import build_plant
from src.retrofits.biomass import Biomass
from src.retrofits.char_recycle import CharRecycle
from src.retrofits.hydrogen import Hydrogen
from src.retrofits.vfd import VariableFrequencyDrive
from src.retrofits.whr import WHR

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
CONFIG = os.path.join(os.path.dirname(__file__), "..", "config", "parameters.json")


@pytest.fixture(scope="module")
def solved():
    pl = build_plant(capacity_tpd=100, utilization=0.9)
    return pl, EnergyBalance(pl).calculate_balance()


@pytest.fixture(scope="module")
def base(solved):
    return evaluate(*solved)


# --- variable frequency drives -------------------------------------------

def test_vfd_saving_follows_bhardwaj_fractions(solved):
    pl, _ = solved
    p = pl.p
    v = VariableFrequencyDrive(pl).calculate_impact()
    expected = (p["power.aux_kwh_per_t_dri"] * p["vfd.motor_share_frac"]
                * (1.0 - p["vfd.power_at_reduced_speed_frac"]))
    assert v["power_saving_kwh_per_t_dri"] == pytest.approx(expected)


def test_vfd_cuts_import_and_charges_its_annualised_cost(solved, base):
    pl, eb = solved
    p = pl.p
    r = evaluate(pl, eb, vfd=True, baseline=base)
    v = r["retrofits"]["Variable Frequency Drives"]
    assert r["net_import_kwh_per_t_dri"] == pytest.approx(v["aux_after_kwh_per_t_dri"])
    power_saving = v["power_saving_kwh_per_t_dri"] * p["econ.power_tariff_inr_per_kwh"]
    assert r["cost_delta_inr_per_t_dri"] == pytest.approx(
        v["annualised_cost_inr_per_t_dri"] - power_saving)
    assert r["co2_reduction_frac"] > 0


def test_vfd_with_whr_raises_export_by_the_saving(solved):
    pl, eb = solved
    plain = evaluate(pl, eb, whr=True)
    both = evaluate(pl, eb, whr=True, vfd=True)
    saving = both["retrofits"]["Variable Frequency Drives"]["power_saving_kwh_per_t_dri"]
    assert plain["export_kwh_per_t_dri"] > 0
    assert both["export_kwh_per_t_dri"] - plain["export_kwh_per_t_dri"] == pytest.approx(saving)


# --- char recycling ------------------------------------------------------

def test_char_recycle_replaces_feed_coal_on_equal_fixed_carbon(solved):
    pl, _ = solved
    p = pl.p
    cr = CharRecycle(pl).calculate_impact()
    char_c = pl.c_char * p["char_recycle.separation_frac"]
    assert cr["carbon_returned_kg_per_t_dri"] == pytest.approx(char_c)
    assert cr["feed_coal_replaced_kg_per_t_dri"] * p["coal_feed.fixed_carbon"] == pytest.approx(char_c)
    assert cr["coal_reduction_frac"] == pytest.approx(
        cr["feed_coal_replaced_kg_per_t_dri"] / (pl.coal_feed + pl.coal_inj))


def test_char_recycle_nets_returned_carbon_and_lost_sales(solved, base):
    pl, eb = solved
    p = pl.p
    r = evaluate(pl, eb, char_recycle=True, baseline=base)
    cr = r["retrofits"]["Char Recycling"]
    coal_saved = (pl.coal_feed + pl.coal_inj) * cr["coal_reduction_frac"]
    expected = (cr["lost_char_sales_inr_per_t_dri"] + cr["annualised_cost_inr_per_t_dri"]
                - coal_saved / 1000.0 * p["econ.coal_price_inr_per_t"])
    assert r["cost_delta_inr_per_t_dri"] == pytest.approx(expected)
    # Coal carbon leaving as gas falls, but the recycled char carbon now joins it.
    gross_c = (pl.c_gasified + pl.c_unburnt_vm) * cr["coal_reduction_frac"]
    gross_co2_t = gross_c * MW["CO2"] / MW["C"] / 1000.0
    assert 0 < r["co2_reduction_t_per_t_dri"] < gross_co2_t
    assert r["feasible"]


def test_char_recycle_is_single_pass_and_warns(solved):
    r = evaluate(*solved, char_recycle=True)
    assert any("single-pass" in w for w in r["warnings"])


# --- WHR responds to coal removed ----------------------------------------

def test_whr_after_burner_heat_follows_remaining_coal(solved):
    pl, eb = solved
    plain = WHR(pl).calculate_impact(eb)
    r = evaluate(pl, eb, whr=True, kiln_control=True)
    w = r["retrofits"]["Waste Heat Recovery"]
    kept = 1.0 - pl.p["kiln_control.coal_saving_frac"]
    assert w["from_abc_post_combustion_kj"] == pytest.approx(
        plain["from_abc_post_combustion_kj"] * kept)
    assert w["from_waste_gas_sensible_kj"] == pytest.approx(plain["from_waste_gas_sensible_kj"])
    assert any("after-burner heat is scaled" in w for w in r["warnings"])


def test_whr_alone_is_unchanged_by_the_reordering(solved):
    pl, eb = solved
    r = evaluate(pl, eb, whr=True)
    plain = WHR(pl).calculate_impact(eb)
    assert r["retrofits"]["Waste Heat Recovery"]["gross_generation_kwh_per_t_dri"] == \
        pytest.approx(plain["gross_generation_kwh_per_t_dri"])


# --- sourced retrofit capital --------------------------------------------

def test_hydrogen_compressor_capex_follows_kamal_basis(solved):
    pl, _ = solved
    p = pl.p
    h = Hydrogen(pl, 0.1).calculate_impact()
    kw = (h["h2_required_kg_per_t_dri"] * pl.production_tpd / 24.0
          * p["hydrogen.electrolyser_sec_kwh_per_kg"] / p["hydrogen.electrolyser_array_eff"])
    assert h["equivalent_electrolyser_kw"] == pytest.approx(kw)
    assert h["capex_inr"] == pytest.approx(
        kw * p["hydrogen.compressor_capex_usd_per_kw"] * p["econ.usd_inr"])


def test_biomass_handling_capex_scales_from_the_cea_reference(solved):
    pl, _ = solved
    p = pl.p
    b = Biomass(pl, 0.1).calculate_impact()
    ref = p["biomass.handling_capex_ref_mwth"]
    assert b["capex_inr"] == pytest.approx(scaled_cost(
        p["biomass.handling_capex_inr_per_mwth"] * ref, b["biomass_duty_mwth"], ref,
        p["econ.capex_scale_exponent"]))
    bigger = Biomass(pl, 0.2).calculate_impact()
    assert bigger["capex_inr"] > b["capex_inr"]
    assert bigger["capex_inr"] < 2 * b["capex_inr"]


# --- provenance register -------------------------------------------------

def test_every_status_is_in_the_declared_vocabulary():
    meta = json.load(open(CONFIG))["_meta"]["provenance_status_values"]
    p = Parameters()
    statuses = {r["status"] for r in p.provenance_rows()}
    assert statuses <= set(meta)


def test_needs_citation_is_under_the_phase1_target():
    p = Parameters()
    assert len(p.unsourced_keys()) < 15


def test_every_cited_source_file_exists():
    missing = []
    for r in Parameters().provenance_rows():
        f = r["source_file"]
        if not f:
            continue
        path = (os.path.join(ROOT, "data", f + ".txt") if f.startswith("web/")
                else os.path.join(ROOT, "data", "text", f + ".txt"))
        if not os.path.exists(path):
            missing.append((r["parameter"], f))
    assert missing == []


def test_sourced_statuses_carry_a_source():
    for r in Parameters().provenance_rows():
        if r["status"] in ("verified", "derived", "indicative"):
            assert r["source"].strip(), r["parameter"]
