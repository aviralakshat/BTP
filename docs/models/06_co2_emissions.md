# 06 CO₂ emissions

**Code:** `project/src/emissions/co2_model.py` (`CO2Model.calculate_emissions`)
**Question:** how much CO₂ does a tonne of sponge iron emit, and from where?

## Purpose

CO₂ is counted from the carbon balance, not from a coal emission factor. An earlier version multiplied coal tonnage by 2.4 t CO₂ per tonne of coal. That implies a coal carbon content of 2.4 × 12/44 = 65.5%, while the coal the model uses (Dey et al. 2015, Table 6) measures 60.6 to 62.2% carbon. Counting carbon atoms removes that contradiction, and it also yields the emission factor the coal really implies.

## Boundary

The **stack**: the kiln plus the after-burner chamber. Every carbon atom that reaches the gas phase is counted as CO₂, because the after-burner exists to burn the CO and volatiles before the gas reaches the electrostatic precipitator.

Carbon that leaves in a solid stream (dolochar, flue dust, DRI) is not a stack emission. Dolochar is routinely burnt in captive fluidised-bed boilers, though, so its eventual CO₂ is reported on a separate line rather than dropped.

## Method

```
gas-phase fossil carbon = coal C + dolomite C − char C − dust C − DRI C − carbon displaced by a retrofit
direct CO₂              = gas-phase fossil carbon × 44/12
purchased-power CO₂     = net grid import (kWh/t) × grid factor (0.727 t CO₂/MWh, CEA 2024)
biogenic CO₂            = biomass carbon reaching the gas × 44/12
reported total          = direct + purchased power (+ biogenic, unless zero-rated)
```

| Scope | What it covers |
|---|---|
| Direct (scope 1) | Gas-phase fossil carbon, including dolomite calcination |
| Purchased power (scope 2) | Grid electricity after any waste-heat self-generation. A net export gives a negative figure (avoided grid CO₂). |
| Biogenic | Biomass carbon. Excluded from the fossil total by the IPCC convention when `biomass.biogenic_co2_zero_rated` is 1, and always reported separately. |
| Downstream dolochar | Char carbon if the dolochar is later burnt. Reported, not added. |

Hydrogen carries its own supply emissions (`hydrogen.ef_t_per_t`: zero for green, 9 t CO₂ per tonne for grey), added to purchased power.

## Result on the reference plant

| Line | t CO₂/t DRI |
|---|---:|
| Direct (stack) | 2.083 |
| of which dolomite calcination | 0.014 |
| Purchased power (60 kWh/t) | 0.044 |
| **Reported total** | **2.126** |
| Carbon retained in solids, as CO₂ | 0.228 |
| Downstream dolochar, if burnt | 0.143 |
| Total including dolochar | 2.269 |

The implied coal emission factor is 2.24 t CO₂ per tonne of coal, not 2.4. The direct figure sits inside the 1.39 to 3.2 t/t validation band (see [`../validation/`](../validation/README.md)).

## Tests

`tests/test_model.py` checks that CO₂ agrees with the carbon balance, that the implied coal factor matches the coal's carbon content, that a net export gives negative scope 2, that solid carbon is not counted at the stack, that biomass carbon is reported separately and counted when not zero-rated, and that grey hydrogen adds emissions. `tests/test_hardening.py` checks that stack CO₂ is every gas-phase carbon atom and that scope 2 is net import times the grid factor.
