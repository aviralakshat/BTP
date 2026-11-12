# Data

Where the evidence behind the model is kept, and which files are generated rather than hand-maintained.

## Source documents

| Location | Contents |
|---|---|
| `papers/` | Every source PDF, 26 in all, named `YYYY_Author_Short-title.pdf`. [`papers/INDEX.md`](../../papers/INDEX.md) lists them with what each is used for. |
| `data/text/` | A plain-text extract of every paper, under the same file stem. Grep these before citing a number; a page or table not read here is not cited. |
| `data/web/` | Web pages the parameters cite (prices, exchange rates, CBAM, the GST cess, NIST thermochemistry), each saved with its URL and retrieval date. |

A parameter's `source_file` points at one of these, and a test checks that every cited file exists.

## Calibration and validation sources

| Role | Source | Used for |
|---|---|---|
| Calibration plant | Dey, Dey and Datta (2015), *Case Studies in Thermal Engineering* 6, 1-15 | Every stream analysis and loss fraction: a 453.6 t/day kiln with a complete measured material and heat balance (Tables 4 to 11) |
| Validation | CEEW (Nitturu et al. 2024) | Surveyed ore, coal and auxiliary-power rates |
| Validation | Nduagu et al. (2022) | CO₂ intensity, waste-heat generation and export |
| Validation | TERI (2021), BEE (2019) | Specific energy consumption |
| Validation | Kamal et al. (2026) | Hydrogen stoichiometry (information only) |
| Finance | BEE (2011), waste-heat power plant report for an Orissa sponge-iron cluster | Loan, tax, depreciation and escalation terms |

## Data files

| File | Kind | Contents |
|---|---|---|
| `project/data/parameter_provenance.csv` | Generated | Every parameter with value, range, status and source |
| `project/data/literature_gaps.csv` | Generated | The parameters still needing a citation |
| `project/data/literature_inventory.csv` | Generated | One row per PDF in `papers/`, with whether a text extract exists and its role in the model |
| `project/data/price_series/commodity_prices.json` | Hand-maintained | Names the low, base and high price series; the numbers are read from `parameters.json` |
| `project/outputs/validation_report.txt` | Generated | Model outputs against their validation ranges, with the source of each range |
| `data/literature_parameters.csv` | Hand extraction | Parameters read from the papers during the literature review |
| `data/engineering_assumptions.csv` | Hand extraction | Early engineering assumptions, kept for the record |
| `data/literature_inventory.csv` | Hand extraction | The first literature inventory, kept for the record |

Regenerate everything marked "Generated":

```bash
cd project
./venv/bin/python setup_data.py
```

`setup_data.py` also reports stale absolute paths in the hand-maintained CSVs (left over from when the project lived in `~/Documents/SEM7/BTP`) without rewriting them.

## Presets

| Preset | Coal | Status |
|---|---|---|
| Imported coal (default) | Dey et al. Table 6: 23.74% ash, 22,530 kJ/kg net | Measured |
| Domestic coal | Dey's coal diluted to 30% ash on a dry, ash-free basis, 19,500 kJ/kg | **Not a measured analysis.** No paper gives a full domestic-coal analysis. |

Presets live in `project/src/data/presets.py`.

## Research notes

How the parameters were found, and what was checked, is in [`../project/research/`](../project/research/). `CHECKED_DATA.md` grades every retrofit claim by evidence quality, and `PARAMETER_LIST.md` lists the candidate values with page references.
