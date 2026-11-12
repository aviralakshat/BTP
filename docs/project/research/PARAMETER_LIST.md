# Parameter list, with references

Compiled 10 November 2026. Nothing in this file has been written into `parameters.json`. A value is included only when a paper or a retrieved web page states it. Where two sources disagree, both numbers are kept.

The exchange rate used below, where a dollar figure is turned into rupees, is the study rate of 95 INR per USD. That rate is not printed in the papers.

## 1. Missed in the local CEEW paper

These are in `papers/2024_Nitturu_Decarbonising-coal-DRI.pdf` and were not the values used in the model.

| Parameter | Value | Where in the paper |
|---|---|---|
| Waste-heat capital cost | INR 9 crore per MW, about USD 1 million per MW. A 3 MW boiler is then about INR 27 crore | p. 14, citing Elango et al. 2023. The text says "assuming" |
| Plants under 300 TPD with a waste-heat boiler | 1 of 16 | same page |
| Average kiln size below 300 TPD | 171 TPD | same page |
| Waste-heat boilers, share of surveyed capacity | 65% | p. 13 |
| Pellet use, share of surveyed capacity | above 70% | p. 13 |
| Dolochar burned or sold | penetration above 50%. The paper says dolochar can be mixed with coal for power or sold. It does not give a price | p. 13 |
| Induction-furnace scrap | 10–20%, average 12.5% | p. 14 |

The model currently uses INR 4.68 crore per MW, from Gaurav et al. 2024, Table 2. The CEEW figure is a different, higher project cost. Both stay on the record.

## 2. Found on the web, for the items no local paper priced

### Biomass, India

Rice husk, one Haryana sample, Central Electricity Authority, December 2020 ([viability study](https://cea.nic.in/api/dashboardReports/view-pdf/en/efb59209-2c59-4035-aabb-5f584de7f0d8)):

| Property | Value |
|---|---|
| Volatile matter | 59.9% |
| Fixed carbon | 22.6% |
| Ash | 11.2% |
| Moisture | 6.3% |
| Carbon, dry ash-free | 47.2% |
| Hydrogen, dry ash-free | 6.1% |
| Oxygen, by difference | 46.7% |

The same report uses 3,100 kcal/kg as a conservative gross calorific value for agricultural waste, matching the low end of the BEE 2019 range already in the model. Paddy straw in that report: gross calorific value 3,239 kcal/kg, ash 21.8%, moisture 15.7%, fixed carbon 14.3%.

A separate Andhra Pradesh rice-husk sample reports moisture 8.64%, volatile matter 71.23%, ash 18–21.4%, and fixed carbon 7.3% ([Madras Agricultural Journal, 2019](https://masujournal.org/store_file/archive/106-Special-279-283.pdf)). The two rice-husk ash figures do not agree. They are different samples.

Prices, not a single quotation:

| What | Value | Source |
|---|---|---|
| Factory-gate agro-residue, briquette and pellet makers | INR 2,000–2,500 per tonne | [CSE, Agro-residue for Power, 2020](https://www.cseindia.org/content/downloadreports/10421) |
| Baled paddy straw, delivered 50 km | INR 2,500–3,000 per tonne | [CEEW, ex-situ crop residue, 2023](https://www.ceew.in/publications/ex-situ-crop-residue-management-scalable-solution-for-paddy-stubble-burning) |
| Briquettes and pellets, delivered 50 km | INR 4,000–5,000 per tonne | same CEEW page |
| Estimated pellet production cost | INR 4,473 per tonne | [CEEW, Purohit and Chaturvedi, 2016](https://www.ceew.in/publications/techno-economic-assessment-biomass-pellets-market-and-power-generation-india) |

The model's raw-biomass price is still the old placeholder of INR 4,000 per tonne. The CEEW delivered-bale range is the closest sourced Indian residue price. It is not yet in the model.

### Oxygen

No sponge-iron contract price was retrieved.

- The National Pharmaceutical Pricing Authority fixed oxygen gas at Rs 17.49 per cubic metre. A 7 cubic metre cylinder was reported at Rs 175–200. This is a 2020 medical-gas report, not a kiln supply contract ([Times of India, 23 September 2020](https://timesofindia.indiatimes.com/india/oxygen-price-should-be-capped-for-hospitals-not-suppliers/articleshow/78266626.cms)).
- A project-report site states an industrial range of Rs 14–22 per Nm3 ([KAMRIT oxygen plant report](https://kamrit.com/business-plans/oxygen-plant)). That page is not a price index. A TradeIndia listing at 350 INR per cubic metre is a vendor offer and contradicts the range above. Neither is used as a model price.

### Dolomite and dolochar

- Dolomite prices in India were reported up 9.29% in May 2026, with sponge iron named as a buyer. The article does not print an INR-per-tonne dolomite price ([ChemAnalyst, 18 June 2026](https://www.chemanalyst.com/NewsAndDeals/NewsDetails/steel-boom-pushes-indias-dolomite-prices-up-nearly-10-in-may-42853)).
- Plant returns show dolochar quantities, not prices. Giridhan Metal, Jamuria, generated 40,858 tonnes of dolochar in 2024–25 and reused all of it in the captive boiler ([environmental statement](https://giridhanmetal.com/wp-content/uploads/2026/04/04-Environment-Statement_FY-2024-2025_compressed.pdf)). Super Smelters, Jamuria, generated 119,133 tonnes of dolochar in 2024–25 ([environmental statement](https://supershakti.in/storage/app/public/images/7.%20Environmental%20Statement%202024-25.pdf)).
- A Raipur project report gives a mass balance per 100 tonnes of sponge iron: iron ore 160, coal 120, dolomite 5, char or dolochar 30 ([Om Sponge project report](https://environmentclearance.nic.in/DownloadPfdFile.aspx?FileName=v36BAU8AeO9ukVLW0xTZMFvDQPq5o5H5o2GQxScIXoU9KQ1sGAqSrU1pt7zeOs4CJM0onSHrCSgibExGJYg2Qr94ylRe9aOj0SRoKh2npotYCm528LRkiNajpwigsCuZpaERxgNN0Dlx0jcturfoYg%3D%3D&FilePath=93ZZBm8LWEXfg%20HAlQix2fE2t8z%2FpgnoBhDlYdZCxzUlDadBGu7t8v4JoQvNU6UBlSmL0YQ7WQYaxkvlQvexKQ%3D%3D)). No rupee prices.

### Steam-cycle efficiency and export tariff

No retrieved page states a Rankine-cycle efficiency for an Indian sponge-iron waste-heat plant. The Om Sponge report says the Rankine efficiency can be raised by superheat and reheat, and does not give a percentage.

No retrieved page states a current waste-heat export tariff. One 2026 commentary uses Rs 7 per kWh only as an assumed example and says so ([Senseible, on a TERI Bankura profile](https://www.senseible.com/)). It is not adopted.

## 3. Every local paper, and the parameters it actually states

The model value, where one is in use, is the one in `parameters.json` today. "Held" means the number is recorded and is not the value the model runs on.

| Paper | Parameters stated | In the model? |
|---|---|---|
| Dey et al. 2015 | Calibration plant, 453.6 TPD. Ore Fe, gangue, coal analyses, char, dolomite CaO 28% and MgO 20%, discharge 1,020 °C, feed-end gas 900 °C, radiation loss 6.76% of coal net heating value | Yes. These stay the calibration. They are not replaced by other plants |
| Nitturu et al., CEEW, July 2024 | Pellets 1.4–1.6 t/t, lump 1.8–2.0 t/t, domestic coal 1.4–1.6, imported 0.9–1.1, power 55–65 kWh/t with some plants at 80–100, installed waste heat about 2 MW per 100 TPD (450 kWh/t) and recovery at most 350–380, CO2 2.08 / 1.84 / 1.53 t/t by coal and ore route. Also section 1 above | Survey bands are checks. The INR 9 crore/MW figure is held, not used |
| CEA, version 20, December 2024 | Grid factor 0.727 t CO2/MWh for 2023–24, including renewables. Operating margin 0.962, build margin 0.552 | 0.727 is the model value. The other two factors are not |
| BEE Odisha DPR, 2011 | 2 × 100 TPD, 4 MW, 96,000 / 9,600 / 86,400 kWh/day, gas 1,005 °C to 170 °C, steam 22,561 kg/h at 66 kg/cm2 and 485 °C, investment INR 960.75 lakh, power valued at INR 3.3/kWh. A second set in the same file is about half of this | The 10% auxiliary fraction is used. The 2011 capital cost is the low bound, not the value |
| BEE MSME guidelines, 2019 | Rotary-kiln exhaust 850–900 °C, waste-heat recovery rate 49% standard and 58% target, heat-exchanger efficiency 60% and 65%, flue gas 100–150 °C, biomass fuels 3,100–4,500 kcal/kg, specific energy 0.64–0.82 toe per tonne of sponge iron | 60% and 150 °C and the low-end biomass heating value are used. The toe band is a performance indicator, not an input |
| Prasad, Prasad and Khanam, 2011, design modifications | 500 t/day case. Conventional coal 21.437 t/h. Case 2, feed and air preheat on 850 °C after-burner gas, coal 14.892 t/h, stated as 30.5% less coal and 72.6% less water | Held. Not used as an observed saving |
| Prasad, Kumar and Khanam, Energy Efficiency 2011 | Coal Rs 2,500/t and water Rs 60/t. Combustion efficiency assumed at 70%. One integrated case, capital about Rs 6.2 crore, payback 55 days | Coal price agrees with the later Gaurav table, which is the value used. The 70% is an assumption in that paper, not the BEE heat-exchanger figure |
| Kumar and Khanam, 2012 | Air preheat to 170 °C with a 709 kW exchanger. Coal cut 4.8% in one case and 8.7% in another. Coal Rs 2,500/t, water Rs 2/t. Average moisture of coal and ore stated as 3.58% | Coal price agrees with the value used. The moisture figure is not used, because Dey and Gaurav 2024 state different moistures |
| Tirumalaraju, Khanam and Sahoo, 2012 | 100 TPD. Coal from 6.144 t/h to 5.88 t/h, stated as 4.3%, using gas after the ESP. Power consumption cited as 45–130 kWh/t | Held. The power band is wider than the CEEW survey, which is the value used |
| Gaurav and Khanam, Energy 2017 | Power-only case 8.97 MW, payback 4.17 years. Preheat case 37.4% less coal, payback 3.22 years. Electricity Rs 3.5/kWh. Coal Rs 2,500/t. Feed coal, ore and dolomite specific heats 1,380, 960 and 1,028.38 J/kg·°C | Rs 3.5/kWh and the feed-coal specific heat are used. The 37.4% case is held and is not added to waste-heat power |
| Gaurav et al., Energy 2024 | Table 1 specific heats: kiln feed 1,092.7, kiln air 1,032.6, slinger coal 1,884.30, kiln outlet 687.9, waste gas 1,140 J/kg·°C. Table 2: ore 2,600 INR/t, coal 2,500 INR/t, boiler-turbine 46,800 INR/kW, maintenance 0.2 INR/kWh. Combined case 2.757 MW, payback 2.62 years. Ore moisture 2%, coal moisture 13% | Ore price, coal price, boiler-turbine cost, maintenance and waste-gas specific heat are used. Coal moisture is not used, because the coal analysis is Dey's |
| Rajesh, Nandi and Pabi, 2016 | One 100 TPD kiln. Oxygen 8 Nm3/t. Air 2,600 to 2,150 Nm3/t. Hourly coal 4.29 to 4.15 t/h. Output +6%. Campaign 50 to 100 days. Authors also say specific coal falls 6% | The table is the oxygen case. No oxygen price in the paper |
| TERI, DRI options, 2021 | Producer gas: about 20% energy, 4,200 t coal/year, INR 260 lakh/year, 7,500 t CO2/year, no capital cost. Ore preheat to 650 °C, about 15%, investment INR 350 lakh. Coal drying 3% in the text and 3.5% in the table | Producer gas is a separate case. The two drying figures are not averaged |
| TERI Raipur cluster, 2024 | Repeats the producer-gas figures in Table 10. Waste heat: 4 MW, investment INR 2,800 lakh, payback 3.2 years | Held as the high capital-cost bound |
| TERI financing report, 2023 | Coal-DRI specific energy 4.51 Gcal/t, range 4.10–5.26. Green hydrogen about 4–5 USD/kg. Several retrofit costs in USD, with inconsistent plant sizes | The 4–5 USD/kg is the top of the hydrogen price range, converted at 95. The USD capital costs are not converted into a single rupee project cost |
| Nduagu et al., 2022 | Rotary kiln: power produced 451 kWh/t, net −351 kWh/t. Life-cycle CO2 1,391–1,880 kg/t | Checks. Not used to force the waste-heat calculation |
| Hall et al., TERI, 2025 | Hydrogen about $3.5/kg, tender range $3.27–4.23/kg. Electricity in that figure $50/MWh. Discount rate 8%. Round-the-clock power just over ₹5/kWh in June 2025. Kilns from 50 TPD. Metallisation 89–90% over 8–10 hours | $3.5/kg at 95 INR, and the 8% discount rate, are used. ₹5/kWh is the top of the power-price range |
| Kamal et al., 2026 | Hydrogen for a shaft furnace: literature 53.5–59.6 kg/t, their model 55.7, design value 59.6. Indian electricity tariff ₹3.5/kWh. Project life 20 years. Iron ore 1.5 t per t DRI for their 1 MTPA shaft case | ₹3.5/kWh and the 20-year life are used. 59.6 kg/t is a check, not the kiln stoichiometry |
| CSE, Forging Transition, 2026 | Kiln control 3–5% coal, capital INR 0.5–1 crore. Feed preheat 8–10% against 19.0 GJ/t, capital INR 5–15 crore. Waste heat 60–90 kWh/t, capital INR 30–60 crore. Shell loss 5–10 kcal/kg | Kiln control uses the low end, 3%, capped at 5%, and INR 0.5 crore. The 60–90 kWh/t conflicts with Nduagu and CEEW and is not the generation figure |
| CSE, Decarbonizing India's iron and steel, 2022 | Coal-based DRI-EAF/IF emission factor about 2.8–3.2 t CO2 per tonne of crude steel. Production shares by route | No kiln operating parameter was taken from this report. It is a sector inventory |
| Bhardwaj et al., Chemical Engineering Transactions, 2023 | Per tonne of crude steel: biochar in place of feed coal, direct CO2 cut 1,241.5 kg and power generation down 378.7 kWh. Gravimetric separator, electricity credit 175.9 kWh | Held. The basis is crude steel, not a tonne of DRI |
| Bhardwaj et al., Energy, 2024 | Kiln assumed at 90% of rated capacity. A 350 TPD kiln is discussed. Sponge iron carbon about 0.1%. Dolochar carbon 22%, dust carbon 12%. The paper's own grid factor in one calculation is 0.82 kg/kWh | 90% utilisation is used. The 0.82 factor is the paper's old assumption. The model uses the CEA value 0.727 |
| Vigneswaran et al., 2024 | Palm-kernel-shell charcoal: 24.99 MJ/kg, ash 11.27% in the text and 11.7% in the conclusions, moisture described as absent. Charcoal cost $295–525/t. Business-as-usual carbon footprint 2,525 kg CO2e per tonne of sponge iron. Coal for that case 482 kg per tonne of sponge iron with 1,471 kg of ore | Heating value, ash and the dollar price are stored and are not the fuel the biomass case burns, because elemental carbon is not stated |
| Fan and Friedmann, 2021 | Biomass or charcoal cost $295–525/t, the range Vigneswaran quotes. Hydrogen prices for a shaft or blast-furnace calculation, including green hydrogen at $5.57/kg. One table lists 380 kWh per tonne for coal-based DRI | The dollar range is the charcoal price above. The 380 kWh figure is not used. The CEEW kiln survey is 55–65 kWh/t |
| DRI Update, October 2024 | Coal-based DRI emission intensity 2.15–2.45 t CO2 per tonne, before a further 0.55 t from electric steelmaking. No prices | Held as a sector range. Not a plant input |
| Biswas, Asthana and Rau, 2003 | Combustion efficiency taken as 0.7. About 12 kg of carbon and 37,336 kcal per kmol for the FeO reduction step. Mechanical seal 10 kW on a 2.6 m by 40 m kiln | Not a coal-rate retrofit. The 0.7 is that paper's assumption, not a measured kiln efficiency |

## 4. What is still not a defensible model input

- A dolomite price in INR per tonne. The May 2026 article gives a percentage change and no price.
- A dolochar sale price. The returns give tonnes, not rupees.
- An oxygen price for a kiln. The 2020 regulated gas price and the vendor ranges are not a sponge-iron contract.
- A waste-heat export tariff.
- A steam-cycle efficiency.
- Elemental carbon of an Indian kiln charcoal, paired with that same material's price. Rice-husk carbon is available for the raw husk. Palm-kernel charcoal carbon is not.
- Daily fixed operating cost of a 100 TPD kiln.
- Capital cost of a biomass feed system or a hydrogen injection system, in INR, for a rotary kiln.

## Sources

- [CEEW, Decarbonising coal-based DRI, July 2024](https://www.ceew.in/sites/default/files/decarbonising-coal-based-dri-production.pdf) (10 July 2024)
- [CEA, viability study on agricultural-waste cofiring](https://cea.nic.in/api/dashboardReports/view-pdf/en/efb59209-2c59-4035-aabb-5f584de7f0d8) (December 2020)
- [Madras Agricultural Journal, rice husk characterisation](https://masujournal.org/store_file/archive/106-Special-279-283.pdf) (2019)
- [CSE, Agro-residue for Power](https://www.cseindia.org/content/downloadreports/10421) (October 2020)
- [CEEW, ex-situ crop residue management](https://www.ceew.in/publications/ex-situ-crop-residue-management-scalable-solution-for-paddy-stubble-burning) (20 April 2023)
- [CEEW, biomass pellets for power](https://www.ceew.in/publications/techno-economic-assessment-biomass-pellets-market-and-power-generation-india) (October 2016)
- [Times of India, oxygen price](https://timesofindia.indiatimes.com/india/oxygen-price-should-be-capped-for-hospitals-not-suppliers/articleshow/78266626.cms) (23 September 2020)
- [KAMRIT, oxygen plant project report](https://kamrit.com/business-plans/oxygen-plant)
- [ChemAnalyst, dolomite prices, May 2026](https://www.chemanalyst.com/NewsAndDeals/NewsDetails/steel-boom-pushes-indias-dolomite-prices-up-nearly-10-in-may-42853) (18 June 2026)
- [Giridhan Metal, environmental statement 2024–25](https://giridhanmetal.com/wp-content/uploads/2026/04/04-Environment-Statement_FY-2024-2025_compressed.pdf) (26 September 2025)
- [Super Smelters, environmental statement 2024–25](https://supershakti.in/storage/app/public/images/7.%20Environmental%20Statement%202024-25.pdf) (24 September 2025)

Search output files: `/tmp/dri-prices-1.json`, `/tmp/dri-biomass-h2.json`, `/tmp/dri-gaps.json`, `/tmp/dri-three-prices.json`.
