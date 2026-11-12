# 11 Uncertainty, abatement cost and the search

**Code:** `project/src/analysis/sensitivity.py`, `montecarlo.py`, `macc.py`, `plant_eval.py`, `settings.py`
**Question:** which inputs move the answer, and by how much?

Model 0.5.0. This layer does not change the plant. `parameters.json` is untouched, and the golden baseline still applies. Settings that are method choices, not plant measurements, are in `project/config/analysis.json`. A distribution override, if one is ever warranted, goes in `project/config/distributions.json` and nowhere in the model code.

The numbers below are the imported-coal plant at 100 TPD and 90% utilisation. The dashboard recomputes them for whatever the sidebar is set to.

## One parameter at a time

Each of the 68 sensitivity-flagged parameters is solved at its own minimum and at its own maximum. Everything else stays at the base case. The swing is the absolute change between those two plants. A change below 1 INR/t or 0.0001 t CO2/t is reported as no effect, because the coal-rate solver itself stops within 0.0001 t/t.

Three groups do not get a bar:

- **No cited range.** Coal price, ore price, the discount rate, waste-gas specific heat, the biomass handling rate, char separation and the VFD speed factor have a minimum equal to their maximum. There is nothing to vary. The break-even table still solves for the coal price at which a pathway would tie the baseline; that price is a result, not a range.
- **Not an input.** While `coal.rate_mode` is `solve`, the configured coal rate is replaced by the energy-balance solution.
- **Not a coal.** Moving feed carbon, feed ash or injection carbon on its own makes the analysis fail to sum to 100%, and the plant refuses it. Those rows stay in the table as failures.

Ash is also reported a second way. The closed-analysis row changes the ash and rescales the rest of the coal, including the heating value, on the dry ash-free basis, so the analysis still sums to one. Injection ash has no minimum or maximum in the parameter file, so that closed row uses the store's default band around the measured value.

On the bare plant the largest cost swing is the feed-coal heating value, about INR 1,519/t, with the carbon analysis held fixed. That pair is not a consistent coal: losses follow the carbon, and the input follows the heating value. The closed ash row, which moves them together, swings cost by about INR 545/t. Both are shown, and they answer different questions.

Abatement cost and the CO2 cut are computed on the reference package, waste heat recovery plus 10% biomass plus 10% hydrogen. A parameter that belongs to a lever that package leaves off (oxygen, kiln control, producer gas, char recycling, variable frequency drives) is solved with that lever switched on, and the bar name says so. The biogenic-CO2 switch is evaluated off and on. Its stored band is not used, because both ends of that band stay on.

## Morris

The global screen is the Morris method as set out by Campolongo, Cariboni and Saltelli (2007). Each factor is coded on [0, 1] across its own cited band. There are 8 trajectories and 4 levels, so the step is 2/3 of the band. mu-star is the mean of the absolute elementary effects on that coded factor. A factor moved across its whole band is then comparable with another.

The same runs record bare-plant cost, bare-plant CO2, reference-package cost and reference-package abatement cost. The convergence check splits the 8 trajectories in half and reports the Spearman rank correlation of the two cost rankings. On the base plant that correlation is 0.86: the large effects keep their order, and the order among the smaller ones does not. Scenario choices are not factors. Coal components that must sum to one are replaced by the closed ash draw, and a heating value that is itself a factor is applied after the rescaling.

## Monte Carlo

400 draws. Each factor is triangular on its minimum, its base value and its maximum, independently. No correlation is applied, because none is documented. A draw the plant refuses is counted and left out of the percentiles. On the base plant, 15 of the 400 draws do not solve: the coal rate has no root inside the search range once several bands are taken to their extremes together. The result reports P10, P50 and P90 of the headline metrics, and the share of solved draws in which each saved pathway is feasible, cheaper than the baseline, and lower in CO2. An infeasible draw counts as not cheaper and not lower in CO2.

The dashboard does not run this sample, or the Morris sample, until the button on the Uncertainty tab is pressed. Both are seeded (`20261110` in `analysis.json`), so a repeat is the same sample.

## Abatement curve

The curve follows the dependent-option rule in Bhardwaj et al. (2024), Section 5.1. Start from the bare plant. At each step, recompute every remaining move against the package already chosen and take the one with the lowest marginal abatement cost that still cuts CO2. A move the reductant check rejects is skipped. A move that does not cut CO2 is listed and is not drawn.

Bhardwaj treat char recycling as exclusive with gaseous reductants. This model has no such exclusion. The reductant-carbon ratio is the constraint that is enforced. Stacked coal-cutting studies were not measured as a package, and the tab says so.

On the base plant the first bar is waste heat recovery, about −19,900 INR/t CO2, because the CO2 cut is only the scope 2 of the 60 kWh/t the plant stops buying. Producer gas is next. It has no sourced capital cost, which is why it looks cheap, and the curve carries that warning. Char recycling saves money on its own and costs money once the earlier coal cuts have already removed most of the coal it would have replaced. Variable frequency drives stop cutting CO2 once waste heat recovery has removed the grid purchase, because exported power is not given a negative scope 2; they drop off the curve and remain a cost saving.

A later bar can be cheaper per tonne than an earlier one. Biomass capital scales with the 0.67 exponent, so the next 5% costs less capital per tonne than the first. The curve is the order the measures were added, not a re-sort.

## Search

The continuous search minimises cost per tonne subject to a CO2-reduction target and the reductant-carbon check. Waste heat recovery is on or off. Biomass and hydrogen are continuous up to their caps. Every cell of the pathway grid is evaluated, then a 21-by-21 mesh, then a walk downhill from the best point. Because the grid cells are in the candidate set, the continuous result cannot cost more than the grid result (tolerance 0.05 INR/t). It can cost less, because it can stop between the 5% steps.

At a 10% CO2 cut the grid picks waste heat recovery plus 10% biomass. The continuous result meets the cut at about 8% biomass and saves about INR 90/t against that grid cell. At 30% the grid has to bring in hydrogen, because its biomass steps stop at 20%. The continuous result stays on biomass, near the 30% cap, and avoids that hydrogen.

## Prices

The carbon price at which a pathway ties the baseline is the abatement cost. That identity is used directly. Coal price, power tariff, export tariff and hydrogen price enter the cost linearly. The root of that line is checked at a third price, and a pathway that does not use the price is reported as unaffected. Waste heat recovery does not change the coal bill, so its ranking does not depend on the coal price. It does depend on the power tariff and the export tariff.

There is a separate hydrogen break-even, already in the pathway tab, which is the price at which a kilogram of hydrogen displaces its heating-value equivalent of coal. That figure ignores capital and carbon. The break-even in this layer includes them. On the base plant, waste heat recovery plus 10% biomass plus 10% hydrogen ties the baseline at about INR 19/kg. The energy-parity price is about INR 13/kg. The cited price is INR 332.5/kg.

Two carbon charges are defined. Neither is marked as the official case for the report.

| Case | Charge | Source |
|---|---|---|
| No carbon charge | INR 0/t | The plant-gate cost has no carbon term. The GST compensation cess of Rs 400/t coal was removed by the 56th GST Council, Ministry of Coal, 11 September 2025. GST at 18% is not added as a carbon price. |
| CBAM certificate, Q3 2026 | EUR 82.32/t × 104.8645 INR/EUR = INR 8,632/t | European Commission, price of CBAM certificates, published 5 October 2026. ECB euro reference rate for the rupee on 6 November 2026, the latest rate printed on that page when it was read on 10 November 2026. |

The archived pages are `data/web/2025_PIB_Coal-GST-cess-removed.txt`, `data/web/2026_EC_CBAM-certificate-prices.txt` and `data/web/2026_ECB_Euro-reference-INR.txt`. Whether the report treats the CBAM price as the case is still open (`docs/project/OPEN_QUESTIONS.md`, question 4).
