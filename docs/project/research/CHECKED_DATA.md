# Checked data from the local PDFs

Read from the files in `papers/` on 10 November 2026. Nothing here has been written into `parameters.json`. A row is usable in the model only when its grade and the note below both allow it.

Grades: **A** measured on a plant or a plant survey. **B** peer-reviewed trial on a real kiln. **C** institutional report or survey compilation. **D\*** a published calculation that has not been shown on an operating kiln.

## What the coal-saving percentages actually are

They are not three measurements of one retrofit.

| Claim | What the PDF says | Plant and heat source | Grade |
|---|---|---|---|
| About 4% | Tirumalaraju, Khanam and Sahoo. Coal falls from 6.144 t/h to 5.88 t/h, stated as 4.3%. Feed to 120 °C and air to about 115 °C using gas after the ESP. 100 TPD plant. Table 1. | Low-temperature gas after the dust catcher | D* |
| 30.5% | Prasad, Prasad and Khanam, 2011. Conventional coal 21.437 t/h on a **500 t/day** plant. Case 2, feed plus air preheat, is 14.892 t/h. Abstract and p. 7–8. Air preheater is fed with after-burner gas at 850 °C, cooled to 250 °C. | Hot after-burner gas, not ESP gas. Compared with a plant that has no this preheat | D* |
| 37.4% | Gaurav and Khanam, *Energy* 2017. Option 2 coal 13.587 t/h against an existing 21.72 t/h. Air preheated to 600 °C, feed and slinger coal to 200 °C. Abstract and p. 7. The same paper's power-only option is 8.97 MW, payback 4.17 years, and does not cut coal. | Preheating taken instead of power, on a large calculated plant | D* |

Gaurav and Khanam themselves compare the 37.4% case with Prasad and report Prasad's best case as 12.3% in their Table 9, while Prasad's own abstract says 30.5%. Both sentences are in the PDFs. They are not reconciled. Do not enter 30.5% or 37.4% as an observed saving.

CSE, 2026, Table 4, is a fourth and smaller figure for feed preheating: 8–10% coal against a reference of 19.0 GJ/t, equal to 1.52–1.90 GJ/t, capital Rs 5–15 crore, adoption 15–20%. The same page says preheating and waste-heat power use the same exhaust, so the two savings must not be added.

## Waste-heat power

| Quantity | Value | Where | Grade |
|---|---|---|---|
| Gross / auxiliary / export | 96,000 / 9,600 / 86,400 kWh/day on 2 × 100 TPD | BEE Odisha DPR, 2011, assessment table. That is 480 / 48 / 432 kWh/t | C |
| Gas and steam in that assessment | Kiln outlet 1,005 °C, boiler outlet 170 °C, steam 22,561 kg/h at 66 kg/cm² and 485 °C | Same table | C |
| A second set in the same DPR | 14.256 million kWh/year, steam guarantee 10,000 kg/h, gas 950 °C to 160 °C | Equipment sheets. Half the main electrical total. Do not mix the two sets | C |
| Investment | Rs 960.75 lakh for 4 MW, about Rs 2.4 crore/MW. O&M Rs 19.21 lakh. Power valued at Rs 3.3/kWh | 2011 design estimate, not a present quotation | C |
| Later capital figures | Raipur report: Rs 2,800 lakh for 4 MW, about Rs 7 crore/MW, payback 3.2 years. Gaurav et al. 2024, p. 3: boiler-turbine "standard cost" Rs 46,800/kW, about Rs 4.7 crore/MW | Three eras, three scopes. Keep all three | C / D* |
| Nduagu et al. 2022, Table 2 | Rotary-kiln column: power produced 451 kWh/t, net power −351 kWh/t | Their model, checked against industry data. Not one measured kiln | C |
| CEEW survey, p. 14 | About 2 MW installed per 100 TPD, stated as 450 kWh/t. Plants actually recover at most 350–380 kWh/t | Survey statement | A for the survey, not a heat balance |
| CSE 2026, Table 4 row 7 | 60–90 kWh/t, capital Rs 30–60 crore, adoption 5–20% | Sector catalogue. Far below the other generation figures. Report it as a conflict, do not replace Nduagu or BEE with it | C |
| Boiler efficiency and steam-cycle efficiency | Not stated as a percentage in the BEE DPR or in the Gaurav 2024 sections read | Still open. Gaurav 2024 fixes Carnot efficiency at 43% for a stated temperature pair. That is not a boiler efficiency | — |

## Other retrofits, read from the PDF

| Retrofit | Value | Where | Grade |
|---|---|---|---|
| Oxygen enrichment | One anonymised 100 TPD kiln. Oxygen 8 Nm³/t. Air 2,600 to 2,150 Nm³/t in Table 8 (the abstract says 2,609 to 2,150). End-zone bed 1,132 °C. Campaign 50 to 100 days. Ore feed +6% (7.0 to 7.42 t/h). Metallic iron stays about 75% | Rajesh, Nandi and Pabi, 2016, Table 8 and p. 6–7 | B, one industrial trial |
| Coal in that trial | The paper says specific coal consumption falls 6%. Table 8 shows feed coal 1.93 to 1.85 t/h (−6%) while coarse injection rises 0.35 to 0.55 and fines fall 2.01 to 1.75. Total solid coal 4.29 to 4.15 t/h, about 3% | Same table. Use the table, and state the 6% as the authors' specific-consumption claim | B |
| Kiln control | Coal cut 3–5%, 0.57–0.95 GJ/t. Capital Rs 0.5–1 crore. Adoption under 5% | CSE 2026, section 5.2.4 and Table 4 | C |
| Shell and refractory | Shell temperature 300–350 °C down to 200–250 °C. Saving 5–10 kcal/kg, 0.021–0.042 GJ/t. Capital under Rs 1 crore. Adoption 20–30% | CSE 2026, section 5.2.2 and Table 4 | C |
| Producer gas | 100 TPD, discharge-end injection coal 60 TPD, about 20% energy saving, 4,200 t coal/year, Rs 260 lakh/year, 7,500 t CO₂/year. No gasifier capital cost | TERI 2021 producer-gas section and Raipur Table 10. One estimate repeated, not two trials | C |
| TERI ore preheating | Ore to 650 °C, about 15% saving, investment Rs 350 lakh, benefit Rs 325 lakh/year, payback 1.1 years, on a 100 TPD basis | TERI 2021. Different from the CSE 8–10% figure | C |
| Biochar replaces feed coal | Direct CO₂ cut 1,241.5 kg/t crude steel, power generation falls 378.7 kWh/t crude steel, abatement cost 45.4 US$/t CO₂ | Bhardwaj et al., *Chemical Engineering Transactions* 103, 2023, the options table | D* |
| Gravimetric separation and hot charging | Net electricity credit 175.9 kWh/t crude steel. Kiln discharge 1,020 °C cooled to 110 °C in the base plant, citing Dey | Same table and section 3.1 | D* |
| Natural gas injection | Direct CO₂ cut 607.1 kg/t crude steel, but power generation falls 180.8 kWh/t crude steel | Same table | D* |

## Checks the model already uses, confirmed in the PDF

| Quantity | Value | Where | Grade |
|---|---|---|---|
| Grid factor | **0.727 t CO₂/MWh** for 2023–24, weighted average including renewables, adjusted for cross-border trade. Computed as 1,204.51 Mt / 1,655.7 billion kWh | CEA user guide version 20.0, December 2024, Table S and the worked example. The model uses 0.82 | A |
| Auxiliary power | Most plants 55–65 kWh/t. Some 80–100 kWh/t. Figure 9 is Bellary only | CEEW, Nitturu et al., 2024, key findings and p. 11–12 | A |
| Coal rate | Domestic 1.4–1.6 t/t. Imported 0.9–1.1 t/t | Same, section 3.2 and p. 15 | A |
| Ore rate | Pellets about 1.4–1.6 t/t. Lump ore 1.8–2.0 t/t | Same, p. 8 and p. 15 | A |
| Survey CO₂ | Domestic coal with lump ore 2.08 t/t. Pellets 1.84. Pellets with imported coal 1.53. Pellet-making is given as 0.25 t/t pellet from a Chinese study | Same, p. 13. These are the survey's estimates, not a kiln carbon balance | C |
| Hydrogen price | About **$3.5/kg**, the level of Indian green-ammonia tenders, at which a hydrogen kiln is described as close to competitive with coal DRI. Electricity in that figure is $50/MWh and the discount rate is 8% | Hall, Bhaskar and Görnerup, TERI, 2025, p. 12 and Figure 6 | C |
| Hydrogen for full reduction | Literature band 53.5–59.6 kg/t. Their model gives 55.7. They adopt **59.6 kg/t** as a conservative design value for inefficiencies | Kamal et al., 2026, p. 3. This is shaft-furnace hydrogen DRI, not a kiln retrofit | C |
| Rotary-kiln CO₂ range | 1,391.1–1,880.0 kg CO₂e/t. Base case 1,880 without the export credit. 1,590 after crediting 351 kWh/t. 1,391 if unburnt volatile carbon is burned inside the kiln and coal falls | Nduagu et al., 2022, abstract, p. 6 and p. 7 | C |

## Still not in these PDFs

No sourced current price for ore, coal, dolomite or dolochar. Gaurav et al. 2024, p. 3, assume Rs 2,600/t ore and Rs 2,500/t coal. Those are the paper's inputs and are far below recent market prices, so they are not adopted. No Indian agri-residue carbon, ash, moisture, heating value and price as one consistent set. No producer-gas capital cost. No boiler efficiency. Biswas, Asthana and Rau, 2003, is about kiln seals and shell losses. The only plant figure located is 10 kW for the mechanical seal on a 2.6 m by 40 m kiln. It is not a coal-rate retrofit.
