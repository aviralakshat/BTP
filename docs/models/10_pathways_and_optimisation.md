# 10 Pathways and optimisation

**Code:** `project/src/analysis/scenarios.py` (`pathway_grid`, `least_cost`, `pareto_front`, `h2_breakeven_price`), `project/src/optimization/search.py` (`search_all`), `project/src/analysis/macc.py`
**Question:** which combination of retrofits reaches a CO₂ target at the lowest cost per tonne?

## The pathway grid

`pathway_grid()` evaluates every combination of:

| Lever | Levels |
|---|---|
| Waste heat recovery | off, on |
| Biomass | 0, 5, 10, 15, 20% |
| Hydrogen | 0, 5, 10, 15, 20, 30% |

That is 60 plants, each evaluated with `evaluate()` on one solved baseline, so biomass and hydrogen are checked together on one reductant-carbon balance. Any of the other levers (oxygen, kiln control, producer gas, char recycling, variable-speed drives) switched on in the controls is applied to every row.

## Least cost to a target

`least_cost(target)` returns the cheapest feasible row whose CO₂ cut is at least the target. The roadmap repeats this for targets of 10% to 60% in 10-point steps.

Reference plant (100 t/day, imported coal, green hydrogen at ₹332.5/kg):

| Target | Least-cost pathway | CO₂ cut | Cost, ₹/t | Change | Abatement cost, ₹/t CO₂ | Capital |
|---:|---|---:|---:|---:|---:|---:|
| 10% | WHR + rice husk 10% | 11.8% | 6,942 | −293 | −1,168 | ₹14.7 crore |
| 20% | WHR + rice husk 20% | 21.5% | 7,434 | +200 | 437 | ₹18.1 crore |
| 30% | WHR + rice husk 20% + hydrogen 10% | 31.2% | 13,843 | +6,608 | 9,948 | ₹23.4 crore |
| 40% | WHR + rice husk 20% + hydrogen 20% | 41.0% | 20,251 | +13,017 | 14,942 | ₹28.7 crore |
| 50% | WHR + rice husk 20% + hydrogen 30% | 50.7% | 26,660 | +19,425 | 18,018 | ₹34.0 crore |
| 60% | Not reachable within the substitution caps | | | | | |

The maximum cut on the grid is 50.7%. The cost curve has a sharp knee at about 20%. Below it, waste heat and biomass pay for themselves or nearly so. Above it, every extra point needs hydrogen, at roughly ₹10,000 to ₹18,000 per tonne of CO₂ avoided.

## Pareto front

`pareto_front()` keeps the feasible rows that no other row beats on both cost and CO₂. It is the efficient frontier drawn in the Pathways view.

## Hydrogen break-even

`h2_breakeven_price()` finds the hydrogen price at which substitution adds no operating cost. Coal, power and hydrogen prices enter cost linearly, so the break-even is the root of a straight line. On the reference plant it is about ₹13 per kg, against ₹332.5 used.

## Continuous search

`search_all()` in `src/optimization/search.py` relaxes the grid. It evaluates every grid cell, then a mesh from zero to each cap, then walks downhill from the best point in halving steps. The reductant check and the CO₂ target are hard constraints. Because the grid cells are inside the candidate set, the continuous result can never be worse than the grid result by more than the cost tolerance, and a point between cells can be better. A test enforces that.

## Marginal abatement curve

`marginal_curve()` in `src/analysis/macc.py` follows the dependent-option rule of Bhardwaj et al. (2024), Section 5.1. Start from the bare plant. At each step, recompute every remaining move against the package already chosen, and take the move with the lowest marginal abatement cost that still cuts CO₂. A move the reductant check rejects is skipped. A move that does not cut CO₂ is listed but not drawn.

`carbon_overlay()` adds a carbon charge to the cost of the baseline and of each pathway. `price_break_evens()` finds the carbon price at which a pathway ties the baseline. That price is the pathway's abatement cost, so the identity is used rather than a second calculation. The carbon-price cases (no charge, and the Q3 2026 EU CBAM certificate price) are in `project/config/analysis.json`.

## Tests

`tests/test_scenarios.py` checks that the frontier is monotone in cost and CO₂, that the least-cost pathway meets its target, that an unreachable target returns nothing, and that the hydrogen break-even zeroes the cost change. `tests/test_uncertainty.py` checks that the abatement-curve marginals add up, that the carbon price tying the baseline is the abatement cost, that the hydrogen break-even is linear, and that the continuous search meets its target without losing to the grid.
