# Advanced kiln control

**Code:** `project/src/retrofits/kiln_control.py` (`KilnControl.calculate_impact`)

## What it does

Sensor-based control of kiln air and coal. CSE (Kumar and Haldar 2026), Table 4, gives a coal saving of 3 to 5% and an indicative capital cost of ₹0.5 to 1 crore.

## Method

```
coal cut = min(kiln_control.coal_saving_frac, upper bound of its range)  = 3%, capped at 5%
capital  = ₹0.5 crore, the low end of the published range
```

The capital is not scaled with plant size, because the table does not state a kiln size.

## Result on the reference plant

| Quantity | Value |
|---|---:|
| Coal cut | 3% |
| CO₂ change | −2.9% |
| Cost change | −₹60/t |
| Capital | ₹0.50 crore |
| Equity NPV | ₹1.07 crore |
| Equity IRR | 61.5% |
| Payback | 1.9 years |

## Limits

The saving is a published range for the sector, not a trial on this kiln.
