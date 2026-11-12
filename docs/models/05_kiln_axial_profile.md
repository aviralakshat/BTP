# 05 Axial kiln profile

**Code:** `project/src/kiln/axial.py` (`axial_profile`)
**Question:** where along the 80 m kiln is the heat used?

Model 0.7.0. This is a reconstruction of the kiln in Dey, Dey and Datta (2015), not a rate model.

## What is measured

The calibration kiln, run at 453.875 t/d of sponge iron:

| Quantity | Value | Source |
|---|---|---|
| Length | 80 m | Dey et al. 2015, process description |
| Internal diameter | 4.55 m | same |
| External diameter | 5 m | same |
| Inclination | 2.5° | same |
| Preheat zone | the first half of the length | same, "approximately half" |
| Reduction zone | the second half | same |
| Solids temperature | 1020 °C, maintained | same |
| Waste gas at the feed end | 900 °C | same, and `kiln.waste_gas_temp_c` |
| Waste gas at the discharge end | 1170 °C | same |

Feed coal enters at the feed end. Injection coal is blown in from the discharge end. Air is supplied along the length. The ledger has no separate air enthalpy, so the axial model does not invent a port-by-port air schedule.

## What is not measured, and is therefore not in the model

Figure 4 plots gas temperature, bed temperature and metallisation along the kiln. It is a figure, not a table. Nothing in the extracted text gives a rotation speed, a fill fraction, or a rate constant for the Boudouard reaction or the iron-oxide steps. Tirumalaraju (2012) says the residence time of ore in a kiln is about 10 hours. That sentence is not a measurement on Dey's 80 m kiln, so it is not used. Biswas et al. (2003) give 2.6 m by 40 m for a 100 TPD kiln. The capacity slider does not switch to that geometry, because no rule is given for how length and diameter scale.

Without those inputs a kinetic solver would be a set of assumed constants tuned to the measured metallisation. That is not done.

## What the code does

`src/kiln/axial.py` divides the 80 m into `kiln.n_cells` equal cells (20 by choice, not by measurement). Each global term of the kiln energy ledger is placed once:

- Feed-coal heating value at the feed-end cell. Injection-coal heating value at the discharge-end cell.
- Moisture evaporation and coal devolatilisation across the preheating cells.
- Unburnt volatiles, CO slip, waste gas and flue dust leaving at the feed end, where the gas leaves.
- Reduction, and dolomite calcination, across the reduction cells. Dey says reduction starts in that half. Dey lists dolomite decomposition as a duty of the heat and does not name its zone; it is placed where the bed is at reaction temperature.
- Product solids and the carbon locked in them leaving at the discharge end.
- Shell loss spread evenly. Dey does not give a distribution.

Gas temperature at a cell is the straight line between 900 °C and 1170 °C. Solids temperature is 1020 °C in every cell. Metallisation is zero through the preheating half and a straight line to the measured product value at the discharge face.

Cells do not exchange heat. A cell residual is the heat that would have to travel along the kiln for that cell to close. It is printed and not moved. The sum of the cell residuals is the kiln residual, at 10 cells and at 40 cells.

## What would make it a prediction

A digitised Figure 4, the kiln rotation speed, and a cited rate law with its constants. Until those exist, discharge metallisation stays an input of the planning twin, and the axial page says so.
