# Validation report

Model 0.5.0, 10 November 2026. Imported-coal preset, 100 TPD rated, 90% utilisation, coal rate solved from the kiln energy balance. Regenerate the table with `./venv/bin/python src/validation/literature_check.py`; the full text is in `project/outputs/validation_report.txt`.

## Literature checks

| Check | Model | Band | Verdict |
|---|---|---|---|
| Iron ore consumption, t/t | 1.589 | 1.4–1.6 | PASS |
| Coal consumption, t/t | 1.025 | 0.9–1.6 | PASS |
| Specific energy consumption, Gcal/t | 5.586 | 4.9–8.2 | PASS |
| DRI total iron | 0.926 | 0.89–0.93 | PASS |
| Degree of metallisation | 0.902 | 0.88–0.94 | PASS |
| Direct (stack) CO2, t/t | 2.083 | 1.39–3.2 | PASS |
| Auxiliary power, kWh/t | 60 | 55–100 | PASS |
| WHR gross generation, kWh/t | 418 | 350–460 | PASS |
| WHR export, kWh/t | 316 | 300–400 | PASS |
| Waste-gas sensible heat share | 0.231 | 0.18–0.30 | PASS |
| H2 for complete reduction, kg/t | 46.9 | 53.5–59.6 | INFO |

Mass balance closes to 1.20% and all seven element balances pass. The energy balance closes to under 0.001%.

Three of these passes are weak evidence. Metallisation and DRI iron follow from configured product composition, so they cannot fail. The coal band is wide because it spans imported and domestic coal. The waste-heat checks depend on a boiler efficiency and a cycle efficiency that are design figures from BEE documents, not a measured boiler test.

The hydrogen line is reference only. The model's 46.9 kg/t is the stoichiometric requirement for the oxygen it removes; Kamal et al.'s 53.5–59.6 includes excess hydrogen for a shaft furnace.

## What moved in 0.5.0

Three sourced values replaced engineering defaults inside the balance:

- **Excess air** 0.15 → 0.11348, Dey (2015) Section 3.7, Eq. (37). Less excess air means less nitrogen and oxygen heated to the waste-gas temperature. The solved coal falls from 1.048 to 1.025 t/t, SEC from 5.71 to 5.59 Gcal/t and direct CO2 from 2.131 to 2.083 t/t. The waste-gas sensible share falls from 0.239 to 0.231.
- **After-burner combustion** 0.95 → 1.0, from Prasad (2011) and Tirumalaraju (2012), who both describe complete burn-out in the ABC. With less coal to burn, WHR gross still falls slightly, from 421 to 418 kWh/t.
- **Calcined flux heat capacity** 0.92 → 1.037 kJ/kg·K, from NIST Shomate data for CaO and MgO weighted by Dey's dolomite. The flux stream is about 15 kg/t (31.7 kg dolomite × 48% CaO + MgO), so the effect is small.

None of these was chosen to fit a band. All ten scored checks passed before and after.

## Waste heat: cycle efficiency

In 0.3.0, gross generation was 466 kWh/t, a warning against Nduagu's 460 edge, with an unsourced cycle efficiency of 0.25. The BEE 2011 DPR, Annexure 2, gives the whole steam balance for its 4 MW plant: 22,561 kg/h of steam at 66 kg/cm² and 485 °C, enthalpy 800 kcal/kg, feed water 127 kcal/kg. Heat into steam is 22,561 × 673 = 15.18 Gcal/h, which matches the table's own row 23, or 17,658 kW. Four MW from that is a gross cycle efficiency of 0.2265.

The same report's turbine specification gives 2 MW from 18 t/h, which would mean 0.142. That table does not balance (18 t/h in, 1.75 bled, 9.125 to the condenser), so the heat-balance annexure is used and 0.142 is kept as the lower bound.

The value was not chosen to fit the band. It came from the only source in the folder that states a steam balance, and the gross check moved into the band as a result.

## Domestic coal investigation

**Finding: the 2.05 t/t result was an input error, not a physics error.**

The Domestic Coal preset changed four numbers: feed ash 0.30, injection ash 0.28, and the two heating values. It left Dey's carbon, hydrogen, oxygen, nitrogen, sulphur, volatile matter and fixed carbon untouched. Dey's analyses sum to exactly 1.000. The preset's feed coal summed to 1.063 and its injection coal to 1.067. The kiln was charged for a coal containing 60.6% carbon and 30% ash at once, and the energy balance computes its carbon losses (unburnt volatiles, char, dust) from carbon content. Those losses stayed at their high-carbon level while the heating value fell, which is the superlinear response noted in the plan.

The fix holds Dey's dry, ash-free composition and dilutes it with the new ash (`src/data/coal.py`, `daf_rescale`). Ash and heating value are exactly the preset's. Coal that misses 100% by more than 0.5% is now refused with an error.

| Case, 100 TPD, model 0.5.0 | Feed NHV, kJ/kg | Coal, t/t | SEC, Gcal/t |
|---|---|---|---|
| Dey coal (imported preset) | 22,530 | 1.025 | 5.59 |
| Preset as shipped in 0.3.0 (coal sums to 106%) | 19,500 | 2.02 | 9.52 |
| Domestic preset, composition closed (injection 28% ash, 20,200 kJ/kg) | 19,500 | 1.416 | 6.68 |
| Feed and injection both 30% ash, 19,500 kJ/kg | 19,500 | 1.450 | 6.75 |
| Same ash, NHV scaled from Dey on a dry ash-free basis | 20,592 | 1.171 | 5.76 |

The 2.02 row was measured on 0.3.0 before the char and dust change.

**What is still sensitive.** The 30%-ash rows differ by 0.28 t/t for a 5% difference in heating value. That spread is real model behaviour: the losses follow carbon content, the input follows heating value, so a heating value below what the composition implies is amplified. The preset's 19,500 kJ/kg implies a dry ash-free heating value of 29,200 kJ/kg against Dey's 30,860, i.e. a lower-rank coal than Dey's diluted with ash. Whether that is right depends on a full domestic analysis, and no paper in the folder gives one. CEEW give the 1.4–1.6 t/t consumption band but no coal analysis, and BEE 2019 says only "Indian coal up to 5,000 kcal per kg". The preset lands inside CEEW's domestic band, but its ash and heating value are not sourced.

The three points in the old open-work note, on a closed composition and model 0.5.0: 23.7% ash / 22,826 kJ/kg gives 1.000; 28% / 20,500 gives 1.282; 30% / 19,500 gives 1.450 (feed and injection set to the same values).

## Solids partition

While sweeping ash, the plant had no solution at 15% ash (the first point tried). Char was a fixed 0.1335 t per tonne of coal at 69.6% ash, so it demanded 93 kg of ash per tonne of coal whatever the coal held. Dust was a fixed share of the ore, but Dey's own ash balance (Table 10) assigns the dust's 35.94% SiO2 + Al2O3 to coal ash, so the dust also demanded about 53 kg of coal ash per tonne of DRI.

Both streams are now built from their sources, using shares computed from Dey Tables 6, 9 and 10:

- char ash = 0.406 × coal ash; char carbon = 0.0912 × coal fixed carbon;
- dust iron oxide = the ore's iron lost to dust; dust SiO2 + Al2O3 = 0.229 × coal ash; carbon and minor phases keep their Table 9 shares;
- free ash to cooler = the remainder (0.365 of coal ash at Dey's point, as in Table 10).

At Dey's measured coal rate this reproduces Dey's 0.1335 t char per tonne of coal and 0.1053 t dust per tonne of ore. The plant solves and both balances close from 5% to 45% ash (model 0.5.0):

| Ash | NHV, kJ/kg | Coal, t/t | SEC, Gcal/t |
|---|---|---|---|
| 0.05 | 28,333 | 0.781 | 5.29 |
| 0.15 | 25,236 | 0.901 | 5.44 |
| 0.24 | 22,450 | 1.046 | 5.61 |
| 0.30 | 20,592 | 1.171 | 5.76 |
| 0.40 | 17,495 | 1.464 | 6.12 |
| 0.45 | 15,947 | 1.672 | 6.37 |

(Feed and injection at the same ash, heating value scaled from Dey on a dry ash-free basis.)

## Boundary audit

Tests in `tests/test_hardening.py` hold the following:

- Every carbon atom entering in coal and dolomite leaves in char, dust, DRI, unburnt volatiles or gasified carbon.
- Stack CO2 is exactly every gas-phase carbon atom, including the volatiles that leave the kiln unburnt and burn in the after-burner.
- Every chemical-energy term leaving the kiln is labelled either "(lost)" (carbon in solids) or "to ABC" (volatiles and CO). The "to ABC" terms equal the energy the waste-heat module claims back, and the "(lost)" terms equal the solid-carbon loss.
- Scope 2 is net purchased power times the CEA grid factor.

Since 0.5.0, when a coal-cutting lever (kiln control, producer gas, oxygen, char recycling) runs with WHR, the after-burner heat WHR claims is scaled to the coal that remains. Before, WHR kept the baseline's after-burner heat whatever coal had been removed.

## Still open

- No measured domestic-coal ultimate analysis with a heating value.
- The cycle and boiler efficiencies are design figures, not a boiler test.
- Fixed daily cost is from one 2016 pre-feasibility report, in 2016 rupees; the scale exponent applied to it is carried over from capital cost.
- Five parameters still need a citation; `docs/parameters/data_provenance.md` gives the reason for each.
- Lump ore is not a preset.
