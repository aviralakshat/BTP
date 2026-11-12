# 01 Baseline plant

**Code:** `project/src/models/baseline.py` (`BaselinePlant`)
**Question:** what goes into and comes out of the kiln for every tonne of sponge iron?

## Purpose

The baseline plant is the stream model every other model builds on. It takes the measured analyses of the ore, coal, flux and product and turns them into a full stream table on a basis of 1,000 kg of DRI. Everything is then scaled to the plant's daily output.

Only independent quantities are read from the parameter file. The ore rate, combustion air, waste-gas composition and oxygen removed are derived. Because the stream table is built from atom balances, it closes by construction, and the derived quantities become results that can be checked against the literature.

## Calibration plant

All stream analyses and loss fractions come from Dey, Dey and Datta (2015), *Case Studies in Thermal Engineering* 6, 1-15. It is a 453.6 t/day kiln with a complete measured material and heat balance (Tables 4 to 11). Deriving the ore rate from those analyses gives 1.589 t of ore per tonne of DRI, against Dey's measured 1.587.

## Inputs

| Group | Key parameters | Reference value |
|---|---|---|
| Ore (Dey Table 5) | `ore.fe_total_frac`, `ore.gangue_frac`, `ore.moisture_frac` | 63% Fe, 4.06% gangue, 2% moisture |
| Iron losses (Dey Table 10) | `ore.fe_loss_to_dust_frac`, `ore.fe_other_loss_frac` | 4.96% to dust, 2.54% other |
| Product (Dey Table 7) | `dri.fe_metallic_frac`, `dri.feo_frac`, `dri.gangue_frac`, `dri.carbon_frac` | 83.5% metallic Fe, 11.71% FeO, 4.62% gangue, 0.17% C |
| Coal rate | `coal.rate_t_per_t_dri`, `coal.injection_share` | Solved (see model 02); 35.6% injected at the discharge end |
| Coal analysis (Dey Table 6) | `coal_feed.*`, `coal_inj.*` | Feed coal 60.6% C, 23.74% ash, 22,530 kJ/kg net |
| Flux (Dey Table 8) | `dolomite.rate_t_per_t_dri`, `dolomite.cao_frac`, `dolomite.mgo_frac` | 31.7 kg/t, 28% CaO, 20% MgO |
| Char and dust (Dey Tables 6, 9, 10) | `char.ash_partition_frac`, `char.fc_unburnt_frac`, `dust.*` | Shares of coal ash and fixed carbon |
| Kiln gas (Dey Tables 4, 10) | `kiln.unburnt_vm_carbon_frac`, `kiln.h2_burnt_in_kiln_frac`, `kiln.co_in_waste_gas_frac`, `kiln.excess_air_frac` | 24.5% of coal carbon leaves as unburnt volatiles; 11.35% excess air |

## Method

The calculation runs from the product backwards.

1. **Product.** Fix 1,000 kg of DRI. Its metallic iron, FeO, gangue and carbon follow from the product analysis. Metallisation is metallic iron over total iron, so it is an input, not a prediction.
2. **Ore.** The ore needed is the iron in the product divided by the ore's iron content and by the iron yield (one minus the dust and other losses):

   ore = Fe in DRI / (Fe fraction of ore × (1 − dust loss − other loss))

3. **Coal.** The coal rate is split into feed coal and injection coal. Carbon, hydrogen, oxygen, nitrogen, sulphur, ash, moisture and net heating value are summed over both.
4. **Char and dust.** Dolochar is built from what it contains: a share of the coal ash plus the unburnt share of the coal's fixed carbon. Flue dust is the ore's iron lost to dust (as Fe₂O₃) plus a share of the coal ash. The shares come from Dey's Table 10.
5. **Carbon partition.** Coal carbon is split into char carbon, dust carbon, product carbon, unburnt volatile carbon and gasified carbon. If nothing is left to gasify, the plant refuses to build.
6. **Oxygen removed.** All iron entered as Fe₂O₃. The oxygen removed is the oxygen bound to that iron minus the oxygen still held in the product's FeO.
7. **Reductant adequacy.** In the worst case every removed oxygen atom leaves on its own CO molecule, so the minimum carbon is oxygen removed × 12/16. The reductant-carbon ratio is gasified carbon over that minimum. Below 1, the bed cannot be reduced and a scenario is marked infeasible.
8. **Air.** A global oxygen balance gives the oxygen needed to burn gasified carbon to CO₂ and CO (in the measured CO:CO₂ split) and to burn the hydrogen that combusts inside the kiln. The oxygen removed from the ore and the oxygen in the coal are credited. Excess air is then added.
9. **Waste gas.** CO₂ (from carbon and dolomite calcination), CO, H₂O, N₂, excess O₂, SO₂ and the unburnt volatiles.
10. **Free ash.** Inerts in minus inerts accounted for elsewhere. Dey obtains this stream by difference too, and a negative value stops the build.

## Result on the reference plant

| Inputs | kg/t DRI | Outputs | kg/t DRI |
|---|---:|---|---:|
| Iron ore (dry) | 1,589.1 | Sponge iron | 1,000.0 |
| Ore moisture | 32.4 | Dolochar | 136.8 |
| Feed coal | 659.8 | Flue dust | 159.0 |
| Injection coal | 364.8 | Calcined flux | 15.2 |
| Dolomite | 31.7 | Free ash | 93.4 |
| Combustion air | 4,272.2 | Unreduced fines | 36.4 |
| | | Waste gas | 5,425.7 |

The reductant-carbon ratio is 2.02, so the kiln has about twice the carbon it needs to reduce the ore. That margin is what the biomass and hydrogen retrofits draw down.

## Tests

`tests/test_model.py` checks that no stream is negative, that the waste-gas species sum to the waste-gas stream, that the ore rate reproduces the calibration plant, and that the reductant carbon is adequate. `tests/test_hardening.py` checks that the char and dust partitions reproduce Dey's char and dust, and that the carbon partition is exhaustive. The golden test freezes the whole stream table.

## Limits

- One coal analysis for feed and one for injection. The ore is a single pellet-grade feed.
- Metallisation and product composition are inputs from Dey's Table 7.
- The kiln is treated as a steady-state black box here. Its internal profile is model 05.
