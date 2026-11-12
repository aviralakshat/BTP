# Waste heat recovery

**Code:** `project/src/retrofits/whr.py` (`WHR.calculate_impact`)

## What it does

A waste-heat recovery boiler raises steam from the kiln's off-gas and drives a turbine. The model sizes it from the kiln's own energy balance, not from a blanket "35% of input energy" rule.

## Heat sources

1. **Waste-gas sensible heat** above the boiler's stack temperature. Only the share between the gas temperature (900 °C) and the stack (150 °C) can be taken out: (900 − 150) / (900 − 25) = 85.7%.
2. **After-burner combustion** of the volatiles and CO that leave the kiln unburnt (the "to ABC" terms in model 04). On this plant it is the larger source, which is why sponge-iron waste-heat plants generate as much power as they do.

## Method

```
heat available = sensible heat × 85.7% + after-burner chemical energy × coal remaining
steam          = heat available × boiler efficiency (0.60, BEE 2019)
gross power    = steam × cycle efficiency (0.2265, derived from the BEE 2011 report)
delivered      = gross × (1 − 10% auxiliary use, BEE 2011)
self-used      = min(delivered, plant auxiliary load)
export         = delivered − self-used
capital        = ₹4.68 crore/MW × 2.757 MW × (capacity / 2.757 MW)^0.67   (Gaurav et al. 2024)
maintenance    = ₹0.20 per kWh generated
```

## Result on the reference plant

| Quantity | Value | Literature check |
|---|---:|---|
| Heat available | 11.08 GJ/t (4.64 sensible + 6.44 after-burner) | |
| Gross generation | 418 kWh/t | 350 to 460 band (Nduagu et al.: 450 to 451) |
| Auxiliary use | 42 kWh/t | |
| Self-used by the kiln | 60 kWh/t | |
| Export | 316 kWh/t | 300 to 400 band (Nduagu et al.: 351) |
| Capacity | 1.57 MW | |
| Capital | ₹8.84 crore (₹5.64 crore/MW) | |
| Cost change | −₹867/t | |

## Limits

The boiler and cycle efficiencies are design values from one detailed project report, not a measured boiler test. The capital cost is extrapolated from a single 2.757 MW reference on a 0.67 exponent.
