# BTP - DRI Digital Twin Project Context

## Project Overview
A digital twin of **coal-based rotary-kiln Direct Reduced Iron (DRI) production**
for the Indian secondary steel sector. It simulates a baseline plant from
first-principles mass and energy balances, then evaluates the technical,
CO2 and economic impact of retrofits: waste heat recovery (WHR), biomass
substitution and hydrogen substitution.

## Tech Stack
- Python 3.14, Streamlit dashboard, pandas/numpy, pytest.
- Virtual environment at `project/venv`.

## Modelling principles
These are the rules the codebase is built on. Preserve them when extending it.

1. **No magic numbers.** Every numeric assumption lives in
   `project/config/parameters.json` with a `source`, a plausible `min`/`max`, and
   a `status` of `verified` / `needs_citation` / `physical_constant` / `derived`.
   Model code reads parameters through `src/data/parameters.py`; genuine physical
   constants (molar masses, standard enthalpies) live in that module instead.
   If you are about to type a number into a model file, add it to the JSON.
2. **Validation targets are not inputs.** `config/validation_targets.json` holds
   literature acceptance bands for model *outputs*. Nothing in the model reads
   them, which is what makes a PASS evidence rather than a tautology. A test
   enforces that no target key is also a parameter key.
3. **Derive rather than assume.** Only independent quantities are configured.
   Ore rate, air rate, waste-gas composition and the coal rate are solved, so
   the mass balance closes by construction and those values become checkable
   results. Deriving the ore rate reproduces Dey's measured 1.587 t-ore/t-DRI
   to within 0.2%.
4. **Report residuals, never distribute them.** Both balances print an explicit
   residual. Do not add a fudge factor to make a balance look tight.
5. **Be explicit about the system boundary.** The kiln boundary and the stack
   (kiln + after-burner chamber) boundary give different answers and the
   literature uses both. Volatile matter leaves the *kiln* unburnt but is
   post-combusted in the ABC, so it is a transfer, not a loss -- energy terms are
   labelled `to ABC` and WHR claims them back.

## Calibration and validation
- **Calibration plant**: Dey et al. (2015), *Case Studies in Thermal Engineering*
  6, 1-15 -- a 453.6 TPD kiln with a complete measured material and heat balance
  (Tables 4-11). Source of all stream analyses and loss fractions.
- **Validation bands**: CEEW (Nitturu et al. 2024) for surveyed consumption
  rates, Nduagu et al. for CO2 and WHR output, TERI and BEE for specific energy
  consumption, Kamal et al. for hydrogen stoichiometry.
- Extracted paper text is in `data/text/*.txt`; grep it before asserting any
  citation. Do not cite a page or table number you have not read.

Current state: **mass balance closes to 1.14%** with all seven element balances
passing (Fe, C, H, N, S exact), **energy balance closes to <0.01%** in solve
mode, **8 of 11 literature checks PASS**. The two WHR checks FAIL by 20-30% --
this is a known, documented open gap, not something to tune away. See the notes
in `config/validation_targets.json`.

## Project Structure
- `project/app.py` - Streamlit UI only. Six tabs: Overview, Mass & Energy,
  Emissions, Economics, Validation, Parameters. No calculations here. The model
  run is wrapped in `st.cache_data` keyed on the control values, so switching
  tabs re-renders rather than re-solving. Cache-key arguments must NOT be
  underscore-prefixed - Streamlit excludes those from the key, which would make
  two different scenarios collide on one cached result.
- `project/src/ui/` - presentation layer. `theme.py` holds the validated
  palette, the Plotly template and the formatters; `charts.py` the six chart
  builders; `components.py` the hero figure, stat tiles and chips; `labels.py`
  the Title Case conversion with acronym and formula guards.
- `project/.streamlit/config.toml` - pins the light theme. The palette was
  validated against the light surface #fcfcfb only; dark mode needs its own
  steps re-validated rather than an automatic inversion.
- `project/setup_data.py` - regenerates `data/literature_inventory.csv`,
  `data/parameter_provenance.csv`, `data/literature_gaps.csv` and
  `outputs/validation_report.txt`. Also reports stale absolute paths in the
  hand-maintained CSVs under `data/` without rewriting them.
- `project/config/` - `parameters.json` (90 parameters) and
  `validation_targets.json` (11 acceptance bands).
- `project/src/`
  - `data/parameters.py` - parameter store, provenance, physical constants.
  - `models/baseline.py` - elemental stream model on a 1 t DRI basis.
  - `models/plant.py` - `build_plant()` and the coal-rate solver. Import plant
    construction from here, not from `baseline.py`, so `coal.rate_mode` is
    honoured.
  - `models/mass_balance.py` - total and per-element closure audit.
  - `models/energy_balance.py` - itemised ledger on a coal-NHV basis.
  - `emissions/co2_model.py` - CO2 from the carbon balance, with scopes.
  - `economics/economics.py` - OPEX, annualised CAPEX, export revenue.
  - `retrofits/{whr,biomass,hydrogen}.py` - deltas on the validated baseline.
  - `validation/literature_check.py` - runs the model against the bands.
  - `analysis/`, `optimization/` - empty; sensitivity and MACC work goes here.
- `project/tests/test_model.py` - 45 tests: balance closure, stream positivity,
  retrofit direction, scaling, provenance integrity.
- `*.pdf` (repository root) - the 13 source documents.

## Presentation rules
The chart palette is the validated reference instance and was checked with the
data-viz validator, not by eye. The four adjacent categorical slots pass the
lightness band, chroma floor, CVD separation (worst adjacent dE 9.1 against a
>= 8 target) and normal-vision floor (dE 22.9 against a >= 15 floor), with a
**contrast WARN** on the aqua and yellow slots. That warning is not
dismissable: it obligates visible direct labels plus a table view, which is why
every chart in the app has a "Show Data Table" twin. Keep that pairing if you
add a chart. Other standing rules: one axis per chart and never a second
y-scale; categorical hues assigned in fixed order and never cycled; status
colours reserved and always shipped with an icon or shape as well as colour;
sequential magnitude on one hue; nominal categories on a single colour rather
than a value ramp.

## Common Commands
```bash
cd project
./venv/bin/streamlit run app.py        # dashboard
./venv/bin/python -m pytest tests/ -q  # 45 tests
./venv/bin/python src/validation/literature_check.py   # validation report
./venv/bin/python setup_data.py        # regenerate derived data + provenance
./venv/bin/python src/models/plant.py  # solved coal rate and closure
```
Note: the venv was created before the project moved from `~/Documents/SEM7/BTP`.
It has been rebuilt in place; call `./venv/bin/python` directly rather than
relying on `source venv/bin/activate`, and recreate it with
`python3.14 -m venv venv && ./venv/bin/pip install -r requirements.txt` if the
project moves again.

## Known open work
1. **WHR generation overshoots literature by 20-30%** (572 vs 450-451 kWh/t-DRI).
   Driven by `kiln.unburnt_vm_carbon_frac` and by an 18.75% gas-to-power
   efficiency that ignores the WHR power plant's own auxiliary load. Needs the
   Gaurav et al. waste-heat paper mined for boiler and cycle efficiencies.
2. **Coal rate is over-sensitive to coal heating value at high ash.** With a
   realistic Indian domestic analysis (30% ash, ~19,500 kJ/kg) the solver
   returns ~2.05 t-coal/t-DRI against CEEW's surveyed 1.4-1.6. Sensitivity
   measured at 100 TPD: 23.7% ash / 22,826 kJ/kg gives 1.02; 28% / 20,500 gives
   1.57; 30% / 19,500 gives 2.05. The superlinear response suggests the
   ash-linked terms (char rate per tonne of coal, free-ash sensible heat) are
   over-penalising low-grade coal. Do NOT fix this by choosing preset values
   that land in band -- the Domestic Coal preset deliberately keeps realistic
   coal quality and fails the check visibly.
3. **38 of 90 parameters still need a citation** - see
   `data/literature_gaps.csv`. The prices, the grid emission factor and all the
   biomass properties are the weakest.
4. **No sensitivity analysis yet.** 54 parameters are flagged
   `sensitivity: true`; `params.sensitivity_keys()` returns them and
   `params.with_overrides()` makes sweeps cheap. `src/analysis/` is empty.
5. `econ.fixed_opex_inr_per_day` does not scale with plant capacity.
6. Coal is characterised by one analysis for feed and one for injection; ore is
   treated as a single pellet-grade feed. Lump-ore operation (1.8-2.0 t/t) is
   not yet a preset and will correctly fail the pellet-based ore-rate band.
