# Variable-speed drives

**Code:** `project/src/retrofits/vfd.py` (`VariableFrequencyDrive.calculate_impact`)

## What it does

Variable-frequency drives on the kiln's motors, so fans and drives run at the speed the process needs instead of throttling at full speed. The method is Bhardwaj et al. (2024), Section 4.2.

## Method

Motors take 90% of the plant's electricity. The unit runs at about 90% of rated capacity, and equipment at 90% of rated speed draws 73% of rated power (the cube law).

```
power saving = motor share × (1 − power at reduced speed) = 0.90 × (1 − 0.73) = 24.3%
```

The saving is applied to this plant's own auxiliary load, not copied from the paper's kWh per tonne of steel. Bhardwaj's Table 3 gives the cost as an annualised charge per tonne of crude steel. It is converted to ₹15.45 per tonne of DRI and carried as an operating charge.

## Result on the reference plant

| Quantity | Value |
|---|---:|
| Auxiliary power | 60 → 45.4 kWh/t |
| Power saved | 14.6 kWh/t |
| CO₂ change | −0.5% |
| Cost change | −₹36/t |
| Equity NPV | ₹0.68 crore |

This lever runs first in a combination, because the lower auxiliary load changes how much waste-heat power is left to export.
