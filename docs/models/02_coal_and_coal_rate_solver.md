# 02 Coal and the coal-rate solver

**Code:** `project/src/data/coal.py`, `project/src/models/plant.py` (`build_plant`, `solve_coal_rate`)
**Question:** how much coal does the kiln need per tonne of sponge iron?

## Purpose

The coal rate is the most important number in the plant. It sets fuel cost, CO₂ and the heat available for waste-heat power. Rather than typing it in, the model solves for the coal rate at which the kiln heat balance closes. A good coal rate then becomes evidence that the heat balance is right.

## Coal composition rules

`src/data/coal.py` enforces that a coal is a physical material.

- The ultimate analysis (C, H, O, N, S, ash and moisture) and the proximate analysis (fixed carbon, volatile matter, ash and moisture) must each sum to one. `check_composition()` raises `InconsistentInputError` if either does not.
- A coal with different ash is built with `daf_rescale()`, which keeps the organic matter in the same proportions on a dry, ash-free basis. Changing the ash on its own would leave the kiln paying for carbon the coal cannot contain.

This rule found a real input error: the old domestic-coal preset summed to 106% and gave 2.05 t of coal per tonne. Closed properly on Dey's dry, ash-free basis, the same 30% ash, 19,500 kJ/kg coal solves to 1.416 t/t.

## Solver

`solve_coal_rate()` finds the coal rate at which the kiln energy residual is zero.

- **Method:** bisection between 0.60 and 2.50 t of coal per tonne of DRI, stopping when the residual is under 1 kJ or the bracket is narrower than 0.0001 t/t.
- **Why bisection is safe:** more coal adds to both sides of the ledger, but the reduction duty and the product's sensible heat are fixed per tonne of DRI. The residual is therefore monotonic in coal rate, so there is one root.
- **When it fails:** if the residual does not change sign over the bracket, the coal quality or loss fractions are inconsistent. The solver says so and returns `converged = False` rather than a number.

`build_plant()` honours `coal.rate_mode`:

| Mode | Behaviour |
|---|---|
| `solve` (default) | Coal rate is solved from the heat balance. |
| `specified` | `coal.rate_t_per_t_dri` (0.95) is used as given, and the heat balance reports whatever residual results. |

Import plant construction from `plant.py`, not from `baseline.py`, so the mode is honoured.

## Result on the reference plant

| Coal | Solved rate | Heating value in | Check |
|---|---:|---:|---|
| Imported (Dey's analysis) | 1.025 t/t | 5.586 Gcal/t | Within the CEEW survey range of 0.9 to 1.6 t/t |
| Domestic, 30% ash | 1.416 t/t | | Inside the domestic survey range of 1.4 to 1.6 t/t |

The plant solves from 5% to 45% coal ash.

## Tests

`tests/test_hardening.py` checks that the configured analyses sum to one, that raising ash alone is refused, that `daf_rescale()` keeps the organic ratios, that the plant solves and closes across the ash range with the coal rate rising smoothly, and that an unsolvable coal raises instead of returning a default. `tests/test_model.py` checks that the solver brackets a root and that specified mode uses the configured rate.

## Limits

The domestic result moves by about 0.28 t/t between the preset heating value and one scaled from Dey's coal, because losses follow carbon content while heat input follows heating value. A measured domestic ultimate analysis with its own heating value is needed. Picking a heating value to land in the band would be tuning, not validation.
