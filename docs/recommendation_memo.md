# Memo: where new access points should go

**For:** the financial inclusion team of a regulator, development bank or microfinance provider
**Evidence:** this repository. Branches at 2024-12-31, census 2023, Global Findex 2024, wallet statistics Apr-Jun 2024 to Apr-Jun 2026.

## Bottom line

Pakistan has 27% of adults with an account, 25 points below what its income predicts, and the gap is widest for women and for rural districts. Four years of branch growth did not close it. If 1,000 new access points (5% of today's network) are placed to **even out people per branch**, no district stays below half the national average and inequality of branches falls by 19%. If they are placed by a peer-adjusted model gap, they go to big cities and inequality rises.

## What the data show

**Low ownership is not an income story.** At Pakistan's income (5,502 dollars per person, PPP) the typical economy has 53% of adults with an account; Pakistan has 27%, which is 6th lowest of 138. Men are at 42% and women at 12%.

**The people left out are getting further away.** From 2021 to 2024 men gained 14 points and the richest 60% gained 13. Women lost 1.6 points and the poorest 40% lost 4. Behind the account gap sits a phone gap: 30% of women own a phone against 95% of men.

**Reasons are money and cost.** Of adults without a bank account, 64% say they do not have enough money, 48% that services are too expensive, 32% that the branch is too far, 26% that they lack documents and 19% that they do not trust financial institutions. For mobile money, 47% of all adults say they lack the money to use it and 35% say it is too expensive.

**Branches follow cities.** 61% of people are rural, with 30% of branches. The ten districts with the most branches hold 51% of them and 31% of people; the 48 districts with the fewest branches per person hold 20% of people and 8% of branches. Microfinance banks are more rural (52% of their branches) than banks (28%).

**New branches did not reach the districts that needed them.** Of 2,766 net new bank branches since 2020, the half of districts that started with the fewest per person received 15%. The slope of gains against starting level is 0.020 (95% interval -0.07 to 0.11, p = 0.66): no sign of catch-up.

**The wallet network grew by count, not by use.** Agents rose 26% to 837 thousand, yet the share that were active fell from 42% to 26%. Only 47% of 159 million wallet accounts were active.

## Recommendations

**1. Place new points to even out people per branch, and use the model gap to audit cities.**
Of 1,000 new points, the equity rule leaves 0 districts below half the national average (today 41), cuts the Gini coefficient from 0.30 to 0.25 and brings the worst district from 203,368 people per branch to 22,370. The model-gap rule leaves 44 districts below half the average (the average itself rises as points go to cities), raises the Gini to 0.32 and does not change the worst district. The model is still useful as a check: it flags 15 districts as short of branches for their size (for example Gujranwala, Sheikhupura, Hyderabad) and puts the total shortfall at about 2,362 branches (90% range 785 to 5,509). Chance alone would flag about 12 of 120 districts, so treat the flagged districts as cases to review, not as a rollout list.

**2. Reach rural Pakistan through microfinance branches and agents first.**
Rural residents have 3.7 branches per 100,000 against 13.7 for urban residents (3.7 times as many). Microfinance banks already put 52% of their branches in rural areas. Wallet agents per 100,000 adults range from 252 in Balochistan and 420 in Khyber Pakhtunkhwa to 661 in Punjab: the widest gap in the digital layer is in those two provinces.

**3. Design products for low incomes and low cost before distance.**
Opening more branches addresses the reason 32% give. Not having enough money (64%) and cost (48%) call for different tools: zero-fee accounts with no minimum balance, cheap or free transfers, and products that work with irregular income. Simpler identity checks help the 26% who lack documents, and visible complaint handling and local agents people know address the 19% who do not trust financial institutions.

**4. Close the phone gap alongside the account gap for women.**
A woman without a phone in her own name cannot use a wallet. Pair account opening with SIM and handset access, recruit women agents and pay government transfers into accounts held in women's names. Where branches go matters less here than who they serve: the districts with the fewest branches are also those where women read least, so the equity rule already sends 90% of points to the 62 districts where under 40% of women can read. A variant that weights districts by the literacy gap between men and women (86% to those districts) costs little in inequality (Gini 0.26 against 0.25), so it can be used when the stated goal is the gender gap rather than overall access.

**5. Pay for activity, not for registration.**
The agent network is 26% larger, but the share of agents that are active fell from 42% to 26%. Tie agent incentives to monthly activity and track the active share by district.

**6. Measure use, not presence, and publish it by district.**
This analysis could count branches but not customers. District-level data on active wallets, agent locations and transaction values would turn the planner from a placement tool into a performance tool. Track two numbers each year: the Gini coefficient of branches (0.304 now, banks and microfinance together) and the number of districts below half the national average (41 now).

## What this analysis cannot tell you

- Whether a new point would be used. Branches are a necessary condition, not a measure of inclusion.
- Costs. The planner treats a branch, an agent and a wallet campaign alike.
- Account ownership by district. The Findex survey is national and by group; the district results are about branches.
- Cause. The access model compares districts with their peers; it does not show that more branches would raise account ownership.
- Azad Jammu & Kashmir and Gilgit-Baltistan, which the census district tables do not cover.

## Key numbers

The districts furthest below the model's expectation (ranked by shortfall in branches):

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

Placing 1,000 new points under three rules ("people in them" is the share of the population living in districts below half the national average):

| Rule | Districts below half the average | People in them | Gini | People per branch, worst district | Points to districts where under 40% of women read |
| --- | ---: | ---: | ---: | ---: | ---: |
| Today | 41 | 13.6% | 0.304 | 203,368 |  |
| Even out people per branch | 0 | 0.0% | 0.246 | 22,370 | 90% |
| Close the peer-adjusted model gap first | 44 | 16.9% | 0.321 | 203,368 | 0% |
| Even out people per branch, weighted to districts where women are furthest behind | 20 | 7.2% | 0.260 | 65,055 | 86% |

Method, data and checks: [`docs/methodology.md`](methodology.md), [`docs/data_sources.md`](data_sources.md).
