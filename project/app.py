import streamlit as st
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from models.baseline import BaselineModel
from models.mass_balance import MassBalance
from models.energy_balance import EnergyBalance
from emissions.co2_model import CO2Model
from economics.economics import EconomicsModel
from retrofits.whr import WHR
from retrofits.biomass import Biomass
from retrofits.hydrogen import Hydrogen

st.set_page_config(page_title="DRI Digital Twin", layout="wide")

st.title("Industrial-Grade Digital Twin: Coal-Based Rotary-Kiln DRI")

# Sidebar inputs
st.sidebar.header("Plant Parameters")
capacity = st.sidebar.slider("Plant Capacity (TPD)", 100, 500, 100, 50)
utilization = st.sidebar.slider("Utilization", 0.5, 1.0, 0.9, 0.05)

st.sidebar.header("Retrofits")
whr_enabled = st.sidebar.checkbox("Enable Waste Heat Recovery (WHR)")
biomass_pct = st.sidebar.slider("Biomass Substitution (%)", 0, 30, 0, 5) / 100.0
h2_pct = st.sidebar.slider("Hydrogen Substitution (%)", 0, 30, 0, 5) / 100.0

# Run Models
model = BaselineModel(capacity, utilization)
mb = MassBalance(model)
eb = EnergyBalance(model)

base_results = model.run_simulation()
mb_results = mb.calculate_balance()
eb_results = eb.calculate_balance()

# Apply Retrofits
coal_tpd = model.coal_feed_rate_tpd
electricity_mwh = 24 # baseline assumption
co2_reduction = 0
added_costs = 0
capex = 0

if whr_enabled:
    whr = WHR(model)
    whr_res = whr.calculate_impact(eb_results)
    electricity_mwh = max(0, electricity_mwh - whr_res['power_generated_mwh_d'])
    capex += whr_res['whr_capex']

if biomass_pct > 0:
    bm = Biomass(model, biomass_pct)
    bm_res = bm.calculate_impact()
    coal_tpd -= bm_res['coal_displaced_tpd']
    co2_reduction += bm_res['fossil_co2_reduction_tpd']
    added_costs += bm_res['biomass_cost_d']

if h2_pct > 0:
    h2 = Hydrogen(model, h2_pct)
    h2_res = h2.calculate_impact()
    coal_tpd -= h2_res['coal_displaced_tpd']
    co2_reduction += h2_res['fossil_co2_reduction_tpd']
    added_costs += h2_res['h2_cost_d']

# Run CO2 & Econ
co2 = CO2Model(model)
co2_results = co2.calculate_emissions(coal_tpd, electricity_mwh)

econ = EconomicsModel(model)
econ_results = econ.calculate_economics(coal_tpd, model.ore_feed_rate_tpd, model.dolomite_feed_rate_tpd, electricity_mwh)
econ_results['total_daily_opex'] += added_costs
econ_results['cost_per_t_dri'] = econ_results['total_daily_opex'] / model.production_tpd

# Dashboard Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Executive Dashboard", "Mass & Energy Balance", "Emissions", "Economics"])

with tab1:
    st.subheader("Executive Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Production (TPD)", f"{model.production_tpd:.1f}")
    col2.metric("CO2 Emissions (t/t DRI)", f"{co2_results['co2_per_t_dri']:.2f}")
    col3.metric("Cost (₹/t DRI)", f"₹{econ_results['cost_per_t_dri']:,.0f}")
    col4.metric("CAPEX Added", f"₹{capex:,.0f}")
    
with tab2:
    st.subheader("Mass Balance")
    st.write(mb_results)
    st.subheader("Energy Balance")
    st.write(eb_results)

with tab3:
    st.subheader("CO2 Accounting")
    st.write(co2_results)
    st.metric("Total CO2 Reduction (tpd)", f"{co2_reduction:.1f}")

with tab4:
    st.subheader("Economics")
    st.write(econ_results)

