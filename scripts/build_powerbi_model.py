"""Prepare the tables that Power BI Desktop imports.

Reads data/clean/ and writes three flat tables to powerbi/data/:
  - districts.csv   one row per analysis unit, with population, branches and flags
  - provinces.csv   one row per province
  - findex.csv      account ownership by country, year and measure

Power BI relates districts[province] to provinces[province]. Measures are written in
powerbi/measures.dax, so the tables only carry values that are fixed by the data.

Run from the project root, after scripts/build_clean_data.py:
  python scripts/build_powerbi_model.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "powerbi" / "data"


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    density = pd.read_csv(CLEAN / "branch_density_district.csv")
    province = pd.read_csv(CLEAN / "branch_density_province.csv")
    findex = pd.read_csv(CLEAN / "findex_account_ownership.csv")

    # National density uses matched units only, so it matches the README and memo.
    matched = density[density["branch_data_found"]]
    national = matched["branches_total"].sum() / matched["population_2023"].sum() * 100_000
    half = national / 2

    districts = pd.DataFrame({
        "district": density["unit"].str.title(),
        "province": density["province"].str.title(),
        "province_key": density["province"],
        "is_combined_unit": density["unit"].str.contains(r"\(combined\)", regex=True),
        "population_2023": density["population_2023"],
        "branches_total": density["branches_total"],
        "branches_per_100k": density["branches_per_100k"],
        "has_branch_data": density["branch_data_found"],
    })
    districts["status"] = density["status"].str.replace(
        "no 2020 branch row (district created after 2020)", "Created after 2020", regex=False
    ).replace({"matched": "Matched"})
    districts["below_half_national_avg"] = (districts["has_branch_data"]) & (districts["branches_per_100k"] < half)
    districts["national_branches_per_100k"] = round(national, 2)
    districts = districts.sort_values(["province", "district"])
    districts.to_csv(OUT / "districts.csv", index=False)

    provinces = pd.DataFrame({
        "province": province["province"].str.title(),
        "province_key": province["province"],
        "population_2023": province["population_2023"],
        "branches_total": province["branches_total"],
        "branches_per_100k": province["branches_per_100k"],
    })
    provinces.to_csv(OUT / "provinces.csv", index=False)

    findex_out = findex.assign(
        country_year=findex["country"] + " " + findex["year"].astype(str),
        measure_label=findex["measure"].map({"total": "All adults", "male": "Men", "female": "Women"}),
    )
    findex_out.to_csv(OUT / "findex.csv", index=False)

    print(f"districts.csv: {len(districts)} rows | matched: {int(districts['has_branch_data'].sum())} "
          f"| below half national avg: {int(districts['below_half_national_avg'].sum())}")
    print(f"provinces.csv: {len(provinces)} rows | findex.csv: {len(findex_out)} rows")
    print(f"National density used: {national:.2f} per 100k (half = {half:.2f})")


if __name__ == "__main__":
    build()
