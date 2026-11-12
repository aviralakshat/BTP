# 07 Plant economics

**Code:** `project/src/economics/economics.py` (`EconomicsModel`, `capital_recovery_factor`, `scaled_cost`, `fixed_opex_inr_per_day`)
**Question:** what does a tonne of sponge iron cost at the plant gate?

## Purpose

This is the cost per tonne that the pathway search minimises. It prices the physical streams from the baseline plant, credits the by-products, and puts retrofit capital on the same per-tonne basis as operating cost.

## Method

```
variable  = ore + coal + dolomite + purchased power + retrofit operating cost
cash cost = variable + fixed cost − dolochar credit − power export revenue
cost      = cash cost + annualised capital
```

| Line | Formula | Price parameter | Reference price |
|---|---|---|---:|
| Iron ore | wet ore (t/t) × price | `econ.ore_price_inr_per_t` | ₹2,600/t |
| Coal | (feed + injection coal) × price | `econ.coal_price_inr_per_t` | ₹2,500/t |
| Dolomite | flux rate × price | `econ.dolomite_price_inr_per_t` | ₹2,000/t (indicative) |
| Purchased power | net grid import × tariff | `econ.power_tariff_inr_per_kwh` | ₹3.5/kWh |
| Fixed cost | daily fixed cost ÷ daily output | `econ.fixed_opex_inr_per_day` | ₹35,000/day at 100 TPD |
| Dolochar credit | char made × price | `econ.char_credit_inr_per_t` | ₹1,500/t (indicative) |
| Power export | exported kWh × tariff | `econ.export_tariff_inr_per_kwh` | ₹3.3/kWh |

### Capital

Retrofit capital is annualised with a capital recovery factor, so capital and operating cost can be added:

```
CRF = r (1 + r)^n / ((1 + r)^n − 1)        r = 8%, n = 20 years  →  CRF = 0.1019
annualised capital per tonne = (capex × CRF + capital-linked annual cost) / annual tonnes
```

The 8% is the weighted average cost of capital in Hall et al. (TERI 2025). The 20 years are from Kamal et al. (2026), Table 3. This charge is pre-tax and all-equity. The financed view with debt and tax is model 08.

### Scaling with plant size

Capital and fixed cost scale on a power law, C = C_ref × (S / S_ref)^0.67 (Kamal et al. 2026, Eq. 4). Fixed cost scales on rated capacity, not on production, because labour and overheads are paid whether or not the kiln runs full.

## Result on the reference plant

| Line | ₹ per tonne DRI |
|---|---:|
| Iron ore | 4,216 |
| Coal | 2,561 |
| Fixed cost | 389 |
| Purchased power | 210 |
| Dolomite | 63 |
| Dolochar credit | −205 |
| **Cost per tonne** | **7,234** |

Annual output is 29,700 t (100 t/day × 90% × 330 days). Ore is 58% of cost and coal 35%. So the coal-cutting retrofits move cost by hundreds of rupees per tonne, not thousands.

## Two corrections this model carries

- **Export revenue is not discarded.** An earlier version clamped waste-heat power to in-plant demand with `max(0, …)`, which threw away the export revenue that is most of the waste-heat business case.
- **Capital enters the cost.** An earlier version displayed retrofit capital but never added it to the cost per tonne, so every retrofit looked cheaper than the baseline.

## Tests

`tests/test_model.py` checks that capital raises cost, that the capital recovery factor is sane, that the breakdown sums to the total, and that waste-heat export revenue is kept. `tests/test_hardening.py` checks that fixed cost equals the configured value at its reference size, falls per tonne with capacity, and that waste-heat unit cost falls with size and matches Gaurav et al. at the reference size.

## Limits

The fixed daily cost at 100 TPD comes from one 2016 pre-feasibility report, in 2016 rupees, and its 0.67 exponent is carried over from capital cost. Dolomite and dolochar prices are indicative supplier quotes.
