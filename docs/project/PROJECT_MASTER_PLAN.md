# PROJECT MASTER PLAN: Coal-Based DRI Kiln Digital Twin and Decarbonisation Decision Product

**Owner:** Aviral Akshat (2023MS11098), B.Tech, Materials Science & Engineering, IIT Delhi
**Repo:** https://github.com/aviralakshat/BTP (branch `main`)
**Audience of this file:** the implementing model (Claude Opus) and any human reviewer.
**Status of this file:** living document. Update the checklist in Section 16 as work completes.
**Last verified against the repo:** 10 Nov 2026, commit `c662404` (see Section 4.1).

---

## 0. How to use this document (read first)

1. **Read the repo before changing anything.** This plan was written from a project brief and then checked against the code (Section 4.1). Verify module names, function signatures and file paths with `ls`, `grep` and by reading the file. If reality differs from this plan, reality wins; record the difference in `docs/project/PLAN_DEVIATIONS.md`.
2. **Work one phase at a time.** Each phase in Section 7 has tasks, acceptance criteria and a stop condition. Do not start phase N+1 until phase N's acceptance criteria pass and tests are green.
3. **Never mix model changes and UI/agent changes in one commit or one session.** Model changes alter numbers; UI and agent changes must not.
4. **Every session starts with:** `project/venv/bin/python -m pytest project/tests -q` and records the pass count. Every session ends with the same, plus the golden-baseline check (Section 6.3).
5. **Run with `project/venv/bin/python` and `project/venv/bin/streamlit`**, not an activated shell.
6. **Grep before asserting.** Thirteen literature PDFs are at the repo root with text extracts in `data/text/`. Never state a page, table or figure number from memory. Grep the extract and quote the location.
7. **When blocked or uncertain about a scientific choice, stop and write the question into `docs/project/OPEN_QUESTIONS.md`** instead of guessing. A wrong silent assumption is worse than a documented gap.

---

## 1. Vision

### 1.1 One-sentence product

A decision-grade digital twin of an Indian coal-based rotary-kiln DRI plant that tells a plant owner, in rupees and tonnes of CO2, **which decarbonisation retrofit to buy, in what order, at what cost, with what confidence, and why**, and lets them interrogate the answer through an AI analyst that can only speak from the model's calculations.

### 1.2 What "McKinsey-grade" means here (concrete, testable)

This is a bar for rigour and communication, not a visual style.

| Principle | What it means in this product | How it is verified |
|---|---|---|
| **Answer first** | Every page leads with the decision and the number, then the evidence. | Overview page has a one-screen "recommendation" card; reviewed against Section 10. |
| **Defensible numbers** | Every number traces to a parameter with a source, a status and a range, or to a derived calculation with a closed balance. | Provenance panel; parameter register; no hard-coded constants (test). |
| **Honest uncertainty** | Point values are always paired with a range (P10-P90) once Phase 3 exists. | Monte Carlo outputs on all headline metrics. |
| **Reproducible** | A number quoted in a report can be regenerated from a model version plus a parameter-file hash. | Version stamp on every export; CI regenerates golden values. |
| **Known limits stated** | Known gaps (WHR overshoot, domestic coal sensitivity, 38 uncited parameters) are shown to the user, not buried. | "Confidence and limits" panel; agent system prompt. |
| **So-what, not just what** | Outputs say what to do: sequence of retrofits, payback, abatement cost, break-even prices. | MACC, roadmap and break-even views. |
| **Exportable** | The user can leave with an executive one-pager, a full technical report and an Excel workbook. | Phase 7 deliverables. |

### 1.3 What it is not (keep in every README and report)

Not a 3-D CFD model. Not a real-time controller. Not a machine-learning predictor of plant behaviour. Not calibrated on live plant data. Not a greenfield hydrogen shaft-furnace model. If Phase 5 (kiln physics) is built, the claim changes to "calibrated to one published plant" and no further.

---

## 2. Users and the questions they ask

| User | Questions the product must answer |
|---|---|
| Plant owner / CFO | What does a 20/40/60% CO2 cut cost per tonne DRI and per year? Payback? What if H2 or coal prices move? |
| Plant manager / process engineer | What is my coal, ore and energy balance? Where are the heat losses? How much waste heat is recoverable? Will the burden still reduce with biomass or H2? |
| Sustainability / policy lead | What are Scope 1, 2 and biogenic emissions? What does a carbon price or CBAM exposure do to the ranking? |
| Academic examiner | Is every input sourced? Does the model close? Where does it disagree with the literature, and is that disclosed? |
| Any of the above via chat | "What is the cheapest route to a 40% cut at 200 TPD, and how sure are we?" |

---

## 3. Non-negotiable rules (inherited, plus additions)

Inherited from the project brief (do not weaken):

1. **No magic numbers.** A new numeric assumption goes into `project/config/parameters.json` with `value`, `unit`, `min`, `max`, `source`, `status`, and is read through `project/src/data/parameters.py`. Model files contain no numeric constants beyond mathematical ones and the molar masses already held in `parameters.py`.
2. **Validation targets are not inputs.** Bands in `validation_targets.json` are never read by the model. A test asserts no target key equals a parameter key. Never copy a band into a parameter to make a check pass.
3. **Derive rather than assume.** Ore rate, air rate, waste-gas composition and (in solve mode) coal rate stay solved.
4. **Report residuals.** Never spread an imbalance or add a fudge factor to close a balance.
5. **Keep the KILN and STACK boundaries distinct.** KILN: volatiles leave unburnt (Dey's boundary, the energy-balance boundary). STACK: kiln plus after-burner chamber (CO2 boundary and the heat WHR can claim). Energy terms are labelled "to ABC".
6. **Do not tune the known failures into the bands** (Section 5.2).
7. **UI stays in `app.py` and `src/ui/`.** New calculations go in `src/`. Keys passed to `st.cache_data` must not start with an underscore.
8. **Every chart has a table twin** ("Show Data Table" expander). One axis per chart, no second y-axis. Categorical colours follow the fixed SERIES order. Status colours always ship with an icon or shape.

Additions for this plan:

9. **The AI agent never computes.** Every number it states comes from a tool call into `src/`. See Section 8.
10. **The agent and UI never write `parameters.json` or `validation_targets.json`.** Scenario overrides are session-only and range-checked against each parameter's `min`/`max`.
11. **Golden baseline is protected.** Phases other than model phases must not change any golden value (Section 6.3). Model phases must change golden values only deliberately, with a changelog entry explaining why.
12. **A claim is only as strong as its status.** Anything depending on a `needs_citation` parameter is displayed as provisional.
13. **No silent success.** A validation band that passes because an input was set to the band's value is not a pass. Mark such bands "input, not evidence" (e.g. metallisation, which is an input via `dri.fe_metallic_frac = 0.835`).

---

## 4. Current state snapshot

- **Plant default:** 100 TPD rated, 90% utilisation (90 TPD), 330 operating days/year. UI capacities: 50, 100, 175, 200, 350, 500, 600 TPD.
- **Calibration plant:** Dey et al. (2015), *Case Studies in Thermal Engineering* 6, 1-15, 453.6 TPD, Tables 4-11.
- **Baseline (imported-coal preset, solve mode, 10 Nov 2026):** coal 1.059 t/t DRI; ore 1.622 t wet ore/t DRI (deriving it reproduces Dey's measured 1.587 within 0.2% on the calibration basis); metallisation 90.2% (input); 5.77 Gcal/t DRI; mass closure 1.14%; energy closure 0.0004%; CO2 2.151 t/t direct, 2.200 t/t reported; cost about INR 19,050/t DRI.
- **Stack:** Python 3.14, Streamlit 1.64, Plotly, pandas, numpy, pytest. 73 tests pass.
- **Parameters:** 90 total; 50 verified, 38 needs_citation, 2 physical_constant; 57 flagged `sensitivity: true`.
- **Modules (project/src):** `data/parameters.py`, `models/{baseline,plant,mass_balance,energy_balance}.py`, `emissions/co2_model.py`, `economics/economics.py`, `retrofits/{whr,biomass,hydrogen}.py`, `analysis/scenarios.py`, `validation/literature_check.py`, `ui/`, empty `optimization/`.
- **Dashboard:** seven tabs (Overview, Retrofit Pathways, Mass & Energy, Emissions, Economics, Validation, Parameters); light theme pinned in `project/.streamlit/config.toml`.
- **Validation:** 11 bands; 8 pass; two WHR bands fail (documented); full-DR hydrogen band is informational.
- **Pathway result (100 TPD, green H2 INR 305/kg):** 20% cut via WHR + 20% biomass at -INR 2,121/t; 30% via + 10% H2; 40% via WHR + 20% biomass + 20% H2 at +INR 8,476/t; 50% via + 30% H2; 60% unreachable inside caps (reductant-carbon ratio < 1). H2 break-even about INR 42/kg.

### 4.1 Verified against the repo (10 Nov 2026, commit `c662404`)

Confirmed: every figure in the list above was regenerated from the code on this date (tests run, parameter statuses counted from `parameters.json`, baseline solved with `build_plant()` defaults, pathway table from `pathway_grid` / `least_cost`). The module list matches `project/src`.

Differences between this plan and the repo. Copy these into `docs/project/PLAN_DEVIATIONS.md` during Phase 0:

| # | Plan says or assumes | Repo has | Action |
|---|---|---|---|
| 1 | `docs/`, `README.md`, `CHANGELOG.md`, `.github/workflows/`, `src/version.py` | None of these exist. Root has `RUN.md`, `REPORT_SUMMARY.md`, `PRESENTATION_CONTENT.md`, `CLAUDE.md` | Create in Phase 0; fold `RUN.md` into the README |
| 2 | Tests split into `unit/ integration/ golden/ agent_evals/` | Flat: `test_model.py` (39 functions), `test_ui.py` (13), `test_scenarios.py` (6); 73 cases after parametrisation | Keep flat files; add `golden/` and `agent_evals/` as new folders only |
| 3 | `src/optimization/` is a package | Empty directory, no `__init__.py` | Add `__init__.py` when Phase 3 starts |
| 4 | Repo-root PDFs are the 13 literature sources | 15 PDFs: the 13 sources plus `BTP_Mid_Sem_Report_2023MS11098.pdf` and `IITD Webmail __ BTP_reports_instructions_2026-27.pdf` | Treat only the 13 as literature. Check repo visibility before public deployment |
| 5 | `CLAUDE.md` is the always-applied context | It is stale: says 45 tests (now 73), 54 sensitivity-flagged (now 57), six tabs (now seven) | Update `CLAUDE.md` in Phase 0 so the implementing model is not misled |
| 6 | One virtualenv at `project/venv` | A second 466 MB virtualenv at `project/tests/venv`, untracked by git | Owner to confirm and delete; pytest must not collect it |
| 7 | Literature inventory in one place | Two copies: `data/literature_inventory.csv` (hand-maintained, root) and `project/data/literature_inventory.csv` (generated by `setup_data.py`) | Keep the generated copy authoritative; record which is which |
| 8 | Biomass and H2 retrofit costs | Both modules return `capex_inr = 0.0`; costs are operating cost only | Phase 1 task 3 |
| 9 | Scale effects | `plant.capacity_tpd` itself is `needs_citation`; fixed OPEX INR 50,000/day flat; WHR CAPEX INR 6 crore/MW linear. The 100/200/350/500 table returns identical choices | Phase 1 task 4 |
| 10 | Agent model strings `claude-sonnet-5-5` / `claude-opus-5-5` | Not yet used anywhere | Verify against Anthropic docs at implementation time |

---

## 5. Known gaps and how this plan treats them

### 5.1 Gaps to be closed by real work (Phase 1)

| Gap | Why it matters | Planned fix |
|---|---|---|
| WHR gross generation overshoots Nduagu et al. (450-451 kWh/t generated, 351 exported) by 20-30% | WHR savings, which drive the headline "saves money" result, are optimistic | Mine Gaurav et al. for boiler and cycle efficiencies; add WHR auxiliary load; re-check `kiln.unburnt_vm_carbon_frac` (0.245, Dey Table 10) against its source |
| 38 of 90 parameters `needs_citation` | Weakest: prices, grid emission factor, all biomass properties | Source each from `project/data/literature_gaps.csv`; CEA for grid factor; promote status only with a real citation |
| Biomass and hydrogen have no handling/supply CAPEX | 40-50% cases are flattered | Add cited CAPEX parameters (storage, feed system, H2 piping/storage/injection) |
| No economy of scale (fixed OPEX flat, WHR CAPEX linear) | The 100/200/350/500 comparison returns the same answer at every size | Add scaling exponent for CAPEX and OPEX scaling with capacity, each cited; if no citation exists, mark `needs_citation` and show the effect as provisional |
| No process-optimisation or syngas case | Both are in the original brief | Implement as scenario types in `analysis/scenarios.py` with cited parameters |
| `src/optimization/` empty; sensitivity flagged not run | No uncertainty or ranking of drivers | Phase 3 |
| No Gaurav-based WHR cross-check | See first row | Same |

### 5.2 Documented limitations that must stay visible (do NOT "fix" by choosing nicer inputs)

- **Domestic coal over-sensitivity.** 30% ash / ~19,500 kJ/kg solves to ~2.05 t coal/t DRI against CEEW's surveyed 1.4-1.6. At 100 TPD: 23.7% ash / 22,826 kJ/kg gives ~1.02; 28% / 20,500 gives ~1.57; 30% / 19,500 gives ~2.05. The Domestic preset is meant to fail that check visibly. Investigate the physics (ash and heating-value coupling in the energy balance, fixed-carbon accounting) and document findings, but do not adjust inputs to pass.
- **Metallisation, DRI carbon and accretion risk are not predicted.** Making them outputs is Phase 5 (a new model).
- **Lump-ore operation** (1.8-2.0 t ore/t) is not a preset and correctly fails the pellet ore-rate band.
- **Hydrogen price is an assumption** (INR 305/kg). Show it as the dominant uncertainty.

---

## 6. Target architecture and repository template

### 6.1 Target layout

```
BTP/
├── README.md                       # product + science summary, quick start, limits
├── docs/project/PROJECT_MASTER_PLAN.md          # this file
├── CHANGELOG.md                    # model version history (see 6.4)
├── LICENSE / CITATION.cff
├── .github/workflows/ci.yml        # pytest + golden + lint on every push
├── Dockerfile / docker-compose.yml
├── data/text/                      # existing: PDF text extracts (read-only)
├── *.pdf                           # existing: 13 literature PDFs
├── docs/
│   ├── PLAN_DEVIATIONS.md          # where repo differs from this plan
│   ├── OPEN_QUESTIONS.md           # scientific / scoping questions for the owner
│   ├── model_description.md        # equations, boundaries, assumptions (KILN vs STACK)
│   ├── data_provenance.md          # how each parameter was sourced
│   ├── validation_report.md        # all bands, pass/fail, honest commentary
│   ├── agent_design.md             # tool contracts, guardrails, eval results
│   ├── user_guide.md
│   ├── research/                   # literature review and materials-model options
│   └── thesis_figures/             # exported figures with data tables
└── project/
    ├── app.py                      # Streamlit shell only
    ├── config/
    │   ├── parameters.json         # the single source of numeric truth
    │   ├── validation_targets.json # never read by model
    │   └── scenarios/              # saved named scenarios (JSON)
    ├── data/
    │   ├── literature_gaps.csv
    │   └── price_series/           # dated price datasets with source files (Phase 4)
    ├── src/
    │   ├── data/parameters.py
    │   ├── models/                 # baseline, plant, mass_balance, energy_balance
    │   ├── kiln/                   # Phase 5: 1-D axial kiln model (new)
    │   ├── emissions/co2_model.py
    │   ├── economics/              # economics.py + financial.py (NPV/IRR/LCOP) + carbon_price.py
    │   ├── retrofits/              # whr, biomass, hydrogen (+ syngas, process_opt)
    │   ├── analysis/               # scenarios, sensitivity, montecarlo, macc, roadmap
    │   ├── optimization/           # continuous optimiser, constraint handling
    │   ├── validation/             # literature_check
    │   ├── agent/                  # tools, schemas, prompts, agent, grounding, evals
    │   ├── api/                    # Phase 8: FastAPI wrapper around src/
    │   ├── reporting/              # PDF/Excel/PPT exporters
    │   └── ui/                     # components, charts, theme, pages, chat
    ├── tests/
    │   ├── test_model.py test_ui.py test_scenarios.py   # existing, keep flat
    │   ├── golden/ agent_evals/                          # new
    │   └── fixtures/
    └── .streamlit/config.toml
```

If the existing layout differs, keep the existing layout and add only what is missing. Record any divergence.

### 6.2 Layering rule

`ui/` and `agent/` and `api/` may import from `src/` models. Models must never import from `ui/`, `agent/` or `api/`. Parameters are read only through `data/parameters.py`.

### 6.3 Golden baseline (regression protection)

Create `project/tests/golden/baseline_100tpd_imported.json` containing the solved values listed in Section 4 plus the pathway table, generated from the current code before any change. A test compares live outputs to it with explicit tolerances (for example 1e-6 relative for mass and energy, 1e-4 for cost). Rules:

- UI, agent, API, reporting and docs phases must leave it untouched.
- Model phases may change it only in a dedicated commit that updates the file, adds a `CHANGELOG.md` entry, and states the cause.

### 6.4 Versioning

`src/version.py` holds `MODEL_VERSION` (semver). Every result object, export and agent answer carries `model_version` plus a SHA-256 of `parameters.json`. A quoted number must be reproducible from those two values.

---

## 7. Phases

Each phase lists tasks, acceptance criteria (AC) and a stop condition. Estimated effort assumes one focused implementer.

### Phase 0: Orientation and safety net (1-2 days)

Tasks
- Read the whole `project/src` tree, `app.py`, `parameters.json`, `validation_targets.json`, tests. Write `docs/models/README.md` skeleton from what the code actually does.
- Run tests; record pass count (expected 73).
- Generate the golden baseline file and the golden test (Section 6.3).
- Add `src/version.py`, parameter-file hashing, `CHANGELOG.md`.
- Create `docs/project/PLAN_DEVIATIONS.md` (seed it from Section 4.1) and `docs/project/OPEN_QUESTIONS.md`.
- Update the stale counts in `CLAUDE.md`.
- Add CI (GitHub Actions) running pytest and the golden test.

AC: all existing tests pass; golden test passes; CI green; no numeric change anywhere.

### Phase 1: Model hardening (2-3 weeks). MODEL PHASE

Goal: make the existing planning twin defensible before building on it.

Tasks
1. **WHR rework.** Read Gaurav et al. and Nduagu et al. extracts. Extract boiler efficiency, steam-cycle efficiency, auxiliary power, stack temperature practice. Add parameters with citations. Model WHR auxiliary load explicitly. Re-evaluate the 18.75% gas-to-power efficiency as boiler x cycle with sourced values. Report the new WHR validation bands honestly, whether they pass or still fail. Do not tune toward the band.
2. **Citation campaign.** For each of the 38 `needs_citation` parameters: find a source in the 13 PDFs or a public authoritative source (CEA, MoP, MNRE, CEEW, IEA, Hall et al.), grep for the table or page, record `source` with location, update `status` only when verified, tighten `min`/`max` to the source's range. Where nothing is found, leave `needs_citation` and note it in `literature_gaps.csv`. Priority: grid emission factor, coal/ore/dolomite/power prices, biomass properties, WHR capex.
3. **Retrofit CAPEX completeness.** Add handling/supply CAPEX and OPEX for biomass (yard, drying, feed) and hydrogen (storage, compression, injection, safety), as cited parameters. Include them in `economics`, payback and pathway cost.
4. **Scale effects.** Add capex scaling exponent, fixed-OPEX scaling, and labour scaling with capacity, each cited. Regenerate the 100/200/350/500 table; it should now differ by size or the plan must state why not.
5. **Missing cases.** Add syngas injection and process-optimisation cases (e.g. excess-air reduction, coal-char management, dust loss reduction) as `evaluate()` options with joint reductant-carbon checks.
6. **Domestic coal investigation.** Trace why 30% ash gives ~2.05 t/t. Check ash dilution, fixed-carbon fraction, volatile release and heating-value basis. Document the finding in `docs/validation/validation_report.md`. Change the model only if a real error is found; a real error fix updates the golden file with explanation.
7. **Boundary audit.** Confirm every energy term is labelled KILN or STACK ("to ABC") and every CO2 line is on the STACK boundary.

AC
- Parameter statuses re-counted and published in `docs/parameters/data_provenance.md` (target: `needs_citation` under 15, with each remaining one justified).
- WHR validation shows result with sourced efficiencies; residual gap, if any, explained.
- Biomass and hydrogen scenarios include supply CAPEX; pathway table regenerated.
- All tests green; new tests for every new parameter path and scenario type; golden file updated with changelog.

Stop condition: do not proceed to uncertainty work until WHR and CAPEX changes are merged, because they move the headline numbers.

### Phase 2: Agent MVP (1.5-2 weeks). AGENT PHASE, no model changes

See Section 8 for the full specification. Deliver: `src/agent/`, `src/ui/chat.py`, an eighth "Analyst" tab, evals, tests, `docs/software/agent_design.md`.

AC
- Agent answers the 40-question eval set (Section 8.6) with zero ungrounded numbers.
- Agent cannot modify parameter or validation files (test).
- Golden baseline unchanged.

### Phase 3: Uncertainty, sensitivity and optimisation (2-3 weeks). ANALYSIS PHASE

Tasks
1. **Tornado / one-at-a-time sensitivity** over the 57 sensitivity-flagged parameters, using each parameter's `min`/`max`. Outputs: ranked impact on INR/t, CO2 cut, and abatement cost.
2. **Global sensitivity (Sobol or Morris)** with a documented sample size and convergence check.
3. **Monte Carlo** with parameter distributions: triangular on `[min, value, max]` by default; allow per-parameter override in a separate `config/distributions.json` (not in model code). Correlations only where documented. Report P10/P50/P90 and probability that a pathway beats the base case.
4. **Continuous optimiser** in `src/optimization/` over biomass and H2 fractions and WHR on/off with the hard reductant-carbon constraint; compare to the 60-cell grid to verify it reproduces grid results.
5. **MACC** (marginal abatement cost curve) and a **carbon-price sweep** (INR/t CO2 range, including a CBAM-style case, with the price source cited or marked assumption).
6. **Break-even analysis:** H2 price, coal price, power price, carbon price at which the ranking flips.
7. Expose all as agent tools and UI views.

AC: every headline metric has a P10-P90 range; tornado chart and table twin exist; optimiser reproduces grid optimum within tolerance; tests cover seeded reproducibility.

### Phase 4: Financial model and data layer (2 weeks). MODEL + DATA PHASE

Tasks
- `economics/financial.py`: NPV, IRR, LCOP (levelised cost of DRI), payback (simple and discounted), tax, depreciation schedule, debt/equity split, escalation of prices, working capital. Every financial assumption is a cited parameter or explicit scenario input.
- Price time series in `project/data/price_series/` with source files and retrieval dates (coal, power tariffs, green H2 cost trajectories from Hall et al. and other cited sources, carbon price scenarios). Scenarios: low / base / high.
- **Scenario manager:** save, name, load, diff and export scenarios as JSON in `config/scenarios/`; every saved scenario stores model version and parameter hash.
- Reconcile the simple CRF-based INR/t (11% over 20 yr) with the financial model; show both and explain differences.

AC: NPV/IRR/LCOP tests against hand-calculated cases; scenario round-trip test; reconciliation table in docs.

### Phase 5: Kiln process model (6-10 weeks). NEW MODEL. Optional but required for the "actually models the kiln" claim

Gate: the owner decides in `docs/project/OPEN_QUESTIONS.md` whether this phase is in scope. If not in scope, the product is described as a "planning twin" everywhere.

Tasks
1. **Specification document first** (`docs/models/05_kiln_axial_profile.md`): axial discretisation (e.g. 50-200 cells), state variables (bed temperature, gas temperature, wall temperature, solid composition by phase, gas composition), governing equations (solid and gas energy balances, radiation/convection/conduction to wall and bed, wall and shell losses, char and volatile combustion, gas-phase combustion), kinetics (Boudouard gasification, stepwise iron-oxide reduction Fe2O3 to Fe3O4 to FeO to Fe, ash and dolomite desulphurisation), solids transport (residence time from kiln slope, rotation, fill level), air-port injection along the kiln. Cite every correlation and kinetic parameter; each becomes a parameter in `parameters.json`.
2. **Implementation** in `src/kiln/` as a steady-state solver first (ODE boundary-value or marching solver with iteration on gas flow). Dynamic version only after steady state is validated.
3. **Closure with the global balance:** the 1-D model's integral over the kiln must close the mass and energy balance; residuals are reported.
4. **Calibration** to Dey et al. (453.6 TPD) only, with parameters fitted ahead of time and frozen. Hold out other literature points (Bhardwaj, Vigneswaran, CEEW bands) as unseen tests. Report fit and holdout error separately.
5. **Metallisation becomes a prediction**, with its error versus Dey's measured value reported. The planning twin's `dri.fe_metallic_frac` input remains for the planning mode; the UI shows which mode is active.
6. **Surrogate emulator** (optional): train a fast regression emulator (e.g. Gaussian process or gradient boosting) on kiln-model runs so the optimiser and agent can query thousands of cases. Validate against held-out physics runs and show emulator error on every surrogate-based answer. The emulator never replaces the physics model for the headline claim.
7. **Plant data hook** (optional, only if real data is obtained): a data-ingestion schema (CSV or OPC-UA exported CSV) for coal feed, ore feed, product analysis, shell temperature; data reconciliation (weighted least squares) to estimate unmeasured variables with uncertainty. Without real data, do not claim a "live twin".

AC: documented fit/holdout errors; metallisation prediction error stated; closure residuals printed; physics tests (mass conservation per cell, energy conservation, monotonic limits, grid-refinement convergence).

### Phase 6: Product UI and experience (2-3 weeks, runs in parallel with Phases 3-4). UI PHASE, no model changes

Design system
- Keep the light theme and `#fcfcfb` surface. Fixed SERIES colour order. Status colours with icons. One axis per chart. Table twin for every chart.
- Typography: one family, a clear scale; numbers use tabular figures. Consistent units and rounding rules across pages (a `ui/format.py` helper; no ad hoc formatting).

Pages (restructure existing seven tabs plus new ones)
1. **Executive Summary** (new first page): the recommendation card (cheapest route to the selected target, cost per tonne, annual cost, CO2 cut, payback, confidence range), a three-number headline row, and a "what would change this answer" list (top three sensitivities).
2. **Plant Model:** the kiln schematic with live stream numbers (coal, ore, air, dolomite, DRI, waste gas, char), KILN vs STACK toggle, Sankey of energy and carbon flows.
3. **Retrofit Pathways:** roadmap (sequenced steps), pathway grid heatmap, Pareto front, and infeasibility explanations in plain language (the 60% case).
4. **Economics:** cost waterfall, MACC, NPV/IRR/LCOP, carbon-price sweep.
5. **Risk and Sensitivity:** tornado, Monte Carlo distributions, break-even prices.
6. **Emissions:** Scope 1, 2, biogenic, per tonne and per year, with boundary toggles.
7. **Validation and Provenance:** all bands with pass/fail/input/informational states; parameter register with status icons; "confidence and limits" panel.
8. **Scenario Compare:** side-by-side saved scenarios with diff highlighting.
9. **Analyst (chat):** Section 8.
10. **Reports:** export buttons (Section 12).
11. **Parameters (advanced):** searchable register, session-only overrides with min/max enforcement and visible "modified" badge; reset button.

UX requirements
- Loading states, input validation messages in plain language, a persistent banner when any override is active or any `needs_citation` parameter materially influences the shown result.
- Responsive layout checked at laptop and tablet widths.
- Accessibility: contrast checked on all text and status colours; no meaning by colour alone; keyboard-reachable controls; chart alt text via the table twin.
- Performance: results cached with legal cache keys; first paint under 3 s on the default case; pathway grid under 2 s (profile and fix if not).

AC: a non-technical reviewer can reach the headline recommendation in under 30 seconds without reading documentation; UI tests (Streamlit `AppTest`) cover every page without exceptions; no calculation code in `app.py`.

### Phase 7: Reporting and deliverables (1-2 weeks)

Exports (all stamped with model version, parameter hash, date, scenario name):
- **Executive one-pager (PDF):** recommendation, three numbers, one chart, the top risks and limits.
- **Technical report (PDF):** methods, boundaries, assumptions table with sources, results, sensitivity, validation (including failures), limitations.
- **Excel workbook:** inputs, balances, pathway table, financial model with formulas where practical, and a data sheet per chart.
- **Slide deck (PPTX):** optional, generated from the same data.
- **Assumption register (CSV/Excel):** every parameter with value, unit, range, source, status.

AC: reports regenerate identically from a saved scenario; every figure in a report has its table in the appendix.

### Phase 8: Engineering and deployment (1-2 weeks, parallel)

- Split a thin FastAPI layer (`src/api/`) exposing the same functions the agent tools use; Streamlit and the agent call the same contracts. Pydantic schemas for all inputs and outputs.
- Dockerfile and docker-compose; pinned dependencies (`requirements.lock` or `uv.lock`).
- Deployment: Streamlit Community Cloud with repository `aviralakshat/BTP`, branch `main`, main file `project/app.py`, Python 3.13 or 3.14. Secrets (API key) via Streamlit secrets, never committed. Add a `/health` check if using the API.
- Lint and typing: ruff, mypy (at least on `src/`), pre-commit hooks.
- Test pyramid: unit (every function), integration (plant to economics), golden, UI (`AppTest`), agent evals. Target line coverage above 85% on `src/`.
- Security: no secrets in repo; the agent's tool layer validates all inputs; rate limit and per-session cap on LLM calls; log tool calls without logging user personal data.

AC: fresh clone to running app in under 10 minutes following the README; CI green on a clean machine; deployed app loads the default case.

### Phase 9: Documentation and academic packaging (2 weeks)

- README: problem, approach, results table, screenshots, limitations, quick start.
- `docs/models/README.md` with every equation and boundary diagram.
- `docs/validation/validation_report.md` with all bands including failures, plus the domestic-coal investigation.
- Thesis/report chapters mapped to code modules; figures exported with data tables.
- A one-page "claims and evidence" table: each claim in the thesis, the code path, the test, the source.
- Viva preparation: a list of the 20 hardest questions an examiner could ask and the repo-grounded answers (include the failures).

---

## 8. AI agent specification

### 8.1 Purpose

A conversational analyst that explains the model, runs scenarios, compares options and explains why, using only the model's calculations. It is an orchestrator over `src/`, not a calculator.

### 8.2 Architecture

```
Streamlit chat tab ──► Agent loop (Anthropic API, tool use)
                            │  system prompt + tool schemas
                            ▼
                   src/agent/tools.py   (typed wrappers; JSON in/out; validation)
                            │
                            ▼
    build_plant · evaluate · pathway_grid · least_cost · pareto_front ·
    h2_breakeven_price · literature_check · parameters lookup ·
    sensitivity · montecarlo · optimiser · financial · report export
```

- Model: default `claude-sonnet-5-5` (balance of cost and quality); allow `claude-opus-5-5` for complex analysis through a config key. Verify current model strings in Anthropic docs at implementation time.
- API key: `st.secrets["ANTHROPIC_API_KEY"]`; never in repo; handle missing key gracefully (chat tab explains it is disabled).
- Streaming responses; conversation memory kept in session state; tool results trimmed to what is needed (large tables are summarised in the tool result with a handle to the full data).

### 8.3 Tool contracts (minimum set)

| Tool | Inputs (validated) | Returns |
|---|---|---|
| `run_scenario` | capacity_tpd, utilisation, coal_preset, coal_rate_mode, whr_on, biomass_frac, h2_frac, h2_type, overrides | Full result dict: streams, closure residuals, energy ledger, CO2 (direct, reported, biogenic), cost breakdown, reductant-carbon ratio, feasibility flag, model_version, param_hash |
| `find_least_cost` | target_cut, capacity, preset, h2_type, price overrides | Chosen combination, actual cut, cost change, abatement cost, CAPEX, payback; or an explicit "not feasible within caps" with the binding constraint |
| `pareto_frontier` | scenario context | Table of non-dominated combinations |
| `compare_scenarios` | list of scenario specs | Side-by-side table and deltas |
| `h2_breakeven` | scenario context | Break-even price and assumed price |
| `get_parameter` | name or search term | value, unit, min, max, source, status |
| `list_parameters_by_status` | status, sensitivity flag | Filtered list |
| `run_validation` | scenario context | All bands with pass / fail / input-not-evidence / informational |
| `explain_closure` | scenario context | Mass and energy residuals per element/stream |
| `sensitivity` | metric, top_n | Ranked tornado data (Phase 3) |
| `monte_carlo` | metric, n, seed | P10/P50/P90 and probability statements (Phase 3) |
| `optimise` | objective, constraints | Continuous optimum (Phase 3) |
| `financials` | scenario context, price scenario | NPV, IRR, LCOP, payback (Phase 4) |
| `export_report` | scenario name, format | File path for the dashboard to offer as download (Phase 7) |
| `propose_ui_state` | sidebar settings | Returns a proposal; the UI asks the user to confirm before applying |

### 8.4 Guardrails (each needs a test)

1. **Grounding check.** After each reply, extract numeric tokens and verify each appears in some tool result from this turn (within rounding tolerance) or in the user's own message. Ungrounded numbers trigger one automatic regeneration with a correction note; if still ungrounded, the reply is marked "unverified" in the UI.
2. **Read-only data.** The tool layer cannot write `parameters.json` or `validation_targets.json`. Overrides are session-scoped, range-checked, and shown in the UI as active.
3. **Status honesty.** If a tool result depends on `needs_citation` parameters, the agent says so. If a validation band is an input (metallisation) or informational, it never calls it a successful validation.
4. **Known-limits injection.** The system prompt lists: WHR overshoot; domestic coal failing on purpose; metallisation as input; hydrogen price assumed; no process twin unless Phase 5 shipped; no live plant data.
5. **Scope refusal.** CFD, real-time control, greenfield H2 shaft furnace, refractory design: politely not modelled here.
6. **No cherry-picking.** If a result is bad or infeasible (the 60% case), the agent states it plainly and explains the binding constraint.
7. **Calculation trace.** Every answer has a "Show calculation" expander listing tool calls, inputs and raw outputs, matching the table-twin rule.
8. **Cost control.** Per-session message and token caps; clear message on reaching the cap.
9. **Prompt-injection hygiene.** Text from documents or parameter sources is treated as data, never instructions.

### 8.5 System prompt skeleton (store in `src/agent/prompts.py`, not inline)

- Role: analyst for a coal-based DRI kiln decarbonisation model.
- Hard rule: never perform arithmetic on model quantities yourself; call a tool; quote tool outputs.
- Always report: capacity and preset assumed, whether results are provisional, the model version.
- Style: answer first, then the supporting numbers, then caveats, short paragraphs, no filler.
- Ambiguity: if the user omits capacity, preset or target, state the default you used rather than asking, unless the answer would materially change.
- Limits: the injected list from guardrail 4.

### 8.6 Evaluation

- `project/tests/agent_evals/` with 40+ cases in YAML: question, expected tool calls, expected numeric fields (computed live by the model, not typed in), expected caveats, forbidden behaviours.
- Categories: factual lookups (parameter source), scenario runs, target searches (including infeasible), comparisons, "why" questions (binding constraints), uncertainty questions (Phase 3), adversarial (asking it to change a parameter, to invent a citation, to skip the model, to say domestic coal passes).
- Two modes: stubbed LLM for CI (checks the tool layer and grounding checker), and a live-model run triggered manually before releases, with results saved to `docs/software/agent_design.md`.
- Metrics: grounding rate (target 100%), correct tool selection, refusal correctness, latency, cost per answer.

### 8.7 Optional later agent features

- Multi-step "analyst mode" that plans a study (e.g. "build me a decarbonisation roadmap for 200 TPD") and produces a report through the export tools.
- Voice or file upload for plant data (only after Phase 5 data hook).

---

## 9. Data strategy ("better data")

1. **Parameter register as product.** `parameters.json` plus a generated `data_provenance.md`: each row has value, unit, range, source with page/table, status, which outputs it affects (from sensitivity), and the date last reviewed.
2. **Source hierarchy:** measured plant data (Dey) > peer-reviewed review/survey (CEEW, Nduagu, TERI, BEE) > government statistics (CEA, MoP, MNRE) > vendor or industry reports > assumption (explicitly marked).
3. **Price data:** dated series with source and retrieval date; never silently update a price without storing the old one.
4. **Gap register:** `literature_gaps.csv` is maintained; each unresolved parameter has an owner, a search note and a priority from its sensitivity rank.
5. **Second calibration plant:** currently out of scope; if a second plant's data becomes available, add it as a holdout validation dataset, not a tuning dataset, unless Phase 5 has already frozen parameters.
6. **Data reconciliation (Phase 5 optional):** only with real plant measurements.

---

## 10. Communication standards (the "consulting-grade" layer)

- **Headline sentences** that carry the so-what: for example "A 40% cut costs about INR X per tonne (P10-P90: A to B), driven mainly by the hydrogen price; hydrogen reaches parity with coal at about INR 42/kg."
- **Chart rules:** a title that states the finding, units on axes, source and model version in the footer, one message per chart, direct labels over legends where possible, table twin always.
- **Language:** plain, no jargon without a tooltip; units always explicit (INR/t DRI, t CO2/t DRI, Gcal/t DRI).
- **Show the limits next to the result**, not on a separate page only.
- **Decision framing:** every pathway page ends with "Recommended", "Conditional on", and "Not recommended because".

---

## 11. Testing and quality gates

| Gate | Requirement |
|---|---|
| Unit | Every model function; parameter read path; boundary (KILN vs STACK) tests |
| Conservation | Elemental closure for Fe, C, H, N, S; energy closure in solve mode; residual reporting tests |
| Rule enforcement | No numeric literals in model files (AST-based test with an allowlist for mathematical constants); no validation-target key equals a parameter key |
| Golden | Section 6.3 |
| Property tests | Hypothesis-style: monotonicity (more biomass never raises fossil CO2), bounds, no negative flows |
| Convergence | Coal-rate bisection tolerance; kiln-grid refinement (Phase 5) |
| UI | `AppTest` for each page; no exceptions under extreme inputs |
| Agent | Section 8.6 |
| Performance | Time budget tests for pathway grid and Monte Carlo (seeded) |
| Docs | Docs build or markdown link check |

Release criteria for any tagged version: all gates green; changelog updated; validation report regenerated.

---

## 12. Work-session protocol for the implementing model

Each session:

1. State the phase and task being done. Re-read the relevant rules (Section 3).
2. Run tests and record counts.
3. Make the smallest coherent change. Add or update tests in the same change.
4. Run tests and the golden check. If the golden changed unexpectedly, stop and investigate before continuing.
5. Update docs touched by the change (`model_description.md`, `data_provenance.md`, `CHANGELOG.md`).
6. Write a short session note in `docs/project/sessions/YYYY-MM-DD.md`: what changed, what numbers moved and why, what is left, any deviation or open question.
7. Commit with a message of the form `phase-N: <what> (golden: unchanged|updated)`.

Never: add a constant to a model file; edit a validation band to pass a check; change an input to hit a literature value; delete a failing test; commit secrets; claim a source says something without grepping the extract.

### Suggested prompt sequence for Claude Opus

0. "Execute the materials-science literature expansion in `docs/project/research/RESEARCH_TASK.md`. Research and planning only; write only under `docs/project/research/`."
1. "Read `docs/project/PROJECT_MASTER_PLAN.md` and the repo. Execute Phase 0 only. Report pass count, golden file, CI status, and every deviation between plan and repo."
2. "Execute Phase 1 tasks 1-2 (WHR rework and citation campaign). Stop and report before touching CAPEX."
3. "Execute Phase 1 tasks 3-7."
4. "Execute Phase 2 (agent MVP). No model changes."
5. "Execute Phase 3 (sensitivity, Monte Carlo, optimiser, MACC)."
6. "Execute Phase 4 (financial model, price series, scenario manager)."
7. "Execute Phase 6 UI restructure in two sessions: shell and Executive Summary first, then remaining pages."
8. "Execute Phase 7 reporting."
9. "Execute Phase 8 engineering and deployment."
10. "If approved, execute Phase 5 starting with the kiln model specification document only; wait for review before implementing."
11. "Execute Phase 9 documentation and viva preparation."

Step 0 produces `docs/project/research/MASTER_PLAN_V2.md`. Once the owner accepts it, it replaces this file and the phase order above is revised from it.

---

## 13. Timeline (indicative)

| Weeks | Work |
|---|---|
| 1 | Research step (Section 12, step 0) and Phase 0 |
| 2-4 | Phase 1 |
| 5-6 | Phase 2 |
| 7-9 | Phase 3 (with Phase 6 UI in parallel) |
| 10-11 | Phase 4 |
| 12-13 | Phase 7 and Phase 8 |
| 14-15 | Phase 9 |
| 6-10 additional weeks | Phase 5 if approved (can run after Phase 4) |

Total: about 15 weeks without the kiln physics model, 21-25 weeks with it.

---

## 14. Risks and how to handle them

| Risk | Impact | Mitigation |
|---|---|---|
| Fixing WHR removes the "saves money" headline | Result changes materially | Treat as a finding; report both; keep the old version in the changelog |
| Citations cannot be found for some parameters | Provisional results persist | Keep status `needs_citation`; show provisional badge; never invent a source |
| LLM states an ungrounded number | Credibility | Grounding check, regeneration, "unverified" marker, eval coverage |
| Scope creep into Phase 5 without data | Overclaiming | Gate decision in `OPEN_QUESTIONS.md`; wording discipline in Section 1.3 |
| Kiln model cannot be calibrated tightly to one plant | Weak predictive claim | Report fit and holdout separately; call it "calibrated to one published plant" |
| Streamlit performance on Monte Carlo | Poor UX | Vectorise, cache, run heavy jobs on a button with progress and seeded results |
| Python 3.14 package incompatibilities | Deploy failure | Pin versions, test on a clean Docker build, fall back to 3.13 |
| Examiner challenges "AI" claims | Credibility | Describe the agent as a grounded interface to a physics model; no claim that AI computes |
| Price assumptions dominate results | Misleading precision | Scenario bands, break-even analysis, explicit "assumed" labels |
| Public repo exposes the literature PDFs and the IITD webmail PDF | Copyright and privacy | Confirm repo visibility before deployment; Streamlit Cloud can deploy from a private repo |

---

## 15. Open decisions for the owner (record answers in `docs/project/OPEN_QUESTIONS.md`)

1. Is Phase 5 (1-D kiln physics) in scope, or is the product defined as a planning twin?
2. Is any real plant data obtainable (even one anonymised operating month)? If yes, the data hook and reconciliation become worthwhile.
3. Which LLM provider and budget for the agent, and is a public deployment with an API key acceptable, or should the chat run only locally?
4. Which carbon-price and CBAM scenarios should be treated as official cases?
5. Should hydrogen price scenarios follow a cited trajectory (for example Hall et al.) rather than a single INR 305/kg?
6. Report audience: thesis examiners only, or also an industry-facing version?
7. Can `project/tests/venv` (466 MB, untracked) be deleted?
8. Is the GitHub repository public or private? This decides whether the PDFs at the root can stay there.

---

## 16. Definition of done (product-level checklist)

Model and data
- [ ] All tests green; golden file current; CI green on a clean clone
- [ ] No parameter with an undisclosed source; `needs_citation` count published and justified
- [ ] WHR validation reflects sourced efficiencies; residual gap explained
- [ ] Biomass and hydrogen supply CAPEX included; scale effects included and cited (or flagged provisional)
- [ ] Syngas and process-optimisation cases implemented
- [ ] Domestic-coal behaviour investigated and documented, still failing visibly if that is the physics
- [ ] Financial model (NPV, IRR, LCOP) with scenario manager and price series

Analysis
- [ ] Tornado, Sobol/Morris, Monte Carlo, optimiser, MACC, carbon-price sweep, break-evens
- [ ] Every headline number has a P10-P90 range

Agent
- [ ] Tool layer, grounding check, read-only data guarantee, calculation trace
- [ ] Eval set with 100% grounding in the stubbed run and a documented live run
- [ ] Adversarial cases handled (parameter tampering, fake citations, domestic coal pass claims)

Product experience
- [ ] Executive Summary page with recommendation card
- [ ] Kiln schematic with live streams and KILN/STACK toggle
- [ ] Scenario compare, provenance panel, confidence-and-limits panel
- [ ] Exports: one-pager PDF, technical report PDF, Excel workbook, assumption register
- [ ] Accessibility and responsive checks pass

Engineering
- [ ] API layer, Docker, pinned dependencies, lint/type gates, deployment on Streamlit Cloud
- [ ] Fresh-clone-to-running in under 10 minutes

Academic
- [ ] Documentation set complete, claims-and-evidence table, viva question bank (with failures included)

Optional (Phase 5)
- [ ] 1-D kiln model with documented fit and holdout error; metallisation predicted, error stated
- [ ] Surrogate with reported emulator error
- [ ] Plant data hook, only if real data exists

Already done (before this plan)
- [x] Steady-state mass and energy balance, calibrated to Dey et al. (2015), closing to 1.14% and 0.0004%
- [x] 90-parameter register with provenance; validation bands kept separate from inputs
- [x] WHR, biomass and hydrogen retrofit modules; carbon-balance CO2 with scopes; CRF economics
- [x] Pathway grid, least-cost search, Pareto front and H2 break-even (`analysis/scenarios.py`, commit `c662404`)
- [x] Seven-tab Streamlit dashboard with table twins; 73 tests

Phase 0, local, 10 Nov 2026 (not yet committed or pushed)
- [x] Golden baseline and golden test. 78 tests passed at the end of Phase 0
- [x] `src/version.py`, `CHANGELOG.md`, `docs/models/README.md`, `docs/project/PLAN_DEVIATIONS.md`, `docs/project/OPEN_QUESTIONS.md`
- [x] Stale counts in `CLAUDE.md` corrected
- [ ] GitHub Actions green. The workflow is in `.github/workflows/ci.yml` and runs only after this work is pushed

Phase 1, started 10 Nov 2026, model version 0.2.0 (local, not committed)
- [x] Grid factor set to the CEA 2023-24 average, 0.727 t CO2/MWh
- [x] WHR auxiliary fraction of 0.10 from the BEE 4 MW table, deducted before export. Gross generation not tuned
- [x] Oxygen, kiln control and producer gas are separate cases, with tests
- [x] Biomass and hydrogen capital-cost parameters exist and stay zero: no INR source
- [ ] `needs_citation` is 37 of 109. Prices, biomass properties and boiler efficiency are still absent from the papers
- [ ] Scale effects, syngas as a solved stream, and the domestic-coal investigation are not done

---

## 17. Glossary

- **DRI:** direct-reduced iron (sponge iron). **TPD:** tonnes per day.
- **KILN boundary:** rotary kiln only; volatiles leave unburnt (Dey's boundary).
- **STACK boundary:** kiln plus after-burner chamber (ABC); CO2 and WHR heat boundary.
- **WHR:** waste-heat recovery, here a steam power cycle off the kiln waste gas.
- **Reductant-carbon ratio:** carbon available for reduction divided by stoichiometric carbon needed to remove the oxygen; below 1.0 the burden cannot be reduced.
- **Solve vs specified mode:** whether coal rate is found by bisection to close the energy balance or set by the user.
- **MACC:** marginal abatement cost curve. **LCOP:** levelised cost of production. **CRF:** capital recovery factor.
- **Planning twin / process twin:** steady-state mass-energy-economics model versus axial kiln physics model.
