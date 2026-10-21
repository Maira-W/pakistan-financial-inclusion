# Financial inclusion in Pakistan: where the gaps are and who is left out

[![tests](https://github.com/Maira-W/pakistan-financial-inclusion/actions/workflows/ci.yml/badge.svg)](https://github.com/Maira-W/pakistan-financial-inclusion/actions/workflows/ci.yml)
![python 3.11](https://img.shields.io/badge/python-3.11-blue)

Only {{acct:.0f}}% of Pakistani adults have a financial account, {{shortfall_pts:.0f}} points fewer than the country's income would predict. This project asks **where the gaps are and who is left out**, by combining four public sources down to {{n_units}} districts: the World Bank Global Findex survey, the State Bank of Pakistan's branch registers and wallet statistics, and the 2023 census. It is delivered as reproducible Python code, an interactive dashboard, a nine-page Power BI report, a notebook and a policy memo.

| | |
|---|---|
| **Interactive dashboard** | [maira-w.github.io/pakistan-financial-inclusion](https://maira-w.github.io/pakistan-financial-inclusion/) (seven tabs, a district map and a branch-placement planner) |
| **Power BI report** | [`powerbi/Pakistan_Financial_Inclusion.pbix`](powerbi/Pakistan_Financial_Inclusion.pbix): nine pages, {{n_measures}} DAX measures ([guide](docs/powerbi.md)) |
| **Recommendation memo** | [`docs/recommendation_memo.md`](docs/recommendation_memo.md) |
| **Analysis notebook** | [`notebooks/analysis.ipynb`](notebooks/analysis.ipynb), executed |
| **Method and data** | [methodology](docs/methodology.md) · [data sources](docs/data_sources.md) · [data dictionary](docs/data_dictionary.md) |

## What the data show

1. **Income does not explain it.** Pakistan ranks {{rank_lowest_ord}} lowest of {{n_economies}} economies for account ownership and sits {{shortfall_pts:.0f}} points below the {{expected_acct:.0f}}% that its income predicts.
2. **Women and the poorest lost ground.** Between 2021 and 2024 men's account ownership rose from {{men_2021:.0f}}% to {{men_2024:.0f}}%, but women's fell from {{women_2021:.1f}}% to {{women_2024:.1f}}% and the poorest 40% fell from {{poor_2021:.0f}}% to {{poor_2024:.0f}}%. Only {{phone_women:.0f}}% of women own a mobile phone against {{phone_men:.0f}}% of men: {{phone_gap_phrase}}.
3. **Money and cost matter more than distance.** Among adults without a bank account, {{b_money:.0f}}% say they do not have enough money and {{b_cost:.0f}}% that services are too expensive; {{b_distance:.0f}}% cite distance and {{b_trust:.0f}}% a lack of trust.
4. **Branches are an urban good.** {{rural_pop_share:.0f}}% of people live in rural areas but only {{rural_branch_share:.0f}}% of the {{branches:,}} bank and microfinance branches do: {{rural_per_100k:.1f}} branches per 100,000 rural residents against {{urban_per_100k:.1f}} for urban residents.
5. **Four years of new branches did not reach the underserved.** Bank branches grew {{bank_growth:.0f}}% between 2020 and 2024, but the half of districts that started with the fewest per person (home to {{low_pop_share:.0f}}% of people) got {{low_new_share:.0f}}% of the {{net_new:,}} net new branches. The Gini coefficient of bank branches did not move: {{gini_2020:.3f}} in 2020 and {{gini_2024:.3f}} in 2024.
6. **Two sensible rules disagree about where to build.** A model of how many branches a district of that size, urbanisation and development should have flags {{n_robust}} districts as short (for example {{robust_3}}; chance alone would flag about {{chance_flags:.0f}}, so read it as a review list), and its largest gaps in branches are in big cities: {{top3_names}}. Placing {{k_default:,}} new points by that gap would *raise* inequality (Gini {{plan_gini_before:.2f}} to {{plan_gini_gap:.2f}}), while evening out people per branch removes all {{plan_units_before}} low-density districts and cuts it to {{plan_gini_equity:.2f}}.
7. **The digital layer is dense but hollow.** Wallet agents grew {{agents_growth:.0f}}% since {{wallet_first}}, yet the share that are active fell from {{active_agents_first:.0f}}% to {{active_agents_last:.0f}}%.

<table>
<tr>
<td width="50%"><a href="docs/figures/01_cross_country_account_vs_income.png"><img src="docs/figures/01_cross_country_account_vs_income.png" alt="Account ownership against income"></a><br><sub>Account ownership against income, {{n_economies}} economies</sub></td>
<td width="50%"><a href="docs/figures/03_who_is_left_out.png"><img src="docs/figures/03_who_is_left_out.png" alt="Who is left out"></a><br><sub>Who gained and who lost, 2021 to 2024</sub></td>
</tr>
<tr>
<td><a href="docs/figures/06_map_branch_density.png"><img src="docs/figures/06_map_branch_density.png" alt="Branches per 100,000 people by district"></a><br><sub>Branches per 100,000 people, by district</sub></td>
<td><a href="docs/figures/09_rural_urban_gap.png"><img src="docs/figures/09_rural_urban_gap.png" alt="Rural and urban branch density"></a><br><sub>The rural and urban gap</sub></td>
</tr>
<tr>
<td><a href="docs/figures/11_no_catch_up.png"><img src="docs/figures/11_no_catch_up.png" alt="No catch-up"></a><br><sub>Districts that started behind did not catch up</sub></td>
<td><a href="docs/figures/14_planner_outcomes.png"><img src="docs/figures/14_planner_outcomes.png" alt="Planner outcomes"></a><br><sub>Where {{k_default:,}} new points go changes who is reached</sub></td>
</tr>
</table>

All fifteen figures are in [`docs/figures`](docs/figures).

## The Power BI report

Four of the {{n_pbi_pages}} pages, saved from Power BI Desktop. The rest are in [`docs/powerbi_pages`](docs/powerbi_pages), and the [guide](docs/powerbi.md) describes the model and the measures.

{{pbi_gallery_readme}}

## How it works

```
data/raw  ──build──▶  data/interim  ──analyze──▶  data/processed  ──report──▶  docs/figures · dashboard/ · powerbi/ · docs/
 (checksummed)         (clean, validated)          (models, rankings)           (everything you open)
```

| Stage | What it does |
|---|---|
| `ingest` | Downloads the raw files once and records a SHA-256 checksum, source and licence for each in [`data/raw/MANIFEST.json`](data/raw/MANIFEST.json). `verify` checks them. |
| `build` | Parses the census tables, the SBP branch register (Excel), the SBP 2020 district appendix and the quarterly wallet statistics (PDF); maps every name to {{n_units}} districts on 2020 boundaries; reconciles the totals to the official ones. |
| `analyze` | Fits a negative binomial access model with leave-one-out expectations, district types (k-means), inequality and catch-up tests, a cross-country benchmark and the branch-placement planner. |
| `report` | Draws the figures, the dashboard, the Power BI project and these documents. |

The documents (including this file) are generated from [`fininc/templates/docs`](fininc/templates/docs), so a number in the text cannot disagree with the data. Edit the template, not the output.

## Data

| Source | Used for | Vintage |
|---|---|---|
| World Bank Global Findex and World Development Indicators | Account ownership, phones, reasons for having no account, income | 2011 to {{findex_year}} |
| State Bank of Pakistan, list of bank and microfinance branches | Branches by district, rural flag, bank | {{register_date}} |
| State Bank of Pakistan, statistics on scheduled banks (appendices) | 2020 baseline of bank branches by district | {{baseline_date}} |
| State Bank of Pakistan, branchless banking statistics | Wallet accounts and agents by region | {{wallet_first}} to {{wallet_last}} |
| Pakistan Bureau of Statistics, 7th census | Population, literacy, housing and services by district | {{census_year}} |
| geoBoundaries (WFP humanitarian boundaries) | District map | 2022 |

Details, licences and every data problem found are in [`docs/data_sources.md`](docs/data_sources.md).

## Quality checks

- **Population reconciles exactly.** District populations add up to the official PBS provincial totals for 2023 and 2017, with zero difference.
- **Branches reconcile to the source.** All {{register_rows:,}} register rows and all {{sbp20_districts}} district rows of the 2020 appendix are accounted for: {{register_in:,}} register branches and {{sbp20_in:,}} 2020 branches fall inside the {{n_units}} districts, and the rest are in Azad Jammu & Kashmir and Gilgit-Baltistan.
- **An outside check.** Bank branches per 100,000 adults come to {{mine_2024:.1f}} here against {{wdi_2024:.1f}} in the World Bank's indicator for {{findex_year}} (the difference is the two regions this project leaves out and the age shares used).
- **Unknown names fail loudly.** A district name that is not mapped raises an error instead of being dropped.
- **Tests.** `pytest` covers the district mapping, the loaders, every model on cases with known answers, the planner, the dashboard data, the Power BI project, the data dictionary and the generated documents. They run on every push.
- **Power BI.** All {{n_measures}} measures were evaluated in Power BI Desktop against the Python results, and every page was opened and checked (see [`docs/powerbi.md`](docs/powerbi.md)).

## Limitations

- A branch counts where it is, not where its customers live, so cities that serve their surroundings look better served than they are. Branch counts say nothing about use.
- The Findex survey cannot be broken down to districts. District results are about branches, not about account ownership.
- The access model is a peer comparison. It says which districts have fewer branches than similar districts, not how many a district needs.
- The planner shows who is reached, not what it costs, and treats branches, agents and wallets alike.
- Azad Jammu & Kashmir and Gilgit-Baltistan are not covered because the census district tables do not include them.
- {{wallet_flags}} wallet figures printed by the SBP jump out of line with the quarters either side and are left out of charts rather than corrected.

## Corrections to the first version

An audit for this version found one error in version 1 (tag `v1.0.0`): a census block for Tando Muhammad Khan (272,427 people) was counted twice in the published population table, which inflated Sindh by that number. The new loader checks every province against the official totals and stops on any difference.

Two further mistakes were caught while this version was being built and were never published. The share of pakka (permanent) houses was divided by a total that already included its own total row, halving it (standardisation hides a constant factor, so no result changed). Three of the Global Findex reasons for having no account were first labelled wrongly. Tests now check both.

## Reproduce it

```bash
python -m venv .venv && .venv\Scripts\activate        # macOS or Linux: source .venv/bin/activate
pip install -r requirements-dev.txt                   # requirements.txt alone is enough to run the pipeline
python -m fininc verify        # raw files match their checksums
python -m fininc all           # build, analyze and report (about two minutes)
python -m fininc notebook      # run notebooks/analysis.ipynb and save it with its outputs
pytest                         # run the tests (about two minutes)
```

`python -m fininc ingest --refresh` downloads the raw data again (it needs the internet and the SBP and World Bank sites to be up). Outputs are deterministic: the random seed is {{seed}} and no timestamps are written.

The Power BI project opens with a **Refresh now** banner the first time (a project stores no data); click it once. The `.pbix` already contains the data.

## Layout

```
fininc/            the package: loaders, units, features, models, charts, dashboard, powerbi, docs
  loaders/         one module per source
  templates/       dashboard page and script, document templates
data/raw/          source files and MANIFEST.json (checksums, licences)
data/interim/      cleaned tables passed between stages
data/processed/    model outputs, summary.json, district boundaries
docs/              methodology, data sources, data dictionary, memo, figures, Power BI screenshots
dashboard/         the interactive dashboard (one HTML file)
powerbi/           Power BI project (.pbip), report snapshot (.pbix), measures.dax
notebooks/         the analysis notebook
tests/             pytest suite
.github/workflows/ the continuous integration job (lint, checksums, tests)
requirements*.txt  pinned package versions; pyproject.toml describes the package
```

## What this project shows

Data engineering (messy PDFs and spreadsheets turned into validated tables with provenance), statistics (count models with leave-one-out and bootstrap uncertainty, PCA, clustering, inequality decomposition, regression with robust errors), decision support (a placement planner with explicit trade-offs), business intelligence (a star-schema Power BI model with {{n_measures}} DAX measures) and communication (a dashboard and a plain-language memo), all reproducible from one command.
