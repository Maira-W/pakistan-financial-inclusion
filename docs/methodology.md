# Methodology

This document explains how every number in the project is produced, what was checked, and what the methods cannot do. Numbers are filled in from the results, so they match the data. Code is in [`fininc/`](../fininc), and `python -m fininc all` reproduces everything.

## 1. The question and the unit of analysis

The question is *where are the gaps in financial access in Pakistan, and who is left out?* Survey data on account ownership (Global Findex) exist only for the country and for groups of people, so they cannot say where. Branch and census data exist for districts, so they can. The project therefore joins the two kinds of evidence: national and group results come from the survey, and district results describe **physical access** (branches per person) rather than account ownership.

The unit of analysis is the **district on its 2020 boundaries**. The 2023 census has 136 districts, but the State Bank's 2020 appendix lists some of them together, and several were created after it. Rather than guess how a parent's branches were split, 26 census districts are grouped into 10 units: the seven Karachi districts (reported as one), Upper and Lower Chitral, the three Kohistan districts, and seven districts created since 2020 together with their parents (Chaman, Duki, Sherani, Surab, Sohbatpur, Sujawal and Tank with Killa Abdullah, Loralai, Zhob, Kalat, Jaffarabad, Thatta and Dera Ismail Khan). That gives **120 units** that mean the same thing in the census, the 2020 baseline and the 2024 register, and that can be drawn on the map by dissolving the district polygons. Azad Jammu & Kashmir and Gilgit-Baltistan are not in the census district tables and are left out; their branches (about 793 in the 2024 register and 638 in 2020) are counted and set aside, not dropped silently.

Every district name in a State Bank file is mapped by an explicit alias table. A name that is neither mapped nor listed as outside coverage raises an error, so a new spelling in a future release cannot disappear from the totals.

## 2. Access measures

- **Branches** are bank branches plus microfinance bank and development finance institution branches in the SBP register at 2024-12-31. The 2020 baseline counts scheduled bank branches only (the appendix has no microfinance), so every change between 2020 and 2024 uses bank branches alone.
- **Per 100,000 people** divides by the 2023 census population (2017 for the 2020 baseline). A per-adult version divides by the adult population implied by the census age shares.
- **Rural and urban** use the register's own rural flag for branches and the census urban and rural populations for people. The two definitions differ at the margin, so district values for rural branches per rural resident are indicative.
- **Low density** means fewer than 50% of the national branches per person (41 districts holding 13.6% of people).

## 3. A development index

District development is summarised by the first principal component of seven census indicators: literacy, female literacy, pakka (permanent) housing, electricity, improved drinking water, flush toilets and clean cooking fuel. Indicators are standardised first, the sign is set so that higher means more developed, and the score is standardised again to mean 0 and standard deviation 1. The first component explains 79% of the variance and every loading is positive and similar in size (0.32 to 0.41), so the index behaves like an average of the seven rather than a contrast. The detailed census tables (age, literacy, housing, services) cover 99.6% of the population in the headline table, because they leave out some areas (by up to 12% in a district), so each ratio uses its own table's denominator and counts are never mixed across tables.

## 4. How many branches should a district have? (the access model)

**Model.** Branch counts are small integers with more spread than a Poisson model allows, so the model is a negative binomial (NB2) regression:

> branches ~ NegativeBinomial(μ, α), with ln μ = β₀ + β₁ ln(population) + β₂ urban share + β₃ development index, and Var = μ + α μ².

| Term | Coefficient | Std. error | p-value | Rate ratio |
| --- | ---: | ---: | ---: | ---: |
| Intercept | -7.396 | 0.605 | 2.16e-34 |  |
| log(population) | 0.803 | 0.043 | 1.86e-76 | 2.23 |
| Urban share (0 to 1) | 1.008 | 0.194 | 2.03e-07 | 2.74 |
| Development index (1 sd) | 0.528 | 0.041 | 9.14e-38 | 1.70 |
| Dispersion (alpha) | 0.072 | 0.013 | 2.12e-08 |  |

A district with twice the population has 1.74 times the branches, so large districts have fewer per person than small ones. A district that is fully urban has 2.7 times the branches of a fully rural one of the same size and development, and one standard deviation of development raises the count by a factor of 1.70.

**Choosing the specification.** Six specifications were compared on the Akaike information criterion and on leave-one-out prediction error, against a rule that gives every district branches in proportion to its population.

| Model | AIC | Leave-one-out error (branches) | Median relative error |
| --- | ---: | ---: | ---: |
| population only | 1205.9 | 48.9 | 38% |
| population + urban share | 1171.6 | 77.6 | 38% |
| population + development | 1094.2 | 39.1 | 25% |
| population + urban share + development | 1071.5 | 31.6 | 22% |
| ... + population density | 1072.4 | 30.0 | 23% |
| ... + population growth | 1066.5 | 30.5 | 22% |
| baseline: proportional to population | n/a | 67.7 | 58% |

The selected model (population, urban share, development index) cuts the leave-one-out error by 53% against the proportional rule. Adding population density or growth lowers the AIC slightly or leaves it level but does not change the leave-one-out error by more than about two branches, so the simpler model was kept. The correlation between expected and actual branches is 0.98 (rank correlation 0.97).

**Expectations that do not include the district itself.** For each district the model is refitted on the other 119 districts and the district's expected count is predicted from that fit. A district therefore never helps to predict itself, which matters because a few large cities would otherwise pull the fitted line toward themselves and hide their own gaps.

**How unusual is a gap?** With expected count μ and the fitted dispersion, the probability of seeing *so few or fewer* branches is the negative binomial distribution function at the observed count. A district counts as **below expectation** when that probability is under 10%; 15 districts do (and 13 are above). With 120 districts and a 10% threshold, about 12 would fall below expectation by chance even if the model were exactly right, and 15 do, so below expectation is a list to review, not proof that 15 districts are short.

**Is it robust?** 500 bootstrap resamples were drawn; each refit predicts only the districts left out of its resample ("out of bag"), which gives every district a 10th to 90th percentile range for its expected count. A district is **flagged** when it is below expectation and its actual count is also under the 10th percentile: 15 of the 15 districts below expectation. The flags are a list to review, not a test. The **total shortfall** is the sum of the positive gaps, 2,362 branches, with a 90% range of 785 to 5,509 from the same resamples.

The largest gaps in branches are in large cities, because the same proportional shortfall is a bigger number there:

| District | Province | People | Branches | Expected | Shortfall | Chance of so few |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Lahore | Punjab | 13,004,135 | 1,960 | 2,416 | 456 | 0.255 |
| Gujranwala | Punjab | 5,959,750 | 482 | 782 | 300 | 0.060 |
| Karachi | Sindh | 20,382,881 | 2,705 | 2,963 | 258 | 0.404 |
| Sheikhupura | Punjab | 4,049,418 | 241 | 384 | 143 | 0.070 |
| Hyderabad | Sindh | 2,432,540 | 261 | 400 | 139 | 0.087 |
| Faisalabad | Punjab | 9,075,819 | 696 | 827 | 131 | 0.300 |
| Kasur | Punjab | 4,084,286 | 176 | 292 | 116 | 0.056 |
| Hafizabad | Punjab | 1,319,909 | 91 | 146 | 55 | 0.074 |
| Okara | Punjab | 3,515,490 | 206 | 258 | 52 | 0.248 |
| Charsadda | Khyber Pakhtunkhwa | 1,835,504 | 65 | 108 | 43 | 0.067 |

**What it is and is not.** The expected count is what *similar districts* have, not what a district *needs*. If the whole country is under-served, a model of peers will not show it. That is why the planner in section 9 does not rely on it alone.

## 5. District types

K-means clustering on four standardised variables (log population, urban share, development index, log of one plus branches per 100,000) gives four types, named by their average development index. Silhouette scores for two to six clusters range from 0.28 to 0.38 with no clear peak, and the mean adjusted Rand index between the full-sample clusters and clusters from 60 bootstrap resamples is 0.67 for four clusters, so districts form a continuum and the types are a convenient summary, not natural groups. Four was chosen for interpretability.

| Type | Districts | People (m) | Urban | Development index | Women literate | Branches per 100,000 (median) | Rural share of branches | Largest districts |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Frontier and remote | 28 | 15.9 | 10% | -1.20 | 22% | 1.7 | 76% | Tharparkar, Bajaur, Khyber, Kohistan |
| Developing rural | 37 | 41.7 | 24% | -0.46 | 33% | 4.3 | 59% | Khairpur, Rajanpur, Sanghar, Dera Ismail Khan |
| Established districts | 45 | 113.4 | 25% | +0.78 | 52% | 6.0 | 48% | Rahim Yar Khan, Muzaffargarh, Peshawar, Sialkot |
| Metropolitan hubs | 10 | 70.5 | 65% | +1.55 | 70% | 12.0 | 16% | Karachi, Lahore, Faisalabad, Rawalpindi |

## 6. Inequality

The **Lorenz curve** orders districts from fewest to most branches per person and plots the cumulative share of branches against the cumulative share of people. The **Gini coefficient** is one minus twice the area under it (0 means branches follow population, 1 means one district has everything). For bank branches it is 0.325 in 2024 and 0.325 in 2020 (2017 population); for bank and microfinance branches together it is 0.304. The **Theil index** is split into a between-province and a within-province part; 24% of the inequality in bank branches is between provinces and the rest is within them. The ten districts with most branches (Karachi, Lahore, Rawalpindi, Islamabad, Faisalabad, Sialkot, Multan, Gujranwala, Gujrat, Peshawar) hold 51% of branches and 31% of people.

## 7. Did low-branch districts catch up?

The change in bank branches per 100,000 people between 2020 and 2024 is regressed on the 2020 level and on annual population growth, with heteroskedasticity-robust (HC3) standard errors. A negative coefficient on the 2020 level would mean districts that started behind gained more (convergence). The estimate is 0.020 (95% interval -0.07 to 0.11, p = 0.66, R² = 0.005), so there is no sign of catch-up. A simple count gives the same message: the 60 districts below the median density in 2020 hold 30% of people and received 15% of the 2,766 net new bank branches, and 14 districts lost branches. This describes what happened; it does not say why.

## 8. Pakistan against other economies

Account ownership in 138 economies is regressed on the log of GDP per person (PPP, constant 2021 international dollars) with robust errors. Each additional doubling of income goes with about 11 more points of account ownership (R² = 0.58). At Pakistan's income the line predicts 52.6%; Pakistan has 27.3%, a shortfall of 25.3 points. A 90% prediction interval for a single economy at that income runs from 27.7% to 77.5%, so Pakistan sits at the very bottom edge of what income allows. Pakistan's account gap between men and women (30 points) is the 2nd largest gap among 138 economies, and its phone gap (65 points) is the largest gap among 138 economies. Cross-country regressions describe association only.

## 9. The placement planner

The planner answers "if we add *k* access points, where should they go?" under three rules. Each point is placed one at a time, and the rule decides which district gets the next one:

- **Equity:** the district with the most people per (branch + 1).
- **Model gap:** the district with the largest remaining shortfall against its expected count; no point is placed where the shortfall is already filled, so fewer than *k* may be placed.
- **Women:** as equity, with each district's need multiplied by its literacy gap between men and women relative to the average gap.

Each rule is judged on five outcomes: districts below half the national average, the share of people in them, the Gini coefficient, people per branch in the worst-served district (a district with no branch counts as one), and the share of points that go to districts where under 40% of women can read.

For 1,000 points (5% of the 18,322-branch network):

| Rule | Districts below half the average | People in them | Gini | People per branch, worst district | Points to districts where under 40% of women read |
| --- | ---: | ---: | ---: | ---: | ---: |
| Today | 41 | 13.6% | 0.304 | 203,368 |  |
| Even out people per branch | 0 | 0.0% | 0.246 | 22,370 | 90% |
| Close the peer-adjusted model gap first | 44 | 16.9% | 0.321 | 203,368 | 0% |
| Even out people per branch, weighted to districts where women are furthest behind | 20 | 7.2% | 0.260 | 65,055 | 86% |

The ranking holds across sizes: with 500 points the equity rule already leaves only 6 low-density districts, and with 4,000 it lowers the Gini to 0.15. The rules disagree because the model's biggest gaps are in cities with many people and many branches, while the districts with the most people per branch are mostly rural. The same logic runs in the dashboard (written in JavaScript); its results were checked against the Python ones for every rule.

## 10. Wallet and agent statistics

The SBP publishes branchless banking statistics each quarter as a PDF. The pipeline reads 9 quarters (Apr-Jun 2024 to Apr-Jun 2026), takes the national table and the table by province, and checks that the provinces add up to the national total. Wallet accounts and agents are divided by the census adult population of the SBP's reporting region (Punjab and Islamabad are reported together). An account is not a person, so accounts per 100 adults can exceed 100 in principle and should be read as an index of intensity.

Some published figures jump out of line: for example Balochistan's accounts rise 45% and fall back in the quarters either side. A figure is flagged when it is more than 25% from the average of the quarters either side (or, for the women's share, more than 4 points), worst first, setting each flagged value aside before checking the next. 3 points are flagged. They stay in the data (flagged) and are left out of charts rather than corrected.

## 11. Survey data

Account ownership by group and over time is read from the Global Findex database through the World Bank API. Every indicator code's label in [`fininc/config.py`](../fininc/config.py) was compared with the World Bank's own name for it (a test pins the meaning of the reason codes). The reasons for having no bank account are published as a share of adults without one, except lack of documents, which is only published as a share of all adults; it is divided by the share of adults without a bank-type account (26.2% after division), a calculation checked against the ratios of the other reasons, which give the same base to within half a point. The reasons for having no mobile money account are published as a share of all adults and are not comparable with the bank figures.

## 12. Reproducibility and testing

- The raw files, their sources, licences and SHA-256 checksums are in `data/raw/MANIFEST.json`; `python -m fininc verify` fails if one changed.
- Randomness (bootstrap, clustering) uses seed 42. No stage writes a timestamp, so rerunning on unchanged data reproduces the outputs.
- Package versions are pinned in `requirements.txt`.
- The tests check the district mapping, each loader's reconciliation to official totals, each model on a case with a known answer, the planner's rules, the dashboard data, the Power BI project (every field a visual or measure uses must exist), the data dictionary against every output table, and that the committed documents are what the templates and data produce.

## 13. What would change the conclusions

- A different definition of low density (the threshold is 50% of the national average) would change the count of districts but the planner's ranking of rules rests on who has the most people per branch, which does not depend on the threshold.
- If branch counts are a poor proxy for access in places served by agents or mobile branches, the rural gap is overstated. The wallet statistics point the same way (agents per adult are lowest in Balochistan) but do not settle it.
- District results from a single register date cannot show whether a branch is open to the public or what it serves.
