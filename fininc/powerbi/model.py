"""The Power BI semantic model, written as TMDL files in the layout Power BI Desktop itself saves.

Each table is a Power Query partition. Two ways of supplying the rows are supported:

  inline   the rows are stored inside the model (compressed text, the way Power BI's "Enter data" stores them),
           so the project opens from any folder with nothing else alongside it;
  csv      the rows are read from powerbi/data/*.csv through the DataFolder expression, which holds an absolute path.

Lineage tags are derived from the object names, so regenerating the project gives identical files.
"""

from __future__ import annotations

import base64
import json
import re
import uuid
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

from .measures import DESCRIPTIONS, MEASURES, Measure, measure_lines

PROJECT = "Pakistan_Financial_Inclusion"
CULTURE = "en-US"
COMPATIBILITY_LEVEL = 1606
NAMESPACE = uuid.UUID("6f1c2f0e-5f43-4d3b-9a77-3c6d2d6a9b11")

# pandas dtype family -> (Power Query type, TMDL data type)
TYPES = {"int": ("Int64.Type", "int64"), "float": ("type number", "double"),
         "bool": ("type logical", "boolean"), "text": ("type text", "string")}

RELATIONSHIPS = [
    ("districts_to_provinces", "districts.province", "provinces.province"),
    ("districts_to_district_types", "districts.district_type", "district_types.district_type"),
]

# A text column that should sort by another column instead of alphabetically.
SORT_BY = {("districts", "district_type"): "type_rank", ("district_types", "district_type"): "type_rank"}

# Whole-number columns that tables show with thousands separators (Power BI shows a whole number plainly otherwise).
FORMATS = {("districts", "population"): "#,0", ("districts", "branches_2024"): "#,0", ("top_gaps", "branches_2024"): "#,0"}


LINEAGE_TAGS = False


def tag(*parts: str) -> str:
    """A stable lineage tag for an object, from its path in the model."""
    return str(uuid.uuid5(NAMESPACE, "/".join(parts)))


def tag_line(indent: int, *parts: str) -> list[str]:
    """The lineageTag property line for an object (none when lineage tags are switched off)."""
    return [f"{chr(9) * indent}lineageTag: {tag(*parts)}"] if LINEAGE_TAGS else []


def name_token(name: str) -> str:
    """TMDL object names are quoted only when they are not plain identifiers."""
    return name if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) else f"'{name}'"


def kind(series: pd.Series) -> str:
    dtype = str(series.dtype)
    if dtype.startswith("int"):
        return "int"
    if dtype.startswith("float"):
        return "float"
    if dtype == "bool":
        return "bool"
    return "text"


def _cell(value) -> str | None:
    """A value as text, the way Power BI's inline tables hold it (it converts back with the column type)."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (bool, np.bool_)):
        return "true" if bool(value) else "false"
    if isinstance(value, float):
        return format(value, ".10g")
    return str(value)


def inline_payload(df: pd.DataFrame) -> str:
    """Rows as JSON text, raw-deflated and base64 encoded: what Table.FromRows(Json.Document(Binary.Decompress(...))) reads."""
    rows = [[_cell(v) for v in row] for row in df.itertuples(index=False, name=None)]
    raw = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    packer = zlib.compressobj(level=9, wbits=-15)
    return base64.b64encode(packer.compress(raw) + packer.flush()).decode("ascii")


def partition_lines(table: str, df: pd.DataFrame, mode: str) -> list[str]:
    kinds = {c: kind(df[c]) for c in df.columns}
    typed = ", ".join(f'{{"{c}", {TYPES[k][0]}}}' for c, k in kinds.items())
    lines = [f"\tpartition {table} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet"]
    if mode == "inline":
        columns = ", ".join(f"{c} = _t" for c in df.columns)
        lines += [
            f'\t\t\t\t\tSource = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("{inline_payload(df)}", '
            f"BinaryEncoding.Base64), Compression.Deflate)), "
            f"let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [{columns}]),",
            f'\t\t\t\t\tTyped = Table.TransformColumnTypes(Source, {{{typed}}}, "{CULTURE}")',
        ]
    else:
        lines += [
            f'\t\t\t\t\tSource = Csv.Document(File.Contents(DataFolder & "\\{table}.csv"), '
            '[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            "\t\t\t\t\tPromoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
            f"\t\t\t\t\tTyped = Table.TransformColumnTypes(Promoted, {{{typed}}})",
        ]
    lines += ["\t\t\t\tin", "\t\t\t\t\tTyped"]
    return lines


def table_tmdl(table: str, df: pd.DataFrame, mode: str) -> str:
    lines = [f"table {table}", *tag_line(1, table)]
    for column in df.columns:
        lines += ["", f"\tcolumn {column}", f"\t\tdataType: {TYPES[kind(df[column])][1]}"]
        if (table, column) in FORMATS:
            lines.append(f"\t\tformatString: {FORMATS[(table, column)]}")
        lines += [*tag_line(2, table, column), "\t\tsummarizeBy: none", f"\t\tsourceColumn: {column}"]
        if (table, column) in SORT_BY:
            lines.append(f"\t\tsortByColumn: {SORT_BY[(table, column)]}")
    lines += [""] + partition_lines(table, df, mode)
    return "\n".join(lines) + "\n\n"


def measure_tmdl(m: Measure) -> str:
    """One measure. Continuation lines sit three tabs in and properties two tabs in."""
    body = measure_lines(m)
    out = []
    if m.name in DESCRIPTIONS:
        out.append(f"\t/// {DESCRIPTIONS[m.name]}")
    if len(body) == 1:
        out.append(f"\tmeasure {name_token(m.name)} = {body[0]}")
    else:
        out.append(f"\tmeasure {name_token(m.name)} =")
        out += ["\t\t\t" + ln for ln in body]
    if m.fmt:
        out.append(f"\t\tformatString: {m.fmt}")
    out += [f"\t\tdisplayFolder: {m.folder}", *tag_line(2, "_Measures", m.name)]
    return "\n".join(out)


def measures_tmdl() -> str:
    lines = ["table _Measures", *tag_line(1, "_Measures")]
    for m in MEASURES:
        lines += ["", measure_tmdl(m)]
    lines += ["", "\tcolumn Placeholder", "\t\tdataType: string", "\t\tisHidden",
              *tag_line(2, "_Measures", "Placeholder"), "\t\tsummarizeBy: none", "\t\tsourceColumn: Placeholder",
              "", "\tpartition _Measures = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
              '\t\t\t\t\tSource = #table(type table [Placeholder = text], {{"measures"}})', "\t\t\t\tin", "\t\t\t\t\tSource"]
    return "\n".join(lines) + "\n\n"


def platform(kind_name: str) -> str:
    return json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": kind_name, "displayName": PROJECT},
        "config": {"version": "2.0", "logicalId": tag("platform", kind_name)},
    }, indent=2)


def model_tmdl(table_names: list[str]) -> str:
    refs = "".join(f"ref table {name}\n" for name in [*table_names, "_Measures"])
    return (f"model Model\n\tculture: {CULTURE}\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n"
            f"\tdiscourageImplicitMeasures\n\tsourceQueryCulture: {CULTURE}\n\tdataAccessOptions\n"
            f"\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n{refs}\n")


def write_model(folder: Path, tables: dict[str, pd.DataFrame], data_folder: Path, mode: str) -> None:
    definition = folder / "definition"
    tdir = definition / "tables"
    tdir.mkdir(parents=True, exist_ok=True)
    for stale in tdir.glob("*.tmdl"):
        stale.unlink()
    (folder / "definition.pbism").write_text(json.dumps({"version": "4.2", "settings": {}}, indent=2), encoding="utf-8")
    (folder / ".platform").write_text(platform("SemanticModel"), encoding="utf-8")
    (definition / "database.tmdl").write_text(f"database\n\tcompatibilityLevel: {COMPATIBILITY_LEVEL}\n\n", encoding="utf-8")
    (definition / "model.tmdl").write_text(model_tmdl(list(tables)), encoding="utf-8")
    expressions = definition / "expressions.tmdl"
    if mode == "csv":
        expressions.write_text(f'expression DataFolder = "{data_folder}"\n', encoding="utf-8")
    elif expressions.exists():
        expressions.unlink()
    (definition / "relationships.tmdl").write_text(
        "\n".join(f"relationship {name}\n\tfromColumn: {a}\n\ttoColumn: {b}\n" for name, a, b in RELATIONSHIPS) + "\n",
        encoding="utf-8")
    for name, df in tables.items():
        (tdir / f"{name}.tmdl").write_text(table_tmdl(name, df, mode), encoding="utf-8")
    (tdir / "_Measures.tmdl").write_text(measures_tmdl(), encoding="utf-8")
