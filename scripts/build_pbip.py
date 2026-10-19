"""Generate the Power BI project (.pbip) for the Pakistan financial inclusion dashboard.

Writes, under powerbi/:
  Pakistan_Financial_Inclusion.pbip                       project file (open this in Power BI Desktop)
  Pakistan_Financial_Inclusion.SemanticModel/             data model: tables, relationships, measures (TMDL)
  Pakistan_Financial_Inclusion.Report/                    report: three pages with visuals (PBIR JSON)

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
import uuid
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"
DATA = PBI / "data"
MEASURES_FILE = PBI / "measures.dax"

PROJECT = "Pakistan_Financial_Inclusion"
MODEL_DIR = PBI / f"{PROJECT}.SemanticModel"
REPORT_DIR = PBI / f"{PROJECT}.Report"

SCHEMA = "https://developer.microsoft.com/json-schema/fabric/item/report/definition"
VERSION_SCHEMA = f"{SCHEMA}/versionMetadata/1.0.0/schema.json"
REPORT_SCHEMA = f"{SCHEMA}/report/1.0.0/schema.json"
PAGES_SCHEMA = f"{SCHEMA}/pagesMetadata/1.0.0/schema.json"
PAGE_SCHEMA = f"{SCHEMA}/page/2.0.0/schema.json"
VISUAL_SCHEMA = f"{SCHEMA}/visualContainer/2.5.0/schema.json"

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


def tmdl_table(table: str, df: pd.DataFrame, extra_measures: list | None = None) -> str:
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
    if extra_measures:
        for name, body in extra_measures:
            lines += ["", tmdl_measure(name, body)]
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


# ---------- Report (PBIR) ----------

def col(entity: str, prop: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}


def meas(prop: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": prop}}


def projection(field: dict, entity: str, prop: str) -> dict:
    return {"field": field, "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}


def visual(title: str, vtype: str, roles: dict, x: int, y: int, w: int, h: int, z: int) -> dict:
    query_state = {}
    for role, items in roles.items():
        query_state[role] = {"projections": [projection(f, e, p) for f, e, p in items]}
    return {
        "$schema": VISUAL_SCHEMA,
        "name": uuid.uuid4().hex[:20],
        "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z},
        "visual": {
            "visualType": vtype,
            "query": {"queryState": query_state},
            "objects": {
                "title": [{"properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                }}]
            },
        },
    }


def card_row(y: int, measures_list: list[str]) -> list[dict]:
    """A row of cards, spread across the 1280-pixel canvas."""
    out, width, gap = [], 228, 15
    for i, name in enumerate(measures_list):
        x = 20 + i * (width + gap)
        out.append(visual(name, "card", {"Values": [(meas(name), "_Measures", name)]},
                          x, y, width, 110, i))
    return out


def write_page(page_dir: Path, name: str, display: str, visuals: list[dict]) -> None:
    page_dir.mkdir(parents=True, exist_ok=True)
    (page_dir / "page.json").write_text(json.dumps({
        "$schema": PAGE_SCHEMA, "name": name, "displayName": display,
        "displayOption": "FitToPage", "height": 720, "width": 1280,
    }, indent=2), encoding="utf-8")
    vdir = page_dir / "visuals"
    for v in visuals:
        (vdir / v["name"]).mkdir(parents=True, exist_ok=True)
        (vdir / v["name"] / "visual.json").write_text(json.dumps(v, indent=2), encoding="utf-8")


def write_report() -> None:
    definition = REPORT_DIR / "definition"
    pages_dir = definition / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "definition.pbir").write_text(json.dumps({
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{PROJECT}.SemanticModel"}},
    }, indent=2), encoding="utf-8")
    (definition / "version.json").write_text(json.dumps(
        {"$schema": VERSION_SCHEMA, "version": "2.0.0"}, indent=2), encoding="utf-8")
    (definition / "report.json").write_text(json.dumps(
        {"$schema": REPORT_SCHEMA, "layoutOptimization": "None"}, indent=2), encoding="utf-8")

    year_slicer = visual("Year", "slicer", {"Values": [(col("findex", "year"), "findex", "year")]},
                         1000, 130, 260, 90, 9)
    overview = (
        card_row(20, ["Pakistan Account Ownership %", "Gender Gap (pts)", "National Branches per 100k",
                      "Districts Below Half National Avg", "Population Share in Low-Density Districts %"])
        + [
            visual("Account ownership by country", "lineChart",
                   {"Category": [(col("findex", "year"), "findex", "year")],
                    "Series": [(col("findex", "country"), "findex", "country")],
                    "Y": [(meas("Peer Account Ownership %"), "_Measures", "Peer Account Ownership %")]},
                   20, 240, 760, 440, 5),
            visual("Branches per 100k by province", "clusteredBarChart",
                   {"Category": [(col("provinces", "province"), "provinces", "province")],
                    "Y": [(meas("Branches per 100k"), "_Measures", "Branches per 100k")]},
                   800, 240, 460, 440, 6),
            year_slicer,
        ]
    )
    gender = (
        card_row(20, ["Gender Gap (pts)", "Pakistan Men %", "Pakistan Women %"])[:3]
        + [
            visual("Men vs women, Pakistan (%)", "lineChart",
                   {"Category": [(col("findex", "year"), "findex", "year")],
                    "Y": [(meas("Pakistan Men %"), "_Measures", "Pakistan Men %"),
                          (meas("Pakistan Women %"), "_Measures", "Pakistan Women %")]},
                   20, 150, 1240, 520, 4),
        ]
    )
    districts = (
        card_row(20, ["Districts Matched", "Districts Below Half National Avg", "National Branches per 100k"])
        + [
            visual("Province", "slicer", {"Values": [(col("districts", "province"), "districts", "province")]},
                   20, 150, 220, 120, 3),
            visual("Branches per 100k by district", "clusteredBarChart",
                   {"Category": [(col("districts", "district"), "districts", "district")],
                    "Y": [(meas("Branches per 100k"), "_Measures", "Branches per 100k")]},
                   260, 150, 500, 550, 4),
            visual("All districts", "tableEx",
                   {"Values": [(col("districts", "district"), "districts", "district"),
                               (col("districts", "province"), "districts", "province"),
                               (col("districts", "population_2023"), "districts", "population_2023"),
                               (col("districts", "branches_total"), "districts", "branches_total"),
                               (col("districts", "branches_per_100k"), "districts", "branches_per_100k")]},
                   780, 150, 480, 550, 5),
        ]
    )

    pages = [("overview", "Overview", overview), ("gender", "Gender", gender), ("districts", "Districts", districts)]
    for name, display, visuals in pages:
        write_page(pages_dir / name, name, display, visuals)
    (pages_dir / "pages.json").write_text(json.dumps({
        "$schema": PAGES_SCHEMA,
        "pageOrder": [p[0] for p in pages],
        "activePageName": pages[0][0],
    }, indent=2), encoding="utf-8")


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
