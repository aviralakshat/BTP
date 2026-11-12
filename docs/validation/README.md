# Validation

**Code:** `project/src/validation/literature_check.py` (`collect_outputs`, `run_checks`, `format_report`)
**Ranges:** `project/config/validation_targets.json`

## The rule

The validation ranges are acceptance criteria for model **outputs**, never inputs. No model reads `validation_targets.json`, and a test enforces that no target key is also a parameter key. That separation is what makes a pass evidence rather than a tautology.

## The checks

Reference plant: imported coal, 100 t/day, 90% utilisation, coal rate solved from the kiln heat balance.

| Check | Model | Range | Result | Source of the range |
|---|---:|---|---|---|
| Iron ore, t/t DRI | 1.589 | 1.4 to 1.6 | PASS | CEEW (Nitturu et al. 2024), pellets; Dey measured 1.587 |
| Coal, t/t DRI | 1.025 | 0.9 to 1.6 | PASS | CEEW: imported 0.9 to 1.1, domestic 1.4 to 1.6 |
| Specific energy, Gcal/t DRI | 5.586 | 4.9 to 8.2 | PASS | TERI (2021) lower bound, BEE (2019) sector range |
| DRI total iron | 0.926 | 0.89 to 0.93 | PASS | Dey Table 7; TERI |
| Metallisation | 0.902 | 0.88 to 0.94 | PASS | Bhardwaj et al. (2024) |
| Direct CO₂, t/t DRI | 2.083 | 1.39 to 3.2 | PASS | Nduagu et al. (2022) lower bound |
| Auxiliary power, kWh/t | 60 | 55 to 100 | PASS | CEEW |
| Waste-heat gross generation, kWh/t | 418 | 350 to 460 | PASS | Nduagu et al.: 450 to 451 |
| Waste-heat export, kWh/t | 316 | 300 to 400 | PASS | Nduagu et al.: 351 |
| Waste-gas sensible heat share | 0.231 | 0.18 to 0.30 | PASS | Dey Table 11 |
| H₂ for complete reduction, kg/t | 46.9 | 53.5 to 59.6 | INFO | Kamal et al. (2026). Not scored: their figure includes excess hydrogen for a shaft furnace. |

10 of 10 scored checks pass.

## How strong each pass is

Not every pass is equally good evidence. [`validation_report.md`](validation_report.md) sorts them.

- **Strong.** The ore rate and specific energy are solved quantities. Nothing about them is configured, so landing in band tests the balances. The ore rate also reproduces Dey's measured 1.587 t/t.
- **Weak by construction.** DRI total iron and metallisation follow directly from the configured product analysis, so they cannot fail.
- **Weak because the band is wide.** The coal range spans imported and domestic coal.
- **Design values.** The waste-heat figures depend on a boiler efficiency and a cycle efficiency taken from design reports, not a measured boiler test.

## Running it

```bash
cd project
./venv/bin/python src/validation/literature_check.py
```

The full text, with the source of each range, is written to `project/outputs/validation_report.txt` by `setup_data.py`.

## Other evidence

- **Mass and energy closure.** Model 03 closes the total mass to 1.20% and every conserved element exactly. Model 04 closes the heat ledger to under 0.01%.
- **Calibration reproduction.** `tests/test_hardening.py` checks that the char and dust partitions reproduce Dey's measured char and dust.
- **Golden baseline.** `project/tests/golden/baseline_100tpd_imported.json` freezes the reference results. Any drift fails the test suite until the version is bumped and the reason written in `CHANGELOG.md`.
