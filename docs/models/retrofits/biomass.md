# Biomass substitution

**Code:** `project/src/retrofits/biomass.py` (`Biomass.calculate_impact`)

## What it does

Rice husk replaces a fraction of the coal, energy for energy. It is a delta on the validated baseline, not a rebuilt stream table.

## Method

```
energy displaced = coal NHV × fraction
biomass needed   = energy displaced / biomass NHV (12,979 kJ/kg)
coal saved       = coal rate × fraction
fossil carbon    = gas-phase coal carbon × fraction, removed from the stack
biogenic carbon  = biomass × 33.7% C × (1 − share of carbon retained in char)
operating cost   = biomass × ₹3,500/t − coal saved × ₹2,500/t
handling capital = ₹56.3 lakh/MWth × 195.47 MWth × (duty / 195.47 MWth)^0.67
```

The fraction is capped at `biomass.max_substitution_frac` (30%).

## Two checks it makes

- **Reductant carbon.** Coal is the kiln's reductant as well as its fuel, so replacing it on heat alone can leave too little carbon to reduce the ore. The adequacy ratio is recomputed with biomass carbon credited at a reactivity factor of 0.8 (`biomass.char_reactivity`, still to be cited).
- **Biogenic accounting.** Biomass CO₂ is reported separately. It is left out of the fossil total only when `biomass.biogenic_co2_zero_rated` is switched on, not credited as an automatic reduction at coal's emission factor.

## Result on the reference plant

| Fraction | Biomass | Coal saved | Extra ash | CO₂ change | Cost change | Reductant ratio |
|---:|---:|---:|---:|---:|---:|---:|
| 20% | 360 kg/t (32.4 t/day) | 205 kg/t | 68 kg/t | −19.5% | +₹1,067/t | 1.97 |
| 30% | 541 kg/t (48.7 t/day) | 307 kg/t | 103 kg/t | −29.2% | +₹1,541/t | 1.94 |

Rice husk has a little over half the heating value of coal, so it takes 1.76 t of husk to replace a tonne of coal. At ₹3,500 against ₹2,500, the heat costs more.

## Limits

The char reactivity and the 30% cap still need a citation. The rice-husk price and the handling capital are indicative. The capital is a cross-industry analogue extrapolated about 80-fold down in size. The extra ash is reported but its effect on accretion and on the product is not modelled.
