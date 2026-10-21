# Memo: where new access points should go

**For:** the financial inclusion team of a regulator, development bank or microfinance provider
**Evidence:** this repository. Branches at {{register_date}}, census {{census_year}}, Global Findex {{findex_year}}, wallet statistics {{wallet_first}} to {{wallet_last}}.

## Bottom line

Pakistan has {{acct:.0f}}% of adults with an account, {{shortfall_pts:.0f}} points below what its income predicts, and the gap is widest for women and for rural districts. Four years of branch growth did not close it. If {{k_default:,}} new access points ({{k_share:.0f}}% of today's network) are placed to **even out people per branch**, no district stays below half the national average and inequality of branches falls by {{plan_gini_cut:.0f}}%. If they are placed by a peer-adjusted model gap, they go to big cities and inequality rises.

## What the data show

**Low ownership is not an income story.** At Pakistan's income ({{gdp_pc:,.0f}} dollars per person, PPP) the typical economy has {{expected_acct:.0f}}% of adults with an account; Pakistan has {{acct:.0f}}%, which is {{rank_lowest_ord}} lowest of {{n_economies}}. Men are at {{acct_men:.0f}}% and women at {{acct_women:.0f}}%.

**The people left out are getting further away.** From 2021 to 2024 men gained {{men_gain:.0f}} points and the richest 60% gained {{rich_gain:.0f}}. Women lost {{women_loss:.1f}} points and the poorest 40% lost {{poor_loss:.0f}}. Behind the account gap sits a phone gap: {{phone_women:.0f}}% of women own a phone against {{phone_men:.0f}}% of men.

**Reasons are money and cost.** Of adults without a bank account, {{b_money:.0f}}% say they do not have enough money, {{b_cost:.0f}}% that services are too expensive, {{b_distance:.0f}}% that the branch is too far, {{b_docs:.0f}}% that they lack documents and {{b_trust:.0f}}% that they do not trust financial institutions. For mobile money, {{mm_money:.0f}}% of all adults say they lack the money to use it and {{mm_cost:.0f}}% say it is too expensive.

**Branches follow cities.** {{rural_pop_share:.0f}}% of people are rural, with {{rural_branch_share:.0f}}% of branches. The ten districts with the most branches hold {{top10_branch_share:.0f}}% of them and {{top10_pop_share:.0f}}% of people; the {{bottom20_units}} districts with the fewest branches per person hold {{bottom20_pop:.0f}}% of people and {{bottom20_branches:.0f}}% of branches. Microfinance banks are more rural ({{mfb_rural_share:.0f}}% of their branches) than banks ({{bank_rural_share:.0f}}%).

**New branches did not reach the districts that needed them.** Of {{net_new:,}} net new bank branches since 2020, the half of districts that started with the fewest per person received {{low_new_share:.0f}}%. The slope of gains against starting level is {{conv_slope:.3f}} (95% interval {{conv_lo:.2f}} to {{conv_hi:.2f}}, p = {{conv_p:.2f}}): no sign of catch-up.

**The wallet network grew by count, not by use.** Agents rose {{agents_growth:.0f}}% to {{wallet_agents_k:,.0f}} thousand, yet the share that were active fell from {{active_agents_first:.0f}}% to {{active_agents_last:.0f}}%. Only {{active_accounts_last:.0f}}% of {{wallet_accounts_m:.0f}} million wallet accounts were active.

## Recommendations

**1. Place new points to even out people per branch, and use the model gap to audit cities.**
Of {{k_default:,}} new points, the equity rule leaves {{plan_units_equity}} districts below half the national average (today {{plan_units_before}}), cuts the Gini coefficient from {{plan_gini_before:.2f}} to {{plan_gini_equity:.2f}} and brings the worst district from {{plan_worst_before:,.0f}} people per branch to {{plan_worst_equity:,.0f}}. The model-gap rule leaves {{plan_units_gap}} districts below half the average (the average itself rises as points go to cities), raises the Gini to {{plan_gini_gap:.2f}} and does not change the worst district. The model is still useful as a check: it flags {{n_robust}} districts as short of branches for their size (for example {{robust_3}}) and puts the total shortfall at about {{shortfall_total:,.0f}} branches (90% range {{shortfall_lo:,.0f}} to {{shortfall_hi:,.0f}}). Chance alone would flag about {{chance_flags:.0f}} of {{n_units}} districts, so treat the flagged districts as cases to review, not as a rollout list.

**2. Reach rural Pakistan through microfinance branches and agents first.**
Rural residents have {{rural_per_100k:.1f}} branches per 100,000 against {{urban_per_100k:.1f}} for urban residents ({{urban_rural_ratio:.1f}} times as many). Microfinance banks already put {{mfb_rural_share:.0f}}% of their branches in rural areas. Wallet agents per 100,000 adults range from {{agents_baloch:.0f}} in Balochistan and {{agents_kp:.0f}} in Khyber Pakhtunkhwa to {{agents_punjab:.0f}} in Punjab: the widest gap in the digital layer is in those two provinces.

**3. Design products for low incomes and low cost before distance.**
Opening more branches addresses the reason {{b_distance:.0f}}% give. Not having enough money ({{b_money:.0f}}%) and cost ({{b_cost:.0f}}%) call for different tools: zero-fee accounts with no minimum balance, cheap or free transfers, and products that work with irregular income. Simpler identity checks help the {{b_docs:.0f}}% who lack documents, and visible complaint handling and local agents people know address the {{b_trust:.0f}}% who do not trust financial institutions.

**4. Close the phone gap alongside the account gap for women.**
A woman without a phone in her own name cannot use a wallet. Pair account opening with SIM and handset access, recruit women agents and pay government transfers into accounts held in women's names. Where branches go matters less here than who they serve: the districts with the fewest branches are also those where women read least, so the equity rule already sends {{plan_female_equity:.0f}}% of points to the {{plan_low_female_units}} districts where under {{low_female_literacy:.0f}}% of women can read. A variant that weights districts by the literacy gap between men and women ({{plan_female_women:.0f}}% to those districts) costs little in inequality (Gini {{plan_gini_women:.2f}} against {{plan_gini_equity:.2f}}), so it can be used when the stated goal is the gender gap rather than overall access.

**5. Pay for activity, not for registration.**
The agent network is {{agents_growth:.0f}}% larger, but the share of agents that are active fell from {{active_agents_first:.0f}}% to {{active_agents_last:.0f}}%. Tie agent incentives to monthly activity and track the active share by district.

**6. Measure use, not presence, and publish it by district.**
This analysis could count branches but not customers. District-level data on active wallets, agent locations and transaction values would turn the planner from a placement tool into a performance tool. Track two numbers each year: the Gini coefficient of branches ({{plan_gini_before:.3f}} now, banks and microfinance together) and the number of districts below half the national average ({{units_below_half}} now).

## What this analysis cannot tell you

- Whether a new point would be used. Branches are a necessary condition, not a measure of inclusion.
- Costs. The planner treats a branch, an agent and a wallet campaign alike.
- Account ownership by district. The Findex survey is national and by group; the district results are about branches.
- Cause. The access model compares districts with their peers; it does not show that more branches would raise account ownership.
- Azad Jammu & Kashmir and Gilgit-Baltistan, which the census district tables do not cover.

## Key numbers

The districts furthest below the model's expectation (ranked by shortfall in branches):

{{table_shortfalls}}

Placing {{k_default:,}} new points under three rules ("people in them" is the share of the population living in districts below half the national average):

{{table_scenarios}}

Method, data and checks: [`docs/methodology.md`](methodology.md), [`docs/data_sources.md`](data_sources.md).
