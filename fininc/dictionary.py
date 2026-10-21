"""Data dictionary: what every column in the output tables means.

docs/data_dictionary.md is generated from this file, and a test fails if an output table gains, loses or reorders a
column without this file being updated.
"""

from __future__ import annotations

# (column, unit or type, description), in the order the columns appear in the file
UNITS = [
    ("unit", "text", "District on its 2020 boundaries. Ten units absorb districts created after 2020 (see members)."),
    ("unit_id", "text", "Lower-case name with underscores. Matches properties.unit_id in unit_boundaries.geojson."),
    ("province", "text", "Province, or Islamabad Capital Territory."),
    ("n_districts", "count", "Number of 2023 census districts inside the unit."),
    ("members", "text", "The 2023 census districts inside the unit, separated by semicolons."),
    ("area_sqkm", "km2", "Area, PBS Census 2023 Table 01."),
    ("pop", "people", "Population, 2023 census (Table 01). This is the figure that adds up to the official provincial totals."),
    ("pop_male", "people", "Male population, 2023. Male plus female falls short of pop by the transgender count."),
    ("pop_female", "people", "Female population, 2023."),
    ("pop_urban", "people", "Urban population, 2023."),
    ("pop_rural", "people", "Rural population, 2023."),
    ("pop_2017", "people", "Population at the 2017 census, summed over the same member districts."),
    ("age_15_64", "people", "People aged 15 to 64 (Table 05). The detailed census tables leave out restricted areas, so their counts are a little below pop; only shares are compared with other tables."),
    ("age_60plus", "people", "People aged 60 and over (Table 05). Overlaps age_15_64 for ages 60 to 64."),
    ("age_all", "people", "People of all ages counted in Table 05."),
    ("age_under15", "people", "People under 15 (Table 05)."),
    ("pop10", "people", "People aged 10 and over (Table 12)."),
    ("pop10_f", "people", "Women aged 10 and over."),
    ("pop10_m", "people", "Men aged 10 and over."),
    ("lit10", "people", "Literate people aged 10 and over."),
    ("lit10_f", "people", "Literate women aged 10 and over."),
    ("lit10_m", "people", "Literate men aged 10 and over."),
    ("pop5", "people", "People aged 5 and over (Table 12)."),
    ("pop5_f", "people", "Women aged 5 and over."),
    ("pop5_m", "people", "Men aged 5 and over."),
    ("never_school", "people", "People aged 5 and over who have never been to school."),
    ("never_school_f", "people", "Women aged 5 and over who have never been to school."),
    ("never_school_m", "people", "Men aged 5 and over who have never been to school."),
    ("hh_pakka", "households", "Households in pakka (permanent) houses (Table 20)."),
    ("hh_housing_total", "households", "Households in all house types: pakka, semi-pakka and kacha (Table 20 total). Equals hh_total in every district, which the pipeline checks."),
    ("hh_total", "households", "Households (Table 22)."),
    ("hh_electricity", "households", "Households that light their home with electricity (Table 22)."),
    ("hh_water_improved", "households", "Households whose main drinking water is an improved source (Table 23)."),
    ("hh_flush_toilet", "households", "Households with a flush toilet (Table 24)."),
    ("hh_owned", "households", "Households that own the home they live in (Table 25)."),
    ("owner_male", "dwellings", "Dwellings whose recorded owner is a man (Table 25)."),
    ("owner_female", "dwellings", "Dwellings whose recorded owner is a woman (Table 25)."),
    ("hh_gas_or_lpg", "households", "Households whose main cooking fuel is natural gas or LPG/CNG (Table 22)."),
    ("density_per_sqkm", "people per km2", "pop divided by area_sqkm."),
    ("urban_share", "%", "pop_urban as a percentage of pop."),
    ("pop_growth_pct_pa", "% a year", "Compound annual growth between the 2017 and 2023 censuses, over six years."),
    ("under15_share", "%", "age_under15 as a percentage of age_all."),
    ("working_age_share", "%", "age_15_64 as a percentage of age_all."),
    ("adults_15plus", "people", "pop multiplied by (1 - under15_share / 100). The denominator for per-adult measures."),
    ("literacy", "%", "lit10 as a percentage of pop10: literate people among those aged 10 and over."),
    ("literacy_female", "%", "As literacy, for women."),
    ("literacy_male", "%", "As literacy, for men."),
    ("literacy_gender_gap", "points", "literacy_male minus literacy_female."),
    ("never_attended_school_share", "%", "never_school as a percentage of pop5."),
    ("pakka_share", "%", "hh_pakka as a percentage of hh_housing_total."),
    ("electricity_share", "%", "hh_electricity as a percentage of hh_total."),
    ("clean_cooking_share", "%", "hh_gas_or_lpg as a percentage of hh_total."),
    ("water_improved_share", "%", "hh_water_improved as a percentage of hh_total."),
    ("flush_toilet_share", "%", "hh_flush_toilet as a percentage of hh_total."),
    ("home_owned_share", "%", "hh_owned as a percentage of hh_total."),
    ("female_owner_share", "%", "owner_female as a percentage of owner_female plus owner_male."),
    ("ses_index", "index", "Development index. First principal component of literacy, female literacy, pakka housing, electricity, improved water, flush toilet and clean cooking, standardised to mean 0 and standard deviation 1 across units. Higher is more developed."),
    ("banks_2020", "branches", "Scheduled bank branches at 31 December 2020 (SBP Statistics on Scheduled Banks, Appendix 3b)."),
    ("islamic_banks_2020", "branches", "Of banks_2020, the branches the appendix lists as Islamic."),
    ("banks_2024", "branches", "Bank branches at 31 December 2024 (SBP register, Banks sheet)."),
    ("mfb_2024", "branches", "Microfinance bank and development finance institution branches at 31 December 2024 (SBP register, MFBs and DFIs sheet)."),
    ("rural_banks_2024", "branches", "Bank branches the register tags as rural."),
    ("rural_mfb_2024", "branches", "Microfinance and DFI branches the register tags as rural."),
    ("islamic_banks_2024", "branches", "Bank branches the register tags as Islamic (full Islamic banks and Islamic windows)."),
    ("n_banks", "count", "Distinct banks with at least one branch in the unit."),
    ("n_mfbs", "count", "Distinct microfinance banks and DFIs with at least one branch in the unit."),
    ("top_bank_share", "share, 0 to 1", "Share of the unit's bank branches that belong to its largest bank. Blank when there is no bank branch."),
    ("bank_hhi", "index, 0 to 1", "Herfindahl-Hirschman index of bank branch shares in the unit. 1 means a single bank. Blank when there is no bank branch."),
    ("branches_2024", "branches", "banks_2024 plus mfb_2024."),
    ("rural_branches_2024", "branches", "rural_banks_2024 plus rural_mfb_2024."),
    ("urban_branches_2024", "branches", "branches_2024 minus rural_branches_2024."),
    ("branches_per_100k", "per 100,000 people", "branches_2024 divided by pop, times 100,000. The main access measure."),
    ("banks_per_100k", "per 100,000 people", "banks_2024 divided by pop, times 100,000."),
    ("mfb_per_100k", "per 100,000 people", "mfb_2024 divided by pop, times 100,000."),
    ("branches_per_100k_adults", "per 100,000 adults", "branches_2024 divided by adults_15plus, times 100,000."),
    ("rural_branches_per_100k_rural", "per 100,000 rural people", "rural_branches_2024 divided by pop_rural, times 100,000. Blank when the unit has no rural population."),
    ("urban_branches_per_100k_urban", "per 100,000 urban people", "urban_branches_2024 divided by pop_urban, times 100,000. Blank when the unit has no urban population."),
    ("rural_branch_share", "%", "rural_branches_2024 as a percentage of branches_2024. Blank when the unit has no branch."),
    ("rural_pop_share", "%", "pop_rural as a percentage of pop."),
    ("mfb_share", "%", "mfb_2024 as a percentage of branches_2024. Blank when the unit has no branch."),
    ("islamic_share", "%", "islamic_banks_2024 as a percentage of banks_2024. Blank when the unit has no bank branch."),
    ("density_2020", "per 100,000 people", "banks_2020 divided by pop_2017, times 100,000."),
    ("density_2024_banks", "per 100,000 people", "banks_2024 divided by pop, times 100,000. Bank branches only, so it is comparable with density_2020."),
    ("density_change", "per 100,000 people", "density_2024_banks minus density_2020."),
    ("banks_change", "branches", "banks_2024 minus banks_2020."),
    ("banks_growth_pct", "%", "banks_change as a percentage of banks_2020. Blank when banks_2020 is zero."),
    ("log_pop", "log", "Natural log of pop. Input to the access model."),
    ("urban", "share, 0 to 1", "urban_share divided by 100. Input to the access model."),
    ("log_density", "log", "Natural log of density_per_sqkm. Used only by the density specification in the model comparison."),
    ("log_branch_density", "log", "Natural log of 1 plus branches_per_100k. Input to the district-type clustering."),
    ("expected_branches", "branches", "Leave-one-out prediction of the negative binomial model: how many branches (banks plus microfinance) a unit with this population, urban share and development index would be expected to have."),
    ("expected_low", "branches", "10th percentile of the out-of-bag bootstrap predictions for the unit."),
    ("expected_high", "branches", "90th percentile of the out-of-bag bootstrap predictions for the unit."),
    ("branch_gap", "branches", "expected_branches minus branches_2024. Positive means fewer branches than expected."),
    ("gap_ratio", "ratio", "branches_2024 divided by expected_branches."),
    ("p_below_expected", "probability", "Chance of seeing this many branches or fewer if the model were right (negative binomial, expected_branches as the mean)."),
    ("p_above_expected", "probability", "Chance of seeing this many branches or more if the model were right."),
    ("below_expected", "true or false", "p_below_expected is below 0.10."),
    ("above_expected", "true or false", "p_above_expected is below 0.10."),
    ("robust_shortfall", "true or false", "below_expected, and branches_2024 is also below expected_low."),
    ("people_per_branch", "people", "pop divided by branches_2024. Blank when the unit has no branch."),
    ("cluster", "text", "District type from k-means on log population, urban share, development index and log branch density."),
    ("cluster_rank", "0 to 3", "0 is the least developed type and 3 the most developed."),
]

# The table written by `build`: everything in units.csv up to the 2020 to 2024 change measures, before the models run.
UNIT_FEATURES = UNITS[:next(i for i, c in enumerate(UNITS) if c[0] == "banks_growth_pct") + 1]

PROVINCES = [
    ("province", "text", "Province, or Islamabad Capital Territory."),
    ("pop", "people", "Population, 2023, covered units only."),
    ("pop_urban", "people", "Urban population, 2023."),
    ("pop_rural", "people", "Rural population, 2023."),
    ("pop_2017", "people", "Population at the 2017 census."),
    ("area_sqkm", "km2", "Area in square kilometres (census Table 01)."),
    ("adults_15plus", "people", "Population aged 15 and over, from the census age shares."),
    ("banks_2020", "branches", "Bank branches, 31 December 2020."),
    ("banks_2024", "branches", "Bank branches, 31 December 2024."),
    ("mfb_2024", "branches", "Microfinance bank and DFI branches, 31 December 2024."),
    ("rural_banks_2024", "branches", "Rural bank branches."),
    ("rural_mfb_2024", "branches", "Rural microfinance and DFI branches."),
    ("islamic_banks_2024", "branches", "Islamic bank branches."),
    ("units", "count", "Analysis units in the province."),
    ("branches_2024", "branches", "Banks plus microfinance."),
    ("rural_branches_2024", "branches", "Rural branches."),
    ("urban_branches_2024", "branches", "Urban branches."),
    ("urban_share", "%", "Urban population as a percentage of the total."),
    ("branches_per_100k", "per 100,000 people", "Branches per 100,000 people."),
    ("banks_per_100k", "per 100,000 people", "Bank branches per 100,000 people."),
    ("mfb_per_100k", "per 100,000 people", "Microfinance and DFI branches per 100,000 people."),
    ("rural_branches_per_100k_rural", "per 100,000 rural people", "Rural branches per 100,000 rural residents."),
    ("urban_branches_per_100k_urban", "per 100,000 urban people", "Urban branches per 100,000 urban residents."),
    ("rural_branch_share", "%", "Rural branches as a percentage of all branches."),
    ("density_2020", "per 100,000 people", "Bank branches per 100,000 people in 2020 (2017 population)."),
    ("density_2024_banks", "per 100,000 people", "Bank branches per 100,000 people in 2024."),
    ("banks_growth_pct", "%", "Growth in bank branches, 2020 to 2024."),
    ("mfb_share", "%", "Microfinance and DFI branches as a percentage of all branches."),
]

WALLET_REGIONS = [
    ("province", "text", "Province name as printed by the SBP (Punjab includes Islamabad)."),
    ("accounts", "accounts", "Branchless banking (mobile wallet) accounts."),
    ("transactions", "transactions", "Transactions in the quarter."),
    ("agents", "agents", "Registered branchless banking agents."),
    ("accounts_male", "accounts", "Accounts held by men."),
    ("accounts_female", "accounts", "Accounts held by women."),
    ("quarter", "text", "Quarter, for example 2026Q2 for April to June 2026."),
    ("label", "text", "Quarter as the SBP writes it."),
    ("region", "text", "Reporting region used here. Punjab (incl. Islamabad) combines Punjab and Islamabad."),
    ("pop", "people", "Census 2023 population of the region. Blank for Azad Kashmir and Gilgit-Baltistan, which are outside the census coverage used here."),
    ("adults_15plus", "people", "Adults in the region. Blank where pop is blank."),
    ("accounts_per_100_adults", "per 100 adults", "accounts divided by adults, times 100. Accounts are not people."),
    ("agents_per_100k_adults", "per 100,000 adults", "agents divided by adults, times 100,000."),
    ("female_share", "%", "accounts_female as a percentage of accounts_female plus accounts_male."),
    ("transactions_per_account", "ratio", "transactions divided by accounts."),
    ("accounts_vs_neighbours_pct", "%", "accounts compared with the average of the quarters either side. Blank for the first and last quarter."),
    ("flag_accounts", "true or false", "The accounts figure is out of line with the quarters either side (more than 25% away, worst first)."),
    ("flag_female", "true or false", "The women's share is more than 4 points away from the quarters either side."),
]

WALLET_NATIONAL = [
    ("quarter", "text", "Quarter, for example 2026Q2."),
    ("label", "text", "Quarter as the SBP writes it."),
    ("agents", "agents", "Registered agents."),
    ("active_agents", "agents", "Agents that were active in the quarter, as defined by the SBP."),
    ("accounts", "accounts", "Wallet accounts."),
    ("active_accounts", "accounts", "Accounts that were active in the quarter."),
    ("deposits_pkr_mn", "PKR million", "Wallet deposits as on the quarter end (SBP: Deposits as on Quarter)."),
    ("active_account_share", "%", "active_accounts as a percentage of accounts."),
    ("active_agent_share", "%", "active_agents as a percentage of agents."),
]

CROSS_COUNTRY = [
    ("country", "text", "ISO 3-letter country code."),
    ("name", "text", "Economy name."),
    ("region", "text", "World Bank region."),
    ("income", "text", "World Bank income group."),
    ("account", "% of adults", "Adults with a financial institution or mobile money account (Global Findex 2024)."),
    ("account_women", "% of women", "Women with an account."),
    ("account_men", "% of men", "Men with an account."),
    ("account_gap", "points", "account_men minus account_women."),
    ("phone", "% of adults", "Adults who own a mobile phone."),
    ("phone_women", "% of women", "Women who own a phone."),
    ("phone_men", "% of men", "Men who own a phone."),
    ("phone_gap", "points", "phone_men minus phone_women."),
    ("mobile_money", "% of adults", "Adults with a mobile money account. Blank where not surveyed."),
    ("fi_account", "% of adults", "Adults with a bank or similar financial institution account."),
    ("digital_payment", "% of adults", "Adults who made or received a digital payment. Blank where not surveyed."),
    ("gdp_pc_ppp", "constant 2021 international $", "GDP per person, PPP, latest year up to 2024 (World Development Indicators)."),
    ("gdp_year", "year", "Year of the GDP value."),
    ("expected_account", "% of adults", "Account ownership predicted from log GDP per person by an ordinary least squares fit across the economies."),
    ("account_residual", "points", "account minus expected_account. Negative means fewer adults with an account than income predicts."),
    ("pred_low", "% of adults", "Lower end of the 90% prediction interval for one economy at this income."),
    ("pred_high", "% of adults", "Upper end of the 90% prediction interval."),
]

FINDEX_CROSS_SECTION = [
    ("country", "text", "ISO 3-letter country code."),
    ("name", "text", "Economy name."),
    ("account", "% of adults", "Adults with a financial institution or mobile money account (Global Findex 2024)."),
    ("account_women", "% of women", "Women with an account."),
    ("account_men", "% of men", "Men with an account."),
    ("phone", "% of adults", "Adults who own a mobile phone."),
    ("phone_women", "% of women", "Women who own a phone."),
    ("phone_men", "% of men", "Men who own a phone."),
    ("mobile_money", "% of adults", "Adults with a mobile money account. Blank where not surveyed."),
    ("fi_account", "% of adults", "Adults with a bank or similar financial institution account."),
    ("digital_payment", "% of adults", "Adults who made or received a digital payment. Blank where not surveyed."),
    ("region", "text", "World Bank region."),
    ("income", "text", "World Bank income group."),
    ("gdp_pc_ppp", "constant 2021 international $", "GDP per person, PPP, latest year up to 2024 (World Development Indicators)."),
    ("gdp_year", "year", "Year of the GDP value."),
    ("account_gap", "points", "account_men minus account_women."),
    ("phone_gap", "points", "phone_men minus phone_women."),
    ("log_gdp_pc", "log", "Natural log of gdp_pc_ppp. The income measure in the benchmark regression."),
]

FINDEX_SEGMENTS = [
    ("indicator", "text", "World Bank Findex indicator code."),
    ("segment", "text", "Group of adults, for example Women or Poorest 40%."),
    ("group", "text", "Kind of group: gender, age, education, income, location, labour or overall."),
    ("year", "year", "Survey year."),
    ("value", "% of the group", "Share of the group with an account."),
]

FINDEX_BARRIERS = [
    ("indicator", "text", "World Bank Findex indicator code."),
    ("reason", "text", "Reason given for having no bank or similar account."),
    ("share_of_unbanked", "%", "Share of adults without such an account who give the reason. Several reasons can be given."),
    ("derived", "true or false", "True when calculated here: documentation is published as a share of all adults and divided by the share without an account."),
]

FINDEX_MM_BARRIERS = [
    ("indicator", "text", "World Bank Findex indicator code."),
    ("reason", "text", "Reason given for having no mobile money account."),
    ("value", "% of all adults", "Share of all adults aged 15 and over, as published by the World Bank. Not a share of adults without an account, so it cannot be compared with findex_barriers."),
]

FINDEX_PANEL = [
    ("indicator", "text", "World Bank Findex indicator code."),
    ("label", "text", "Plain-English label."),
    ("group", "text", "Kind of indicator: account_type, age, barrier, credit, digital, education, g2p, gender, income, labour, location, mm_barrier, mobile, overall, remittance or saving."),
    ("country", "text", "ISO 3-letter code: PAK, IND, BGD or LKA."),
    ("year", "year", "Survey year."),
    ("value", "%", "Value for the indicator, usually percent of adults."),
    ("country_name", "text", "Country name."),
]

SCENARIO_CURVE = [
    ("points_requested", "count", "New branches or agent points the planner is asked to place. 0 is today's network, repeated under every rule."),
    ("strategy", "text", "Rule key: equity, gap or women."),
    ("rule", "text", "The rule in words."),
    ("points_placed", "count", "Points the rule actually placed. The gap rule stops once every shortfall is filled."),
    ("national_density", "per 100,000 people", "Branches per 100,000 people after placement."),
    ("units_below_half", "count", "Districts with fewer than half the national average of branches per person."),
    ("population_below_half_pct", "%", "Share of the population living in those districts."),
    ("gini", "0 to 1", "Gini coefficient of branches against population after placement. Lower is more even."),
    ("worst_people_per_branch", "people", "People per branch in the worst-served district. A district with no branch counts as one."),
    ("share_to_low_female_literacy_pct", "%", "Share of placed points that went to districts where under 40% of women are literate. Blank when nothing is placed."),
]

# table file (relative to the repository root) -> list of column descriptions
TABLES = {
    "data/processed/units.csv": UNITS,
    "data/interim/unit_features.csv": UNIT_FEATURES,
    "data/interim/provinces.csv": PROVINCES,
    "data/interim/bb_regions_quarterly.csv": WALLET_REGIONS,
    "data/interim/bb_national_quarterly.csv": WALLET_NATIONAL,
    "data/processed/cross_country.csv": CROSS_COUNTRY,
    "data/processed/findex_segments.csv": FINDEX_SEGMENTS,
    "data/processed/findex_barriers.csv": FINDEX_BARRIERS,
    "data/processed/findex_mobile_money_barriers.csv": FINDEX_MM_BARRIERS,
    "data/interim/findex_panel.csv": FINDEX_PANEL,
    "data/processed/scenario_curve.csv": SCENARIO_CURVE,
    "data/interim/findex_cross_section.csv": FINDEX_CROSS_SECTION,
}

TITLES = {
    "data/processed/units.csv": "District table: one row per analysis unit (120 rows)",
    "data/interim/unit_features.csv": "District table before the models: the first columns of units.csv",
    "data/interim/provinces.csv": "Province table (5 rows)",
    "data/interim/bb_regions_quarterly.csv": "Wallet statistics by region and quarter",
    "data/interim/bb_national_quarterly.csv": "Wallet statistics, national, by quarter",
    "data/processed/cross_country.csv": "Cross-country benchmark (Global Findex 2024)",
    "data/processed/findex_segments.csv": "Findex: account ownership by group, Pakistan",
    "data/processed/findex_barriers.csv": "Findex: reasons for having no bank account, Pakistan 2024",
    "data/processed/findex_mobile_money_barriers.csv": "Findex: reasons for having no mobile money account, Pakistan 2024",
    "data/interim/findex_panel.csv": "Findex panel: Pakistan and three neighbours, 2011 to 2024",
    "data/processed/scenario_curve.csv": "Planner outcomes by programme size and rule",
    "data/interim/findex_cross_section.csv": "Global Findex 2024 and income for each economy, before the benchmark model",
}

OTHER_OUTPUTS = [
    ("data/processed/summary.json", "Headline numbers, model coefficients and diagnostics, specification comparison, district types, inequality, convergence test, cross-country results and planner outcomes."),
    ("data/processed/lorenz_curves.json", "Lorenz curve points for 2020 banks, 2024 banks and 2024 all branches."),
    ("data/processed/scenario.json", "Planner outcomes for 250 to 4,000 new points under three rules."),
    ("data/processed/unit_boundaries.geojson", "District polygons merged to the analysis units (properties: unit_id, unit, province)."),
    ("data/processed/province_boundaries.geojson", "Province outlines."),
    ("data/interim/data_quality.json", "Reconciliation results, exclusions and flagged points."),
]


def render_markdown() -> str:
    lines = ["# Data dictionary", "",
             "Every column in the project's output tables. This file is generated from `fininc/dictionary.py` "
             "(`python -m fininc report`); a test fails if a table has a column that is not described here.", ""]
    for path, columns in TABLES.items():
        lines += [f"## {TITLES[path]}", "", f"File: `{path}`", "", "| Column | Unit | Meaning |", "|---|---|---|"]
        lines += [f"| `{name}` | {unit} | {text} |" for name, unit, text in columns]
        lines.append("")
    lines += ["## Other outputs", "", "| File | Contents |", "|---|---|"]
    lines += [f"| `{path}` | {text} |" for path, text in OTHER_OUTPUTS]
    lines.append("")
    return "\n".join(lines)
