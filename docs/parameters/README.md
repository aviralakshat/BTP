# Parameters

Every number the plant model uses lives in one file, `project/config/parameters.json`. No numeric assumption is typed into a model file. If a number is not in the JSON, the model does not use it.

| File | Contents | Read by the model? |
|---|---|---|
| [`parameter_reference.md`](parameter_reference.md) | Every parameter, grouped by plant area, with value, range, status and source | Generated |
| [`data_provenance.md`](data_provenance.md) | The same register grouped by status, with the reason each open gap is still open | Generated |
| `project/config/parameters.json` | 145 parameters: the single source of truth | Yes |
| `project/config/validation_targets.json` | 11 published ranges that outputs are checked against | **No**, by design |
| `project/config/analysis.json` | Uncertainty and optimisation settings, finance stress cases, carbon-price cases | No (analysis layer only) |
| `project/config/distributions.json` | Optional overrides of the Monte Carlo distributions (currently none) | No (analysis layer only) |
| `project/data/price_series/commodity_prices.json` | Names the low, base and high price series. The numbers themselves are read from `parameters.json`. | No (analysis layer only) |

Both generated files are rebuilt with `./venv/bin/python setup_data.py`. Do not edit them by hand.

## What a parameter entry holds

```json
"plant.utilization": {
  "value": 0.9,
  "unit": "-",
  "min": 0.7,
  "max": 0.95,
  "status": "verified",
  "sensitivity": true,
  "source": "Bhardwaj et al., Energy 2024: the rotary kiln is assumed to operate at 90% of its rated capacity.",
  "source_file": "2024_Bhardwaj_Decarbonizing-kiln-induction-furnace",
  "notes": ""
}
```

| Field | Meaning |
|---|---|
| `value` | The number the model uses |
| `unit` | Per tonne of DRI unless stated. Energy is in kJ internally; Gcal is for display only. |
| `min`, `max` | The plausible range. The tornado moves each flagged parameter to these ends; the Monte Carlo draws a triangular distribution on min, value and max. |
| `status` | How well the value is sourced (below) |
| `sensitivity` | `true` puts the parameter into the uncertainty runs. 68 parameters are flagged. |
| `source` | The citation, with the table or page it was read from |
| `source_file` | The text extract in `data/text/` or archived web page in `data/web/`. A test checks that every cited file exists. |
| `notes` | The derivation, for a derived value, or the reason a gap is still open |

## Status

| Status | Count | Meaning |
|---|---:|---|
| `verified` | 112 | Read directly from the cited source: a paper extract or an archived web page with its URL and retrieval date |
| `derived` | 12 | Not printed as one number in any source, but computed by stated arithmetic from numbers that are. The working is in `notes`. |
| `indicative` | 7 | A market quote, supplier listing or analogue from a different equipment class. Good enough for a range, not for a headline claim. |
| `scenario_choice` | 7 | A decision for the study, not a fact: plant size, exchange rate, accounting convention, hydrogen route |
| `physical_constant` | 2 | A thermodynamic or stoichiometric constant |
| `needs_citation` | 5 | A plausible engineering default not yet traced to a source |

The five still needing a citation are the specific heats of DRI and char, biomass char reactivity, and the biomass and hydrogen substitution caps. Each is listed with the reason in [`data_provenance.md`](data_provenance.md).

## Groups

| Prefix | Area | Count |
|---|---|---:|
| `plant` | Size, utilisation, operating days | 3 |
| `ore`, `dri` | Iron ore feed and sponge-iron product | 12 |
| `coal`, `coal_feed`, `coal_inj` | Coal rate mode and the two coal analyses | 25 |
| `char`, `dust`, `dolomite` | Dolochar, flue dust and flux | 16 |
| `kiln` | Temperatures, air, losses, geometry | 16 |
| `power` | Auxiliary load and grid emission factor | 2 |
| `whr`, `biomass`, `hydrogen`, `oxygen`, `kiln_control`, `producer_gas`, `char_recycle`, `vfd` | One group per retrofit | 50 |
| `econ` | Prices, cost scaling, discount rate, tax, loan terms | 21 |

## Rules for changing a parameter

1. **Add, do not hard-code.** A new number goes into `parameters.json` with a source, a range and a status, and is read through `src/data/parameters.py`.
2. **Archive the source.** A paper needs its text extract in `data/text/`. A web page is saved in `data/web/` with its URL and retrieval date.
3. **Keep coal analyses closed.** A coal's ultimate and proximate analyses must each sum to one. Build a different coal with `daf_rescale()`, not by editing the ash alone.
4. **Never make a validation target a parameter.** A test enforces that no key in `validation_targets.json` is also a parameter key.
5. **Bump the version.** Any change to `parameters.json` changes its SHA-256 and fails the golden test. Bump `MODEL_VERSION` in `src/version.py`, explain why in `CHANGELOG.md`, and regenerate with `tests/golden/regenerate.py`.

## Overrides at run time

The dashboard and the analysis layer never write to `parameters.json`. `Parameters.with_overrides()` returns an independent copy carrying the session's values, and `out_of_range()` flags any override outside its min and max. The SHA-256 attached to a result is of the file, so a session override cannot pass itself off as the reference case.
