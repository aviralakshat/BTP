"""Regenerate the derived data files and the provenance exports.

Run from the project directory:

    ./venv/bin/python setup_data.py

What it writes:
  data/literature_inventory.csv   one row per source document actually present
  data/parameter_provenance.csv   every model parameter with its source
  data/literature_gaps.csv        just the parameters still needing a citation
  ../docs/parameters/data_provenance.md
                                  the same register, grouped by status, with the
                                  reason each open gap is still open
  ../docs/parameters/parameter_reference.md
                                  every parameter, grouped by plant area
  outputs/validation_report.txt   model outputs against their literature bands

What it deliberately does not touch: ../data/literature_parameters.csv, which is
a hand extraction. It is checked for stale absolute paths and reported on, but
never rewritten.
"""
from __future__ import annotations

import csv
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.parameters import Parameters, load_validation_targets
from src.validation.literature_check import format_report, run_checks
from src.version import stamp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SOURCE_DIR = os.path.join(REPO, "papers")
TEXT_DIR = os.path.join(REPO, "data", "text")
DATA_DIR = os.path.join(HERE, "data")
OUT_DIR = os.path.join(HERE, "outputs")

#: Documents whose numbers the model actually consumes, and what for.
ROLE = {
    "2015_Dey_Energy-survey": (
        "CALIBRATION PLANT: full measured material and heat balance "
        "(Tables 4-11) for a 453.6 TPD kiln. Source of the ore, coal, char, "
        "dust, DRI and dolomite analyses and of the loss fractions."),
    "2024_Nitturu_Decarbonising": (
        "VALIDATION BANDS: surveyed ore 1.4-1.6 (pellet) / 1.8-2.0 (lump), "
        "coal 0.9-1.1 (imported) / 1.4-1.6 (domestic) t/t-DRI, "
        "auxiliary power 55-65 kWh/t-DRI."),
    "2022_Nduagu_LCA": (
        "VALIDATION BANDS: rotary kiln CO2 1391-1880 kgCO2e/t-DRI, "
        "WHR generation 450-451 and export 351 kWh/t-DRI."),
    "2021_TERI_Energy-efficient": (
        "VALIDATION BAND: SEC 5.54 Gcal/t-iron at 89% Fe, coal-to-iron 0.95, "
        "coal 5200 kcal/kg."),
    "2019_BEE_MSME": (
        "VALIDATION BAND: sector SEC 0.64-0.82 toe/t. Note its 4500 kcal/kg is "
        "a GROSS calorific value and must not be used as a net heating value."),
    "2025_Hall_Hydrogen": (
        "PARAMETER: hydrogen price, $3.5/kg for competitiveness in India."),
    "2026_Kamal_Hydrogen": (
        "VALIDATION BAND: 53.5-59.6 kg H2/t-DRI for complete H2 direct "
        "reduction (55.7 modelled, 59.6 conservative design value)."),
    "2024_Bhardwaj_Decarbonizing-kiln": (
        "PARAMETER: metallisation 88-91%, reduction zone 1000-1050 degC; "
        "char recycling (Section 4.6) and variable frequency drives (Section "
        "4.2, Table 3) cases; export tariff upper bound."),
    "2024_Vigneswaran": (
        "CROSS-CHECK: 1471 kg ore and 27 kg dolomite per t sponge iron; "
        "biochar gasification reactivity relative to coal char."),
    "2024_Gaurav_WHR-preheating": (
        "Not yet mined for parameters. Review for WHR boiler and cycle "
        "efficiencies, which are the model's largest uncited assumptions."),
    "2021_Fan_Low-carbon": (
        "CONTEXT ONLY: global decarbonisation routes; biomass $295-525/t is "
        "not applicable to Indian agri-residue pricing."),
    "2024_DRI-Update": (
        "CONTEXT ONLY."),
}


def _role_for(name: str) -> str:
    for key, role in ROLE.items():
        if key.lower() in name.lower():
            return role
    return "Not yet classified."


def write_inventory() -> int:
    pdfs = sorted(f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(".pdf"))
    texts = set()
    if os.path.isdir(TEXT_DIR):
        texts = {os.path.splitext(f)[0] for f in os.listdir(TEXT_DIR)
                 if f.endswith(".txt")}

    path = os.path.join(DATA_DIR, "literature_inventory.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file_name", "relative_path", "text_extracted", "title",
                    "author", "year", "role_in_model"])
        for f in pdfs:
            stem = os.path.splitext(f)[0]
            title, _, author = stem.rpartition("_")
            m = re.search(r"\b(19|20)\d{2}\b", stem)
            w.writerow([f, os.path.join("..", "papers", f), stem in texts,
                        title or stem, author, m.group(0) if m else "",
                        _role_for(stem)])
    return len(pdfs)


def write_provenance(params: Parameters) -> tuple[int, int]:
    rows = params.provenance_rows()
    fields = ["parameter", "value", "unit", "min", "max", "status",
              "sensitivity_required", "source", "source_file", "notes"]
    with open(os.path.join(DATA_DIR, "parameter_provenance.csv"), "w",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    gaps = [r for r in rows if r["status"] == "needs_citation"]
    with open(os.path.join(DATA_DIR, "literature_gaps.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(gaps)
    return len(rows), len(gaps)


STATUS_ORDER = ("verified", "derived", "indicative", "scenario_choice",
                "physical_constant", "needs_citation")


def _cell(text) -> str:
    return str(text if text is not None else "").replace("|", "\\|").replace("\n", " ")


def _value(r: dict) -> str:
    v = r["value"]
    num = f"{v:,.6g}" if isinstance(v, (int, float)) else _cell(v)
    unit = "" if r["unit"] in (None, "-") else _cell(r["unit"])
    return f"{num} {unit}".strip()


def write_provenance_md(params: Parameters) -> str:
    """docs/parameters/data_provenance.md: the parameter register grouped by status."""
    with open(params.path) as fh:
        statuses = json.load(fh)["_meta"]["provenance_status_values"]
    rows = params.provenance_rows()
    summary = params.provenance_summary()
    v = stamp(params.path)
    lines = [
        "# Data Provenance",
        "",
        "Generated by `project/setup_data.py` from `project/config/parameters.json`. "
        "Do not edit by hand.",
        "",
        f"Model {v['model_version']}, parameters SHA-256 `{v['parameters_sha256'][:12]}`. "
        f"{summary['total']} parameters.",
        "",
        "Paper extracts are in `data/text/`; retrieved web pages, with URL and "
        "retrieval date, are in `data/web/`.",
        "",
        "| Status | Count | Meaning |",
        "|---|---:|---|",
    ]
    for s in STATUS_ORDER:
        lines.append(f"| {s} | {summary.get(s, 0)} | {_cell(statuses.get(s, ''))} |")
    for s in STATUS_ORDER:
        group = [r for r in rows if r["status"] == s]
        if not group:
            continue
        lines += ["", f"## {s.replace('_', ' ').title()} ({len(group)})", ""]
        if s == "needs_citation":
            lines += ["| Parameter | Value | Why it is still open |", "|---|---|---|"]
            lines += [f"| `{r['parameter']}` | {_value(r)} | {_cell(r['notes'] or r['source'])} |"
                      for r in group]
        else:
            lines += ["| Parameter | Value | Source | File |", "|---|---|---|---|"]
            lines += [f"| `{r['parameter']}` | {_value(r)} | {_cell(r['source'])} | "
                      f"{_cell(r['source_file'])} |" for r in group]
    path = os.path.join(REPO, "docs", "parameters", "data_provenance.md")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


#: Parameter-key prefix, heading and what the group describes, in reading order.
GROUPS = (
    ("plant", "Plant", "Size, utilisation and operating days of the case being run."),
    ("ore", "Iron ore", "Pellet-grade feed analysis and iron losses."),
    ("dri", "Sponge iron product", "Product composition and discharge temperature."),
    ("coal", "Coal (common)", "Coal-rate mode, feed/injection split and thermal properties."),
    ("coal_feed", "Feed coal", "Ultimate and proximate analysis of coal charged with the ore."),
    ("coal_inj", "Injection coal", "Ultimate and proximate analysis of coal blown in at the discharge end."),
    ("char", "Dolochar", "Char leaving with the solids."),
    ("dust", "Flue dust", "Dust carried out with the waste gas."),
    ("dolomite", "Dolomite", "Desulphurising flux rate and composition."),
    ("kiln", "Kiln", "Temperatures, air, shell loss and the calibration kiln geometry."),
    ("power", "Electricity", "Auxiliary load and grid emission factor."),
    ("whr", "Waste heat recovery", "Boiler, cycle and capital-cost basis."),
    ("biomass", "Biomass", "Rice husk properties, price, cap and handling capital."),
    ("hydrogen", "Hydrogen", "Heating value, price, emission factor and cap."),
    ("oxygen", "Oxygen enrichment", "Rajesh et al. (2016) plant trial and oxygen price."),
    ("kiln_control", "Advanced kiln control", "Coal saving and capital cost."),
    ("producer_gas", "Producer gas", "Energy saving and reference-plant figures."),
    ("char_recycle", "Char recycling", "Char recovery fraction and cost."),
    ("vfd", "Variable-speed drives", "Motor share, part-speed power and cost."),
    ("econ", "Economics and finance", "Prices, cost scaling, discount rate, tax and loan terms."),
)


def write_parameter_reference(params: Parameters) -> str:
    """docs/parameters/parameter_reference.md: every parameter, by plant area."""
    rows = {r["parameter"]: r for r in params.provenance_rows()}
    v = stamp(params.path)
    lines = [
        "# Parameter Reference",
        "",
        "Generated by `project/setup_data.py` from `project/config/parameters.json`. "
        "Do not edit by hand.",
        "",
        f"Model {v['model_version']}, parameters SHA-256 `{v['parameters_sha256'][:12]}`. "
        f"{len(rows)} parameters. Range is the plausible minimum to maximum used by the "
        "sensitivity analysis. A tick in the S column means the parameter is varied in the "
        "tornado, Morris and Monte Carlo runs.",
        "",
        "| Group | Parameters |",
        "|---|---:|",
    ]
    grouped = {prefix: [r for k, r in rows.items() if k.split(".")[0] == prefix]
               for prefix, _, _ in GROUPS}
    for prefix, title, _ in GROUPS:
        if grouped[prefix]:
            anchor = title.lower().replace(" ", "-").replace("(", "").replace(")", "")
            lines.append(f"| [{title}](#{anchor}) | {len(grouped[prefix])} |")
    for prefix, title, blurb in GROUPS:
        group = grouped[prefix]
        if not group:
            continue
        lines += ["", f"## {title}", "", blurb, "",
                  "| Parameter | Value | Range | Status | S | Source |",
                  "|---|---|---|---|:-:|---|"]
        for r in group:
            rng = ("" if r["min"] is None or r["max"] is None
                   else f"{r['min']:,.6g} to {r['max']:,.6g}"
                   if isinstance(r["min"], (int, float)) else f"{r['min']} to {r['max']}")
            lines.append(
                f"| `{r['parameter']}` | {_value(r)} | {_cell(rng)} | "
                f"{r['status'].replace('_', ' ')} | {'✓' if r.get('sensitivity_required') else ''} | "
                f"{_cell(r['source'])} |")
    unlisted = [k for k in rows if k.split(".")[0] not in grouped]
    if unlisted:
        lines += ["", "## Other", "", "| Parameter | Value |", "|---|---|"]
        lines += [f"| `{k}` | {_value(rows[k])} |" for k in unlisted]
    path = os.path.join(REPO, "docs", "parameters", "parameter_reference.md")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def write_validation_report(params: Parameters) -> str:
    result = run_checks(params)
    text = format_report(result)
    targets = load_validation_targets()
    lines = [text, "", "SOURCES FOR EACH BAND", "=" * 96]
    for t in targets:
        lines.append(f"\n{t['label']} [{t['unit']}]  {t['min']} - {t['max']}")
        lines.append(f"  {t['source']}")
        if t.get("note"):
            lines.append(f"  NOTE: {t['note']}")
    path = os.path.join(OUT_DIR, "validation_report.txt")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return path


def check_stale_paths() -> list[str]:
    """The project moved from ~/Documents/SEM7/BTP to its current location, so
    absolute paths recorded in the hand-maintained CSVs no longer resolve."""
    stale = []
    legacy_dir = os.path.join(REPO, "data")
    if not os.path.isdir(legacy_dir):
        return stale
    for name in os.listdir(legacy_dir):
        if not name.endswith(".csv"):
            continue
        p = os.path.join(legacy_dir, name)
        with open(p, newline="") as fh:
            for i, row in enumerate(csv.reader(fh), start=1):
                for cell in row:
                    if os.path.isabs(cell) and not os.path.exists(cell):
                        stale.append(f"{name}:{i}: {cell}")
    return stale


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)
    params = Parameters()

    n_docs = write_inventory()
    n_params, n_gaps = write_provenance(params)
    provenance_md = write_provenance_md(params)
    reference_md = write_parameter_reference(params)
    report = write_validation_report(params)

    print(f"literature_inventory.csv    {n_docs} source documents")
    print(f"parameter_provenance.csv    {n_params} parameters "
          f"({n_params - n_gaps} traced to a source)")
    print(f"literature_gaps.csv         {n_gaps} still need a citation")
    print(f"data_provenance.md          {provenance_md}")
    print(f"parameter_reference.md      {reference_md}")
    print(f"validation_report.txt       {report}")

    stale = check_stale_paths()
    if stale:
        print(f"\n{len(stale)} stale absolute path(s) in the hand-maintained CSVs "
              f"under {os.path.relpath(os.path.join(REPO, 'data'), HERE)} -- these "
              "point at the pre-move location and no longer resolve. Left "
              "untouched, since those files are manual extractions:")
        for s in stale[:8]:
            print(f"  {s}")
        if len(stale) > 8:
            print(f"  ... and {len(stale) - 8} more")


if __name__ == "__main__":
    main()
