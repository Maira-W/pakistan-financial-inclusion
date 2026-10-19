"""Generate the Power BI project (.pbip) for the Pakistan financial inclusion dashboard.

Writes, under powerbi/:
  Pakistan_Financial_Inclusion.pbip                       project file (open this in Power BI Desktop)
  Pakistan_Financial_Inclusion.SemanticModel/             data model: tables, relationships, measures (TMDL)
  Pakistan_Financial_Inclusion.Report/report.json         report: three pages with visuals (single-file format)

The data model reads the CSV tables in powerbi/data/ (written by scripts/build_powerbi_model.py).
Measures come from powerbi/measures.dax, so the DAX is kept in one place.

Run from the project root:
  python scripts/build_pbip.py

Power BI Desktop must be able to open the project folder. The CSV folder is written as an absolute
path into the model (expression DataFolder). If the repo moves, update it under
Transform data > Data source settings, or rerun this script.
"""

import json
import re
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"
DATA = PBI / "data"
MEASURES_FILE = PBI / "measures.dax"

PROJECT = "Pakistan_Financial_Inclusion"
MODEL_DIR = PBI / f"{PROJECT}.SemanticModel"
REPORT_DIR = PBI / f"{PROJECT}.Report"

# How each measure is displayed in Power BI. Values are shown as stored in the CSVs (percent points or fractions).
FORMATS = {
    "Pakistan Account Ownership %": '0.0"%"',
    "Pakistan Men %": '0.0"%"',
    "Pakistan Women %": '0.0"%"',
    "India Account Ownership %": '0.0"%"',
    "Peer Account Ownership %": '0.0"%"',
    "Gender Gap (pts)": '0.0" pts"',
    "Total Branches": "#,0",
    "Matched Population": "#,0",
    "Branches per 100k": "0.00",
    "National Branches per 100k": "0.00",
    "Density vs National (x)": '0.00"x"',
    "Districts Matched": "0",
    "Districts Below Half National Avg": "0",
    "Population Share in Low-Density Districts %": "0.0%",
    "Districts Created After 2020": "0",
    "Latest Year": "0",
    "Selected Year": "0",
}

# Power Query type for each pandas dtype, and the matching TMDL data type.
M_TYPES = {"int64": ("Int64.Type", "int64"), "float64": ("type number", "double"),
           "bool": ("type logical", "boolean"), "object": ("type text", "string")}


# ---------- Measures ----------

def read_measures() -> list[tuple[str, list[str]]]:
    """Split powerbi/measures.dax into (name, expression lines). Comments are dropped."""
    lines = [ln.rstrip() for ln in MEASURES_FILE.read_text(encoding="utf-8").splitlines()
             if not ln.strip().startswith("//")]
    measures, name, body = [], None, []
    prev_blank = True
    for ln in lines:
        if ln.strip() == "":
            if name:
                measures.append((name, body))
                name, body = None, []
            prev_blank = True
            continue
        match = re.match(r"^([A-Za-z][^=]*?)\s*=\s*(.*)$", ln)
        if prev_blank and match and name is None:
            name = match.group(1).strip()
            body = [match.group(2)] if match.group(2) else []
        elif name is not None:
            body.append(ln)
        prev_blank = False
    if name:
        measures.append((name, body))
    return measures


def tmdl_measure(name: str, body: list[str]) -> str:
    """One measure in TMDL. Continuation lines sit three tabs in; properties sit two tabs in."""
    quoted = f"'{name}'"
    out = []
    if len(body) == 1:
        out.append(f"\tmeasure {quoted} = {body[0].strip()}")
    else:
        out.append(f"\tmeasure {quoted} =")
        out += ["\t\t\t" + ln.strip() for ln in body]
    if name in FORMATS:
        out.append(f"\t\tformatString: {FORMATS[name]}")
    return "\n".join(out)


# ---------- Tables ----------

def column_definitions(df: pd.DataFrame) -> dict[str, str]:
    types = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        if dtype.startswith("int"):
            key = "int64"
        elif dtype.startswith("float"):
            key = "float64"
        elif dtype == "bool":
            key = "bool"
        else:
            key = "object"
        types[col] = key
    return types


def tmdl_table(table: str, df: pd.DataFrame) -> str:
    types = column_definitions(df)
    lines = [f"table {table}"]
    for col, key in types.items():
        _, tmdl_type = M_TYPES[key]
        lines += [
            "",
            f"\tcolumn {col}",
            f"\t\tdataType: {tmdl_type}",
            f"\t\tsourceColumn: {col}",
            "\t\tsummarizeBy: none",
        ]
    typed_cols = [f'{{"{c}", {M_TYPES[k][0]}}}' for c, k in types.items()]
    lines += [
        "",
        f"\tpartition {table} = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\tlet",
        f'\t\t\t\tSource = Csv.Document(File.Contents(DataFolder & "\\{table}.csv"), '
        '[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "\t\t\t\tPromoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
        f"\t\t\t\tTyped = Table.TransformColumnTypes(Promoted, {{{', '.join(typed_cols)}}})",
        "\t\t\tin",
        "\t\t\t\tTyped",
    ]
    return "\n".join(lines) + "\n"


def tmdl_measures_table(measures: list) -> str:
    lines = [
        "table _Measures",
        "",
        "\tcolumn Placeholder",
        "\t\tdataType: string",
        "\t\tsourceColumn: Placeholder",
        "\t\tsummarizeBy: none",
        "\t\tisHidden",
    ]
    for name, body in measures:
        lines += ["", tmdl_measure(name, body)]
    lines += [
        "",
        "\tpartition _Measures = m",
        "\t\tmode: import",
        "\t\tsource =",
        "\t\t\tlet",
        '\t\t\t\tSource = #table(type table [Placeholder = text], {{"measures"}})',
        "\t\t\tin",
        "\t\t\t\tSource",
    ]
    return "\n".join(lines) + "\n"


def write_model(measures: list) -> None:
    tdir = MODEL_DIR / "definition" / "tables"
    tdir.mkdir(parents=True, exist_ok=True)
    (MODEL_DIR / "definition.pbism").write_text(json.dumps({"version": "4.2", "settings": {}}, indent=2),
                                                encoding="utf-8")
    (MODEL_DIR / "definition" / "database.tmdl").write_text(
        "database\n\tcompatibilityLevel: 1567\n", encoding="utf-8")
    (MODEL_DIR / "definition" / "model.tmdl").write_text(
        "model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
        "\tsourceQueryCulture: en-US\n\tdiscourageImplicitMeasures\n\n"
        "ref table districts\nref table provinces\nref table findex\nref table _Measures\n",
        encoding="utf-8")
    (MODEL_DIR / "definition" / "expressions.tmdl").write_text(
        f'expression DataFolder = "{DATA}"\n', encoding="utf-8")
    (MODEL_DIR / "definition" / "relationships.tmdl").write_text(
        "relationship districts_to_provinces\n"
        "\tfromColumn: districts.province_key\n"
        "\ttoColumn: provinces.province_key\n",
        encoding="utf-8")

    districts = pd.read_csv(DATA / "districts.csv")
    provinces = pd.read_csv(DATA / "provinces.csv")
    findex = pd.read_csv(DATA / "findex.csv")
    (tdir / "districts.tmdl").write_text(tmdl_table("districts", districts), encoding="utf-8")
    (tdir / "provinces.tmdl").write_text(tmdl_table("provinces", provinces), encoding="utf-8")
    (tdir / "findex.tmdl").write_text(tmdl_table("findex", findex), encoding="utf-8")
    (tdir / "_Measures.tmdl").write_text(tmdl_measures_table(measures), encoding="utf-8")


# ---------- Report (single-file report.json) ----------

# Each visual is a plain spec: the title, the Power BI visual type, the fields for each role, and its position.
# A field is (entity, property). Measures live in the _Measures table; everything else is a column.
def card(title: str, measure: str, x: int, y: int) -> dict:
    return {"title": title, "type": "card", "roles": {"Values": [("_Measures", measure)]},
            "x": x, "y": y, "w": 228, "h": 110}


def spec(title: str, vtype: str, roles: dict, x: int, y: int, w: int, h: int) -> dict:
    return {"title": title, "type": vtype, "roles": roles, "x": x, "y": y, "w": w, "h": h}


def cards_row(names: list[str], y: int = 20) -> list[dict]:
    return [card(name, name, 20 + i * 243, y) for i, name in enumerate(names)]


ALIASES = {"districts": "d", "provinces": "p", "findex": "f", "_Measures": "m"}


def visual_container(index: int, v: dict) -> dict:
    """One visual in the legacy layout format. The config is stored as a JSON string, as Power BI expects."""
    projections: dict[str, list] = {}
    selects, from_aliases = [], {}
    for role, fields in v["roles"].items():
        projections[role] = []
        for entity, prop in fields:
            alias = ALIASES[entity]
            from_aliases[entity] = alias
            kind = "Measure" if entity == "_Measures" else "Column"
            ref = f"{entity}.{prop}"
            projections[role].append({"queryRef": ref, "active": True})
            select = {kind: {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}, "Name": ref}
            if select not in selects:
                selects.append(select)
    from_list = [{"Name": alias, "Entity": entity, "Type": 0} for entity, alias in from_aliases.items()]
    config = {
        "name": f"visual{index:02d}",
        "layouts": [{"id": 0, "position": {"x": v["x"], "y": v["y"], "z": index,
                                           "width": v["w"], "height": v["h"], "tabOrder": index}}],
        "singleVisual": {
            "visualType": v["type"],
            "projections": projections,
            "prototypeQuery": {"Version": 2, "From": from_list, "Select": selects},
            "drillFilterOtherVisuals": True,
            "objects": {"title": [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": f"'{v['title']}'"}}},
            }}]},
        },
    }
    return {"config": json.dumps(config), "filters": "[]",
            "height": float(v["h"]), "width": float(v["w"]),
            "x": float(v["x"]), "y": float(v["y"]), "z": float(index)}


def build_sections() -> list[dict]:
    year_slicer = spec("Year", "slicer", {"Values": [("findex", "year")]}, 1000, 130, 260, 90)
    overview = cards_row(["Pakistan Account Ownership %", "Gender Gap (pts)", "National Branches per 100k",
                          "Districts Below Half National Avg", "Population Share in Low-Density Districts %"]) + [
        spec("Account ownership by country", "lineChart",
             {"Category": [("findex", "year")], "Series": [("findex", "country")],
              "Y": [("_Measures", "Peer Account Ownership %")]}, 20, 240, 760, 440),
        spec("Branches per 100k by province", "clusteredBarChart",
             {"Category": [("provinces", "province")], "Y": [("_Measures", "Branches per 100k")]},
             800, 240, 460, 440),
        year_slicer,
    ]
    gender = cards_row(["Gender Gap (pts)", "Pakistan Men %", "Pakistan Women %"]) + [
        spec("Men vs women, Pakistan (%)", "lineChart",
             {"Category": [("findex", "year")],
              "Y": [("_Measures", "Pakistan Men %"), ("_Measures", "Pakistan Women %")]},
             20, 150, 1240, 520),
    ]
    districts = cards_row(["Districts Matched", "Districts Below Half National Avg",
                           "National Branches per 100k"]) + [
        spec("Province", "slicer", {"Values": [("districts", "province")]}, 20, 150, 220, 120),
        spec("Branches per 100k by district", "clusteredBarChart",
             {"Category": [("districts", "district")], "Y": [("_Measures", "Branches per 100k")]},
             260, 150, 500, 550),
        spec("All districts", "tableEx",
             {"Values": [("districts", "district"), ("districts", "province"),
                         ("districts", "population_2023"), ("districts", "branches_total"),
                         ("districts", "branches_per_100k")]}, 780, 150, 480, 550),
    ]
    pages = [("Overview", overview), ("Gender", gender), ("Districts", districts)]
    sections = []
    for i, (display, visuals) in enumerate(pages):
        sections.append({
            "config": json.dumps({}),
            "displayName": display,
            "displayOption": 1,
            "filters": "[]",
            "height": 720.0,
            "name": display.lower(),
            "ordinal": i,
            "visualContainers": [visual_container(j, v) for j, v in enumerate(visuals)],
            "width": 1280.0,
        })
    return sections


def write_report() -> None:
    # The PBIR folder layout is not read by this version of Power BI Desktop, so remove it and write
    # the single report.json that the app does read.
    shutil.rmtree(REPORT_DIR / "definition", ignore_errors=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "definition.pbir").write_text(json.dumps({
        "version": "1.0",
        "datasetReference": {"byPath": {"path": f"../{PROJECT}.SemanticModel"}},
    }, indent=2), encoding="utf-8")
    report = {
        "config": json.dumps({
            "version": "5.56",
            "themeCollection": {},
            "activeSectionIndex": 0,
            "defaultDrillFilterOtherVisuals": True,
            "settings": {"useNewFilterPaneExperience": True, "allowChangeFilterTypes": True,
                         "useStylableVisualContainerHeader": True, "exportDataMode": 1},
        }),
        "layoutOptimization": 0,
        "resourcePackages": [],
        "sections": build_sections(),
    }
    (REPORT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_project_file() -> None:
    (PBI / f"{PROJECT}.pbip").write_text(json.dumps({
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{PROJECT}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }, indent=2), encoding="utf-8")


def main() -> None:
    measures = read_measures()
    write_model(measures)
    write_report()
    write_project_file()
    print(f"Measures: {len(measures)} | tables: districts, provinces, findex, _Measures")
    print(f"Project written to {PBI / (PROJECT + '.pbip')}")


if __name__ == "__main__":
    main()
