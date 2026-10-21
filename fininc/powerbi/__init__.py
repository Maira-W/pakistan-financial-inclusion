"""Write the Power BI project: a semantic model and a report, as files Power BI Desktop opens.

    powerbi/Pakistan_Financial_Inclusion.pbip                  open this in Power BI Desktop
    powerbi/Pakistan_Financial_Inclusion.SemanticModel/        tables, relationships and DAX measures (TMDL)
    powerbi/Pakistan_Financial_Inclusion.Report/               nine report pages (PBIR) and a colour theme
    powerbi/measures.dax                                       the measures as text

Everything is generated from data/processed, so the report always matches the dashboard and the documents.

A project holds no data cache, so Power BI Desktop shows a "Refresh now" banner the first time it opens one. The
Pakistan_Financial_Inclusion.pbix beside it is a snapshot saved from the opened project (File > Save as), with the data
inside, for readers who just want to look at the report. Regenerating the project does not change that file.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from .. import config
from ..paths import POWERBI
from ..results import load
from .measures import MEASURES, measures_text
from .model import PROJECT, write_model
from .report import write_report
from .tables import make_tables

DEFAULT_MODE = "inline"

THEME = {
    "name": "Financial Inclusion",
    "dataColors": [config.NAVY, config.TEAL, config.ORANGE, config.AMBER, config.GREY, config.PURPLE],
    "background": "#FFFFFF", "foreground": "#1D2733", "tableAccent": config.NAVY,
    "good": config.TEAL, "bad": config.ORANGE, "neutral": config.GREY,
    "textClasses": {
        "callout": {"fontSize": 24, "fontFace": "Segoe UI Semibold", "color": config.NAVY},
        "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": config.NAVY},
        "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": config.NAVY},
        "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": "#4A5568"},
    },
    "visualStyles": {"*": {"*": {"*": [{"fontFamily": "Segoe UI"}]}}},
}


def build(mode: str = DEFAULT_MODE, folder: Path = POWERBI) -> None:
    if mode not in ("inline", "csv"):
        raise ValueError("mode must be 'inline' or 'csv'")
    r = load()
    tables = make_tables(r)
    folder.mkdir(parents=True, exist_ok=True)
    data = folder / "data"
    if mode == "csv":
        data.mkdir(exist_ok=True)
        for name, df in tables.items():
            df.round(4).to_csv(data / f"{name}.csv", index=False)
    else:
        shutil.rmtree(data, ignore_errors=True)

    write_model(folder / f"{PROJECT}.SemanticModel", {n: d.round(4) for n, d in tables.items()}, data, mode)
    write_report(folder / f"{PROJECT}.Report", THEME)
    (folder / f"{PROJECT}.pbip").write_text(json.dumps({
        "version": "1.0", "artifacts": [{"report": {"path": f"{PROJECT}.Report"}}],
        "settings": {"enableAutoRecovery": True},
    }, indent=2), encoding="utf-8")
    (folder / "measures.dax").write_text(measures_text(), encoding="utf-8")
    for old in ("theme.json", f"{PROJECT}_PowerBI.zip"):        # replaced by the theme inside the report and the .pbix
        (folder / old).unlink(missing_ok=True)
    print(f"[powerbi] {len(tables)} tables, {len(MEASURES)} measures, {mode} data -> {folder / (PROJECT + '.pbip')}")
