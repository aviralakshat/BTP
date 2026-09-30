"""Regenerate the derived data files and the provenance exports.

Run from the project directory:

    ./venv/bin/python setup_data.py

What it writes:
  data/literature_inventory.csv   one row per source document actually present
  data/parameter_provenance.csv   all 89 model parameters with their sources
  data/literature_gaps.csv        just the parameters still needing a citation
  outputs/validation_report.txt   model outputs against their literature bands

What it deliberately does not touch: ../data/literature_parameters.csv, which is
a hand extraction. It is checked for stale absolute paths and reported on, but
never rewritten.
"""
from __future__ import annotations

import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data.parameters import Parameters, load_validation_targets
from src.validation.literature_check import format_report, run_checks

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SOURCE_DIR = REPO                      # the PDFs live in the repository root
TEXT_DIR = os.path.join(REPO, "data", "text")
DATA_DIR = os.path.join(HERE, "data")
OUT_DIR = os.path.join(HERE, "outputs")

#: Documents whose numbers the model actually consumes, and what for.
ROLE = {
    "Energy survey of the coal based sponge iron industry": (
        "CALIBRATION PLANT: full measured material and heat balance "
        "(Tables 4-11) for a 453.6 TPD kiln. Source of the ore, coal, char, "
        "dust, DRI and dolomite analyses and of the loss fractions."),
    "Decarbonising Coal-based DRI Production": (
        "VALIDATION BANDS: surveyed ore 1.4-1.6 (pellet) / 1.8-2.0 (lump), "
        "coal 0.9-1.1 (imported) / 1.4-1.6 (domestic) t/t-DRI, "
        "auxiliary power 55-65 kWh/t-DRI."),
    "Comparative life cycle assessment of natural gas and coal-based DRI": (
        "VALIDATION BANDS: rotary kiln CO2 1391-1880 kgCO2e/t-DRI, "
        "WHR generation 450-451 and export 351 kWh/t-DRI."),
    "ENERGY-EFFICIENT TECHNOLOGY OPTIONS FOR DIRECT REDUCTION": (
        "VALIDATION BAND: SEC 5.54 Gcal/t-iron at 89% Fe, coal-to-iron 0.95, "
        "coal 5200 kcal/kg."),
    "ENERGY CONSERVATION GUIDELINES FOR MSME SECTOR": (
        "VALIDATION BAND: sector SEC 0.64-0.82 toe/t. Note its 4500 kcal/kg is "
        "a GROSS calorific value and must not be used as a net heating value."),
    "Hydrogen Rotary Kilns for Ironmaking in India": (
        "PARAMETER: hydrogen price, $3.5/kg for competitiveness in India."),
    "Techno-economic assessment of hydrogen-based direct reduction": (
        "VALIDATION BAND: 53.5-59.6 kg H2/t-DRI for complete H2 direct "
        "reduction (55.7 modelled, 59.6 conservative design value)."),
    "Decarbonizing rotary kiln induction furnace based sponge iron": (
        "PARAMETER: metallisation 88-91%, reduction zone 1000-1050 degC."),
    "Pathways for decarbonizing the sponge iron industries": (
        "CROSS-CHECK: 1471 kg ore and 27 kg dolomite per t sponge iron; "
        "biochar gasification reactivity relative to coal char."),
    "Recovery and utilisation of waste heat for sponge iron process": (
        "Not yet mined for parameters. Review for WHR boiler and cycle "
        "efficiencies, which are the model's largest uncited assumptions."),
    "Low-carbon production of iron and steel": (
        "CONTEXT ONLY: global decarbonisation routes; biomass $295-525/t is "
        "not applicable to Indian agri-residue pricing."),
    "DRI UPDATE Indias major sources of Renewal Energy": (
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
            w.writerow([f, os.path.join("..", f), stem in texts,
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
    report = write_validation_report(params)

    print(f"literature_inventory.csv    {n_docs} source documents")
    print(f"parameter_provenance.csv    {n_params} parameters "
          f"({n_params - n_gaps} traced to a source)")
    print(f"literature_gaps.csv         {n_gaps} still need a citation")
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
