# 09 Retrofits

**Code:** `project/src/retrofits/`, combined in `project/src/analysis/scenarios.py` (`evaluate`)
**Question:** what does each decarbonisation lever change, on its own and in combination?

Each retrofit is a **delta on the solved baseline plant**, not a rebuilt plant. The baseline's balances are validated, and a retrofit changes only the streams its source describes.

| Lever | Document | Mechanism | Source |
|---|---|---|---|
| Waste heat recovery | [whr.md](whr.md) | Power from waste-gas heat and after-burner combustion | BEE 2011 and 2019, Gaurav et al. 2024, Nduagu et al. 2022 |
| Biomass | [biomass.md](biomass.md) | Rice husk replaces coal, energy for energy | Vigneswaran et al. 2024, supplier prices |
| Hydrogen | [hydrogen.md](hydrogen.md) | Hydrogen replaces coal as fuel and as reductant | Kamal et al. 2026, Hall et al. 2025 |
| Oxygen enrichment | [oxygen.md](oxygen.md) | 8 Nm³/t of oxygen; less coal, more output | Rajesh, Nandi and Pabi 2016, Table 8 |
| Advanced kiln control | [kiln_control.md](kiln_control.md) | Sensor-based air and coal control | CSE (Kumar and Haldar 2026), Table 4 |
| Producer gas | [producer_gas.md](producer_gas.md) | Gasified coal fines replace injection coal | TERI 2021 |
| Char recycling | [char_recycle.md](char_recycle.md) | Dolochar carbon returned to the feed | Bhardwaj et al. 2024, Section 4.6 |
| Variable-speed drives | [vfd.md](vfd.md) | Lower motor power at part speed | Bhardwaj et al. 2024, Section 4.2 |

## Each lever alone on the reference plant

100 t/day, imported coal, 90% utilisation. Baseline: ₹7,234 per tonne and 2.126 t CO₂ per tonne. Equity NPV is the financed cash flow from model 08 (75% debt at 10%, 33.99% tax, 8% discount rate, 20 years).

| Lever | Cost change, ₹/t | CO₂ change | Capital | Equity NPV |
|---|---:|---:|---:|---:|
| Waste heat recovery | −867 | −2.1% | ₹8.84 crore | ₹14.60 crore (IRR 47.9%, payback 2.7 yr) |
| Producer gas | −512 | −19.5% | none | ₹9.86 crore |
| Oxygen enrichment | −86 | −8.5% | none | ₹1.75 crore |
| Advanced kiln control | −60 | −2.9% | ₹0.50 crore | ₹1.07 crore (IRR 61.5%, payback 1.9 yr) |
| Variable-speed drives | −36 | −0.5% | none (annualised charge) | ₹0.68 crore |
| Char recycling | −30 | −2.1% | none | ₹0.57 crore |
| Biomass, 20% | +1,067 | −19.5% | ₹9.27 crore | −₹31.5 crore |
| Hydrogen, 20% (green) | +12,817 | −19.5% | ₹10.62 crore | −₹374 crore |

Waste heat recovery has the best business case but a small CO₂ effect. Its main gain is export revenue, and at 100 t/day the plant already draws little grid power. The deep CO₂ cuts come from replacing coal, which costs money unless the substitute is cheaper per unit of heat.

## How levers combine

`evaluate()` applies them in a fixed order. The order matters, so keep it.

1. **Variable-speed drives first.** They lower the auxiliary load, which every later power figure uses.
2. **Coal-cutting levers next** (producer gas, kiln control, oxygen, char recycling). Each is applied to the coal **remaining** after the previous one, so savings compound rather than add: two 20% cuts remove 36%, not 40%. The combination is flagged, because no plant has trialled these measures together.
3. **Biomass and hydrogen** replace a fraction of the coal energy.
4. **Waste heat recovery last.** The after-burner heat comes from the volatiles and CO of the coal that is still burnt, so it is scaled by the coal remaining. The waste-gas sensible heat stays on the baseline.

## The reductant check

Coal in a rotary kiln is fuel and reductant at once. It supplies the carbon that strips oxygen from the ore. A lever that removes coal can starve the bed even if the heat is replaced.

```
reductant-carbon ratio = carbon available to gasify / carbon needed to remove the ore's oxygen as CO
```

The baseline has a ratio of 2.02. Biomass and hydrogen are checked **together** on one balance, because each can pass alone and still starve the bed when both remove coal carbon. A scenario below 1.0 is marked infeasible and excluded from the pathway search. Hydrogen raises the ratio rather than lowering it, because it removes oxygen without carbon.

## Tests

`tests/test_model.py` checks the direction of each lever: biomass displaces coal monotonically, is capped, erodes the reductant margin and reports biogenic carbon separately; hydrogen spares reductant carbon and has physical stoichiometry; waste-heat sources sum to the total, and generation splits into self-use and export. `tests/test_process_cases.py` checks the five process cases against their sources. `tests/test_financial_robustness.py` sweeps every lever combination through the financial model.
