"""The Power BI report, written in the project format Power BI Desktop itself saves (PBIR).

Each page is a folder with a page.json and one visual.json per visual. A visual is described by a small spec: a
title, a Power BI visual type, the fields for each role and a position on a 1280 x 720 page. A field is
(table, name); measures live in _Measures and everything else is a column.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .. import config
from .model import PROJECT, tag

PAGE_W, PAGE_H = 1280, 720
GAP = 16

SCHEMAS = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
VISUAL_SCHEMA = f"{SCHEMAS}/visualContainer/2.14.0/schema.json"
PAGE_SCHEMA = f"{SCHEMAS}/page/2.1.0/schema.json"
PAGES_SCHEMA = f"{SCHEMAS}/pagesMetadata/1.1.0/schema.json"
REPORT_SCHEMA = f"{SCHEMAS}/report/3.3.0/schema.json"
VERSION_SCHEMA = f"{SCHEMAS}/versionMetadata/1.0.0/schema.json"
THEME_FILE = "FinancialInclusion.json"

PAGE_BACKGROUND = "#F3F5F8"
PANEL = "#FFFFFF"
BORDER = "#D9DEE5"
MUTED = "#4A5568"

# Column headers shown in table visuals (the model keeps the machine-friendly column names).
HEADERS = {
    "district": "District", "province": "Province", "population": "People", "branches_2024": "Branches",
    "branches_per_100k": "Per 100k", "expected_branches": "Expected", "shortfall": "Shortfall", "gap_rank": "Rank",
    "chance_of_this_few": "Chance of so few", "flagged_short": "Flagged", "country_name": "Economy",
    "account": "Account %", "account_women": "Women %", "account_men": "Men %", "phone_women": "Phone, women %",
    "phone_men": "Phone, men %", "topic": "Topic", "note": "Note",
}

Field = tuple[str, str]


def col(table: str, name: str) -> Field:
    return (table, name)


def msr(name: str) -> Field:
    return ("_Measures", name)


# ---------------------------------------------------------------------------
# visual specs
# ---------------------------------------------------------------------------
def spec(title: str, vtype: str, roles: dict[str, list[Field]], x: int, y: int, w: int, h: int,
         labels: bool = False, sort: str | None = None, log: bool = False, widths: dict[Field, int] | None = None) -> dict:
    return {"title": title, "type": vtype, "roles": roles, "x": x, "y": y, "w": w, "h": h, "labels": labels,
            "sort": sort, "log": log, "widths": widths or {}}


def card(title: str, measure: str, x: int, y: int, w: int, h: int = 104) -> dict:
    return spec(title, "card", {"Values": [msr(measure)]}, x, y, w, h)


def cards_row(items: list[tuple[str, str]], y: int = GAP) -> list[dict]:
    n = len(items)
    w = (PAGE_W - 2 * GAP - (n - 1) * GAP) // n
    return [card(title, measure, GAP + i * (w + GAP), y, w) for i, (title, measure) in enumerate(items)]


def slicer(title: str, field: Field, x: int, y: int, w: int, h: int) -> dict:
    return spec(title, "slicer", {"Values": [field]}, x, y, w, h)


def line(title: str, category: Field, measures: list[str], x: int, y: int, w: int, h: int, series: Field | None = None) -> dict:
    roles = {"Category": [category], "Y": [msr(m) for m in measures]}
    if series:
        roles["Series"] = [series]
    return spec(title, "lineChart", roles, x, y, w, h)


def bars(title: str, category: Field, measures: list[str], x: int, y: int, w: int, h: int,
         series: Field | None = None, labels: bool = True, sort: str | None = None) -> dict:
    """Horizontal bars. sort="Descending" orders the bars by the first measure, largest at the top."""
    roles = {"Category": [category], "Y": [msr(m) for m in measures]}
    if series:
        roles["Series"] = [series]
    return spec(title, "clusteredBarChart", roles, x, y, w, h, labels=labels, sort=sort)


def scatter(title: str, category: Field, x_measure: str, y_measure: str, series: Field | None,
            x: int, y: int, w: int, h: int, log: bool = False) -> dict:
    roles = {"Category": [category], "X": [msr(x_measure)], "Y": [msr(y_measure)]}
    if series:
        roles["Series"] = [series]
    return spec(title, "scatterChart", roles, x, y, w, h, log=log)


def table(title: str, columns: list[Field], x: int, y: int, w: int, h: int, widths: dict[Field, int] | None = None) -> dict:
    return spec(title, "tableEx", {"Values": columns}, x, y, w, h, widths=widths)


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------
RAIL = 200                      # width of the slicer column on the left of a page
BODY_Y = 136                    # where charts start, below a row of cards
BODY_H = PAGE_H - BODY_Y - GAP  # 568


def page_overview() -> list[dict]:
    return cards_row([
        ("Adults with an account", "Pakistan Account Ownership %"),
        ("Gender gap in accounts", "Account Gender Gap (pts)"),
        ("Branches per 100,000 people", "National Branches per 100k"),
        ("Districts below half the average", "Districts Below Half National Avg"),
        ("Gini of bank branches, 2024", "Gini of Bank Branches 2024"),
    ]) + [
        line("Adults with an account, by country (%)", col("findex", "year"), ["Account Ownership %"],
             GAP, BODY_Y, 760, BODY_H, series=col("findex", "country_name")),
        bars("Branches per 100,000 people, by province", col("provinces", "province"), ["Branches per 100k"],
             792, BODY_Y, 472, BODY_H, sort="Descending"),
    ]


def page_who() -> list[dict]:
    right = GAP + 540 + GAP
    half = (PAGE_W - right - GAP - GAP) // 2
    return cards_row([
        ("Women with an account", "Pakistan Women %"),
        ("Men with an account", "Pakistan Men %"),
        ("Gender gap in accounts", "Account Gender Gap (pts)"),
        ("Gender gap in phone ownership", "Phone Gender Gap (pts)"),
    ]) + [
        bars("Adults with an account, by group (%): 2021 and 2024", col("segments", "segment"),
             ["Segment Account Ownership %"], GAP, BODY_Y, 540, BODY_H, series=col("segments", "year"), sort="Descending"),
        line("Women and men with an account (%)", col("findex", "year"), ["Pakistan Women %", "Pakistan Men %"],
             right, BODY_Y, PAGE_W - right - GAP, 250),
        bars("No bank account: why (% of those without)", col("barriers", "reason"), ["Bank Barrier Share %"],
             right, BODY_Y + 250 + GAP, half, BODY_H - 250 - GAP, sort="Descending"),
        bars("No mobile money: why (% of all adults)", col("barriers", "reason"), ["Mobile Money Barrier Share %"],
             right + half + GAP, BODY_Y + 250 + GAP, half, BODY_H - 250 - GAP, sort="Descending"),
    ]


def page_where() -> list[dict]:
    left, mid = GAP, GAP + RAIL + GAP
    right = mid + 516 + GAP
    return cards_row([
        ("Branches in the register", "Total Branches"),
        ("Branches per 100,000 people", "Branches per 100k"),
        ("Share of branches in rural areas", "Rural Branch Share %"),
        ("Share of people in rural areas", "Rural Population Share %"),
        ("Districts below half the average", "Districts Below Half National Avg"),
    ]) + [
        slicer("Province", col("provinces", "province"), left, BODY_Y, RAIL, 230),
        slicer("District type", col("district_types", "district_type"), left, BODY_Y + 230 + GAP, RAIL, 200),
        bars("Branches per 100,000 residents: rural against urban", col("provinces", "province"),
             ["Rural Branches per 100k Rural People", "Urban Branches per 100k Urban People"],
             mid, BODY_Y, 516, BODY_H),
        bars("Branches per 100,000 people, by district type", col("district_types", "district_type"),
             ["Branches per 100k"], right, BODY_Y, PAGE_W - right - GAP, 284),
        bars("Bank branches per 100,000 people: 2020 against 2024", col("provinces", "province"),
             ["Bank Branches per 100k 2020", "Bank Branches per 100k 2024"],
             right, BODY_Y + 284 + GAP, PAGE_W - right - GAP, BODY_H - 284 - GAP),
    ]


def page_explorer() -> list[dict]:
    left, mid = GAP, GAP + 250 + GAP
    right = mid + 380 + GAP
    return [
        slicer("Measure", col("metric_choice", "metric"), left, GAP, 250, 170),
        slicer("Province", col("provinces", "province"), left, GAP + 170 + GAP, 250, 190),
        slicer("District type", col("district_types", "district_type"), left, GAP + 170 + GAP + 190 + GAP, 250,
               PAGE_H - GAP - (GAP + 170 + GAP + 190 + GAP)),
        bars("Districts, by the measure selected on the left", col("districts", "district"), ["Selected District Metric"],
             mid, GAP, 380, PAGE_H - 2 * GAP, labels=False, sort="Descending"),
        table("District detail", [col("districts", "district"), col("districts", "province"), col("districts", "population"),
                                  col("districts", "branches_2024"), col("districts", "branches_per_100k"),
                                  col("districts", "shortfall")],
              right, GAP, PAGE_W - right - GAP, PAGE_H - 2 * GAP,
              widths={col("districts", "district"): 100, col("districts", "province"): 135, col("districts", "population"): 80,
                      col("districts", "branches_2024"): 72, col("districts", "branches_per_100k"): 68,
                      col("districts", "shortfall"): 76}),
    ]


def page_gaps() -> list[dict]:
    right = GAP + 600 + GAP
    return cards_row([
        ("Flagged below expected", "Districts Flagged Below Expected"),
        ("Shortfall (branches)", "Model Shortfall (branches)"),
        ("Error cut vs per capita", "Model Error Reduction %"),
        ("Bank branch Gini, 2020", "Gini of Bank Branches 2020"),
        ("Bank branch Gini, 2024", "Gini of Bank Branches 2024"),
        ("New branches to low half", "New Branches Reaching Low-Density Half %"),
    ]) + [
        scatter("Branches per 100,000 people: actual against expected", col("districts", "district"),
                "Expected Branches per 100k", "Branches per 100k", col("districts", "district_type"),
                GAP, BODY_Y, 600, BODY_H),
        bars("Largest shortfalls against the model (branches)", col("top_gaps", "district"), ["Top Gap Shortfall"],
             right, BODY_Y, PAGE_W - right - GAP, 270, sort="Descending"),
        table("Districts furthest below expectation",
              [col("top_gaps", "gap_rank"), col("top_gaps", "district"), col("top_gaps", "province"),
               col("top_gaps", "branches_2024"), col("top_gaps", "expected_branches"), col("top_gaps", "shortfall"),
               col("top_gaps", "chance_of_this_few"), col("top_gaps", "flagged_short")],
              right, BODY_Y + 270 + GAP, PAGE_W - right - GAP, BODY_H - 270 - GAP,
              widths={col("top_gaps", "gap_rank"): 45, col("top_gaps", "district"): 95, col("top_gaps", "province"): 85,
                      col("top_gaps", "branches_2024"): 72, col("top_gaps", "expected_branches"): 72,
                      col("top_gaps", "shortfall"): 76, col("top_gaps", "chance_of_this_few"): 88,
                      col("top_gaps", "flagged_short"): 62}),
    ]


def page_planner() -> list[dict]:
    left, mid = GAP, GAP + RAIL + GAP
    w = (PAGE_W - mid - GAP - GAP) // 2
    h = (BODY_H - GAP) // 2
    series = col("scenario", "rule")
    axis = col("scenario", "points_added")
    return cards_row([
        ("Gini today, all branches", "Gini Today"),
        ("Gini after 1000: equity rule", "Gini After 1000 Points (Even People per Branch)"),
        ("Gini after 1000: model-gap rule", "Gini After 1000 Points (Model Gap First)"),
        ("Districts below half today", "Districts Below Half Today"),
        ("Below half after 1000: equity", "Districts Below Half After 1000 Points (Even People per Branch)"),
    ]) + [
        slicer("Rule", series, left, BODY_Y, RAIL, 260),
        line("Gini of branches against population (lower is more even)", axis, ["Scenario Gini"],
             mid, BODY_Y, w, h, series=series),
        line("Share of people in districts below half the average (%)", axis, ["Scenario Population Below Half %"],
             mid + w + GAP, BODY_Y, w, h, series=series),
        line("People per branch in the worst-served district", axis, ["Scenario Worst People per Branch"],
             mid, BODY_Y + h + GAP, w, h, series=series),
        line("Share of new points reaching districts with low female literacy (%)", axis,
             ["Scenario Share to Low Female Literacy %"], mid + w + GAP, BODY_Y + h + GAP, w, h, series=series),
    ]


def page_digital() -> list[dict]:
    left, mid = GAP, GAP + RAIL + GAP
    w = (PAGE_W - mid - GAP - GAP) // 2
    h = (BODY_H - GAP) // 2
    region = col("wallet", "region")
    quarter = col("wallet", "quarter")
    return cards_row([
        ("Wallet accounts (million)", "Latest Wallet Accounts (million)"),
        ("Registered agents (thousand)", "Latest Wallet Agents (thousand)"),
        ("Agents active, latest quarter", "Latest Active Agent Share %"),
        ("Agents active, first quarter", "First Active Agent Share %"),
        ("Wallet deposits (PKR billion)", "Latest Wallet Deposits (PKR billion)"),
    ]) + [
        slicer("Region", region, left, BODY_Y, RAIL, 300),
        line("Wallet agents per 100,000 adults", quarter, ["Wallet Agents per 100k Adults"], mid, BODY_Y, w, h, series=region),
        line("Wallet accounts per 100 adults", quarter, ["Wallet Accounts per 100 Adults"],
             mid + w + GAP, BODY_Y, w, h, series=region),
        line("Women share of wallet accounts (%)", quarter, ["Wallet Women Share %"], mid, BODY_Y + h + GAP, w, h, series=region),
        line("Share of agents and accounts that are active (%)", col("wallet_national", "quarter"),
             ["Active Agent Share %", "Active Account Share %"], mid + w + GAP, BODY_Y + h + GAP, w, h),
    ]


def page_income() -> list[dict]:
    right = GAP + 740 + GAP
    return cards_row([
        ("Adults with an account", "Pakistan Account Ownership %"),
        ("Expected at Pakistan income", "Pakistan Expected Account Ownership %"),
        ("Shortfall against income", "Pakistan Account Shortfall vs Income (pts)"),
        ("Rank from lowest", "Pakistan Rank From Lowest"),
        ("Economies compared", "Economies Compared"),
    ]) + [
        scatter("Account ownership against income, 2024", col("countries", "country_name"), "Country GDP per Person",
                "Country Account Ownership %", col("countries", "highlight"), GAP, BODY_Y, 740, BODY_H),
        slicer("World Bank region", col("countries", "world_region"), right, BODY_Y, PAGE_W - right - GAP, 170),
        table("Economies",
              [col("countries", "country_name"), col("countries", "account"), col("countries", "account_women"),
               col("countries", "account_men"), col("countries", "phone_women"), col("countries", "phone_men")],
              right, BODY_Y + 170 + GAP, PAGE_W - right - GAP, BODY_H - 170 - GAP,
              widths={col("countries", "country_name"): 120, col("countries", "account"): 60, col("countries", "account_women"): 60,
                      col("countries", "account_men"): 55, col("countries", "phone_women"): 78, col("countries", "phone_men"): 72}),
    ]


def page_about() -> list[dict]:
    return [table("About the data", [col("notes", "topic"), col("notes", "note")], GAP, GAP, PAGE_W - 2 * GAP,
                  PAGE_H - 2 * GAP, widths={col("notes", "topic"): 170, col("notes", "note"): 1030})]


PAGE_NOTES = {
    "overview": "The headline: account ownership against peer countries, branch density by province, and how unevenly branches are spread.",
    "who": "Who is left out: account ownership by gender, age, income, education and place, women and men over time, and why people have no account.",
    "where": "Where branches are: rural against urban, by district type, and bank branches in 2020 against 2024. Slicers for province and district type.",
    "explorer": "Pick a measure and compare all 120 districts; filter by province and district type; a table of district detail.",
    "gaps": "What the model expects: actual against expected branches, the districts furthest below expectation, and the lack of catch-up.",
    "planner": "Where new points go: four outcomes under three placement rules for programme sizes up to 4,000 points.",
    "digital": "The digital layer: wallet accounts, agents per 100,000 adults, the women's share and how many agents are active.",
    "income": "Pakistan against other economies: account ownership against income, with Pakistan and South Asia highlighted.",
    "about": "Sources, definitions and caveats.",
}

PAGES = [
    ("overview", "Overview", page_overview),
    ("who", "Who is left out", page_who),
    ("where", "Where branches are", page_where),
    ("explorer", "District explorer", page_explorer),
    ("gaps", "Gaps and drivers", page_gaps),
    ("planner", "Planner", page_planner),
    ("digital", "Digital layer", page_digital),
    ("income", "Income benchmark", page_income),
    ("about", "About the data", page_about),
]


# ---------------------------------------------------------------------------
# serialisation
# ---------------------------------------------------------------------------
def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def text(value: str) -> dict:
    return lit("'" + value.replace("'", "''") + "'")


def number(value: float) -> dict:
    return lit(f"{value}D")


def flag(value: bool) -> dict:
    return lit("true" if value else "false")


def colour(hex_code: str) -> dict:
    return {"solid": {"color": text(hex_code)}}


def projection(field: Field, header: str | None = None) -> dict:
    entity, prop = field
    kind = "Measure" if entity == "_Measures" else "Column"
    out = {"field": {kind: {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
           "queryRef": f"{entity}.{prop}", "active": True}
    if header:
        out["displayName"] = header
    return out


def visual_objects(v: dict) -> dict:
    """Formatting of the visual itself (data labels, slicer header)."""
    objects: dict = {}
    if v["type"] == "card":
        objects["labels"] = [{"properties": {"fontSize": number(22), "color": colour(config.NAVY),
                                             "labelDisplayUnits": number(1)}}]
        objects["categoryLabels"] = [{"properties": {"show": flag(False)}}]
    elif v["type"] == "slicer":
        objects["header"] = [{"properties": {"show": flag(False)}}]
    elif v["type"] == "clusteredBarChart" and v["labels"]:
        objects["labels"] = [{"properties": {"show": flag(True), "fontSize": number(9)}}]
    elif v["type"] == "tableEx":
        objects["values"] = [{"properties": {"fontSize": number(10), "wordWrap": flag(True)}}]
        objects["columnHeaders"] = [{"properties": {"fontSize": number(10), "bold": flag(True), "wordWrap": flag(True)}}]
        if v["widths"]:
            objects["columnWidth"] = [{"selector": {"metadata": f"{entity}.{prop}"}, "properties": {"value": number(px)}}
                                      for (entity, prop), px in v["widths"].items()]
    if "Series" in v["roles"] or len(v["roles"].get("Y", [])) > 1:
        objects["legend"] = [{"properties": {"show": flag(True), "showTitle": flag(False)}}]
    if v["log"]:
        objects["categoryAxis"] = [{"properties": {"axisScale": text("Log")}}]
        objects["valueAxis"] = [{"properties": {"axisScale": text("Log")}}]
    return objects


def container_objects(title: str) -> dict:
    """Formatting of the frame around a visual: title, white panel and a light border."""
    return {
        "title": [{"properties": {"show": flag(True), "text": text(title), "fontSize": number(11), "bold": flag(True),
                                  "fontColor": colour(MUTED), "alignment": text("left")}}],
        "background": [{"properties": {"show": flag(True), "color": colour(PANEL), "transparency": number(0)}}],
        "border": [{"properties": {"show": flag(True), "color": colour(BORDER), "radius": number(8)}}],
    }


def visual_json(page_id: str, index: int, v: dict) -> dict:
    headers = v["type"] == "tableEx"
    query: dict = {"queryState": {role: {"projections": [projection(f, HEADERS[f[1]] if headers else None) for f in fields]}
                                  for role, fields in v["roles"].items()}}
    if v["sort"]:
        first = next(iter(v["roles"]["Y"]))
        query["sortDefinition"] = {"sort": [{"field": projection(first)["field"], "direction": v["sort"]}],
                                   "isDefaultSort": True}
    visual = {"visualType": v["type"], "query": query}
    objects = visual_objects(v)
    if objects:
        visual["objects"] = objects
    visual["visualContainerObjects"] = container_objects(v["title"])
    visual["drillFilterOtherVisuals"] = True
    return {"$schema": VISUAL_SCHEMA, "name": f"{page_id}_{index:02d}",
            "position": {"x": v["x"], "y": v["y"], "z": index * 1000, "height": v["h"], "width": v["w"],
                         "tabOrder": index * 1000},
            "visual": visual}


def page_json(page_id: str, display: str) -> dict:
    return {"$schema": PAGE_SCHEMA, "name": page_id, "displayName": display, "displayOption": "FitToPage",
            "height": PAGE_H, "width": PAGE_W,
            "objects": {"background": [{"properties": {"color": colour(PAGE_BACKGROUND), "transparency": number(0)}}]}}


def _dump(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_report(folder: Path, theme: dict) -> None:
    """Replace the report folder's definition with the current pages. Local settings (.pbi) are left alone."""
    for stale in ("definition", "StaticResources"):
        shutil.rmtree(folder / stale, ignore_errors=True)
    (folder / "report.json").unlink(missing_ok=True)       # the older single-file layout
    definition = folder / "definition"

    _dump(folder / "definition.pbir", {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{PROJECT}.SemanticModel"}}})
    (folder / ".platform").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": PROJECT},
        "config": {"version": "2.0", "logicalId": tag("platform", "Report")},
    }, indent=2), encoding="utf-8")

    versions = {"visual": "2.14.0", "report": "3.4.0", "page": "2.3.1"}
    _dump(definition / "version.json", {"$schema": VERSION_SCHEMA, "version": "2.0.0"})
    _dump(definition / "report.json", {
        "$schema": REPORT_SCHEMA,
        "themeCollection": {"customTheme": {"name": THEME_FILE, "reportVersionAtImport": versions,
                                            "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": THEME_FILE, "path": THEME_FILE, "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": False},
    })
    _dump(folder / "StaticResources" / "RegisteredResources" / THEME_FILE, theme)
    _dump(definition / "pages" / "pages.json", {"$schema": PAGES_SCHEMA, "pageOrder": [p[0] for p in PAGES],
                                                "activePageName": PAGES[0][0]})
    for page_id, display, builder in PAGES:
        _dump(definition / "pages" / page_id / "page.json", page_json(page_id, display))
        for i, v in enumerate(builder()):
            _dump(definition / "pages" / page_id / "visuals" / f"{page_id}_{i:02d}" / "visual.json", visual_json(page_id, i, v))
