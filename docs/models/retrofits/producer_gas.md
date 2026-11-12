# Producer gas

**Code:** `project/src/retrofits/producer_gas.py` (`ProducerGas.calculate_impact`)

## What it does

Coal fines are gasified and the producer gas replaces the coal injected at the discharge end. TERI (2021) describes the scheme and states an energy saving of about 20%.

## Method

```
coal cut = 20% of coal energy (producer_gas.energy_saving_frac)
capital  = none charged
```

The same TERI section gives 4,200 t of coal, ₹260 lakh and 7,500 t of CO₂ saved a year for one 100 t/day reference kiln. Those figures are reported alongside the result, not added to the 20%, so the saving is not counted twice.

## Result on the reference plant

| Quantity | Value |
|---|---:|
| Coal cut | 20% |
| CO₂ change | −19.5% |
| Cost change | −₹512/t |
| Capital | none charged |
| Equity NPV | ₹9.86 crore |

## Limits

No source gives a capital cost for the gasifier, so none is charged. The NPV is therefore an upper bound, and IRR and payback are undefined (`no_investment`). This is the lever that most needs a capital-cost source before it is relied on.
