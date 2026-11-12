"""Downloads: an Excel workbook and a one-page HTML brief.

Both are built from results the model already computed. The HTML brief is
what a browser prints to PDF. No second set of numbers is typed in here.
"""
from __future__ import annotations

import html
import io
import zipfile
from xml.sax.saxutils import escape


def _sheet_xml(rows: list[list]) -> str:
    body = []
    for r_index, row in enumerate(rows, start=1):
        cells = []
        for c_index, value in enumerate(row, start=1):
            ref = f"{_col(c_index)}{r_index}"
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                text = escape("" if value is None else str(value))
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>')
        body.append(f'<row r="{r_index}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(body)}</sheetData></worksheet>'
    )


def _col(index: int) -> str:
    letters = ""
    while index:
        index, rem = divmod(index - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def workbook_bytes(sheets: dict[str, list[list]]) -> bytes:
    """A minimal xlsx. `sheets` maps a sheet name to rows of cells."""
    names = list(sheets)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as book:
        overrides = "".join(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
            f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(1, len(names) + 1))
        book.writestr("[Content_Types].xml",
                      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                      '<Default Extension="xml" ContentType="application/xml"/>'
                      '<Override PartName="/xl/workbook.xml" '
                      'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                      f'{overrides}</Types>')
        book.writestr("_rels/.rels",
                      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                      '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                      '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                      '</Relationships>')
        sheet_tags = "".join(
            f'<sheet name="{escape(name)[:31]}" sheetId="{i}" r:id="rId{i}"/>'
            for i, name in enumerate(names, start=1))
        book.writestr("xl/workbook.xml",
                      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                      '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                      f'<sheets>{sheet_tags}</sheets></workbook>')
        rels = "".join(
            f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>'
            for i in range(1, len(names) + 1))
        book.writestr("xl/_rels/workbook.xml.rels",
                      '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                      '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                      f'{rels}</Relationships>')
        for i, name in enumerate(names, start=1):
            book.writestr(f"xl/worksheets/sheet{i}.xml", _sheet_xml(sheets[name]))
    return buffer.getvalue()


def plant_workbook(scenario: dict, pathways: list[dict], checks: list[dict],
                   version: str, parameter_hash: str) -> bytes:
    cover = [
        ["Field", "Value"],
        ["Model version", version],
        ["Parameter hash", parameter_hash],
        ["Preset", scenario.get("preset", "")],
        ["Capacity TPD", scenario.get("capacity_tpd", "")],
        ["Coal t/t", scenario.get("coal_t_per_t", "")],
        ["CO2 t/t", scenario.get("co2_total_t_per_t", "")],
        ["Cost INR/t", scenario.get("cost_inr_per_t", "")],
        ["Mass closure %", scenario.get("mass_closure_percent", "")],
        ["Energy closure %", scenario.get("energy_closure_percent", "")],
    ]
    path_rows = [["Label", "Feasible", "CO2 cut", "Cost INR/t", "Payback yr"]]
    for row in pathways:
        path_rows.append([
            row.get("label"), row.get("feasible"), row.get("co2_reduction_frac"),
            row.get("cost_per_t_dri"), row.get("payback_yr"),
        ])
    check_rows = [["Key", "Verdict", "Model value"]]
    for row in checks:
        check_rows.append([row.get("key"), row.get("verdict"), row.get("model_value")])
    return workbook_bytes({"Baseline": cover, "Pathways": path_rows, "Validation": check_rows})


def html_brief(scenario: dict, recommendation: dict | None, version: str) -> str:
    route = "No route reaches the target." if recommendation is None else recommendation["label"]
    cost = "" if recommendation is None else f"{recommendation['cost_per_t']:,.0f}"
    cut = "" if recommendation is None else f"{100 * recommendation['co2_cut_frac']:.0f}%"
    body = f"""
    <h1>DRI kiln, one page</h1>
    <p>Model {html.escape(version)}. Preset {html.escape(str(scenario.get('preset', '')))}.
    Capacity {scenario.get('capacity_tpd')} TPD.</p>
    <p>This plant: coal {scenario.get('coal_t_per_t'):.3f} t/t,
    CO2 {scenario.get('co2_total_t_per_t'):.3f} t/t,
    cost INR {scenario.get('cost_inr_per_t'):,.0f}/t.</p>
    <p>Recommendation: {html.escape(route)}. Cost INR {html.escape(cost)}/t.
    CO2 cut {html.escape(cut)}.</p>
    <p>Metallisation is an input. The axial kiln view does not predict it.
    Domestic coal is not a measured analysis. Parameters that still need a
    citation are listed in the app.</p>
    """
    return ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>DRI brief</title>"
            "<style>body{font-family:sans-serif;max-width:40rem;margin:2rem;}"
            "h1{font-size:1.4rem}</style></head><body>"
            f"{body}</body></html>")
