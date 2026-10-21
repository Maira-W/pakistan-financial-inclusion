"""Analysis units: districts on their 2020 boundaries.

The 2023 census, the SBP 2020 appendix and the SBP 2024 register do not share district boundaries or
spellings. Districts created since 2020 are folded back into their parent, so every source describes the same
areas and the map polygons can be dissolved to match. That gives 120 units for Pakistan outside Azad Jammu &
Kashmir and Gilgit-Baltistan, which the census district tables do not cover.
"""

from __future__ import annotations

import re

import pandas as pd

# 2023 census districts that sit inside a larger 2020 district.
MERGED_INTO = {
    "KARACHI CENTRAL": "Karachi", "KARACHI EAST": "Karachi", "KARACHI SOUTH": "Karachi",
    "KARACHI WEST": "Karachi", "KORANGI": "Karachi", "MALIR": "Karachi", "KEAMARI": "Karachi",
    "UPPER CHITRAL": "Chitral", "LOWER CHITRAL": "Chitral",
    "UPPER KOHISTAN": "Kohistan", "LOWER KOHISTAN": "Kohistan", "KOLAI PALAS KOHISTAN": "Kohistan",
    "CHAMAN": "Killa Abdullah", "DUKI": "Loralai", "SHERANI": "Zhob", "SURAB": "Kalat",
    "SOHBATPUR": "Jaffarabad", "SUJAWAL": "Thatta", "TANK": "Dera Ismail Khan",
}

# Spellings used in the SBP files that differ from the census names.
SBP_ALIASES = {
    "Bajaur Agency": "Bajaur", "Batgram": "Batagram", "Bunner": "Buner", "Bolan (Dhadar)": "Kachhi",
    "D.G.Khan": "Dera Ghazi Khan", "D.I.Khan": "Dera Ismail Khan", "Dera Bughti": "Dera Bugti",
    "Jaffarabad(Dera Allah Yar)": "Jaffarabad", "Jaffarabad(Dera Allah Y": "Jaffarabad",   # register truncates at 23 characters
    "Kamber/Shahdadkot": "Kambar Shahdad Kot",
    "Kech(Turbat)": "Kech", "Khyber Agency": "Khyber", "Kurram Agency": "Kurram", "Lasbella": "Lasbela",
    "Mahmand Agency": "Mohmand", "N.Waziristan Agency": "North Waziristan",
    "Naushro Feroze": "Naushahro Feroze", "Noshki": "Nushki", "Orakzai Agency": "Orakzai",
    "Panjgoor": "Panjgur", "S.Waziristan Agency": "South Waziristan",
    "Tando Mohammad Khan": "Tando Muhammad Khan", "Tharparkar (Mithi)": "Tharparkar", "Tor Ghar": "Torghar",
    "Umerkot": "Umer Kot", "Rajan Pur": "Rajanpur",
    # Created after 2020 but listed on their own in some SBP files:
    "Tank": "Dera Ismail Khan", "Sujawal": "Thatta",
}

# Districts of Azad Jammu & Kashmir and Gilgit-Baltistan (not in the census district tables).
OUTSIDE_COVERAGE = {
    "Astore", "Bagh", "Bhimber", "Diamar", "Ghanchi", "Ghizer", "Gilgit", "Hattian", "Hattian Bala",
    "Haveli Kahuta", "Hunza", "Kotli", "Mirpur", "Muzaffarabad", "Nagar", "Neelum", "Rawlakot (Poonch)",
    "Sakardu", "Sudhnuthi",
}

# Branches the register lists under the wrong district, fixed by tehsil.
REGISTER_TEHSIL_OVERRIDES = {("Sibi", "Gandawah"): "Jhal Magsi"}


def key(name: str) -> str:
    """Letters only, upper case: 'D.G.Khan' and 'D G KHAN' compare equal."""
    return re.sub(r"[^A-Z]", "", str(name).upper())


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def unit_for_census_district(name: str) -> str:
    """Unit that a 2023 census district belongs to."""
    upper = name.strip().upper()
    return MERGED_INTO.get(upper, upper.title())


def build_units(districts: pd.DataFrame) -> pd.DataFrame:
    """Unit list from the census district table: unit, unit_id, province, member districts."""
    work = districts[["district", "province"]].copy()
    work["unit"] = work["district"].map(unit_for_census_district)
    grouped = work.groupby("unit").agg(province=("province", "first"), n_districts=("district", "size"),
                                       members=("district", lambda s: sorted(s)))
    if (work.groupby("unit")["province"].nunique() > 1).any():
        raise ValueError("A unit spans more than one province")
    units = grouped.reset_index()
    units["unit_id"] = units["unit"].map(slug)
    if units["unit_id"].duplicated().any():
        raise ValueError("Duplicate unit ids")
    return units[["unit_id", "unit", "province", "n_districts", "members"]]


class UnitResolver:
    """Maps names used in SBP files to analysis units."""

    def __init__(self, units: pd.DataFrame):
        self.names = set(units["unit"])
        self.by_key = {key(u): u for u in self.names}

    def resolve(self, name: str, tehsil: str | None = None) -> str | None:
        """Unit for an SBP district name, or None when the district lies outside the census coverage.

        Raises KeyError for a name that is neither mapped nor known as outside coverage, so a new spelling
        in a future SBP release cannot be dropped silently.
        """
        name = " ".join(str(name).split())
        if tehsil is not None and (name, tehsil) in REGISTER_TEHSIL_OVERRIDES:
            return REGISTER_TEHSIL_OVERRIDES[(name, tehsil)]
        if name in OUTSIDE_COVERAGE:
            return None
        if name in SBP_ALIASES:
            return SBP_ALIASES[name]
        if key(name) in self.by_key:
            return self.by_key[key(name)]
        raise KeyError(f"No analysis unit for SBP district {name!r}")
