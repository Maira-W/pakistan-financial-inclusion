"""The tables Power BI imports, all derived from the pipeline outputs so the report and the dashboard agree."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .. import config
from ..results import Results

COUNTRY_NAMES = {"PAK": "Pakistan", "IND": "India", "BGD": "Bangladesh", "LKA": "Sri Lanka"}
PROVINCE_CODES = {"Balochistan": "BA", "Islamabad": "ICT", "Khyber Pakhtunkhwa": "KP", "Punjab": "PB", "Sindh": "SD"}

# The measures a viewer can pick for the district bar chart (a disconnected table drives a SWITCH measure).
DISTRICT_METRICS = [
    "Branches per 100,000 people",
    "People per branch",
    "Rural branches per 100,000 rural people",
    "Expected branches",
    "Shortfall against expected (branches)",
]

SHORT_REASONS = {
    "Lack of trust in financial institutions": "No trust",
    "Financial services are too expensive": "Too costly",
    "Financial institutions are too far away": "Too far",
    "Lack of necessary documentation": "No papers",
    "Insufficient funds": "No money",
    "Someone in the family has an account": "Family has one",
    "Not enough money to use a mobile money account": "No money",
    "Mobile money products are too expensive": "Too costly",
    "Mobile money agents are too far away": "Agents far",
}

RULE_NAMES = {"equity": "Equity rule", "gap": "Model-gap rule", "women": "Women rule"}

TABLE_NOTES = {
    "districts": "One row per analysis unit: population, branches 2020 and 2024, expected branches, shortfall and flags. The fact table.",
    "provinces": "The five provinces and territories. Filters districts.",
    "district_types": "The four district types, with averages. Filters districts and sorts them by development.",
    "top_gaps": "The 10 districts furthest below the model's expectation.",
    "findex": "Global Findex indicators for Pakistan, India, Bangladesh and Sri Lanka, 2011 to 2024.",
    "segments": "Account ownership in Pakistan by group, 2021 and 2024.",
    "barriers": "Reasons for having no bank account or no mobile money account.",
    "scenario": "Planner outcomes by number of points added and placement rule.",
    "wallet": "Mobile wallet accounts and agents by region and quarter (irregular figures left blank).",
    "wallet_national": "Wallet totals by quarter: accounts, agents, deposits and the active shares.",
    "countries": "Account ownership, phones and income for every economy in the benchmark.",
    "headline": "One row of single numbers (Gini, shortfall, catch-up) read by cards.",
    "metric_choice": "The measures a slicer can pick on the District explorer page (a disconnected table).",
    "notes": "The text on the About page.",
}

NOTES = [
    ("Branches", "SBP register of scheduled bank and microfinance bank branches, 31 December 2024. A branch counts where it is, "
                 "not where its customers live, so cities that serve their surroundings look better served than they are."),
    ("Population", "PBS Census 2023. Districts are on their 2020 boundaries, so districts created after 2020 are merged "
                   "into the district they came from. Azad Jammu & Kashmir and Gilgit-Baltistan are not covered."),
    ("Account ownership", "World Bank Global Findex, 2011 to 2024. A survey of adults, so every figure carries sampling error "
                          "and the district view cannot be built from it."),
    ("Expected branches", "A negative binomial model of branches on population, urban share and a development index, "
                          "predicted without the district itself. It is a peer comparison, not a target."),
    ("Shortfall", "Expected minus actual branches. Positive means fewer than similar districts have. "
                  "Districts below expectation are flagged only when the chance of so few is under 10%."),
    ("Planner", "Equity rule: each new point goes where people per branch is highest. Model-gap rule: where the shortfall "
                "against the model is largest. Women rule: as equity, weighted to districts with a wide literacy gap. "
                "Results show who is reached, not what points cost, and branches are not agents or wallets."),
    ("Wallet statistics", "SBP branchless banking statistics, April-June 2024 to April-June 2026. Figures the SBP prints "
                          "that jump out of line with neighbouring quarters are left blank rather than plotted."),
    ("Income benchmark", "Account ownership against GDP per person (PPP) for the economies with both. "
                         "The expected value is a straight-line fit on the log of income."),
]


def _int(series: pd.Series) -> pd.Series:
    return series.round().astype("int64")


def provinces(r: Results) -> pd.DataFrame:
    names = sorted(r.units["province"].unique())
    return pd.DataFrame({"province": names, "province_code": [PROVINCE_CODES[n] for n in names]})


def district_types(r: Results) -> pd.DataFrame:
    profile = pd.DataFrame(r.summary["clusters"]["profile"])
    return pd.DataFrame({
        "district_type": profile["cluster"], "type_rank": profile["cluster_rank"], "districts": profile["units"],
        "population": _int(profile["population"]), "average_urban_share": profile["urban_share"],
        "average_development_index": profile["ses_index"], "average_female_literacy": profile["literacy_female"],
        "median_branches_per_100k": profile["branches_per_100k"], "average_rural_branch_share": profile["rural_branch_share"],
        "largest_districts": profile["largest_units"],
    }).sort_values("type_rank")


def districts(r: Results) -> pd.DataFrame:
    u = r.units
    national = u["branches_2024"].sum() / u["pop"].sum() * 1e5
    out = pd.DataFrame({
        "district": u["unit"], "province": u["province"], "district_type": u["cluster"], "type_rank": u["cluster_rank"],
        "population": _int(u["pop"]), "population_2017": _int(u["pop_2017"]),
        "urban_population": _int(u["pop_urban"]), "rural_population": _int(u["pop_rural"]),
        "urban_share": u["urban_share"], "development_index": u["ses_index"],
        "female_literacy": u["literacy_female"], "literacy_gap": u["literacy_gender_gap"],
        "banks_2020": u["banks_2020"], "banks_2024": u["banks_2024"], "microfinance_2024": u["mfb_2024"],
        "branches_2024": u["branches_2024"], "rural_branches_2024": u["rural_branches_2024"],
        "urban_branches_2024": u["urban_branches_2024"], "bank_branch_change": u["banks_change"],
        "branches_per_100k": u["branches_per_100k"], "people_per_branch": u["people_per_branch"],
        "expected_branches": u["expected_branches"], "expected_low": u["expected_low"], "expected_high": u["expected_high"],
        "shortfall": u["branch_gap"], "gap_ratio": u["gap_ratio"], "chance_of_this_few": u["p_below_expected"],
        "below_expected": u["below_expected"], "flagged_short": u["robust_shortfall"],
        "below_half_national": u["branches_per_100k"] < config.LOW_DENSITY_SHARE_OF_AVERAGE * national,
        "low_female_literacy": u["literacy_female"] < config.LOW_FEMALE_LITERACY,
    })
    return out.sort_values(["province", "district"]).reset_index(drop=True)


def top_gaps(r: Results, n: int = 10) -> pd.DataFrame:
    u = r.units.sort_values("branch_gap", ascending=False).head(n).reset_index(drop=True)
    return pd.DataFrame({
        "gap_rank": np.arange(1, len(u) + 1), "district": u["unit"], "province": u["province"],
        "district_type": u["cluster"], "population": _int(u["pop"]), "branches_2024": u["branches_2024"],
        "expected_branches": u["expected_branches"], "expected_low": u["expected_low"], "expected_high": u["expected_high"],
        "shortfall": u["branch_gap"], "chance_of_this_few": u["p_below_expected"], "flagged_short": u["robust_shortfall"],
    })


def findex(r: Results) -> pd.DataFrame:
    p = r.panel
    return pd.DataFrame({
        "country": p["country"], "country_name": p["country"].map(COUNTRY_NAMES), "indicator": p["indicator"],
        "label": p["label"], "group": p["group"], "year": p["year"].astype("int64"), "value": p["value"],
    }).sort_values(["indicator", "country", "year"]).reset_index(drop=True)


def segments(r: Results) -> pd.DataFrame:
    """Account ownership by group for the two most recent survey rounds, so the chart can compare them."""
    s = r.segments[r.segments["year"].isin([config.FINDEX_PREVIOUS_YEAR, config.FINDEX_YEAR])]
    return pd.DataFrame({"segment": s["segment"], "group": s["group"], "year": s["year"].astype("int64"),
                         "value": s["value"]}).reset_index(drop=True)


def barriers(r: Results) -> pd.DataFrame:
    bank = pd.DataFrame({"account_type": "Bank or similar account", "reason": r.barriers["reason"].map(SHORT_REASONS),
                         "reason_full": r.barriers["reason"], "share": r.barriers["share_of_unbanked"],
                         "base": "% of adults without an account", "derived": r.barriers["derived"]})
    mobile = pd.DataFrame({"account_type": "Mobile money account", "reason": r.mm_barriers["reason"].map(SHORT_REASONS),
                           "reason_full": r.mm_barriers["reason"], "share": r.mm_barriers["value"],
                           "base": "% of all adults aged 15+", "derived": False})
    out = pd.concat([bank, mobile], ignore_index=True)
    if out["reason"].isna().any():
        raise KeyError(f"No short label for: {out.loc[out['reason'].isna(), 'reason_full'].tolist()}")
    return out


def scenario(r: Results) -> pd.DataFrame:
    c = r.curve
    return pd.DataFrame({
        "points_added": c["points_requested"].astype("int64"), "rule_key": c["strategy"], "rule": c["strategy"].map(RULE_NAMES),
        "points_placed": c["points_placed"].astype("int64"), "national_density": c["national_density"],
        "districts_below_half": c["units_below_half"].astype("int64"),
        "population_below_half_pct": c["population_below_half_pct"], "gini": c["gini"],
        "worst_people_per_branch": c["worst_people_per_branch"],
        "share_to_low_female_literacy_pct": c["share_to_low_female_literacy_pct"],
    })


def wallet(r: Results) -> pd.DataFrame:
    """Regional wallet statistics. Figures that jump out of line with the quarters either side are left blank."""
    b = r.bb_regions
    bad_accounts = b["flag_accounts"]
    bad_share = b["flag_accounts"] | b["flag_female"]
    return pd.DataFrame({
        "region": b["region"], "quarter": b["quarter"], "quarter_label": b["label"],
        "accounts": b["accounts"].where(~bad_accounts), "agents": b["agents"],
        "adults_15plus": b["adults_15plus"],
        "accounts_per_100_adults": b["accounts_per_100_adults"].where(~bad_accounts),
        "agents_per_100k_adults": b["agents_per_100k_adults"],
        "female_share": b["female_share"].where(~bad_share),
        "figure_withheld": bad_accounts | b["flag_female"],
    })


def wallet_national(r: Results) -> pd.DataFrame:
    n = r.bb_national.sort_values("quarter").reset_index(drop=True)
    out = n.copy()
    out.insert(2, "quarter_index", np.arange(1, len(out) + 1))
    return out


def countries(r: Results) -> pd.DataFrame:
    c = r.cross.copy()
    south_asia = set(config.SOUTH_ASIA)
    c["highlight"] = np.where(c["country"] == "PAK", "Pakistan",
                              np.where(c["country"].isin(south_asia), "Other South Asia", "Other economies"))
    return c.rename(columns={"name": "country_name", "region": "world_region", "income": "income_group"})


def headline(r: Results) -> pd.DataFrame:
    h, ineq = r.headline, r.summary["inequality"]
    conv, model = r.summary["convergence"], r.summary["access_model"]
    return pd.DataFrame([{
        "gini_banks_2020": ineq["banks_2020"]["gini"], "gini_banks_2024": ineq["banks_2024"]["gini"],
        "gini_all_branches_2024": ineq["branches_2024"]["gini"],
        "net_new_banks": conv["net_new_banks"],
        "low_density_share_of_new_pct": conv["low_density_share_of_new"] * 100,
        "low_density_share_of_population_pct": conv["low_density_share_of_population"] * 100,
        "convergence_slope": conv["slope_initial_density"], "convergence_p_value": conv["p_value"],
        "total_shortfall": model["shortfall_total"], "shortfall_p05": model["shortfall_p05"],
        "shortfall_p95": model["shortfall_p95"], "districts_flagged": model["units_robust_shortfall"],
        "model_error_reduction_pct": model["mae_reduction_vs_baseline"] * 100,
        "development_index_variance_pct": h["ses_explained_variance"] * 100,
    }])


def metric_choice() -> pd.DataFrame:
    return pd.DataFrame({"metric": DISTRICT_METRICS})


def notes() -> pd.DataFrame:
    return pd.DataFrame(NOTES, columns=["topic", "note"])


def make_tables(r: Results) -> dict[str, pd.DataFrame]:
    """Table name -> data, in the order they appear in the model."""
    return {
        "districts": districts(r), "provinces": provinces(r), "district_types": district_types(r), "top_gaps": top_gaps(r),
        "findex": findex(r), "segments": segments(r), "barriers": barriers(r), "scenario": scenario(r),
        "wallet": wallet(r), "wallet_national": wallet_national(r), "countries": countries(r),
        "headline": headline(r), "metric_choice": metric_choice(), "notes": notes(),
    }
