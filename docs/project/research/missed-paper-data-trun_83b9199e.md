# Defensible Inputs for Indian Rotary-Kiln DRI Economics

## Executive Summary

**This is a partial, source-located extraction, not a complete model dataset.** Several requested papers yielded only abstracts or incomplete previews. Missing inputs are identified explicitly rather than filled with assumptions.

- **Do Not Pool Coal-Saving Percentages**: The NIT proceedings calculation gives **5.4%**, while the Gaurav-Khanam comparison reports **37.4%** for a different heat-recovery configuration. The requested approximately 4% and 30.5% claims were not conclusively located -> retain separate scenarios rather than an averaged saving. [12][5]
- **Separate Gross Power From Export**: BEE's proposed plant produces **96,000 kWh/day**, consumes **9,600 kWh/day** internally, and leaves **86,400 kWh/day** available for the grid -> auxiliaries must precede any export-revenue calculation. [15]
- **BEE Contains Material Internal Conflicts**: Its main annual output is **28.512 million kWh**, but another passage uses **14.256 million kWh**; annual benefits also vary -> use a reconciled calculation, not whichever summary appears most attractive. [15]
- **Producer Gas Is An Estimated Opportunity**: TERI reports approximately **20% energy saving**, **4,200 tonnes/year coal saving**, and **INR 260 lakh/year** monetary benefit for the stated kiln case, but provides no corresponding producer-gas CAPEX -> the operating benefit alone cannot establish investment attractiveness. [14]
- **Historical WHR Costs Differ Sharply**: BEE's **INR 960.75 lakh for 4 MW** implies approximately **INR 2.40 crore/MW**, whereas the Raipur report's **INR 2,800 lakh for 4 MW** implies **INR 7 crore/MW** -> retain both source years and scopes; do not treat either as a current quotation. [15][6]
- **Combined Recovery Is Not Another Independent Saving**: Gaurav et al. report **2.757 MW** for combined preheating and power, with **2.62-year** payback, but only the abstract was available -> do not add its output to a separate full-WHR-power case. [4]

**Evidence grades.** A = measured industrial rotary-kiln evidence; B = peer-reviewed laboratory or pilot evidence; C = institutional/report evidence; D = vendor or unverifiable evidence. The requested scheme has no category for a peer-reviewed simulation. Below, **D*** denotes a published model prediction whose industrial realization is unverified; it does not mean the publication is a vendor source. Institutional engineering estimates remain **C**, not A.

## 1. NIT Heat Integration: Different Heat Sources, Different Savings

### The verified proceedings case gives 5.4%, not the requested approximately 4%

Prasad, Kumar and Khanam's *Generation of Energy Conservation Measures for Sponge Iron Plants* applies **pinch analysis** and a coal-consumption model to alternative heat-recovery configurations. Its results are calculated opportunities, not demonstrated retrofit savings. [12]

| Parameter or result | Extracted value | Source, year and locator | Grade |
|---|---:|---|---|
| Existing-system ore feed | 30 t/h | Prasad, Kumar and Khanam, 2011, Fig. 1/Table I | D* [12] |
| Existing-system feed coal | 14.297 t/h | Same, Fig. 1/Table I | D* [12] |
| Coal injection | 6.13 t/h | Same, existing-system stream data | D* [12] |
| Dolomite feed | 0.5 t/h | Same, Fig. 1/Table I | D* [12] |
| Kiln air | 48,000 m3/h at 30 C | Same, Fig. 1/Table I; the extracted unit is m3/h, not explicitly Nm3/h | D* [12] |
| Central-burner air | 12,000 m3/h at 30 C | Same, existing-system stream data | D* [12] |
| Baseline coal consumption | 20.424 t/h | Same, Table III, Case 1 | D* [12] |
| Coal net heating value | 22,930.5 kJ/kg | Same, coal-consumption calculation | D* [12] |
| Case 3 air preheat | 30 to 170 C | Same, Case 3 discussion | D* [12] |
| Recovering-gas flow and cooling | 59,738.8 m3/h; 220 to 80 C | Same, Case 3 discussion | D* [12] |
| Case 3 coal consumption and reduction | 19.325 t/h; 5.4% | Same, Table III/Case 3 results | D* [12] |
| Case 3 water-consumption reduction | 91.3% | Same, results/conclusion | D* [12] |
| Claimed Case 3 profit | INR 10.31 lakh/day | Same, conclusion; historical calculation, not a present-day forecast | D* [12] |

The important distinction is the **heat-recovery boundary**. This paper's air-preheating calculation uses relatively cool gas leaving the ESP. It describes power generation as a suggested recovery option, but the available passage does **not** establish that a WHR power plant was already installed. [12]

### The 37.4% result belongs to a different comparison

| Study/configuration | Quantitative result | Source, year and locator | Grade/access |
|---|---|---|---|
| Gaurav and Khanam, power-generation option | 8.97 MW; payback 4.17 years | *Energy*, 2017, abstract reproduced in the accessible Kumar-Khanam article record | D*; abstract-level evidence [5] |
| Gaurav and Khanam, alternative preheating option | Coal consumption 37.4% lower; water consumption 4.7% lower; payback 3.22 years | Same, abstract comparison | D*; abstract-level evidence [5] |
| Requested approximately 4% claim | Not conclusively source-located | Dey/Prasad-related papers, 2011-2012 | Unresolved; do not enter as a verified input |
| Requested 30.5% claim | Not conclusively source-located | Related NIT literature | Unresolved; do not enter as a verified input |

**Why the percentages can differ:** low-temperature post-ESP air heating and broader feed/air preheating are not equivalent recovery systems. Likewise, directing gas heat to preheating instead of electricity changes the opportunity cost. The accessible evidence supports those distinctions, but does **not** establish the exact denominator, coal grade, or installed-power status behind the approximately 4% and 30.5% claims. A definitive reconciliation of all three percentages is therefore still outstanding.

For the model, use the verified savings only with their own baseline coal rate and heat-exchanger boundary. Do not describe the 37.4% prediction as an observed plant improvement or attribute it automatically to the earlier NIT papers.

### Vivek Kumar and Khanam, Chemical Engineering and Processing, 2012

The accessible article preview identifies **Case 1 as air preheating using gas leaving the ESP**. It reports air heating to **170 C** using a **709 kW** plate heat exchanger. The process description gives ESP gas at **220 C** and sponge iron cooling from **1,020 to 110 C**. These are source-located design/stream values, not a verified complete retrofit performance dataset. **Grade D***. [5]

Its literature discussion also repeats incompatible-looking WHR economic thresholds: above **300 TPD** in one cited statement and approximately **2 x 500 TPD** in another. These are different cited studies, not a single consistent design rule. **Grade C as secondary literature evidence**. [5]

## 2. WHR Power: BEE's 2011 Design And Its Internal Conflicts

### The 4 MW operating and financial inputs

The BEE document is headed *Waste Heat Recovery Power Plant (4 MW) - 200 TPD*, but its bibliographic wording also refers to a **2 MW-100 TPD** report. That mixed wording matters because some internal figures appear to retain the smaller configuration. [15]

| Input | Extracted value | Source, year and locator | Grade |
|---|---:|---|---|
| Kiln configuration | 2 x 100 TPD; 200 TPD total | BEE, 2011, technology-assessment capacity calculation | C [15] |
| Proposed generating capacity | 4 MW | Same, power-generation calculation | C [15] |
| Gross generation | 96,000 kWh/day | Same, power-generation/benefit table | C [15] |
| Auxiliary consumption | 9,600 kWh/day | Same table | C [15] |
| Available for grid | 86,400 kWh/day; 28,512,000 kWh/year | Same table | C [15] |
| Flue-gas flow, assessment | 24,000 Nm3/h per kiln; 48,000 Nm3/h total | Same, technology-assessment calculation | C [15] |
| Kiln-outlet gas temperature, assessment | 1,005 C | Same calculation | C [15] |
| Boiler-outlet/ESP-inlet reference | 170 C | Same calculation | C [15] |
| Steam flow, assessment | 22,561 kg/h | Same, steam-generation calculation | C [15] |
| Steam pressure and temperature, assessment | 66 kg/cm2; 485 C | Same calculation | C [15] |
| Gas flow, equipment proposal | 25,000 Nm3/h | Same, technical-proposal specification | C [15] |
| Gas inlet/outlet, equipment proposal | 950 C; 160 +/- 10 C at economiser outlet | Same specification | C [15] |
| Steam, equipment guarantee | 10,000 kg/h; 66 +/- 0.5 kg/cm2(g); 485 +/- 5 C | Same, technical proposal/guaranteed parameters | C [15] |
| Total investment | INR 960.75 lakh | Same, investment-cost table | C [15] |
| Boiler/system/EPC cost lines | INR 500.00/265.00/45.75 lakh | Same table; these are selected lines, not the complete investment breakdown | C [15] |
| O&M cost line | INR 19.21 lakh | Same, technology-assessment economics | C [15] |
| Manpower cost line | INR 43.2 lakh | Same economics | C [15] |
| Payback | 12 months in executive table; 1.03 years in detailed assessment | Same, executive summary and detailed economics | C [15] |
| Electricity value | INR 3.3/kWh, labelled "Power Cost" | Same, power-benefit table; not separately established as an export tariff | C [15] |
| Coal calorific value | 3,000 kcal/kg | Same, assessment inputs | C [15] |
| Iron-ore consumption | 10.89 t/h | Same, assessment inputs | C [15] |

The main daily and annual electricity figures imply **330 operating days/year**, calculated as 28,512,000 / 86,400. This is an arithmetic implication, not an independently stated availability guarantee. The auxiliary fraction is **10%**, also calculated from the table. **Both are C-derived.** [15]

### Conflicts that must remain visible

| Conflict | Both reported values | Likely explanation and model treatment |
|---|---|---|
| Annual electricity | 28.512 million versus 14.256 million kWh | The latter is exactly half the former, consistent with mixed smaller/larger project material. Use the main configuration only after reconciling equipment scope. [15] |
| Annual monetary benefit | INR 940.90 lakh; INR 499 lakh; INR 998 lakh | Different output/tariff assumptions or retained calculations. At the main output and INR 3.3/kWh, the calculated benefit is INR 940.896 lakh/year, matching the executive figure. [15] |
| Gas temperatures | 1,005/170 C versus 950/(160 +/- 10) C | Assessment inputs versus equipment specification. Do not combine selected values into a fabricated guaranteed heat balance. [15] |
| Steam flow | 22,561 kg/h versus 10,000 kg/h | Aggregate assessment versus a smaller equipment specification is plausible, but not conclusively resolved. [15] |

The investment implies **INR 2.401875 crore/MW**, or approximately **INR 24.02 million/MW**, using the stated total project cost and capacity. This is a **2011, C-derived historical estimate**, not a current turnkey price. [15]

Neither an explicit boiler efficiency nor a steam-cycle efficiency was recovered. The reported heat and steam-enthalpy lines are not substitutes for those efficiencies. [15]

## 3. Combined Preheating And Power: What The 2024 Abstract Supports

For Gaurav, Khanam, Zhang and Liu, *Energy* **301, 131512 (2024)**, the accessible record contains an abstract, not the full paper. It describes recovering waste-gas heat through combined preheating of feed material, kiln air and slinger coal, together with power generation. [4]

| Abstract-reported quantity | Value | Source, year and locator | Grade |
|---|---:|---|---|
| Waste-gas temperature span | 994 to 250 C | Gaurav et al., 2024, abstract | D* [4] |
| Power produced | 2.757 MW | Same | D* [4] |
| Reported steam-temperature conditions | 280 C saturated; 600 C superheated | Same; reproduce literally, not as validated steam-cycle design data | D* [4] |
| Reported superheated pressure | 350 bar | Same; requires full-paper clarification before use | D* [4] |
| Superheater heat requirement | 5,066.9 kW | Same | D* [4] |
| Boiler heat requirement | 12,669.93 kW | Same | D* [4] |
| Preheater heat requirement | 6,873.6 kW | Same | D* [4] |
| Iterated air requirement | 52.588 t/h | Same | D* [4] |
| Iterated waste-gas flow | 22.31 kg/s | Same | D* [4] |
| New heat exchangers | 3 | Same | D* [4] |
| Payback | 2.62 years | Same | D* [4] |
| Literal reported TAC | "INR 8068.8/y" | Same; scale/units unresolved, unsuitable for model costing | D* [4] |

The abstract's pressure and cost notation should be retained as **unresolved**, not silently corrected. It also does not provide a defensibly extracted coal-saving percentage or complete baseline for this pass.

The model implication is straightforward: allocate exhaust heat between useful preheating and power production in one integrated balance. Comparing this output directly with BEE's capacity or the earlier power-only prediction without normalizing throughput, gas conditions and auxiliary loads would be misleading.

## 4. TERI Producer Gas: Useful Operating Estimates, Missing CAPEX

### A gasifier substitutes for discharge-end solid-coal injection

TERI's *Energy-Efficient Technology Options for Direct Reduction of Iron Process*, available through its **2021** publication record, describes converting coal fines to producer gas and supplying that gas back to the kiln. This is a **coal-gasification intervention**, not automatically biomass substitution or hydrogen decarbonisation. [14]

The Raipur report repeats the principal producer-gas figures in **Table 10**. The requested report year is 2024; that year was not independently visible in the extracted passage, so it is retained here as the supplied bibliographic identification rather than a verified cost-estimate date.

| Producer-gas parameter | Extracted value | Source and locator | Grade |
|---|---:|---|---|
| Kiln capacity | 100 TPD | TERI Raipur report, identified as 2024, Table 10 | C [6] |
| Discharge-end coal injection | 60 TPD | Same, Table 10 | C [6] |
| Potential energy saving | About 20% | TERI DRI options, 2021 publication record, producer-gas section; Raipur Table 10 | C [14][6] |
| Annual coal saving | 4,200 t/year | Same sections/Table 10 | C [14][6] |
| Monetary benefit | Approximately INR 260 lakh/year | Same sections/Table 10 | C [14][6] |
| GHG-reduction potential | 7,500 tCO2/year | Same producer-gas discussions | C [14][6] |
| Additional capacity benefit | 20% higher kiln capacity | TERI DRI options, additional-benefits list | C; stated opportunity, not a measured guarantee [14] |
| Producer-gas CAPEX | No numerical value recovered | Both reports say investment is required, without giving the corresponding amount in these passages | C [14][6] |

These reports are not independent corroborating plant trials: the repeated values should be treated as one family of engineering estimates. Also, an energy-saving percentage and a mass saving are not interchangeable unless the fuel basis, operating days and gasification balance are consistent.

### Other TERI options and conflicts

| Option | Quantitative inputs | Source, year and locator | Grade |
|---|---|---|---|
| Iron-ore preheating | 100 TPD basis; ore to 650 C; about 15% saving; 5,200 t/year coal; 2,700 toe/year; 9,300 tCO2/year | TERI DRI options, 2021 publication record, preheating section; repeated in Raipur report | C [14][6] |
| Preheating economics | INR 350 lakh investment; INR 325 lakh/year benefits; 1.1-year payback | TERI DRI options, preheating cost-benefit table | C [14] |
| Raipur WHR power | 4 MW; INR 2,800 lakh investment; 3.2-year payback | Raipur report, WHR cost-benefit section | C [6] |
| Shell-air-fan VFDs | 100 TPD basis; 19,000 kWh/year saving; 16 tCO2/year; INR 2.8 lakh investment; 5.2-year payback | TERI DRI options, VFD section; Raipur Table 13 | C [14][6] |
| ANN kiln control | About 5%-7% production increase | TERI DRI options, kiln-control section; not a coal-saving percentage | C [14] |
| Coal drying, narrative | About 3% saving; 1,065 t/year coal; 1,900 tCO2/year | TERI DRI options, drying discussion | C [14] |
| Coal drying, table | Moisture 10% +/- 2% to 4%; 3.5% saving; 1,275 t/year coal; INR 66 lakh/year benefit; INR 100 lakh investment; 1.5-year payback | Same, drying cost-benefit table | C [14] |
| Coal-fines briquetting/recycling | Potential 8%-10% coal saving | Same, coal-fines discussion | C [14] |

The coal-drying narrative and table disagree on both percentage and annual tonnage. Preserve them as alternative estimates rather than averaging them. Likewise, do not substitute TERI's production improvement for the specifically requested CSE kiln-control coal saving.

## 5. Historical Costs: What Can And Cannot Be Used

### WHR capital cost and electricity valuation

| Input | Defensible extraction | Source, year and locator | Grade/model treatment |
|---|---|---|---|
| WHR capital cost | Approximately INR 2.40 crore/MW, calculated from INR 960.75 lakh and 4 MW | BEE, 2011, investment and generation calculations | C-derived; historical design estimate [15] |
| Alternative WHR capital cost | INR 7 crore/MW, calculated from INR 2,800 lakh and 4 MW | Raipur report identified as 2024, WHR cost-benefit section | C-derived; underlying estimate year not established [6] |
| Electricity valuation | INR 3.3/kWh | BEE, 2011, power-benefit table, "Power Cost" | C; not a current national industrial tariff [15] |
| Separate WHR export tariff | Not established | BEE's label does not independently identify an export purchase rate | Do not assume grid-purchase and export prices are equal |

The capital-cost difference could reflect source date, scope, equipment specification or estimation method. The available passages do not isolate those effects, so attributing the entire difference to inflation would be unsupported.

### TERI financing report, 2023: currency and capacity problems

The accessible *Financing Decarbonization of the Secondary Steel Sector in India* report provides the following WHR figures **in USD**, not a source-located INR equivalent:

| Technology | Reported CAPEX and associated figures | Source, year and locator | Grade |
|---|---|---|---|
| DRI WHR power | USD 3.3902 million CAPEX; USD 1.0582 million annual saving; 19,300 tCO2/year; 3.2-year payback | TERI, 2023, DRI WHR power technology entry | C [11] |
| DRI ore preheating | USD 0.4238 million CAPEX; USD 0.3935 million annual saving; 22,360 Gcal/year; 7,726 tCO2/year; 1.1-year payback | Same, DRI ore-preheating entry | C [11] |
| EAF feedwater WHR | USD 0.012 million; 1,510 tCO2/year, for a 50-tonne EAF | Same, EAF technology summary | C; not rotary-kiln CAPEX [11] |
| EAF scrap preheating | USD 0.50 million; 8,860 tCO2/year, for a 50-tonne EAF | Same summary | C; not rotary-kiln CAPEX [11] |
| EAF scrap-preheating annexure | USD 0.2422 million bucket system; USD 0.4843 million continuous system, both for a 50-tonne furnace | Same, annexure technology entries | C [11] |

The power entry associates its economics with **100 TPD**, while surrounding text describes **4 MW at 200 TPD** and **1.5-2.5 MW potential at 100 TPD**. The preheating entry uses **200 TPD**, unlike the earlier TERI preheating case. These capacity bases should not be harmonized without the underlying calculation. [11]

No defensible INR-denominated biomass-system or hydrogen-system CAPEX was extracted from this report. Converting its USD values using an assumed exchange rate would not meet the request for source-given INR values.

## 6. Requested Sources And Inputs Still Unresolved

The remaining named sources should not be represented as having supplied model-ready parameters in this extraction.

| Requested source | What remains unresolved |
|---|---|
| Nduagu et al., rotary-kiln DRI LCA | CO2 boundary and intensity, gross WHR generation, internal electricity consumption and net export were not retained as a complete, source-located numerical set. No model-ready values are supplied here. |
| Rajesh, Nandi and Pabi, 2016 | The paper was identified, but oxygen Nm3/t, air before/after, coal saving, production change, campaign life and kiln dimensions were not recovered in a sufficiently located numerical extract. |
| CSE, *Forging Transition*, 2026 | Requested kiln-control coal saving, WHR kWh/t and adoption percentages remain unresolved in this answer. |
| CSE, *Decarbonizing India's Iron and Steel Sector*, 2022 | Report identified; requested numerical passages not extracted. |
| CEA version 20, December 2024 | The document actually inspected identifies itself as **version 21, November 2025**, not the requested version. Its factor must not be relabelled as version 20. [3] |
| CEEW, Nitturu et al., July 2024 | Publication identified; a complete source-located set of coal-grade, ore and power-consumption bands is not supplied here. [7] |
| Bhardwaj et al., 2023 and 2024 | Papers identified; biochar substitution and hot-charging savings are not supplied as verified numerical inputs here. The former is *Chemical Engineering Transactions* 103, 607-612. [8] |
| Hall et al., hydrogen rotary kilns | Report and authors identified, but a source-located hydrogen price was not retained. [10] |
| Kamal et al., hydrogen DRI | Exact requested paper and complete-reduction kg H2/t value remain unresolved. No theoretical stoichiometric value is substituted for the requested paper's process requirement. |
| Biswas, Asthana and Rau | No source-located quantitative savings result is supplied. |

The same limitation applies to **NMDC/market ore price, non-coking coal price, dolomite price, dolochar credit, agri-residue biomass price and heating value, and suitable Indian biomass carbon and ash fractions**. No defensible values for these inputs are supplied by the numerical extracts reported above. The coal heating values already listed are not coal prices or biomass properties.

**Five priority quantities still not defensibly sourced after this pass:**

1. The **2023-24 weighted-average grid factor including renewables from CEA version 20**, specifically.
2. **Net WHR electricity export in kWh/t DRI** from the Nduagu case, after distinguishing generation, plant demand and allocation boundaries.
3. **Oxygen consumption in Nm3/t DRI**, with the associated before/after air balance from Rajesh et al.
4. **Installed producer-gas-system CAPEX in INR** for the TERI discharge-end substitution case.
5. A **kiln-suitable Indian agri-residue biomass carbon fraction**, paired with that same material's moisture, ash, heating value and price basis.

These are priority gaps, not the only missing requested fields.

## 7. Synthesis: Build Separate Cases, Not A Stacked Saving

| Intervention | Mechanism | Evidence and scope | Main trade-off | Recommended treatment |
|---|---|---|---|---|
| Post-ESP air preheating | Recovers relatively low-temperature sensible heat | NIT calculated configuration | Limited temperature driving force | Separate heat-exchanger case; do not generalize its saving [12] |
| Broader preheating instead of power | Redirects recoverable heat to kiln inputs | Gaurav-Khanam abstract comparison | Coal saving competes with electricity production | Compare alternative cash flows, not additive benefits [5] |
| WHR power | Converts exhaust heat to electricity | BEE institutional DPR | Auxiliaries, availability and export valuation | Reconcile gross/net output and mixed project sizes [15] |
| Combined preheating and power | Allocates exhaust heat between two uses | Gaurav et al. abstract model | More integration and unresolved design notation | Sensitivity case until full-paper inputs are available [4] |
| Coal-derived producer gas | Changes fuel preparation and discharge-end combustion | TERI engineering estimates | Gasifier investment is missing | Operating-benefit scenario, not a completed investment case [14] |

The central tension is not simply "which option saves most coal?" A preheating option may reduce kiln coal while sacrificing electricity production; a power option may leave kiln coal unchanged while reducing purchased electricity. Those outcomes belong in different energy and cash-flow accounts.

The strongest numerical backbone available here is BEE's historical WHR design, provided its internal inconsistencies remain visible, plus TERI's explicitly estimated producer-gas and preheating opportunities. None of these savings should be multiplied together or stacked without a common mass balance, coal analysis, throughput basis and exhaust-heat allocation.

## References

1. *Some Studies on Energy Savings in Sponge Iron Plants  | J. Energy Resour. Technol. | ASME Digital Collection*. https://asmedigitalcollection.asme.org/energyresources/article/125/3/228/449228/Some-Studies-on-Energy-Savings-in-Sponge-Iron
2. *Decarbonizing rotary kiln–induction furnace based sponge iron production - ScienceDirect*. https://www.sciencedirect.com/science/article/pii/S0360544224022904
3. *Amt für Umweltschutz*. https://cea.nic.in/api/cdm-report-version/view-pdf/en/78
4. *Recovery and utilisation of waste heat for sponge iron process through combined preheating and power generation*. https://ideas.repec.org/a/eee/energy/v301y2024ics0360544224012854.html
5. *Recovery and utilization of waste heat in a coal based sponge iron process - ScienceDirect*. https://www.sciencedirect.com/science/article/abs/pii/S0255270112000621
6. *Situation Analysis of Raipur Secondary Steel Cluster*. https://sameeeksha.org/pdf/Raipur%20Cluster%20Report.pdf
7. *Kartheek Nitturu, Pratheek Sripathy, Rishabh Patidar, Sabarish Elango, Deepak Yadav, and Hemant Mallya Issue Brief | July 2024*. https://www.ceew.in/sites/default/files/decarbonising-coal-based-dri-production.pdf
8. *Decarbonisation Options for Rotary Kiln-Induction Furnace Process of Crude Steel Production*. https://www.cetjournal.it/cet/23/103/102.pdf
9. *FORGING TRANSITION*. https://www.cseindia.org/content/downloadreports/13216
10. *Hydrogen Rotary Kilns for Ironmaking in India*. https://teriin.org/files/Hydrogen-rotary-kilns-for-ironmaking.pdf
11. *Snapfi Steel Report 2023*. https://www.teriin.org/sites/default/files/2023-12/SNAPFI%20Steel%20Report%202023.pdf
12. *Microsoft Word - paper wce 2011-rev1*. https://www.iaeng.org/publication/WCE2011/WCE2011_pp2480-2484.pdf
13. *Profitability analysis of power generation using waste heat of sponge iron process - ScienceDirect*. https://www.sciencedirect.com/science/article/abs/pii/S0360544217315785
14. *DIRECT REDUCTION OF IRON PROCESS*. https://teriin.org/sites/default/files/2021-08/Direct%20Reduction%20of%20Iron%20Process.pdf
15. *1*. https://www.sameeeksha.org/pdf/dpr/Orissa_sponge_iron_cluster/Waste_heat_recovery_power_plant_4mw_200tpd_Orissa.pdf
16. *Benefits of oxygen enrichment in sponge iron rotary kiln emerging from data-driven modelling - N. Rajesh, A. Nandi, S. K. Pabi, 2016 *. https://journals.sagepub.com/doi/10.1080/03019233.2015.1120383
17. *Profitability analysis of power generation using waste heat of sponge iron process*. https://ideas.repec.org/a/eee/energy/v141y2017icp333-347.html
18. *Comparative life cycle assessment of natural gas and coal-based directly reduced iron (DRI) production: A case study for India - ScienceDirect*. https://www.sciencedirect.com/science/article/pii/S0959652622008277
19. *(PDF) Design Modifications for Energy Conservation of Sponge Iron Plants*. https://www.researchgate.net/publication/275091162_Design_Modifications_for_Energy_Conservation_of_Sponge_Iron_Plants
20. *Decarbonizing India’s Iron and Steel Sector report *. https://www.cseindia.org/decarbonizing-india-s-iron-and-steel-sector-report-11434
