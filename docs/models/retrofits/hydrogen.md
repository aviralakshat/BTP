# Hydrogen substitution

**Code:** `project/src/retrofits/hydrogen.py` (`Hydrogen.calculate_impact`)

## What it does

Hydrogen injected into an existing rotary kiln does two jobs at once:

1. **Fuel.** It displaces coal energy.
2. **Reductant.** Fe₂O₃ + 3H₂ → 2Fe + 3H₂O removes oxygen without carbon. Hydrogen therefore spares reductant carbon instead of competing for it. That makes it a different kind of lever from biomass, which must supply carbon to keep the reduction going.

## Method

```
hydrogen needed     = coal NHV × fraction / 119,960 kJ/kg
coal saved          = coal rate × fraction
oxygen removed by H2 = min(oxygen to remove, H2 × 16/2)
carbon spared       = oxygen removed by H2 × 12/16
reductant ratio     = remaining gas-phase carbon / (carbon needed − carbon spared)
operating cost      = H2 × ₹332.5/kg − coal saved × ₹2,500/t
supply CO2          = H2 × emission factor (0 green, 9 t/t grey)
capital             = compressor at $130/kW of equivalent electrolyser
                      (50 kWh/kg, 85% array efficiency), at ₹95 per USD
```

The fraction is capped at `hydrogen.max_substitution_frac` (30%). The hydrogen price is $3.5/kg (Hall et al. 2025), the level at which they find hydrogen competitive in India.

## Result on the reference plant

| Fraction | Hydrogen | CO₂ change | Cost change | Capital |
|---:|---:|---:|---:|---:|
| 20% | 39.0 kg/t (3.5 t/day) | −19.5% | +₹12,817/t | ₹10.6 crore |
| 30% | 58.5 kg/t (5.3 t/day) | −29.2% | +₹19,225/t | ₹15.9 crore |

The stoichiometric hydrogen for the oxygen this plant removes is 46.9 kg/t. Kamal et al. validate complete hydrogen direct reduction against 53.5 to 59.6 kg/t, but their figure includes excess hydrogen for a shaft furnace. The comparison is shown as information, not scored.

At 30% the hydrogen removes all the oxygen, so the ore needs no carbon at all and the reductant ratio is unbounded.

The break-even hydrogen price, at which substitution adds no operating cost, is about ₹13 per kg, 4% of the ₹332.5 used. While coal costs ₹2,500 per tonne, hydrogen is a carbon-abatement cost, not a saving.

## Limits

The 30% cap still needs a citation. Storage and injection lances are not costed. The kiln's response to hydrogen (temperature profile, accretion) is not modelled.
