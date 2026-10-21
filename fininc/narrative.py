"""Plain-English findings, written from the computed numbers so text and tables cannot drift apart."""

from __future__ import annotations

import pandas as pd

from . import config
from .results import Results
from .text import ordinal, rank_largest


def _seg(r: Results, segment: str, year: int) -> float:
    s = r.segments
    return float(s[(s["segment"] == segment) & (s["year"] == year)]["value"].iloc[0])


def findings(r: Results) -> list[dict]:
    """Eight findings, each tied to the dashboard tab where the evidence sits."""
    h = r.headline
    cc = r.summary["cross_country"]
    pak = cc["pakistan"]
    ineq = r.summary["inequality"]
    conv = r.summary["convergence"]
    model = r.summary["access_model"]
    scen = {row["strategy"]: row for row in r.summary["scenario_default"]}
    barriers = r.barriers.set_index("indicator")["share_of_unbanked"]
    bb = r.bb_regions
    last = bb["quarter"].max()
    first = bb["quarter"].min()
    wallet_last = bb[bb["quarter"] == last].set_index("region")
    nat = r.bb_national.set_index("quarter")

    return [
        {"id": "income", "tab": "overview", "title": "Far fewer adults have an account than Pakistan's income predicts",
         "text": f"{pak['account']:.0f}% of adults have an account: the {ordinal(cc['rank_lowest_account'][0])} lowest of "
                 f"{cc['rank_lowest_account'][1]} economies, and {pak['shortfall_pts']:.0f} points below the "
                 f"{pak['expected']:.0f}% that its income would predict."},
        {"id": "left_out", "tab": "who", "title": "Gains since 2021 went to groups that were already included",
         "text": f"Men gained {_seg(r, 'Men', 2024) - _seg(r, 'Men', 2021):.0f} points and the richest 60% "
                 f"{_seg(r, 'Richest 60%', 2024) - _seg(r, 'Richest 60%', 2021):.0f}. Women fell "
                 f"{abs(_seg(r, 'Women', 2024) - _seg(r, 'Women', 2021)):.1f} points to {_seg(r, 'Women', 2024):.0f}% and the "
                 f"poorest 40% fell {abs(_seg(r, 'Poorest 40%', 2024) - _seg(r, 'Poorest 40%', 2021)):.0f} points "
                 f"to {_seg(r, 'Poorest 40%', 2024):.0f}%."},
        {"id": "phones", "tab": "who", "title": "The phone gap comes before the account gap",
         "text": f"{pak['phone_women']:.0f}% of women own a mobile phone against {pak['phone_men']:.0f}% of men: a "
                 f"{pak['phone_gap']:.0f}-point gap, the {rank_largest(cc['rank_largest_phone_gap'][0])} of "
                 f"{cc['rank_largest_phone_gap'][1]} economies. The account gap ({pak['account_gap']:.0f} points) is the "
                 f"{rank_largest(cc['rank_largest_account_gap'][0])}."},
        {"id": "barriers", "tab": "who", "title": "Money and cost matter more than distance",
         "text": f"Among adults without a bank account, {barriers['fin11d.s']:.0f}% say they lack the money and "
                 f"{barriers['fin11b.s']:.0f}% that services are too expensive; {barriers['fin11a.s']:.0f}% cite distance. "
                 f"Missing documents ({barriers['fin11c']:.0f}%, derived) and a lack of trust ({barriers['fin11f.s']:.0f}%) follow."},
        {"id": "rural", "tab": "where", "title": "Rural Pakistan has far fewer branches per person",
         "text": f"{h['rural_pop_share']:.0f}% of people live in rural areas but {h['rural_branch_share']:.0f}% of branches "
                 f"do: {h['rural_per_100k_rural']:.1f} per 100,000 rural residents against "
                 f"{h['urban_per_100k_urban']:.1f} for urban residents. Microfinance banks are more rural "
                 f"({h['mfb_rural_share']:.0f}% of their branches) than banks ({h['bank_rural_share']:.0f}%)."},
        {"id": "no_catch_up", "tab": "model", "title": "Four years of new branches did not reach the underserved",
         "text": f"Bank branches grew {h['banks_growth_pct']:.0f}% between 2020 and 2024, but the half of districts with "
                 f"the fewest branches in 2020 (home to {conv['low_density_share_of_population'] * 100:.0f}% of people) "
                 f"received {conv['low_density_share_of_new'] * 100:.0f}% of the {conv['net_new_banks']:,} net new branches. "
                 f"The Gini coefficient did not move ({ineq['banks_2020']['gini']:.3f} in 2020, {ineq['banks_2024']['gini']:.3f} in 2024)."},
        {"id": "digital", "tab": "digital", "title": "The digital layer is denser, and follows the same geography",
         "text": f"Wallet agents number {wallet_last.loc['Punjab (incl. Islamabad)', 'agents_per_100k_adults']:.0f} per 100,000 "
                 f"adults in Punjab (with Islamabad) and {wallet_last.loc['Balochistan', 'agents_per_100k_adults']:.0f} in "
                 f"Balochistan. Women hold {wallet_last.loc['Khyber Pakhtunkhwa', 'female_share']:.0f}% of wallet accounts in "
                 f"Khyber Pakhtunkhwa and {wallet_last.loc['Punjab (incl. Islamabad)', 'female_share']:.0f}% in Punjab. "
                 f"The agent network grew {(nat.loc[last, 'agents'] / nat.loc[first, 'agents'] - 1) * 100:.0f}% since "
                 f"{r.bb_national['label'].iloc[0]}, yet the share of agents that are active fell from "
                 f"{nat.loc[first, 'active_agent_share']:.0f}% to {nat.loc[last, 'active_agent_share']:.0f}%."},
        {"id": "planner", "tab": "planner", "title": "Where new points go decides who is reached",
         "text": f"{r.scenario['default_k']:,} new branches or agent points ({r.scenario['default_k'] / r.scenario['network_size'] * 100:.0f}% "
                 f"of the network) placed to even out people per branch would remove all {scen['before']['units_below_half']} "
                 f"low-density districts and cut the Gini from {scen['before']['gini']:.2f} to {scen['equity']['gini']:.2f}. "
                 f"Placed by the peer-adjusted model gap they would raise it to {scen['gap']['gini']:.2f}, because the largest gaps "
                 f"are in big cities. The model flags {model['units_robust_shortfall']} districts as short of branches for their size; "
                 f"chance alone would flag about {config.GAP_SIGNIFICANCE * h['units']:.0f}, so treat them as a review list."},
    ]


def key_numbers(r: Results) -> pd.DataFrame:
    """Every number quoted in the README and memo, in one table, so documents can be checked against it."""
    h = r.headline
    cc = r.summary["cross_country"]
    pak = cc["pakistan"]
    ineq = r.summary["inequality"]
    conv = r.summary["convergence"]
    model = r.summary["access_model"]
    rows = [
        ("Adults with an account, 2024 (%)", pak["account"]),
        ("Account ownership expected at Pakistan's income (%)", pak["expected"]),
        ("Shortfall against income (points)", pak["shortfall_pts"]),
        ("Women with an account (%)", pak["account_women"]),
        ("Men with an account (%)", pak["account_men"]),
        ("Account gender gap (points)", pak["account_gap"]),
        ("Women who own a phone (%)", pak["phone_women"]),
        ("Men who own a phone (%)", pak["phone_men"]),
        ("Phone gender gap (points)", pak["phone_gap"]),
        ("Rank, lowest account ownership", cc["rank_lowest_account"][0]),
        ("Rank, largest account gender gap", cc["rank_largest_account_gap"][0]),
        ("Rank, largest phone gender gap", cc["rank_largest_phone_gap"][0]),
        ("Economies compared", cc["n_economies"]),
        ("Districts (analysis units)", h["units"]),
        ("Bank branches 2020", h["banks_2020"]),
        ("Bank branches 2024", h["banks_2024"]),
        ("Microfinance and DFI branches 2024", h["mfb_2024"]),
        ("Bank branch growth 2020-24 (%)", h["banks_growth_pct"]),
        ("Branches per 100,000 people", h["branches_per_100k"]),
        ("Bank branches per 100,000 adults", h["banks_per_100k_adults"]),
        ("Rural share of branches (%)", h["rural_branch_share"]),
        ("Rural share of population (%)", h["rural_pop_share"]),
        ("Branches per 100,000 rural residents", h["rural_per_100k_rural"]),
        ("Branches per 100,000 urban residents", h["urban_per_100k_urban"]),
        ("Districts below half the national average", h["units_below_half_average"]),
        ("Population in those districts (%)", h["population_below_half_average"] * 100),
        ("Gini of bank branches 2020", ineq["banks_2020"]["gini"]),
        ("Gini of bank branches 2024", ineq["banks_2024"]["gini"]),
        ("Gini of all branches 2024", ineq["branches_2024"]["gini"]),
        ("Share of net new bank branches reaching low-density districts (%)", conv["low_density_share_of_new"] * 100),
        ("Share of population in low-density districts (%)", conv["low_density_share_of_population"] * 100),
        ("Convergence slope", conv["slope_initial_density"]),
        ("Convergence p-value", conv["p_value"]),
        ("Districts flagged below model expectation", model["units_robust_shortfall"]),
        ("Total shortfall against the model (branches)", model["shortfall_total"]),
        ("Shortfall, 5th percentile", model["shortfall_p05"]),
        ("Shortfall, 95th percentile", model["shortfall_p95"]),
        ("Model error reduction vs proportional rule (%)", model["mae_reduction_vs_baseline"] * 100),
    ]
    return pd.DataFrame(rows, columns=["measure", "value"])
