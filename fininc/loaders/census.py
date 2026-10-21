"""PBS Population Census 2023 district tables.

The tables are CSV conversions of the PBS Excel tables, so they are checked rather than trusted: the district
populations must add up to the official provincial totals in the PBS National Census Report (Table 4.2).
"""

from __future__ import annotations

import re

import pandas as pd

from .. import config
from ..paths import RAW

CENSUS_DIR = RAW / "pbs" / "census2023_district_tables"

# Spelling differences between tables (Table 01 has a typo for Tando Allahyar).
NAME_FIXES = {"TANDO AHYAR": "TANDO ALLAHYAR"}


def _read(table: str) -> pd.DataFrame:
    frames = []
    for province, slug in config.CENSUS_PROVINCE_FILES.items():
        df = pd.read_csv(CENSUS_DIR / f"table_{table}_{slug}_district.csv")
        df["province"] = province
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["district"] = out["name_admin_unit"].str.strip().str.upper().replace(NAME_FIXES)
    return out[out["admin_unit"].str.upper() == "DISTRICT"]


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", str(text)).strip().upper()


# ---------------------------------------------------------------------------
# Table 01: area, population by rural/urban, 2017 population
# ---------------------------------------------------------------------------
def _table01() -> tuple[pd.DataFrame, list[str]]:
    raw = _read("01")
    notes: list[str] = []

    # One district appears twice in Sindh (Tando Muhammad Khan, with a second block of 272,427 people). The
    # second block does not belong to any of the 30 official districts: removing it makes Sindh match the
    # official provincial total exactly. Keep the largest row per district and region.
    before = len(raw)
    raw = (raw.sort_values("all_sexes", ascending=False)
              .drop_duplicates(subset=["province", "district", "region"], keep="first"))
    dropped = before - len(raw)
    if dropped:
        notes.append(f"Table 01: dropped {dropped} duplicate rows (second Tando Muhammad Khan block, "
                     "272,427 people) so provincial totals match the PBS report.")

    overall = raw[raw["region"] == "OVERALL"].set_index("district")
    rural = raw[raw["region"] == "RURAL"].set_index("district")
    urban = raw[raw["region"] == "URBAN"].set_index("district")
    out = pd.DataFrame({
        "province": overall["province"],
        "area_sqkm": overall["area_sqkm"],
        "pop": overall["all_sexes"],
        "pop_male": overall["male"],
        "pop_female": overall["female"],
        "pop_urban": urban["all_sexes"],
        "pop_rural": rural["all_sexes"],
        "pop_2017": overall["pop_2017"],
        "household_size": overall["avg_hh_size"],
    })
    return out.reset_index(), notes


# ---------------------------------------------------------------------------
# Table 05: age structure (the detailed tables exclude restricted areas, so use shares only)
# ---------------------------------------------------------------------------
def _table05() -> pd.DataFrame:
    raw = _read("05")
    # The column is named differently in the Islamabad file, so take whichever is filled.
    age_cols = [c for c in raw.columns if "age_group" in c]
    raw["age"] = raw[age_cols].bfill(axis=1).iloc[:, 0].map(_clean)
    wanted = {"ALL AGES": "age_all", "UNDER 15": "age_under15", "15 - 64": "age_15_64", "60 & ABOVE": "age_60plus"}
    sub = raw[raw["age"].isin(wanted)].pivot_table(index="district", columns="age", values="all_sexes_overall",
                                                    aggfunc="first")
    sub = sub.rename(columns=wanted)
    missing = set(wanted.values()) - set(sub.columns)
    if missing:
        raise ValueError(f"Table 05 is missing age groups: {missing}")
    return sub.reset_index()


# ---------------------------------------------------------------------------
# Table 12: literacy
# ---------------------------------------------------------------------------
def _table12() -> pd.DataFrame:
    raw = _read("12")
    raw["var"] = raw["vars"].map(_clean)
    keep = {"POPULATION >=10": "pop10", "LITERATE >=10": "lit10", "POPULATION >=5": "pop5",
            "NEVER TO SCHOOL (ALL)": "never_school"}
    parts = []
    for var, name in keep.items():
        sub = raw[raw["var"] == var].set_index("district")
        parts.append(pd.DataFrame({f"{name}": sub["all_sexes_overall"], f"{name}_f": sub["female_overall"],
                                   f"{name}_m": sub["male_overall"]}))
    return pd.concat(parts, axis=1).reset_index()


# ---------------------------------------------------------------------------
# Housing and household services (tables 20, 22-25), overall rows only
# ---------------------------------------------------------------------------
def _table20() -> pd.DataFrame:
    raw = _read("20")
    raw["kind"] = raw["hh_type"].map(_clean)
    wide = raw.pivot_table(index="district", columns="kind", values="overall", aggfunc="first")
    return pd.DataFrame({"hh_pakka": wide["PAKKA"], "hh_housing_total": wide.sum(axis=1)}).reset_index()


def _overall(table: str, columns: dict[str, str]) -> pd.DataFrame:
    raw = _read(table)
    sub = raw[raw["region"].str.upper() == "OVERALL"].set_index("district")
    return pd.DataFrame({new: sub[old] for old, new in columns.items()}).reset_index()


def load_districts() -> tuple[pd.DataFrame, list[str]]:
    """One row per 2023 census district with the counts needed for the unit table, plus data-quality notes."""
    base, notes = _table01()
    # Districts with no urban (or no rural) area have no row for it in Table 01: that is zero people.
    absent = int(base["pop_urban"].isna().sum() + base["pop_rural"].isna().sum())
    base[["pop_urban", "pop_rural"]] = base[["pop_urban", "pop_rural"]].fillna(0)
    gap = (base["pop_urban"] + base["pop_rural"] - base["pop"]).abs()
    if (gap > 0.005 * base["pop"]).any():
        raise ValueError("Urban + rural population differs from the district total by more than 0.5%")
    notes.append(f"Table 01: {absent} missing urban or rural rows treated as zero population.")
    parts = [
        _table05(),
        _table12(),
        _table20(),
        _overall("22", {"households": "hh_total", "light_elect": "hh_electricity", "fuel_gas": "hh_fuel_gas",
                        "fuel_lpgcng": "hh_fuel_lpg"}),
        _overall("23", {"drink_wtr_improve": "hh_water_improved"}),
        _overall("24", {"toilet_flush": "hh_flush_toilet"}),
        _overall("25", {"res_st_owned": "hh_owned", "owner_gender_male": "owner_male",
                        "owner_gender_female": "owner_female"}),
    ]
    out = base
    for part in parts:
        out = out.merge(part, on="district", how="left", validate="one_to_one")
    if out.isna().any().any():
        raise ValueError(f"Missing census values after merging tables:\n{out.isna().sum()[out.isna().sum() > 0]}")
    out["hh_gas_or_lpg"] = out["hh_fuel_gas"] + out["hh_fuel_lpg"]
    return out.drop(columns=["hh_fuel_gas", "hh_fuel_lpg"]), notes


def check_against_official(districts: pd.DataFrame) -> pd.DataFrame:
    """Compare provincial sums of the district table with the official PBS totals.

    Returns one row per province with the difference. All differences must be zero.
    """
    rows = []
    for province in config.CENSUS_PROVINCE_FILES:
        official = config.OFFICIAL_CENSUS_TOTALS[province]
        sub = districts[districts["province"] == province]
        rows.append({"province": province, "districts": len(sub),
                     "pop_2023": int(sub["pop"].sum()), "official_2023": official["2023"],
                     "diff_2023": int(sub["pop"].sum()) - official["2023"],
                     "pop_2017": int(sub["pop_2017"].sum()), "official_2017": official["2017"],
                     "diff_2017": int(sub["pop_2017"].sum()) - official["2017"]})
    return pd.DataFrame(rows)
