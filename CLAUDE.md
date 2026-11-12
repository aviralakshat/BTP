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
   a `status` of `verified` / `derived` / `indicative` / `scenario_choice` /
   `physical_constant` / `needs_citation`. `indicative` is a supplier quote or
   cross-industry analogue; `scenario_choice` is a decision (plant size,
   exchange rate, H2 route), not a fact. Web sources are archived in `data/web/`
   with URL and retrieval date, and a test checks every cited file exists.
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

Current state (model 0.7.1): **mass balance closes to 1.20%**
in solve mode (running `mass_balance.py` directly uses the configured coal rate
and shows 1.31%) with all seven
element balances passing (Fe, C, H, N, S exact), **energy balance closes to
<0.01%** in solve mode, **10 of 10 scored literature checks PASS** (the hydrogen
line is INFO). The plant solves from 5% to 45% coal ash. Baseline at 100 TPD
imported coal: 1.025 t coal/t, 5.586 Gcal/t, 2.083 t CO2/t direct, INR 7,234/t.
190 tests pass, including a finance robustness sweep over every lever combination. See `docs/validation/validation_report.md` for which passes are weak
evidence, and `docs/parameters/data_provenance.md` for the source of every parameter.

## Project Structure
- `project/app.py` - Streamlit UI only. Eight tabs, named for the question
 they answer: Decision, Plant (flows, heat, axial profile, element check),
 Options, Carbon & cost, What if, Evidence (literature checks and the
 parameter register), Compare, Ask. No calculations here. Tabs use
 `st.tabs(..., on_change="rerun")` and each body is guarded by `is_open()`,
 so only the open tab computes. Sidebar widgets carry `w_`-prefixed keys,
 which the reset button clears. The model
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
  `data/parameter_provenance.csv`, `data/literature_gaps.csv`,
  `docs/parameters/data_provenance.md`, `docs/parameters/parameter_reference.md`
  and `outputs/validation_report.txt`. Also reports stale absolute paths in the
  hand-maintained CSVs under `data/` without rewriting them.
- `project/api/server.py` - FastAPI model API (port 8000) for the Next.js
  console in `project/web/` (port 3000). `run_web.sh` starts both.
- `project/config/` - `parameters.json` (145 parameters, 5 still
  `needs_citation`) and `scenarios/` for named override sets.
  `validation_targets.json` (11 acceptance bands).
- `project/src/`
  - `data/parameters.py` - parameter store, provenance, physical constants,
    `out_of_range()`.
  - `data/coal.py` - coal analyses must sum to 100% or the plant refuses them.
    Build a different coal with `daf_rescale()`, never by editing ash alone.
  - `models/baseline.py` - elemental stream model on a 1 t DRI basis.
  - `models/plant.py` - `build_plant()` and the coal-rate solver. Import plant
    construction from here, not from `baseline.py`, so `coal.rate_mode` is
    honoured.
  - `models/mass_balance.py` - total and per-element closure audit.
  - `models/energy_balance.py` - itemised ledger on a coal-NHV basis.
  - `kiln/axial.py` - places that ledger on Dey's 80 m kiln. It does not
    predict metallisation. See `docs/models/05_kiln_axial_profile.md`.
  - `emissions/co2_model.py` - CO2 from the carbon balance, with scopes.
  - `economics/economics.py` - OPEX, annualised CAPEX, export revenue.
    `financial.py` is the cash flow beside that annuity (tax, debt, depreciation).
    It does not change `cost_per_t_dri`.
  - `retrofits/{whr,biomass,hydrogen,oxygen,kiln_control,producer_gas,char_recycle,vfd}.py` -
    deltas on the validated baseline. In `scenarios.evaluate()` the VFD runs
    first (it lowers auxiliary load), then the coal-cutting levers, then WHR, so
    after-burner heat follows the coal that remains. Keep that order.
  - `validation/literature_check.py` - runs the model against the bands.
  - `analysis/scenarios.py` - pathway grid, least-cost search, Pareto front
    and the hydrogen break-even. `sensitivity.py`, `montecarlo.py` and
    `macc.py` are the Phase 3 uncertainty layer. They read
    `config/analysis.json` and `config/distributions.json`, not the plant.
  - `optimization/search.py` - continuous biomass, hydrogen and WHR search.
    It must not cost more than the pathway-grid optimum.
  - `version.py` - model version and the SHA-256 of `parameters.json`.
  - `agent/` - read-only tools, the grounding check, and the analyst that
    quotes them. No language-model API is called. See `docs/software/agent_design.md`.
  - `reporting/export.py` - the workbook and the one-page HTML brief.
- `project/tests/` - balance closure, stream positivity, retrofit direction,
  scaling, provenance, the pathway search, the UI, hardening (coal closure,
  ash range, scale laws, boundary audit) and the golden baseline. Rebuild the
  golden file with `tests/golden/regenerate.py`, only after bumping
  `MODEL_VERSION` and writing the reason in `CHANGELOG.md`.
- `papers/` - every source PDF, named `YYYY_Author_Short-title.pdf`. Text extracts of all 26 are in `data/text/` under the same stem.
- `docs/` - `models/` (one numbered file per model, `retrofits/` one per
  lever), `parameters/`, `data/`, `validation/`, `software/`, `project/`
  (plan, deviations, open questions, sessions, research trail). Index in
  `docs/README.md`. When a model changes, update its file in `docs/models/`.
- `reports/` - course deliverables (proposal, mid-semester report,
  presentation, department guidelines). Not source papers.

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
./venv/bin/python -m pytest tests/ -q  # unit tests plus the golden baseline
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
1. **WHR figures are design values.** Gross 418 kWh/t and export 316 kWh/t are
   inside their bands, using BEE 2019's 60% boiler figure and a 0.2265 cycle
   efficiency derived from the BEE 2011 DPR heat balance. Neither is a
   measured boiler test.
2. **Domestic coal has no sourced analysis.** The old 2.05 t/t was an input
   error: the preset's coal summed to 106%. Closed on Dey's dry ash-free basis,
   the same 30% ash / 19,500 kJ/kg solves to 1.416. The result still moves
   0.28 t/t between the preset heating value and one scaled from Dey's coal
   (20,592 kJ/kg), because losses follow carbon content while input follows
   heating value. Do NOT pick a heating value to land in band; get a measured
   domestic ultimate analysis with its heating value.
3. **5 parameters still need a citation**: DRI and char heat capacity,
   biomass char reactivity, and the biomass and hydrogen substitution caps.
   Seven more are `indicative` (supplier prices and the biomass capital
   analogue, extrapolated about 80-fold down in size). See
   `docs/parameters/data_provenance.md` and `docs/project/OPEN_QUESTIONS.md`.
4. **Uncertainty is computed, not tuned.** 68 parameters are flagged
   `sensitivity: true`. The tornado, Morris sample (8 trajectories, 4 levels),
   400-draw Monte Carlo, abatement curve and continuous search live in
   `src/analysis/` and `src/optimization/search.py`. Coal components that have
   to sum to one are not drawn independently. Method, sample size and the
   carbon-price cases are in `docs/models/11_uncertainty.md`.
5. Fixed daily cost and WHR capital scale with capacity on Kamal et al.'s 0.67
   exponent. The 100 TPD fixed cost (INR 35,000/day) comes from one 2016
   pre-feasibility report in 2016 rupees, and its exponent is carried over
   from capital cost.
6. Coal is characterised by one analysis for feed and one for injection; ore is
   treated as a single pellet-grade feed. Lump-ore operation (1.8-2.0 t/t) is
   not yet a preset and will correctly fail the pellet-based ore-rate band.
7. The cash flow values a retrofit, not the kiln. There is no kiln capital cost
   and no sponge-iron selling price, so there is no whole-plant NPV. See
   `docs/models/08_project_finance.md`.
