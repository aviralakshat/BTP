# Documentation

| Folder | What it explains | Start with |
|---|---|---|
| [`models/`](models/README.md) | Every model, in calculation order: baseline plant, coal solver, mass and energy balances, axial kiln, CO₂, economics, finance, the eight retrofits, pathways, uncertainty | [`models/README.md`](models/README.md) |
| [`parameters/`](parameters/README.md) | The parameter file, its status system, and a generated reference of all 145 parameters | [`parameters/parameter_reference.md`](parameters/parameter_reference.md) |
| [`data/`](data/README.md) | Source papers, text extracts, archived web pages, generated data files, presets | [`data/README.md`](data/README.md) |
| [`validation/`](validation/README.md) | How outputs are checked against published plant data, and how strong each pass is | [`validation/README.md`](validation/README.md) |
| [`software/`](software/README.md) | Architecture, source layout, how to run, the test suite, the analyst design | [`software/README.md`](software/README.md) |
| [`project/`](project/README.md) | Master plan, deviations, open questions, session logs, research trail | [`project/README.md`](project/README.md) |

## Reading paths

- **To understand the plant:** [models 01](models/01_baseline_plant.md) → [02](models/02_coal_and_coal_rate_solver.md) → [04](models/04_energy_balance.md) → [06](models/06_co2_emissions.md) → [07](models/07_plant_economics.md).
- **To judge a retrofit:** [retrofits](models/retrofits/README.md) → [project finance](models/08_project_finance.md) → [pathways](models/10_pathways_and_optimisation.md).
- **To check a number:** [parameter reference](parameters/parameter_reference.md) → [data provenance](parameters/data_provenance.md) → the extract in `data/text/`.
- **To trust the result:** [validation](validation/README.md) → [validation report](validation/validation_report.md) → [uncertainty](models/11_uncertainty.md).

Files marked "Generated" (`parameters/parameter_reference.md`, `parameters/data_provenance.md`) are rebuilt by `project/setup_data.py`. Edit `project/config/parameters.json`, not them.
