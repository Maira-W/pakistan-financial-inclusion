"""Read everything the report stage needs from data/interim and data/processed."""

from __future__ import annotations

import json
from dataclasses import dataclass

import pandas as pd

from .paths import INTERIM, PROCESSED


@dataclass
class Results:
    units: pd.DataFrame
    provinces: pd.DataFrame
    bb_regions: pd.DataFrame
    bb_national: pd.DataFrame
    panel: pd.DataFrame
    segments: pd.DataFrame
    barriers: pd.DataFrame
    mm_barriers: pd.DataFrame
    cross: pd.DataFrame
    curve: pd.DataFrame
    summary: dict
    lorenz: dict
    scenario: dict
    boundaries: dict
    province_boundaries: dict

    @property
    def headline(self) -> dict:
        return self.summary["headline"]


def _json(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load() -> Results:
    return Results(
        units=pd.read_csv(PROCESSED / "units.csv"),
        provinces=pd.read_csv(INTERIM / "provinces.csv"),
        bb_regions=pd.read_csv(INTERIM / "bb_regions_quarterly.csv"),
        bb_national=pd.read_csv(INTERIM / "bb_national_quarterly.csv"),
        panel=pd.read_csv(INTERIM / "findex_panel.csv"),
        segments=pd.read_csv(PROCESSED / "findex_segments.csv"),
        barriers=pd.read_csv(PROCESSED / "findex_barriers.csv"),
        mm_barriers=pd.read_csv(PROCESSED / "findex_mobile_money_barriers.csv"),
        cross=pd.read_csv(PROCESSED / "cross_country.csv"),
        curve=pd.read_csv(PROCESSED / "scenario_curve.csv"),
        summary=_json(PROCESSED / "summary.json"),
        lorenz=_json(PROCESSED / "lorenz_curves.json"),
        scenario=_json(PROCESSED / "scenario.json"),
        boundaries=_json(PROCESSED / "unit_boundaries.geojson"),
        province_boundaries=_json(PROCESSED / "province_boundaries.geojson"),
    )
