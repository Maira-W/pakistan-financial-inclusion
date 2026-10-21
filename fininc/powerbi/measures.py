"""DAX measures for the Power BI report.

This list is the single source: model.py writes it into the semantic model and measures_text() writes
powerbi/measures.dax so the DAX can be read without opening Power BI.

Two rules learned the hard way. Measures live in a table called _Measures (the name "Measures" is rejected), and a
year-filtered measure must keep the year in a VAR: filtering a column by a measure inside CALCULATE makes the
measure invalid.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass


@dataclass(frozen=True)
class Measure:
    name: str
    folder: str
    fmt: str | None
    dax: str


PCT = '0.0"%"'          # values already in percent (12.3 means 12.3%)
FRACTION = "0.0%"       # values stored as fractions (0.123 means 12.3%)
PTS = '0.0" pts"'
WHOLE = "#,0"
ONE = "#,0.0"
TWO = "0.00"
THREE = "0.000"

M = Measure

MEASURES: list[Measure] = [
    # ------------------------------------------------------------------ Helpers
    M("Selected Year", "Helpers", "0", "SELECTEDVALUE ( findex[year], MAX ( findex[year] ) )"),

    # ------------------------------------------------------------------ Account ownership (Global Findex)
    M("Account Ownership %", "Account ownership", PCT, """
CALCULATE ( AVERAGE ( findex[value] ), findex[indicator] = "account.t.d" )"""),
    M("Pakistan Account Ownership %", "Account ownership", PCT, """
VAR y = [Selected Year]
RETURN
    CALCULATE (
        AVERAGE ( findex[value] ),
        findex[country] = "PAK",
        findex[indicator] = "account.t.d",
        findex[year] = y
    )"""),
    M("Pakistan Women %", "Account ownership", PCT, """
VAR y = [Selected Year]
RETURN
    CALCULATE (
        AVERAGE ( findex[value] ),
        findex[country] = "PAK",
        findex[indicator] = "account.t.d.1",
        findex[year] = y
    )"""),
    M("Pakistan Men %", "Account ownership", PCT, """
VAR y = [Selected Year]
RETURN
    CALCULATE (
        AVERAGE ( findex[value] ),
        findex[country] = "PAK",
        findex[indicator] = "account.t.d.2",
        findex[year] = y
    )"""),
    M("Account Gender Gap (pts)", "Account ownership", PTS, "[Pakistan Men %] - [Pakistan Women %]"),
    M("Segment Account Ownership %", "Account ownership", PCT, "AVERAGE ( segments[value] )"),
    M("Bank Barrier Share %", "Account ownership", PCT, """
CALCULATE ( AVERAGE ( barriers[share] ), barriers[account_type] = "Bank or similar account" )"""),
    M("Mobile Money Barrier Share %", "Account ownership", PCT, """
CALCULATE ( AVERAGE ( barriers[share] ), barriers[account_type] = "Mobile money account" )"""),
    M("Pakistan Women Phone Ownership %", "Account ownership", PCT, """
CALCULATE ( AVERAGE ( countries[phone_women] ), countries[country] = "PAK" )"""),
    M("Pakistan Men Phone Ownership %", "Account ownership", PCT, """
CALCULATE ( AVERAGE ( countries[phone_men] ), countries[country] = "PAK" )"""),
    M("Phone Gender Gap (pts)", "Account ownership", PTS, "[Pakistan Men Phone Ownership %] - [Pakistan Women Phone Ownership %]"),

    # ------------------------------------------------------------------ Branches and population
    M("Total Branches", "Branches", WHOLE, "SUM ( districts[branches_2024] )"),
    M("Bank Branches", "Branches", WHOLE, "SUM ( districts[banks_2024] )"),
    M("Microfinance Branches", "Branches", WHOLE, "SUM ( districts[microfinance_2024] )"),
    M("Rural Branches", "Branches", WHOLE, "SUM ( districts[rural_branches_2024] )"),
    M("Population", "Branches", WHOLE, "SUM ( districts[population] )"),
    M("District Count", "Branches", "0", "COUNTROWS ( districts )"),
    M("Branches per 100k", "Branches", TWO, "DIVIDE ( [Total Branches], [Population] ) * 100000"),
    M("National Branches per 100k", "Branches", TWO, """
DIVIDE (
    CALCULATE ( [Total Branches], ALL ( districts ) ),
    CALCULATE ( [Population], ALL ( districts ) )
) * 100000"""),
    M("Density vs National (x)", "Branches", '0.00"x"', "DIVIDE ( [Branches per 100k], [National Branches per 100k] )"),
    M("People per Branch", "Branches", WHOLE, "DIVIDE ( [Population], [Total Branches] )"),
    M("Rural Branch Share %", "Branches", PCT, "DIVIDE ( [Rural Branches], [Total Branches] ) * 100"),
    M("Rural Population Share %", "Branches", PCT, "DIVIDE ( SUM ( districts[rural_population] ), [Population] ) * 100"),
    M("Rural Branches per 100k Rural People", "Branches", TWO, """
DIVIDE ( [Rural Branches], SUM ( districts[rural_population] ) ) * 100000"""),
    M("Urban Branches per 100k Urban People", "Branches", TWO, """
DIVIDE ( SUM ( districts[urban_branches_2024] ), SUM ( districts[urban_population] ) ) * 100000"""),
    M("Bank Branches per 100k 2020", "Branches", TWO, """
DIVIDE ( SUM ( districts[banks_2020] ), SUM ( districts[population_2017] ) ) * 100000"""),
    M("Bank Branches per 100k 2024", "Branches", TWO, "DIVIDE ( [Bank Branches], [Population] ) * 100000"),
    M("Bank Branch Growth 2020-24 %", "Branches", PCT, """
DIVIDE (
    SUM ( districts[banks_2024] ) - SUM ( districts[banks_2020] ),
    SUM ( districts[banks_2020] )
) * 100"""),
    M("Districts Below Half National Avg", "Branches", "0", """
VAR cutoff = [National Branches per 100k] / 2
RETURN
    COUNTROWS (
        FILTER ( districts, DIVIDE ( districts[branches_2024], districts[population] ) * 100000 < cutoff )
    )"""),
    M("Population Share in Low-Density Districts %", "Branches", FRACTION, """
VAR cutoff = [National Branches per 100k] / 2
RETURN
    DIVIDE (
        SUMX (
            FILTER ( districts, DIVIDE ( districts[branches_2024], districts[population] ) * 100000 < cutoff ),
            districts[population]
        ),
        CALCULATE ( [Population], ALL ( districts ) )
    )"""),
    M("Selected District Metric", "Branches", TWO, """
SWITCH (
    SELECTEDVALUE ( metric_choice[metric], "Branches per 100,000 people" ),
    "Branches per 100,000 people", [Branches per 100k],
    "People per branch", [People per Branch],
    "Rural branches per 100,000 rural people", [Rural Branches per 100k Rural People],
    "Expected branches", [Expected Branches],
    "Shortfall against expected (branches)", [Total Shortfall],
    BLANK ()
)"""),

    # ------------------------------------------------------------------ Access-gap model and inequality
    M("Expected Branches", "Access gap model", WHOLE, "SUM ( districts[expected_branches] )"),
    M("Expected Branches per 100k", "Access gap model", TWO, "DIVIDE ( [Expected Branches], [Population] ) * 100000"),
    M("Total Shortfall", "Access gap model", WHOLE, "SUMX ( districts, MAX ( districts[shortfall], 0 ) )"),
    M("Top Gap Shortfall", "Access gap model", WHOLE, "SUM ( top_gaps[shortfall] )"),
    M("Districts Below Expected", "Access gap model", "0", """
CALCULATE ( COUNTROWS ( districts ), districts[below_expected] = TRUE () )"""),
    M("Districts Flagged Below Expected", "Access gap model", "0", """
CALCULATE ( COUNTROWS ( districts ), districts[flagged_short] = TRUE () )"""),
    M("Model Shortfall (branches)", "Access gap model", WHOLE, "MAX ( headline[total_shortfall] )"),
    M("Shortfall 5th Percentile", "Access gap model", WHOLE, "MAX ( headline[shortfall_p05] )"),
    M("Shortfall 95th Percentile", "Access gap model", WHOLE, "MAX ( headline[shortfall_p95] )"),
    M("Model Error Reduction %", "Access gap model", PCT, "MAX ( headline[model_error_reduction_pct] )"),
    M("Gini of Bank Branches 2020", "Access gap model", THREE, "MAX ( headline[gini_banks_2020] )"),
    M("Gini of Bank Branches 2024", "Access gap model", THREE, "MAX ( headline[gini_banks_2024] )"),
    M("New Branches Reaching Low-Density Half %", "Access gap model", PCT, "MAX ( headline[low_density_share_of_new_pct] )"),
    M("Population in Low-Density Half %", "Access gap model", PCT, "MAX ( headline[low_density_share_of_population_pct] )"),

    # ------------------------------------------------------------------ Planner
    M("Scenario Gini", "Planner", THREE, "AVERAGE ( scenario[gini] )"),
    M("Scenario Population Below Half %", "Planner", PCT, "AVERAGE ( scenario[population_below_half_pct] )"),
    M("Scenario Districts Below Half", "Planner", "0", "AVERAGE ( scenario[districts_below_half] )"),
    M("Scenario Worst People per Branch", "Planner", WHOLE, "AVERAGE ( scenario[worst_people_per_branch] )"),
    M("Scenario Share to Low Female Literacy %", "Planner", PCT, "AVERAGE ( scenario[share_to_low_female_literacy_pct] )"),
    M("Gini Today", "Planner", THREE, """
CALCULATE ( AVERAGE ( scenario[gini] ), scenario[points_added] = 0, scenario[rule_key] = "equity" )"""),
    M("Gini After 1000 Points (Even People per Branch)", "Planner", THREE, """
CALCULATE ( AVERAGE ( scenario[gini] ), scenario[points_added] = 1000, scenario[rule_key] = "equity" )"""),
    M("Gini After 1000 Points (Model Gap First)", "Planner", THREE, """
CALCULATE ( AVERAGE ( scenario[gini] ), scenario[points_added] = 1000, scenario[rule_key] = "gap" )"""),
    M("Districts Below Half Today", "Planner", "0", """
CALCULATE ( AVERAGE ( scenario[districts_below_half] ), scenario[points_added] = 0, scenario[rule_key] = "equity" )"""),
    M("Districts Below Half After 1000 Points (Even People per Branch)", "Planner", "0", """
CALCULATE ( AVERAGE ( scenario[districts_below_half] ), scenario[points_added] = 1000, scenario[rule_key] = "equity" )"""),

    # ------------------------------------------------------------------ Digital layer (branchless banking)
    M("Wallet Agents per 100k Adults", "Digital layer", "0", "AVERAGE ( wallet[agents_per_100k_adults] )"),
    M("Wallet Accounts per 100 Adults", "Digital layer", "0", "AVERAGE ( wallet[accounts_per_100_adults] )"),
    M("Wallet Women Share %", "Digital layer", PCT, "AVERAGE ( wallet[female_share] )"),
    M("Active Agent Share %", "Digital layer", PCT, "AVERAGE ( wallet_national[active_agent_share] )"),
    M("Active Account Share %", "Digital layer", PCT, "AVERAGE ( wallet_national[active_account_share] )"),
    M("Latest Wallet Accounts (million)", "Digital layer", ONE, """
VAR q = MAX ( wallet_national[quarter_index] )
RETURN
    DIVIDE ( CALCULATE ( SUM ( wallet_national[accounts] ), wallet_national[quarter_index] = q ), 1000000 )"""),
    M("Latest Wallet Agents (thousand)", "Digital layer", WHOLE, """
VAR q = MAX ( wallet_national[quarter_index] )
RETURN
    DIVIDE ( CALCULATE ( SUM ( wallet_national[agents] ), wallet_national[quarter_index] = q ), 1000 )"""),
    M("Latest Active Agent Share %", "Digital layer", PCT, """
VAR q = MAX ( wallet_national[quarter_index] )
RETURN
    CALCULATE ( AVERAGE ( wallet_national[active_agent_share] ), wallet_national[quarter_index] = q )"""),
    M("First Active Agent Share %", "Digital layer", PCT, """
VAR q = MIN ( wallet_national[quarter_index] )
RETURN
    CALCULATE ( AVERAGE ( wallet_national[active_agent_share] ), wallet_national[quarter_index] = q )"""),
    M("Latest Wallet Deposits (PKR billion)", "Digital layer", WHOLE, """
VAR q = MAX ( wallet_national[quarter_index] )
RETURN
    DIVIDE ( CALCULATE ( SUM ( wallet_national[deposits_pkr_mn] ), wallet_national[quarter_index] = q ), 1000 )"""),

    # ------------------------------------------------------------------ Income benchmark
    M("Country GDP per Person", "Income benchmark", WHOLE, "AVERAGE ( countries[gdp_pc_ppp] )"),
    M("Country Account Ownership %", "Income benchmark", PCT, "AVERAGE ( countries[account] )"),
    M("Expected Account Ownership %", "Income benchmark", PCT, "AVERAGE ( countries[expected_account] )"),
    M("Pakistan Expected Account Ownership %", "Income benchmark", PCT, """
CALCULATE ( AVERAGE ( countries[expected_account] ), countries[country] = "PAK" )"""),
    M("Pakistan Account Shortfall vs Income (pts)", "Income benchmark", PTS, """
CALCULATE (
    AVERAGE ( countries[expected_account] ) - AVERAGE ( countries[account] ),
    countries[country] = "PAK"
)"""),
    M("Economies Compared", "Income benchmark", "0", "COUNTROWS ( ALL ( countries ) )"),
    M("Pakistan Rank From Lowest", "Income benchmark", "0", """
VAR pak = CALCULATE ( AVERAGE ( countries[account] ), countries[country] = "PAK" )
RETURN
    COUNTROWS ( FILTER ( ALL ( countries ), countries[account] <= pak ) )"""),
]


# One line for each measure a report reader is likely to hover over. Shown as the measure description in Power BI.
DESCRIPTIONS = {
    "Selected Year": "The year chosen in a slicer or on an axis; the latest survey year when nothing is chosen.",
    "Pakistan Account Ownership %": "Adults with an account at a bank, similar institution or mobile money provider (Global Findex).",
    "Pakistan Women %": "Women with an account (Global Findex).",
    "Pakistan Men %": "Men with an account (Global Findex).",
    "Account Gender Gap (pts)": "Men minus women with an account, in percentage points.",
    "Phone Gender Gap (pts)": "Men minus women who own a mobile phone, in percentage points (Global Findex 2024).",
    "Total Branches": "Bank and microfinance bank branches in the SBP register at 31 December 2024.",
    "Branches per 100k": "Branches per 100,000 people (2023 census population).",
    "National Branches per 100k": "Branches per 100,000 people across all 120 districts, whatever is selected.",
    "Districts Below Half National Avg": "Districts with fewer than half the national average of branches per person.",
    "Population Share in Low-Density Districts %": "Share of the national population living in those districts.",
    "Selected District Metric": "The measure chosen in the Measure slicer on the District explorer page.",
    "Expected Branches": "Branches a district would be expected to have given its size, urban share and development (leave-one-out model).",
    "Total Shortfall": "Expected minus actual branches, counting only districts below expectation.",
    "Districts Flagged Below Expected": "Districts where the chance of so few branches is under 10% and the count is also below the bootstrap range. A perfect model would still flag about one district in ten, so use the list for review.",
    "Model Error Reduction %": "Fall in the average miss of the leave-one-out model against a rule that gives every district the same branches per person.",
    "Gini of Bank Branches 2024": "Inequality of bank branches against population across districts: 0 is even, 1 is one district.",
    "New Branches Reaching Low-Density Half %": "Share of net new bank branches since 2020 that went to the half of districts that started with fewer branches per person.",
    "Scenario Gini": "Gini of branches after the planner places new points under the rule and size shown.",
    "Latest Active Agent Share %": "Registered branchless banking agents that were active in the latest quarter.",
    "Pakistan Rank From Lowest": "Pakistan's position when economies are ordered from lowest account ownership.",
    "Pakistan Account Shortfall vs Income (pts)": "Account ownership expected at Pakistan's income minus the actual figure, in points.",
}


def measure_lines(measure: Measure) -> list[str]:
    """The DAX of one measure as lines, indented relative to the first line."""
    return [ln.rstrip() for ln in textwrap.dedent(measure.dax).strip("\n").splitlines() if ln.strip()]


def measures_text() -> str:
    """powerbi/measures.dax: every measure, grouped by folder, ready to paste into Power BI Desktop."""
    out = ["// Measures for the Pakistan financial inclusion report. Generated by `python -m fininc report`.",
           "// All measures live in a table called _Measures. A year-filtered measure keeps the year in a VAR:",
           "// filtering a column by a measure inside CALCULATE makes the measure invalid in Power BI.", ""]
    folder = None
    for m in MEASURES:
        if m.folder != folder:
            folder = m.folder
            out += [f"// ---------- {folder} ----------", ""]
        if m.name in DESCRIPTIONS:
            out.append(f"// {DESCRIPTIONS[m.name]}")
        lines = measure_lines(m)
        if len(lines) == 1:
            out.append(f"{m.name} = {lines[0]}")
        else:
            out.append(f"{m.name} =")
            out += lines
        out.append("")
    return "\n".join(out)
