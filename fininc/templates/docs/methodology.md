# Methodology

This document explains how every number in the project is produced, what was checked, and what the methods cannot do. Numbers are filled in from the results, so they match the data. Code is in [`fininc/`](../fininc), and `python -m fininc all` reproduces everything.

## 1. The question and the unit of analysis

The question is *where are the gaps in financial access in Pakistan, and who is left out?* Survey data on account ownership (Global Findex) exist only for the country and for groups of people, so they cannot say where. Branch and census data exist for districts, so they can. The project therefore joins the two kinds of evidence: national and group results come from the survey, and district results describe **physical access** (branches per person) rather than account ownership.

The unit of analysis is the **district on its 2020 boundaries**. The 2023 census has {{n_census_districts}} districts, but the State Bank's 2020 appendix lists some of them together, and several were created after it. Rather than guess how a parent's branches were split, {{n_merged_districts}} census districts are grouped into {{n_merged_units}} units: the seven Karachi districts (reported as one), Upper and Lower Chitral, the three Kohistan districts, and seven districts created since 2020 together with their parents (Chaman, Duki, Sherani, Surab, Sohbatpur, Sujawal and Tank with Killa Abdullah, Loralai, Zhob, Kalat, Jaffarabad, Thatta and Dera Ismail Khan). That gives **{{n_units}} units** that mean the same thing in the census, the 2020 baseline and the 2024 register, and that can be drawn on the map by dissolving the district polygons. Azad Jammu & Kashmir and Gilgit-Baltistan are not in the census district tables and are left out; their branches (about {{register_out}} in the 2024 register and {{sbp20_out}} in 2020) are counted and set aside, not dropped silently.

Every district name in a State Bank file is mapped by an explicit alias table. A name that is neither mapped nor listed as outside coverage raises an error, so a new spelling in a future release cannot disappear from the totals.

## 2. Access measures

- **Branches** are bank branches plus microfinance bank and development finance institution branches in the SBP register at {{register_date}}. The 2020 baseline counts scheduled bank branches only (the appendix has no microfinance), so every change between 2020 and 2024 uses bank branches alone.
- **Per 100,000 people** divides by the 2023 census population (2017 for the 2020 baseline). A per-adult version divides by the adult population implied by the census age shares.
- **Rural and urban** use the register's own rural flag for branches and the census urban and rural populations for people. The two definitions differ at the margin, so district values for rural branches per rural resident are indicative.
- **Low density** means fewer than {{low_share_of_avg:.0%}} of the national branches per person ({{units_below_half}} districts holding {{pop_below_half:.1f}}% of people).

## 3. A development index

District development is summarised by the first principal component of seven census indicators: literacy, female literacy, pakka (permanent) housing, electricity, improved drinking water, flush toilets and clean cooking fuel. Indicators are standardised first, the sign is set so that higher means more developed, and the score is standardised again to mean 0 and standard deviation 1. The first component explains {{ses_var:.0f}}% of the variance and every loading is positive and similar in size ({{loading_min:.2f}} to {{loading_max:.2f}}), so the index behaves like an average of the seven rather than a contrast. The detailed census tables (age, literacy, housing, services) cover {{detailed_cover:.1f}}% of the population in the headline table, because they leave out some areas (by up to {{detailed_gap_max:.0f}}% in a district), so each ratio uses its own table's denominator and counts are never mixed across tables.

## 4. How many branches should a district have? (the access model)

**Model.** Branch counts are small integers with more spread than a Poisson model allows, so the model is a negative binomial (NB2) regression:

> branches ~ NegativeBinomial(μ, α), with ln μ = β₀ + β₁ ln(population) + β₂ urban share + β₃ development index, and Var = μ + α μ².

{{table_coefficients}}

A district with twice the population has {{rr_pop_double:.2f}} times the branches, so large districts have fewer per person than small ones. A district that is fully urban has {{rr_urban:.1f}} times the branches of a fully rural one of the same size and development, and one standard deviation of development raises the count by a factor of {{rr_ses:.2f}}.

**Choosing the specification.** Six specifications were compared on the Akaike information criterion and on leave-one-out prediction error, against a rule that gives every district branches in proportion to its population.

{{table_specs}}

The selected model (population, urban share, development index) cuts the leave-one-out error by {{mae_cut:.0f}}% against the proportional rule. Adding population density or growth lowers the AIC slightly or leaves it level but does not change the leave-one-out error by more than about two branches, so the simpler model was kept. The correlation between expected and actual branches is {{loo_corr:.2f}} (rank correlation {{spearman:.2f}}).

**Expectations that do not include the district itself.** For each district the model is refitted on the other {{n_others}} districts and the district's expected count is predicted from that fit. A district therefore never helps to predict itself, which matters because a few large cities would otherwise pull the fitted line toward themselves and hide their own gaps.

**How unusual is a gap?** With expected count μ and the fitted dispersion, the probability of seeing *so few or fewer* branches is the negative binomial distribution function at the observed count. A district counts as **below expectation** when that probability is under {{gap_significance:.0%}}; {{n_below_expected}} districts do (and {{n_above_expected}} are above). With {{n_units}} districts and a {{gap_significance:.0%}} threshold, about {{chance_flags:.0f}} would fall below expectation by chance even if the model were exactly right, and {{n_below_expected}} do, so below expectation is a list to review, not proof that {{n_below_expected}} districts are short.

**Is it robust?** {{boot_draws}} bootstrap resamples were drawn; each refit predicts only the districts left out of its resample ("out of bag"), which gives every district a 10th to 90th percentile range for its expected count. A district is **flagged** when it is below expectation and its actual count is also under the 10th percentile: {{n_robust}} of the {{n_below_expected}} districts below expectation. The flags are a list to review, not a test. The **total shortfall** is the sum of the positive gaps, {{shortfall_total:,.0f}} branches, with a 90% range of {{shortfall_lo:,.0f}} to {{shortfall_hi:,.0f}} from the same resamples.

The largest gaps in branches are in large cities, because the same proportional shortfall is a bigger number there:

{{table_shortfalls}}

**What it is and is not.** The expected count is what *similar districts* have, not what a district *needs*. If the whole country is under-served, a model of peers will not show it. That is why the planner in section 9 does not rely on it alone.

## 5. District types

K-means clustering on four standardised variables (log population, urban share, development index, log of one plus branches per 100,000) gives four types, named by their average development index. Silhouette scores for two to six clusters range from {{silhouette_min:.2f}} to {{silhouette_max:.2f}} with no clear peak, and the mean adjusted Rand index between the full-sample clusters and clusters from 60 bootstrap resamples is {{stability_4:.2f}} for four clusters, so districts form a continuum and the types are a convenient summary, not natural groups. Four was chosen for interpretability.

{{table_clusters}}

## 6. Inequality

The **Lorenz curve** orders districts from fewest to most branches per person and plots the cumulative share of branches against the cumulative share of people. The **Gini coefficient** is one minus twice the area under it (0 means branches follow population, 1 means one district has everything). For bank branches it is {{gini_2024:.3f}} in 2024 and {{gini_2020:.3f}} in 2020 (2017 population); for bank and microfinance branches together it is {{gini_all:.3f}}. The **Theil index** is split into a between-province and a within-province part; {{theil_between_share:.0f}}% of the inequality in bank branches is between provinces and the rest is within them. The ten districts with most branches ({{top10_names}}) hold {{top10_branch_share:.0f}}% of branches and {{top10_pop_share:.0f}}% of people.

## 7. Did low-branch districts catch up?

The change in bank branches per 100,000 people between 2020 and 2024 is regressed on the 2020 level and on annual population growth, with heteroskedasticity-robust (HC3) standard errors. A negative coefficient on the 2020 level would mean districts that started behind gained more (convergence). The estimate is {{conv_slope:.3f}} (95% interval {{conv_lo:.2f}} to {{conv_hi:.2f}}, p = {{conv_p:.2f}}, R² = {{conv_r2:.3f}}), so there is no sign of catch-up. A simple count gives the same message: the {{low_units}} districts below the median density in 2020 hold {{low_pop_share:.0f}}% of people and received {{low_new_share:.0f}}% of the {{net_new:,}} net new bank branches, and {{units_losing}} districts lost branches. This describes what happened; it does not say why.

## 8. Pakistan against other economies

Account ownership in {{n_economies}} economies is regressed on the log of GDP per person (PPP, constant 2021 international dollars) with robust errors. Each additional doubling of income goes with about {{income_doubling:.0f}} more points of account ownership (R² = {{income_r2:.2f}}). At Pakistan's income the line predicts {{expected_acct:.1f}}%; Pakistan has {{acct:.1f}}%, a shortfall of {{shortfall_pts:.1f}} points. A 90% prediction interval for a single economy at that income runs from {{pi_low:.1f}}% to {{pi_high:.1f}}%, so Pakistan sits at the very bottom edge of what income allows. Pakistan's account gap between men and women ({{acct_gap:.0f}} points) is {{acct_gap_phrase}}, and its phone gap ({{phone_gap:.0f}} points) is {{phone_gap_phrase}}. Cross-country regressions describe association only.

## 9. The placement planner

The planner answers "if we add *k* access points, where should they go?" under three rules. Each point is placed one at a time, and the rule decides which district gets the next one:

- **Equity:** the district with the most people per (branch + 1).
- **Model gap:** the district with the largest remaining shortfall against its expected count; no point is placed where the shortfall is already filled, so fewer than *k* may be placed.
- **Women:** as equity, with each district's need multiplied by its literacy gap between men and women relative to the average gap.

Each rule is judged on five outcomes: districts below half the national average, the share of people in them, the Gini coefficient, people per branch in the worst-served district (a district with no branch counts as one), and the share of points that go to districts where under {{low_female_literacy:.0f}}% of women can read.

For {{k_default:,}} points ({{k_share:.0f}}% of the {{network:,}}-branch network):

{{table_scenarios}}

The ranking holds across sizes: with 500 points the equity rule already leaves only {{plan_units_equity_500}} low-density districts, and with 4,000 it lowers the Gini to {{plan_gini_equity_4000:.2f}}. The rules disagree because the model's biggest gaps are in cities with many people and many branches, while the districts with the most people per branch are mostly rural. The same logic runs in the dashboard (written in JavaScript); its results were checked against the Python ones for every rule.

## 10. Wallet and agent statistics

The SBP publishes branchless banking statistics each quarter as a PDF. The pipeline reads {{wallet_quarters}} quarters ({{wallet_first}} to {{wallet_last}}), takes the national table and the table by province, and checks that the provinces add up to the national total. Wallet accounts and agents are divided by the census adult population of the SBP's reporting region (Punjab and Islamabad are reported together). An account is not a person, so accounts per 100 adults can exceed 100 in principle and should be read as an index of intensity.

Some published figures jump out of line: for example Balochistan's accounts rise 45% and fall back in the quarters either side. A figure is flagged when it is more than 25% from the average of the quarters either side (or, for the women's share, more than 4 points), worst first, setting each flagged value aside before checking the next. {{wallet_flags}} points are flagged. They stay in the data (flagged) and are left out of charts rather than corrected.

## 11. Survey data

Account ownership by group and over time is read from the Global Findex database through the World Bank API. Every indicator code's label in [`fininc/config.py`](../fininc/config.py) was compared with the World Bank's own name for it (a test pins the meaning of the reason codes). The reasons for having no bank account are published as a share of adults without one, except lack of documents, which is only published as a share of all adults; it is divided by the share of adults without a bank-type account ({{b_docs:.1f}}% after division), a calculation checked against the ratios of the other reasons, which give the same base to within half a point. The reasons for having no mobile money account are published as a share of all adults and are not comparable with the bank figures.

## 12. Reproducibility and testing

- The raw files, their sources, licences and SHA-256 checksums are in `data/raw/MANIFEST.json`; `python -m fininc verify` fails if one changed.
- Randomness (bootstrap, clustering) uses seed {{seed}}. No stage writes a timestamp, so rerunning on unchanged data reproduces the outputs.
- Package versions are pinned in `requirements.txt`.
- The tests check the district mapping, each loader's reconciliation to official totals, each model on a case with a known answer, the planner's rules, the dashboard data, the Power BI project (every field a visual or measure uses must exist), the data dictionary against every output table, and that the committed documents are what the templates and data produce.

## 13. What would change the conclusions

- A different definition of low density (the threshold is {{low_share_of_avg:.0%}} of the national average) would change the count of districts but the planner's ranking of rules rests on who has the most people per branch, which does not depend on the threshold.
- If branch counts are a poor proxy for access in places served by agents or mobile branches, the rural gap is overstated. The wallet statistics point the same way (agents per adult are lowest in Balochistan) but do not settle it.
- District results from a single register date cannot show whether a branch is open to the public or what it serves.
