"""Build clean analysis tables from the raw PBS and SBP files.

Inputs (kept untouched in data/raw/):
  - data/raw/pbs/census2023_table01_github/*.csv   District population, PBS Census 2023 (Table 1)
  - data/raw/sbp/sbp_appendices_dec2020.pdf         SBP district-wise scheduled bank branches, 31 Dec 2020

Outputs (written to data/clean/):
  - pbs_population_district_2023.csv
  - sbp_branches_district_2020.csv
  - branch_density_district.csv   (one row per analysis unit, with branches per 100,000 people)
  - branch_density_province.csv

Run from the project root:  python scripts/build_clean_data.py
"""

from pathlib import Path
import re

import pandas as pd
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
RAW_PBS = ROOT / "data" / "raw" / "pbs" / "census2023_table01_github"
RAW_SBP = ROOT / "data" / "raw" / "sbp" / "sbp_appendices_dec2020.pdf"
CLEAN = ROOT / "data" / "clean"

# SBP district-wise table is on these PDF pages (0-indexed).
SBP_PAGES = [4, 5, 6, 7]

# SBP 2020 names -> PBS 2023 names. Old and new district names differ, so this is mapped by hand.
# Districts in AJK and Gilgit-Baltistan are not covered by the PBS 2023 district table, so they map to None.
SBP_TO_PBS = {
    "Astore": None,
    "Bagh": None,
    "Bhimber": None,
    "Bolan (Dhadar)": "KACHHI",
    "Bajaur Agency": "BAJAUR",
    "Batgram": "BATAGRAM",
    "Bunner": "BUNER",
    "Chitral": "GROUP:CHITRAL",
    "D.G.Khan": "DERA GHAZI KHAN",
    "D.I.Khan": "DERA ISMAIL KHAN",
    "Dera Bughti": "DERA BUGTI",
    "Diamar": None,
    "Ghanchi": None,
    "Ghizer": None,
    "Gilgit": None,
    "Hattian": None,
    "Jaffarabad(Dera Allah Yar)": "JAFFARABAD",
    "Kamber/Shahdadkot": "KAMBAR SHAHDAD KOT",
    "Karachi": "GROUP:KARACHI",
    "Kech(Turbat)": "KECH",
    "Khyber Agency": "KHYBER",
    "Kohistan": "GROUP:KOHISTAN",
    "Kotli": None,
    "Kurram Agency": "KURRAM",
    "Malakand": "MALAKAND PROTECTED AREA",
    "Rajan Pur": "RAJANPUR",
    "Tor Ghar": "TORGHAR",
    "Umerkot": "UMER KOT",
    "Killa Abdullah": "KILLA ABDULLAH",
    "Killa Saifullah": "KILLA SAIFULLAH",
    "Lasbella": "LASBELA",
    "Mahmand Agency": "MOHMAND",
    "Mirpur": None,
    "Muzaffarabad": None,
    "N.Waziristan Agency": "NORTH WAZIRISTAN",
    "Naushro Feroze": "NAUSHAHRO FEROZE",
    "Neelum": None,
    "Noshki": "NUSHKI",
    "Orakzai Agency": "ORAKZAI",
    "Panjgoor": "PANJGUR",
    "Rawlakot (Poonch)": None,
    "S.Waziristan Agency": "SOUTH WAZIRISTAN",
    "Sakardu": None,
    "Sudhnuthi": None,
    "Tando Allahyar": "TANDO AHYAR",
    "Tando Mohammad Khan": "TANDO MUHAMMAD KHAN",
    "Tharparkar (Mithi)": "THARPARKAR",
}

# Groups: several 2023 districts that together make up one 2020 SBP district.
GROUPS = {
    "GROUP:KARACHI": ["KARACHI CENTRAL", "KARACHI EAST", "KARACHI SOUTH", "KARACHI WEST",
                      "KORANGI", "MALIR", "KEAMARI"],
    "GROUP:CHITRAL": ["UPPER CHITRAL", "LOWER CHITRAL"],
    "GROUP:KOHISTAN": ["UPPER KOHISTAN", "LOWER KOHISTAN", "KOLAI PALAS KOHISTAN"],
}


def _key(name: str) -> str:
    """Normalise a district name for matching: upper case, letters only."""
    return re.sub(r"[^A-Z]", "", name.upper())


def load_population() -> pd.DataFrame:
    """PBS 2023 total population per district, with province from the file name."""
    frames = []
    for path in sorted(RAW_PBS.glob("table_01_*_district.csv")):
        province = path.name.split("table_01_")[1].split("_district")[0].upper()
        df = pd.read_csv(path)
        df = df[(df["admin_unit"] == "DISTRICT") & (df["region"] == "OVERALL")]
        frames.append(pd.DataFrame({
            "district": df["name_admin_unit"].str.strip().str.upper(),
            "province": province.replace("KP", "KHYBER PAKHTUNKHWA"),
            "population_2023": df["all_sexes"].astype(int),
            "urban_share_pct": df["urban_prop"],
            "area_sqkm": df["area_sqkm"],
        }))
    pop = pd.concat(frames, ignore_index=True)
    return pop


def _to_int(text: str) -> int | None:
    text = text.replace(",", "").strip()
    return int(text) if text.isdigit() else None


def load_branches() -> pd.DataFrame:
    """SBP district-wise scheduled bank branches at 31 Dec 2020, read from the PDF tables."""
    rows = []
    with pdfplumber.open(RAW_SBP) as pdf:
        for i in SBP_PAGES:
            for table in pdf.pages[i].extract_tables():
                for r in table:
                    if not r or not r[0]:
                        continue
                    name = re.sub(r"\s+", " ", r[0]).strip()
                    if name.upper() in {"DISTRICT", "GRAND TOTAL"}:
                        continue
                    conv, islamic, total = (_to_int(c or "") for c in r[1:4])
                    rows.append({"sbp_district": name, "conventional": conv,
                                 "islamic": islamic, "branches_total": total})
    br = pd.DataFrame(rows)
    # Each row must reconcile: conventional + islamic = total.
    bad = br[br["conventional"].fillna(0) + br["islamic"].fillna(0) != br["branches_total"]]
    if len(bad):
        raise ValueError(f"Branch rows do not add up:\n{bad}")
    return br


def build() -> None:
    CLEAN.mkdir(parents=True, exist_ok=True)

    pop = load_population()
    br = load_branches()

    pop.to_csv(CLEAN / "pbs_population_district_2023.csv", index=False)

    # Map SBP rows onto PBS district names. Names that match after removing spaces and punctuation
    # are mapped automatically; everything else must be in SBP_TO_PBS.
    pbs_by_key = {_key(d): d for d in pop["district"].unique()}

    def to_pbs(sbp_name: str):
        if sbp_name in SBP_TO_PBS:
            return SBP_TO_PBS[sbp_name]
        if _key(sbp_name) in pbs_by_key:
            return pbs_by_key[_key(sbp_name)]
        raise ValueError(f"No PBS match for SBP district '{sbp_name}'. Add it to SBP_TO_PBS.")

    br["pbs_district"] = br["sbp_district"].map(to_pbs)
    br["in_scope"] = br["pbs_district"].notna()
    br.to_csv(CLEAN / "sbp_branches_district_2020.csv", index=False)

    # Analysis units: one row per PBS district, except groups, which are combined.
    province_of = dict(zip(pop["district"], pop["province"]))
    units = []
    for _, row in pop.iterrows():
        name = row["district"]
        if any(name in members for members in GROUPS.values()):
            continue  # handled below as part of its group
        units.append({"unit": name, "province": row["province"], "population_2023": row["population_2023"],
                      "members": 1})
    for group, members in GROUPS.items():
        members_df = pop[pop["district"].isin(members)]
        units.append({"unit": group.replace("GROUP:", "") + " (combined)",
                      "province": members_df["province"].iloc[0],
                      "population_2023": members_df["population_2023"].sum(),
                      "members": len(members_df)})
    units = pd.DataFrame(units)

    # Attach branches. A unit's branches are the SBP row mapped to it (group rows map to the group key).
    scoped = br[br["in_scope"]].copy()
    scoped["unit"] = scoped["pbs_district"].map(
        lambda k: k.replace("GROUP:", "") + " (combined)" if k.startswith("GROUP:") else k)
    branch_by_unit = scoped.groupby("unit", as_index=False)["branches_total"].sum()

    density = units.merge(branch_by_unit, on="unit", how="left")
    density["branch_data_found"] = density["unit"].isin(branch_by_unit["unit"])
    # Districts with no 2020 SBP row were created after 2020, so a 0 would be misleading. Leave them blank.
    density["status"] = density["branch_data_found"].map(
        {True: "matched", False: "no 2020 branch row (district created after 2020)"})
    density.loc[~density["branch_data_found"], "branches_total"] = pd.NA
    density["branches_per_100k"] = (density["branches_total"].astype("Float64") /
                                    density["population_2023"] * 100_000).round(2)
    density = density.sort_values("branches_per_100k", na_position="last")
    density.to_csv(CLEAN / "branch_density_district.csv", index=False)

    # Province view: only matched units, so population and branches cover the same places.
    matched = density[density["branch_data_found"]]
    prov = matched.groupby("province", as_index=False)[["population_2023", "branches_total"]].sum()
    prov["branches_per_100k"] = (prov["branches_total"] / prov["population_2023"] * 100_000).round(2)
    prov.to_csv(CLEAN / "branch_density_province.csv", index=False)

    print(f"PBS districts: {len(pop)} | SBP rows: {len(br)} | in scope (mapped): {int(br['in_scope'].sum())}")
    print(f"Analysis units: {len(density)} | matched: {int(density['branch_data_found'].sum())} | "
          f"left blank (no 2020 row): {int((~density['branch_data_found']).sum())}")
    print(f"Total branches in scope: {int(scoped['branches_total'].sum()):,} "
          f"of {int(br['branches_total'].sum()):,} in the SBP table")
    print(prov.to_string(index=False))


if __name__ == "__main__":
    build()
