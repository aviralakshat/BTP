# Coal-Based DRI Kiln: Digital Twin and Decarbonisation Planner

A first-principles model of a coal-based rotary-kiln sponge-iron (direct reduced iron, DRI) plant, the workhorse of India's secondary steel sector. It solves the plant's mass and heat balances, then costs and compares eight retrofits: waste heat recovery, biomass, hydrogen, oxygen enrichment, advanced kiln control, producer gas, char recycling and variable-speed drives.

B.Tech project, Department of Materials Science and Engineering, IIT Delhi. Aviral Akshat, 2023MS11098.

## Reference plant

100 t/day rated, 90% utilisation, imported coal. Model 0.7.1.

| Result | Value | Published range |
|---|---:|---|
| Coal | 1.025 t per t DRI | 0.9 to 1.6 |
| Iron ore | 1.589 t per t DRI | 1.4 to 1.6 (Dey measured 1.587) |
| Specific energy | 5.586 Gcal per t DRI | 4.9 to 8.2 |
| Direct CO₂ | 2.083 t per t DRI | 1.39 to 3.2 |
| Cost at the plant gate | ₹7,234 per t DRI | |
| Mass balance closure | 1.20%, every conserved element exact | |
| Heat balance closure | under 0.01% | |

All 10 scored checks against published plant data pass, and 190 tests pass.

## How it works

- **Calibrated on a real kiln.** Every stream analysis comes from Dey et al. (2015): a 453.6 t/day kiln with a complete measured material and heat balance.
- **Solved, not assumed.** Ore, air, waste gas and coal rate are derived from the balances. The coal rate is the value that closes the kiln heat balance.
- **No magic numbers.** All 145 parameters live in one file, each with a source, a range and a status.
- **Validation is independent.** Published ranges are checked against outputs and never read by the model.
- **Residuals are reported.** No balance is forced shut.

## Quick start

```bash
cd project
./run_web.sh                                   # web console on http://localhost:3000
./venv/bin/streamlit run app.py                # analyst dashboard on http://localhost:8501
./venv/bin/python -m pytest tests/ -q          # test suite
```

First-time setup, every other command, and hosting on Render and Vercel are in [`docs/software/`](docs/software/README.md).

## Repository layout

```
BTP/
├── project/          the software: model, API, web console, Streamlit dashboard, tests
│   ├── src/          the model (physics, economics, retrofits, analysis)
│   ├── config/       parameters, validation ranges, analysis settings
│   ├── api/          model API for the web console
│   ├── web/          Next.js web console
│   ├── app.py        Streamlit dashboard
│   └── tests/        190 tests, including a frozen golden baseline
├── docs/             documentation
│   ├── models/       one document per model, in calculation order
│   ├── parameters/   the parameter system and a full parameter reference
│   ├── data/         sources, extracts, data files, presets
│   ├── validation/   checks against published data
│   ├── software/     architecture, running, testing
│   └── project/      plan, decisions, research trail
├── papers/           the 26 source papers, with an index
├── data/             text extracts of the papers and archived web sources
├── reports/          proposal, mid-semester report, presentation
├── CHANGELOG.md      what changed in each model version, and why
└── CLAUDE.md         working rules for AI-assisted development
```

Start reading at [`docs/README.md`](docs/README.md).
