"""The Power BI project is generated, so its internal consistency can be tested without opening Power BI."""

import base64
import itertools
import json
import re
import zipfile
import zlib

import pytest

from fininc import paths, powerbi
from fininc.powerbi import measures, model, report, tables

PBIX = paths.POWERBI / f"{model.PROJECT}.pbix"
LOCAL_ONLY = {".pbi", "diagramLayout.json", ".pbix"}      # files Power BI writes on a machine, or snapshots


@pytest.fixture(scope="module")
def model_tables(results):
    return tables.make_tables(results)


def normalised(text: str) -> str:
    """Replace each compressed data block by the rows it holds, so the comparison does not depend on how zlib packs bytes."""
    def unpack(match: re.Match) -> str:
        return 'Binary.FromText("' + zlib.decompress(base64.b64decode(match.group(1)), -15).decode() + '"'

    return re.sub(r'Binary\.FromText\("([A-Za-z0-9+/=]+)"', unpack, text)


# --------------------------------------------------------------------------- measures
def test_measure_names_are_unique_and_safe_to_quote():
    names = [m.name for m in measures.MEASURES]
    assert len(names) == len(set(names))
    assert not any(ch in n for n in names for ch in "'[]")


def test_measure_formats_and_folders_are_filled_in():
    for m in measures.MEASURES:
        assert m.folder and m.fmt, m.name
        assert measures.measure_lines(m), m.name


def test_every_column_a_measure_reads_exists(model_tables):
    pattern = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\[([A-Za-z0-9_]+)\]")
    for m in measures.MEASURES:
        for table, column in pattern.findall(m.dax):
            assert table in model_tables, (m.name, table)
            assert column in model_tables[table].columns, (m.name, f"{table}[{column}]")


def test_every_measure_a_measure_calls_exists():
    names = {m.name for m in measures.MEASURES}
    for m in measures.MEASURES:
        for called in re.findall(r"(?<![A-Za-z0-9_])\[([^\]]+)\]", m.dax):
            assert called in names, (m.name, called)


def test_no_measure_filters_a_column_by_a_measure():
    """A column compared with a measure inside CALCULATE made measures invalid in Power BI; the year is held in a VAR."""
    names = {m.name for m in measures.MEASURES}
    for m in measures.MEASURES:
        for called in re.findall(r"\w+\[\w+\]\s*=\s*\[([^\]]+)\]", m.dax):
            assert called not in names, (m.name, called)


def test_descriptions_belong_to_real_measures():
    assert set(measures.DESCRIPTIONS) <= {m.name for m in measures.MEASURES}


def test_measures_dax_lists_every_measure():
    text = measures.measures_text()
    for m in measures.MEASURES:
        assert f"\n{m.name} =" in text, m.name


# --------------------------------------------------------------------------- model
def test_relationships_join_existing_columns_and_a_unique_key(model_tables):
    for name, many, one in model.RELATIONSHIPS:
        (t1, c1), (t2, c2) = many.split("."), one.split(".")
        assert c1 in model_tables[t1].columns and c2 in model_tables[t2].columns, name
        assert model_tables[t2][c2].is_unique, name
        assert set(model_tables[t1][c1]) <= set(model_tables[t2][c2]), name       # no district without a parent


def test_sort_by_columns_exist(model_tables):
    for (table, column), by in model.SORT_BY.items():
        assert column in model_tables[table].columns and by in model_tables[table].columns


def test_table_names_are_not_dax_reserved_words(model_tables):
    assert "clusters" not in model_tables         # needs quoting in DAX queries
    assert all(re.fullmatch(r"[a-z_]+", name) for name in model_tables)


def test_inline_table_data_round_trips(model_tables):
    for name, df in model_tables.items():
        rounded = df.round(4)
        rows = json.loads(zlib.decompress(base64.b64decode(model.inline_payload(rounded)), -15))
        assert len(rows) == len(rounded) and all(len(row) == len(rounded.columns) for row in rows), name


def test_every_column_has_a_power_query_type(model_tables):
    for df in model_tables.values():
        for column in df.columns:
            assert model.kind(df[column]) in model.TYPES


def test_tables_have_the_row_counts_the_report_relies_on(model_tables):
    assert len(model_tables["districts"]) == 120 and len(model_tables["provinces"]) == 5
    assert len(model_tables["district_types"]) == 4 and len(model_tables["top_gaps"]) == 10
    assert len(model_tables["headline"]) == 1
    assert model_tables["barriers"]["reason"].is_unique is False       # 'No money' appears for both account types
    assert model_tables["barriers"].groupby("account_type")["reason"].apply(lambda s: s.is_unique).all()


# --------------------------------------------------------------------------- report
def test_every_field_a_visual_uses_exists(model_tables):
    names = {m.name for m in measures.MEASURES}
    for page_id, _, builder in report.PAGES:
        for visual in builder():
            for fields in visual["roles"].values():
                for entity, prop in fields:
                    if entity == "_Measures":
                        assert prop in names, (page_id, prop)
                    else:
                        assert prop in model_tables[entity].columns, (page_id, entity, prop)


def test_visuals_stay_on_the_page_and_do_not_overlap():
    for page_id, _, builder in report.PAGES:
        boxes = [(v["x"], v["y"], v["x"] + v["w"], v["y"] + v["h"]) for v in builder()]
        for x0, y0, x1, y1 in boxes:
            assert 0 <= x0 < x1 <= report.PAGE_W and 0 <= y0 < y1 <= report.PAGE_H, page_id
        for a, b in itertools.combinations(boxes, 2):
            overlap = min(a[2], b[2]) - max(a[0], b[0]) > 0 and min(a[3], b[3]) - max(a[1], b[1]) > 0
            assert not overlap, (page_id, a, b)


def test_every_page_has_a_note_and_a_title():
    for page_id, display, builder in report.PAGES:
        assert report.PAGE_NOTES[page_id] and display and builder()


def test_card_titles_are_short_enough_to_show(model_tables):
    for page_id, _, builder in report.PAGES:
        cards = [v for v in builder() if v["type"] == "card"]
        limit = 33 if len(cards) <= 5 else 28
        for v in cards:
            assert len(v["title"]) <= limit, (page_id, v["title"])


# --------------------------------------------------------------------------- the files on disk
def test_committed_project_is_what_the_generator_writes(tmp_path):
    powerbi.build(folder=tmp_path)
    generated = {p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file()}
    committed = {p.relative_to(paths.POWERBI) for p in paths.POWERBI.rglob("*")
                 if p.is_file() and not LOCAL_ONLY & set(p.relative_to(paths.POWERBI).parts) and p.suffix != ".pbix"}
    assert generated == committed
    for relative in sorted(generated):
        fresh = normalised((tmp_path / relative).read_text(encoding="utf-8"))
        assert fresh == normalised((paths.POWERBI / relative).read_text(encoding="utf-8")), relative


def test_no_lineage_tags_so_power_bi_loads_the_project_as_new():
    assert not model.LINEAGE_TAGS
    assert "lineageTag" not in (paths.POWERBI / f"{model.PROJECT}.SemanticModel" / "definition" / "model.tmdl").read_text()


def test_pbix_snapshot_is_a_real_package_and_matches_the_report():
    """The .pbix is saved from Power BI Desktop by hand; this fails if the report was regenerated and the snapshot not."""
    assert zipfile.is_zipfile(PBIX)
    z = zipfile.ZipFile(PBIX)
    names = set(z.namelist())
    assert {"Version", "DataModel", "Report/definition/report.json", "Report/definition/pages/pages.json"} <= names
    assert z.getinfo("DataModel").file_size > 50_000
    pages = json.loads(z.read("Report/definition/pages/pages.json"))
    assert pages["pageOrder"] == [p[0] for p in report.PAGES]

    for page_id, _, builder in report.PAGES:
        for index, visual in enumerate(builder()):
            path = f"Report/definition/pages/{page_id}/visuals/{page_id}_{index:02d}/visual.json"
            assert path in names, path
            saved = json.loads(z.read(path))
            wanted = report.visual_json(page_id, index, visual)
            assert saved["visual"]["visualType"] == wanted["visual"]["visualType"], path
            assert saved["visual"]["query"] == wanted["visual"]["query"], path
            assert saved["position"] == wanted["position"], path
            title = saved["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]
            assert title == wanted["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"], path


def test_theme_is_registered_and_present():
    folder = paths.POWERBI / f"{model.PROJECT}.Report"
    theme = json.loads((folder / "StaticResources" / "RegisteredResources" / report.THEME_FILE).read_text(encoding="utf-8"))
    assert theme["dataColors"] == powerbi.THEME["dataColors"]
    definition = json.loads((folder / "definition" / "report.json").read_text(encoding="utf-8"))
    assert definition["themeCollection"]["customTheme"]["name"] == report.THEME_FILE
