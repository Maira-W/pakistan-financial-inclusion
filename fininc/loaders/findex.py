"""World Bank Global Findex and related World Bank indicators.

Raw files are written by fininc.ingest. All values are percentages of adults aged 15+ unless noted.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .. import config
from ..paths import RAW


def _read(rel: str):
    return json.loads((RAW / rel).read_text(encoding="utf-8"))


def load_panel() -> pd.DataFrame:
    """Pakistan and its three peers over time, one row per indicator, country and survey year."""
    raw = _read("worldbank/findex_panel_pakistan_and_peers.json")
    rows = []
    for indicator, items in raw.items():
        label, group = config.FINDEX_CATALOGUE[indicator]
        for item in items:
            rows.append({"indicator": indicator, "label": label, "group": group, "country": item["country"],
                         "year": item["year"], "value": float(item["value"])})
    panel = pd.DataFrame(rows)
    panel["country_name"] = panel["country"].map(config.PEERS)
    return panel.sort_values(["group", "indicator", "country", "year"]).reset_index(drop=True)


def pakistan_series(panel: pd.DataFrame, indicator: str) -> pd.Series:
    sub = panel[(panel["country"] == "PAK") & (panel["indicator"] == indicator)]
    return sub.set_index("year")["value"].sort_index()


def segment_table(panel: pd.DataFrame) -> pd.DataFrame:
    """Account ownership in Pakistan by segment (gender, age, education, income, location, labour) and year."""
    seg = panel[(panel["country"] == "PAK") & (panel["indicator"].isin(config.SEGMENT_INDICATORS))].copy()
    seg = seg.rename(columns={"label": "segment"})
    return seg[["indicator", "segment", "group", "year", "value"]].reset_index(drop=True)


def barrier_table(panel: pd.DataFrame, year: int = config.FINDEX_YEAR) -> pd.DataFrame:
    """Why adults have no bank or similar account, as a share of adults without one.

    Five barriers are published directly. Documentation is only published as a share of all adults, so it is
    divided by the share of adults without a bank or similar account to put it on the same footing. That row
    is marked derived=True.
    """
    pak = panel[(panel["country"] == "PAK") & (panel["year"] == year)].set_index("indicator")["value"]
    rows = [{"indicator": i, "reason": config.BARRIER_INDICATORS[i][0], "share_of_unbanked": float(pak[i]),
             "derived": False} for i in config.BARRIER_INDICATORS if i in pak.index]
    fi_account = pak.get("fiaccount.t.d")
    doc = pak.get(config.DOCUMENTATION_BARRIER)
    if fi_account is not None and doc is not None:
        rows.append({"indicator": config.DOCUMENTATION_BARRIER, "reason": "Lack of necessary documentation",
                     "share_of_unbanked": float(doc) / (1 - fi_account / 100.0), "derived": True})
    return pd.DataFrame(rows).sort_values("share_of_unbanked", ascending=False).reset_index(drop=True)


def mobile_money_barriers(panel: pd.DataFrame, year: int = config.FINDEX_YEAR) -> pd.DataFrame:
    pak = panel[(panel["country"] == "PAK") & (panel["year"] == year)].set_index("indicator")["value"]
    rows = [{"indicator": i, "reason": config.MOBILE_MONEY_BARRIERS[i][0], "value": float(pak[i])}
            for i in config.MOBILE_MONEY_BARRIERS if i in pak.index]
    return pd.DataFrame(rows).sort_values("value", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Cross-country benchmark
# ---------------------------------------------------------------------------
def _wdi_long(name: str) -> pd.DataFrame:
    """A World Bank bulk CSV (one row per country, one column per year) as country, year, value rows."""
    wide = pd.read_csv(RAW / "worldbank" / f"wdi_{name}.csv", skiprows=4, encoding="utf-8-sig")
    wide = wide.loc[:, ~wide.columns.str.startswith("Unnamed")]
    years = [c for c in wide.columns if c.isdigit()]
    long = wide.melt(id_vars=["Country Code"], value_vars=years, var_name="year", value_name="value")
    long = long.dropna(subset=["value"]).rename(columns={"Country Code": "country"})
    long["year"] = long["year"].astype(int)
    return long


def _wdi(name: str, year: int) -> pd.DataFrame:
    """Latest value on or before the given year for each country."""
    long = _wdi_long(name)
    long = long[long["year"] <= year].sort_values("year")
    return long.groupby("country").tail(1)[["country", "value", "year"]]


def _countries() -> pd.DataFrame:
    meta = pd.DataFrame(_read("worldbank/countries.json"))
    return meta[meta["region"] != "Aggregates"].rename(columns={"id": "country"})


def load_cross_section(year: int = config.FINDEX_YEAR) -> pd.DataFrame:
    """One row per economy with Findex outcomes and GDP per capita (PPP) for the benchmark model."""
    world = _read("worldbank/findex_world_2021_2024.json")
    frames = []
    for indicator, items in world.items():
        df = pd.DataFrame(items)
        df = df[df["year"] == year][["country", "name", "value"]].rename(columns={"value": indicator})
        frames.append(df.set_index(["country", "name"]))
    wide = pd.concat(frames, axis=1).reset_index()
    wide = wide.rename(columns={
        "account.t.d": "account", "account.t.d.1": "account_women", "account.t.d.2": "account_men",
        "con1": "phone", "con1.1": "phone_women", "con1.2": "phone_men",
        "mobileaccount.t.d": "mobile_money", "fiaccount.t.d": "fi_account", "g20.any": "digital_payment"})
    wide = wide.merge(_countries()[["country", "region", "income"]], on="country", how="inner")

    gdp = _wdi("gdp_per_capita_ppp", year)
    wide = wide.merge(gdp.rename(columns={"value": "gdp_pc_ppp", "year": "gdp_year"}), on="country", how="left")
    wide["account_gap"] = wide["account_men"] - wide["account_women"]
    wide["phone_gap"] = wide["phone_men"] - wide["phone_women"]
    wide["log_gdp_pc"] = np.log(wide["gdp_pc_ppp"])
    return wide.sort_values("country").reset_index(drop=True)


def load_wdi_branches() -> pd.DataFrame:
    """Commercial bank branches and ATMs per 100,000 adults (IMF Financial Access Survey via WDI), all countries."""
    frames = []
    for name, indicator in (("bank_branches_per_100k_adults", "FB.CBK.BRCH.P5"), ("atms_per_100k_adults", "FB.ATM.TOTL.P5")):
        long = _wdi_long(name)
        frames.append(long.assign(indicator=indicator))
    return pd.concat(frames, ignore_index=True)
