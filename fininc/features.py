"""Assemble the analysis tables.

build_unit_table() joins the census (2023), the SBP branch data (2020 and 2024) and the model-ready features,
one row per analysis unit. province_table() and bb_region_table() roll the results up to provinces and to the
regions used in the SBP branchless banking statistics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from . import config
from . import units as U
from .loaders import census, sbp_bb, sbp_branches

REGISTER_PROVINCE = {
    "Punjab": "Punjab", "Sindh": "Sindh", "Khyber Pakhtunkhwa": "Khyber Pakhtunkhwa", "FATA": "Khyber Pakhtunkhwa",
    "Balochistan": "Balochistan", "Islamabad": "Islamabad",
}
SES_COLUMNS = ["literacy", "literacy_female", "pakka_share", "electricity_share", "water_improved_share",
               "flush_toilet_share", "clean_cooking_share"]
CENSUS_YEARS_BETWEEN = 6   # March 2017 to March 2023
WALLET_ACCOUNT_JUMP_PCT = 25.0    # accounts more than this far from the average of the quarters either side
WALLET_FEMALE_JUMP_PTS = 4.0      # female share more than this many points from the quarters either side


def _share(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return 100.0 * numerator / denominator.replace(0, np.nan)


def _flag_jumps(values: pd.Series, threshold: float, relative: bool) -> pd.Series:
    """Flag points that sit far from the average of the quarters either side, worst first.

    After a point is flagged it is set aside, so one bad quarter does not make its good neighbours look bad.
    relative=True measures the distance in percent of the neighbours' average, False in the series' own units.
    """
    work = values.astype(float).copy()
    flagged = pd.Series(False, index=values.index)
    while True:
        neighbours = (work.ffill().shift(1) + work.bfill().shift(-1)) / 2
        distance = ((work / neighbours - 1) * 100 if relative else work - neighbours).abs()
        if distance.isna().all() or distance.max() <= threshold:
            return flagged
        worst = distance.idxmax()
        flagged[worst] = True
        work[worst] = np.nan


def _census_by_unit(districts: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    work = districts.copy()
    work["unit"] = work["district"].map(U.unit_for_census_district)
    count_cols = [c for c in work.columns if c not in ("district", "province", "unit", "household_size")]
    agg = work.groupby("unit")[count_cols].sum(numeric_only=True)
    out = units.set_index("unit").join(agg).reset_index()

    out["density_per_sqkm"] = out["pop"] / out["area_sqkm"]
    out["urban_share"] = _share(out["pop_urban"], out["pop"])
    out["pop_growth_pct_pa"] = ((out["pop"] / out["pop_2017"]) ** (1 / CENSUS_YEARS_BETWEEN) - 1) * 100
    out["under15_share"] = _share(out["age_under15"], out["age_all"])
    out["working_age_share"] = _share(out["age_15_64"], out["age_all"])
    out["adults_15plus"] = out["pop"] * (1 - out["under15_share"] / 100)
    out["literacy"] = _share(out["lit10"], out["pop10"])
    out["literacy_female"] = _share(out["lit10_f"], out["pop10_f"])
    out["literacy_male"] = _share(out["lit10_m"], out["pop10_m"])
    out["literacy_gender_gap"] = out["literacy_male"] - out["literacy_female"]
    out["never_attended_school_share"] = _share(out["never_school"], out["pop5"])
    out["pakka_share"] = _share(out["hh_pakka"], out["hh_housing_total"])
    out["electricity_share"] = _share(out["hh_electricity"], out["hh_total"])
    out["clean_cooking_share"] = _share(out["hh_gas_or_lpg"], out["hh_total"])
    out["water_improved_share"] = _share(out["hh_water_improved"], out["hh_total"])
    out["flush_toilet_share"] = _share(out["hh_flush_toilet"], out["hh_total"])
    out["home_owned_share"] = _share(out["hh_owned"], out["hh_total"])
    out["female_owner_share"] = _share(out["owner_female"], out["owner_female"] + out["owner_male"])
    return out


def add_ses_index(table: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Socio-economic index: first principal component of literacy and household-service indicators.

    The sign is set so that a higher score means more development. Scores are standardised to mean 0, sd 1.
    """
    scaled = StandardScaler().fit_transform(table[SES_COLUMNS])
    pca = PCA(n_components=1, random_state=config.SEED).fit(scaled)
    score = pca.transform(scaled)[:, 0]
    if np.corrcoef(score, table["literacy"])[0, 1] < 0:
        score = -score
    table = table.copy()
    table["ses_index"] = (score - score.mean()) / score.std(ddof=0)
    loadings = pca.components_[0] * (1 if np.corrcoef(pca.transform(scaled)[:, 0], table["literacy"])[0, 1] > 0 else -1)
    info = {"explained_variance": float(pca.explained_variance_ratio_[0]),
            "loadings": {c: float(v) for c, v in zip(SES_COLUMNS, loadings)}}
    return table, info


def _resolve_register(register: pd.DataFrame, resolver: U.UnitResolver) -> pd.DataFrame:
    register = register.copy()
    pairs = register[["district_reg", "tehsil"]].drop_duplicates()
    lookup = {(d, str(t)): resolver.resolve(d, str(t)) for d, t in pairs.itertuples(index=False)}
    register["unit"] = [lookup[(d, str(t))] for d, t in zip(register["district_reg"], register["tehsil"])]
    return register


def _province_mismatches(register: pd.DataFrame, units: pd.DataFrame) -> pd.DataFrame:
    """Branches whose typed province disagrees with the province of the district they are assigned to."""
    unit_province = units.set_index("unit")["province"]
    sub = register[register["unit"].notna()].copy()
    sub["unit_province"] = sub["unit"].map(unit_province)
    sub["reg_province"] = sub["province_reg"].map(REGISTER_PROVINCE)
    bad = sub[sub["unit_province"] != sub["reg_province"]]
    return (bad.groupby(["district_reg", "province_reg", "unit", "unit_province"]).size()
               .reset_index(name="branches"))


def build_unit_table() -> tuple[pd.DataFrame, dict]:
    """One row per analysis unit, plus a dictionary of data-quality facts for the documentation."""
    districts, census_notes = census.load_districts()
    official = census.check_against_official(districts)
    if (official[["diff_2023", "diff_2017"]] != 0).any().any():
        raise ValueError(f"District populations do not match the official provincial totals:\n{official}")

    units = U.build_units(districts)
    resolver = U.UnitResolver(units)
    table = _census_by_unit(districts, units)
    table, ses_info = add_ses_index(table)

    # --- SBP December 2020 baseline -------------------------------------------------------------------
    df20, total20 = sbp_branches.load_2020_districts()
    df20["unit"] = df20["sbp_name"].map(resolver.resolve)
    in_scope20 = df20[df20["unit"].notna()]
    base = in_scope20.groupby("unit")[["branches", "islamic"]].sum().rename(
        columns={"branches": "banks_2020", "islamic": "islamic_banks_2020"})
    table = table.merge(base, left_on="unit", right_index=True, how="left")
    table[["banks_2020", "islamic_banks_2020"]] = table[["banks_2020", "islamic_banks_2020"]].fillna(0).astype(int)

    # --- SBP December 2024 register -------------------------------------------------------------------
    register = _resolve_register(sbp_branches.load_register(), resolver)
    mismatches = _province_mismatches(register, units)
    inside = register[register["unit"].notna()]
    banks, mfb = inside[inside["kind"] == "Bank"], inside[inside["kind"] == "MFB/DFI"]

    def count(frame: pd.DataFrame, mask=None) -> pd.Series:
        frame = frame if mask is None else frame[mask]
        return frame.groupby("unit").size()

    shares = banks.groupby(["unit", "bank"]).size().rename("n").reset_index()
    shares["share"] = shares["n"] / shares.groupby("unit")["n"].transform("sum")
    bank_stats = shares.groupby("unit").agg(top_bank_share=("share", "max"), bank_hhi=("share", lambda s: (s ** 2).sum()))

    agg = pd.DataFrame({
        "banks_2024": count(banks), "mfb_2024": count(mfb),
        "rural_banks_2024": count(banks, banks["rural"]), "rural_mfb_2024": count(mfb, mfb["rural"]),
        "islamic_banks_2024": count(banks, banks["islamic"]),
        "n_banks": banks.groupby("unit")["bank"].nunique(), "n_mfbs": mfb.groupby("unit")["bank"].nunique(),
    }).join(bank_stats)
    table = table.merge(agg, left_on="unit", right_index=True, how="left")
    zero_cols = ["banks_2024", "mfb_2024", "rural_banks_2024", "rural_mfb_2024", "islamic_banks_2024", "n_banks", "n_mfbs"]
    table[zero_cols] = table[zero_cols].fillna(0).astype(int)

    # --- derived access measures ----------------------------------------------------------------------
    table["branches_2024"] = table["banks_2024"] + table["mfb_2024"]
    table["rural_branches_2024"] = table["rural_banks_2024"] + table["rural_mfb_2024"]
    table["urban_branches_2024"] = table["branches_2024"] - table["rural_branches_2024"]
    table["branches_per_100k"] = table["branches_2024"] / table["pop"] * 1e5
    table["banks_per_100k"] = table["banks_2024"] / table["pop"] * 1e5
    table["mfb_per_100k"] = table["mfb_2024"] / table["pop"] * 1e5
    table["branches_per_100k_adults"] = table["branches_2024"] / table["adults_15plus"] * 1e5
    table["rural_branches_per_100k_rural"] = table["rural_branches_2024"] / table["pop_rural"].replace(0, np.nan) * 1e5
    table["urban_branches_per_100k_urban"] = table["urban_branches_2024"] / table["pop_urban"].replace(0, np.nan) * 1e5
    table["rural_branch_share"] = _share(table["rural_branches_2024"], table["branches_2024"])
    table["rural_pop_share"] = _share(table["pop_rural"], table["pop"])
    table["mfb_share"] = _share(table["mfb_2024"], table["branches_2024"])
    table["islamic_share"] = _share(table["islamic_banks_2024"], table["banks_2024"])

    table["density_2020"] = table["banks_2020"] / table["pop_2017"] * 1e5
    table["density_2024_banks"] = table["banks_2024"] / table["pop"] * 1e5
    table["density_change"] = table["density_2024_banks"] - table["density_2020"]
    table["banks_change"] = table["banks_2024"] - table["banks_2020"]
    table["banks_growth_pct"] = _share(table["banks_change"], table["banks_2020"])

    table = table.sort_values("unit").reset_index(drop=True)

    quality = {
        "census_notes": census_notes,
        "census_official_check": official.to_dict(orient="records"),
        "units": int(len(table)),
        "ses_index": ses_info,
        "sbp_2020": {"districts": int(len(df20)), "grand_total": int(total20),
                     "in_scope": int(in_scope20["branches"].sum()),
                     "outside_coverage": int(df20[df20["unit"].isna()]["branches"].sum()),
                     "outside_districts": int(df20["unit"].isna().sum())},
        "register_2024": {"rows": int(len(register)), "banks": int((register["kind"] == "Bank").sum()),
                          "mfb_dfi": int((register["kind"] == "MFB/DFI").sum()),
                          "in_scope": int(len(inside)), "outside_coverage": int(register["unit"].isna().sum()),
                          "province_mismatches": mismatches.to_dict(orient="records")},
    }
    return table, quality


# ---------------------------------------------------------------------------
# Province roll-up
# ---------------------------------------------------------------------------
SUM_COLUMNS = ["pop", "pop_urban", "pop_rural", "pop_2017", "area_sqkm", "adults_15plus", "banks_2020",
               "banks_2024", "mfb_2024", "rural_banks_2024", "rural_mfb_2024", "islamic_banks_2024"]


def province_table(units: pd.DataFrame) -> pd.DataFrame:
    prov = units.groupby("province")[SUM_COLUMNS].sum()
    prov["units"] = units.groupby("province").size()
    prov["branches_2024"] = prov["banks_2024"] + prov["mfb_2024"]
    prov["rural_branches_2024"] = prov["rural_banks_2024"] + prov["rural_mfb_2024"]
    prov["urban_branches_2024"] = prov["branches_2024"] - prov["rural_branches_2024"]
    prov["urban_share"] = _share(prov["pop_urban"], prov["pop"])
    prov["branches_per_100k"] = prov["branches_2024"] / prov["pop"] * 1e5
    prov["banks_per_100k"] = prov["banks_2024"] / prov["pop"] * 1e5
    prov["mfb_per_100k"] = prov["mfb_2024"] / prov["pop"] * 1e5
    prov["rural_branches_per_100k_rural"] = prov["rural_branches_2024"] / prov["pop_rural"] * 1e5
    prov["urban_branches_per_100k_urban"] = prov["urban_branches_2024"] / prov["pop_urban"] * 1e5
    prov["rural_branch_share"] = _share(prov["rural_branches_2024"], prov["branches_2024"])
    prov["density_2020"] = prov["banks_2020"] / prov["pop_2017"] * 1e5
    prov["density_2024_banks"] = prov["banks_2024"] / prov["pop"] * 1e5
    prov["banks_growth_pct"] = _share(prov["banks_2024"] - prov["banks_2020"], prov["banks_2020"])
    prov["mfb_share"] = _share(prov["mfb_2024"], prov["branches_2024"])
    return prov.reset_index()


# ---------------------------------------------------------------------------
# Branchless banking (mobile wallets and agents), by SBP reporting region
# ---------------------------------------------------------------------------
BB_REGION_OF_PROVINCE = {
    "Punjab": "Punjab (incl. Islamabad)", "Islamabad": "Punjab (incl. Islamabad)", "Sindh": "Sindh",
    "Khyber Pakhtunkhwa": "Khyber Pakhtunkhwa", "Balochistan": "Balochistan",
}
BB_NAME_OF_REGION = {"Punjab (Including ISB)": "Punjab (incl. Islamabad)"}


def bb_region_table(units: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Wallet accounts and agents by region and quarter, scaled by the 2023 census population.

    Returns (regions_by_quarter, national_by_quarter). Azad Kashmir and Gilgit-Baltistan are kept without
    per-capita measures because the census district tables do not cover them.
    """
    national, provinces = sbp_bb.load_all()
    provinces = provinces.copy()
    provinces["region"] = provinces["province"].replace(BB_NAME_OF_REGION)

    pop = units.assign(region=units["province"].map(BB_REGION_OF_PROVINCE)).groupby("region")[["pop", "adults_15plus"]].sum()
    out = provinces.merge(pop, left_on="region", right_index=True, how="left")
    out["accounts_per_100_adults"] = out["accounts"] / out["adults_15plus"] * 100
    out["agents_per_100k_adults"] = out["agents"] / out["adults_15plus"] * 1e5
    out["female_share"] = _share(out["accounts_female"], out["accounts_female"] + out["accounts_male"])
    out["transactions_per_account"] = out["transactions"] / out["accounts"]

    # Some quarters in the published tables are out of line with the quarters on either side (for example
    # Balochistan in Oct-Dec 2024). The provinces still add up to the national total, so the split between
    # provinces is what is irregular. Flag those points so charts can leave them out.
    out = out.sort_values(["region", "quarter"]).reset_index(drop=True)
    by_region = out.groupby("region")
    neighbour_accounts = (by_region["accounts"].shift(1) + by_region["accounts"].shift(-1)) / 2
    out["accounts_vs_neighbours_pct"] = (out["accounts"] / neighbour_accounts - 1) * 100
    out["flag_accounts"] = by_region["accounts"].transform(
        lambda s: _flag_jumps(s, WALLET_ACCOUNT_JUMP_PCT, relative=True))
    out["flag_female"] = by_region["female_share"].transform(
        lambda s: _flag_jumps(s, WALLET_FEMALE_JUMP_PTS, relative=False))
    national = national.copy()
    national["active_account_share"] = _share(national["active_accounts"], national["accounts"])
    national["active_agent_share"] = _share(national["active_agents"], national["agents"])
    return out, national
