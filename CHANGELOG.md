# Changelog

## 0.7.1 — 12 November 2026

Financial layer hardening. The plant balances, the coal rate and the annuity cost per tonne do not move; the regenerated golden baseline differs from 0.7.0 only in the version string. The version is bumped because retrofit cash-flow results can change.

* Tax losses are carried forward and set off against later profit instead of being lost. The losses come from tax depreciation, and unabsorbed depreciation carries forward without limit under s.32(2) of the Income Tax Act. The default 100 TPD waste-heat project has no loss year and is unchanged (equity NPV INR 14.6 crore, equity IRR 47.9%, payback 2.7 years); marginal projects at low utilisation are the ones that move.
* The IRR is found by scanning for every sign change of the net present value, with an open upper end. A sweep of 4,096 plant and lever combinations had found 103 projects with a positive NPV and no IRR, because the equity IRR exceeded the old 500% bracket. A cash flow with several IRRs now reports `irr_status = "multiple"` and quotes none, instead of returning whichever root bisection reached.
* Each project also reports the unlevered project cash flow, NPV and IRR (full capital at year 0, no debt), beside the equity view.
* Impossible terms (debt or tax outside 0 to 1, life below one year, negative capital, discount rate at or below -100%) raise instead of producing a number.
* The analyst no longer reports a missing IRR as 0%, and no longer fails when equity does not pay back.
* Downside stress cases for the web console are in `config/analysis.json` under `finance_stress`.
* The incremental project saving is the per-tonne cash saving times the scenario's output. It used to compare total operating spend at two different outputs, so oxygen enrichment, which raises output 6%, was charged for its extra tonnes and showed a negative NPV despite cutting cost per tonne. Retrofits that leave output unchanged are unaffected.
* A project with no capital outlay reports `irr_status = "no_investment"` instead of `"none"`.

## Product on 0.7.0 — 10 November 2026

Compare tab, report downloads, and a grounded analyst. The parameter file and the model version stay at 0.7.0, so the golden baseline is untouched. Balances and the cost per tonne are the same run as before.

The analyst calls the plant tools and quotes them. A number that is not in the tool result is withheld. It will not edit the parameter file and it will not invent a citation. No language-model API is connected. The design is `docs/software/agent_design.md`.

## 0.7.0 — 10 November 2026

Axial reconstruction of Dey's kiln, and a Summary page. The plant balances and the cost per tonne do not move. The parameter file gains the kiln length, both diameters, the inclination, the half-and-half zone split, the discharge-end gas temperature and the cell count, so the hash changes and the golden baseline is regenerated for that reason.

The axial model places the closed kiln ledger on the 80 m kiln. It does not predict metallisation. Figure 4 is not a table, and the rotation speed and the rate constants are not stated. The specification is `docs/models/05_kiln_axial_profile.md`.

The dashboard opens on a recommendation: the cheapest pathway to a chosen CO2 cut, three plant numbers, and the three parameters that move the cost furthest. Mass & Energy shows the gas temperature, the bed temperature and the prescribed metallisation along the kiln.

## 0.6.0 — 10 November 2026

Financial layer. The plant balances, the coal rate and the annuity cost per tonne do not move. Eight financing parameters are added from the Bureau of Energy Efficiency 2011 waste-heat project report for a 100 TPD kiln, so the parameter-file hash changes and the golden baseline is regenerated for that reason alone.

The cost per tonne remains the pre-tax capital-recovery annuity at Hall's 8% over 20 years. Beside it, a retrofit is now also a cash flow: 75% debt at 10% for 5 years, straight-line book depreciation at 5.28%, tax depreciation at 7.84% written down, and tax at 33.99%. Operating cost escalates at 5%. Coal and power savings do not. With tax, debt and escalation switched off, the cash-flow levelised cost matches the annuity. With them on, the levelised cost of the waste-heat case is about ₹50/t higher, because the loan costs 10% and a cost-only account has no profit for depreciation to shield.

Kamal et al. (2026) discount a different plant at 10%, and their hydrogen-plant NPV crosses zero near 11%. Neither replaces the 8% used here. The kiln has no capital cost in the model, so there is no whole-plant valuation. Price bands are read from the parameter file. A scenario file stores the model version and the parameter hash.

## Analysis on 0.5.0 — 10 November 2026

Phase 3 uncertainty layer. The plant equations and `parameters.json` are unchanged, so the golden baseline and the model version stay at 0.5.0.

One-at-a-time tornado over the 68 sensitivity-flagged parameters, Morris elementary effects (8 trajectories, 4 levels), a 400-draw triangular Monte Carlo, a marginal abatement curve, price break-evens, and a continuous search over biomass, hydrogen and waste heat recovery. Coal components that have to sum to one are not sampled independently: ash is drawn and the analysis is rescaled. Scenario choices are switches, not random variables. The carbon cases are no plant-gate charge (the Rs 400/t coal cess was removed on 11 September 2025) and the Q3 2026 CBAM certificate price. Method and sources are in `docs/models/11_uncertainty.md`. The dashboard's Uncertainty tab shows each chart with its data table.

## 0.5.0 — 10 November 2026

End of Phase 1: citation campaign, retrofit capital, and the process-optimisation cases. The golden file was regenerated on purpose.

**Citations.** Unsourced parameters fall from 26 to 5. Two statuses are added so a weak source is not passed off as a strong one: `indicative` (supplier quotes and analogues, grade D) and `scenario_choice` (plant size, exchange rate, hydrogen route, biogenic accounting, which are decisions rather than facts). Web sources are archived with URL and retrieval date in `data/web/`. `docs/parameters/data_provenance.md` is generated by `setup_data.py` and gives the reason each open gap is still open. `whr.opex_frac_of_capex` was unused and is deleted.

**Values that move the balance.** Excess air 0.15 → 0.11348 (Dey 2015, Eq. 37). After-burner combustion 0.95 → 1.0 (Prasad 2011, Tirumalaraju 2012: complete burn-out). Calcined-flux heat capacity 0.92 → 1.037 kJ/kg·K (NIST Shomate for CaO and MgO, weighted by Dey's dolomite).

**Values that move cost.** Fixed cost INR 50,000 → 35,000 per day at 100 TPD (Kunj Bihari Steel PFR, 2016: salaries 200, overheads 50, repairs and consumables 100 INR/t). Export tariff 4.0 → 3.3 INR/kWh (BEE 2011 Annexure 2). Dolomite 1,500 → 2,000 INR/t, dolochar 1,200 → 1,500 INR/t, rice husk 4,000 → 3,500 INR/t and oxygen 0 → 20 INR/Nm3, all indicative supplier prices. Rice-husk carbon 0.38 → 0.337 and ash 0.15 → 0.19.

**Retrofit capital.** Hydrogen: Kamal et al. (2026) Table 4 compressor cost, 130 US$/kW of equivalent electrolyser at 50 kWh/kg and 85% array efficiency. Biomass: CEA / PSPCL (2020) Rs 110 crore pelletiser for 195 MWth of biomass, scaled to the kiln's duty with the 0.67 exponent. Both replace zeros. The biomass figure is an analogue and is extrapolated about 80-fold down in size.

**New cases.** Char recycling (Bhardwaj et al. 2024, Section 4.6: 90% separation, feed coal replaced on equal fixed carbon, lost dolochar sales charged) and variable frequency drives (Section 4.2: 90% motor share, 73% power at 90% speed; Table 3 cost). Excess-air reduction, dust-loss reduction and kiln painting were not added: no source gives an achievable target for this kiln type. See `docs/project/OPEN_QUESTIONS.md`.

**Coupling fix.** WHR now runs after the coal-cutting levers, so its after-burner heat follows the coal that remains, and a VFD's lower auxiliary load raises WHR export one for one.

Baseline at 100 TPD: coal 1.0478 → 1.0246 t/t, SEC 5.713 → 5.586 Gcal/t, direct CO2 2.131 → 2.083 t/t, cost INR 7,481 → 7,234/t, WHR gross 421 → 418 and export 319 → 316 kWh/t, mass closure 1.15% → 1.20%. Validation: 10 PASS, 0 WARN, 0 FAIL. The domestic preset moves from 1.461 to 1.416 t/t. Least-cost pathways keep their composition, but biomass now carries capital: the 10% case's payback goes from 3.2 to 6.2 years, and the 20% case moves from a saving of INR 147/t to a cost of INR 200/t.

## 0.4.0 — 10 November 2026

Phase 1 model hardening. The golden file was regenerated on purpose, with `tests/golden/regenerate.py`.

**Domestic coal.** The 2.05 t/t result was an input error, not physics. The preset raised ash to 30% and 28% without lowering anything else, so the feed coal summed to 106.3% and the injection coal to 106.7%. That coal carried about 6% more carbon than a 30%-ash coal can hold. The model now refuses any coal whose ultimate or proximate analysis misses 100% by more than 0.5%. The preset is rebuilt on Dey's dry, ash-free composition with the same ash and heating value, and solves to 1.461 t/t.

**Char and dust.** Char was a fixed mass per tonne of coal, so it held a fixed amount of ash, and dust held a fixed amount per tonne of ore. At 15% coal ash the solids balance had no solution. Both streams are now built from what they are made of. Char takes 40.6% of the coal ash and 9.1% of the coal fixed carbon. Dust takes the ore's iron lost to dust plus 22.9% of the coal ash. Each share is computed from Dey Tables 6, 9 and 10, and run at Dey's coal rate they reproduce Dey's char and dust within 0.2% and 1%. The model now solves from 5% to 45% ash.

**Waste heat.** The cycle efficiency is 0.2265, computed from the BEE 2011 DPR heat balance (Annexure 2): 22,561 kg/h of steam from 127 to 800 kcal/kg gives 17.66 MW of heat for 4 MW. It replaces an unsourced 0.25. Gross generation falls from 466 to 421 kWh/t and is now inside the Nduagu band. Export falls from 359 to 319 kWh/t.

**Scale.** Waste-heat capital and fixed daily cost follow C = C_ref (S/S_ref)^0.67, the Kamal et al. 2026 Eq. (4) with their Table 4 exponent. The waste-heat reference is Gaurav et al.'s 2.757 MW system. Fixed cost carries the same exponent through Bhardwaj et al.'s maintenance-as-share-of-capital assumption, and its 100 TPD value is still unsourced.

**Guards.** A coal rate that cannot be solved now raises an error instead of silently using the configured value. `Parameters.out_of_range()` lists any value outside its min and max, and the app shows it as a warning.

Baseline at 100 TPD: coal 1.0506 to 1.0478 t/t, SEC 5.728 to 5.713 Gcal/t, direct CO2 2.133 to 2.131 t/t, cost INR 7,487 to 7,481/t. Validation: 10 PASS, 0 WARN, 0 FAIL. The least-cost pathways are unchanged in composition; the 10% case's payback moves from 2.6 to 3.2 years because waste heat generates less and costs more per MW at 1.6 MW.

## 0.3.0 — 10 November 2026

Replaced unsourced values with figures printed in the papers. Dollar amounts are converted at 95 INR per USD, the rate set for this study.

Coal is 2,500 INR/t and iron ore is 2,600 INR/t, both from Gaurav et al. 2024, Table 2. The purchased-power price is ₹3.5/kWh from Kamal et al. 2026. Hydrogen is ₹332.5/kg, from Hall et al. at about $3.5/kg. The discount rate is 8%, from the same Hall figure. Waste-heat capital cost is ₹46,800/kW from Gaurav et al. 2024, Table 2, and maintenance is ₹0.2/kWh from the same table. The boiler figure is the BEE 2019 estimate of 60%, and the flue-gas temperature is 150 °C, the high end of that table's 100–150 °C. Feed-coal specific heat is 1.38 kJ/kg·K from Gaurav and Khanam 2017. Waste-gas specific heat is 1.14 kJ/kg·K from Gaurav et al. 2024, Table 1. Raw biomass heating value is the low end of the BEE range, 3,100 kcal/kg.

The solved coal rate moves from 1.059 to 1.051 t/t. Cost per tonne falls from about INR 19,053 to about INR 7,487 because the paper prices replace the old placeholders. Waste-heat gross generation is 466 kWh/t, a warning against the 460 kWh/t edge. Export is 359 kWh/t and is inside the band. The steam-cycle efficiency is still unsourced.

Palm-kernel-shell charcoal from Vigneswaran et al. is stored and is not used as the biomass fuel, because the paper does not state its elemental carbon.

## 0.2.0 — 10 November 2026

Sourced values entered. No price, biomass analysis, boiler efficiency or hydrogen capital cost was invented.

The grid factor is now 0.727 t CO2/MWh, from CEA version 20, Table S, for 2023-24 including renewables. Waste-heat gross generation is unchanged. Ten percent of it, from the BEE 2011 4 MW table, is now deducted before export, so export falls from 512 to 455 kWh/t and still fails the Nduagu band. Baseline cost is unchanged at about INR 19,053/t. Reported CO2 falls from 2.200 to 2.194 t/t because purchased power is less carbon-intensive.

Oxygen enrichment, kiln control and producer gas are separate cases. Oxygen follows Rajesh Table 8 rather than the abstract's 6% coal claim. Kiln control is 3% of coal, capped at 5%, with INR 0.5 crore. Producer gas applies TERI's 20% energy saving and carries no capital cost. Biomass handling and hydrogen supply have capital-cost parameters set to zero, because no rupee figure was found.

## 0.1.0 — 10 November 2026

Phase 0 safety net. No parameter value and no balance result was changed.

The imported-coal baseline at 100 TPD and 90% utilisation, the literature verdicts, and the least-cost pathway at each CO2 target are frozen in `project/tests/golden/baseline_100tpd_imported.json`. A quoted result can be tied to model version `0.1.0` and to the SHA-256 of `project/config/parameters.json`.
