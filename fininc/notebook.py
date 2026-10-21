"""Build and run notebooks/analysis.ipynb.

The notebook is written here as a list of cells so that it can be reviewed and tested like code, then executed with
its outputs saved: `python -m fininc notebook`. It recomputes the main results from the district table and checks
them against the pipeline's own outputs, so it is a second, independent route to the same numbers.
"""

from __future__ import annotations

import asyncio
import sys

import nbformat
from nbclient import NotebookClient
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

from .paths import NOTEBOOKS

MD, CODE = "md", "code"

CELLS: list[tuple[str, str]] = [
    (MD, """# Financial inclusion in Pakistan: the analysis, step by step

This notebook walks through the analysis behind the dashboard and the memo. It does not just display results: each
step **recomputes** a result from the district table and **checks it against the pipeline's output**, so a reader can
see where the numbers come from.

Run the whole project first (`python -m fininc all`), then run the notebook from top to bottom.

1. The data
2. The national picture
3. Pakistan against other economies
4. Who is left out
5. Where the branches are
6. How many branches should a district have?
7. Types of district
8. Inequality and catch-up
9. A placement planner
10. The digital layer
11. Conclusions"""),
    (CODE, """import sys
import warnings
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "fininc").is_dir())
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from IPython.display import Image, display

from fininc import config, models
from fininc.paths import FIGURES
from fininc.results import load

pd.set_option("display.width", 140)
pd.set_option("display.max_columns", 30)
plt.rcParams.update({"figure.dpi": 110, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12})

r = load()
units = r.units
print(f"{len(units)} districts, {units['pop'].sum() / 1e6:.1f} million people, {units['branches_2024'].sum():,} branches")"""),

    (MD, """## 1. The data

Four public sources are joined at the level of the **district on its 2020 boundaries** (120 units). Branch and census data
describe districts; the Findex survey describes the country and groups of people. Population is checked against the
official provincial totals, which must match exactly."""),
    (CODE, """check = pd.DataFrame(r.summary["quality"]["census_official_check"])
check[["province", "districts", "pop_2023", "official_2023", "diff_2023", "diff_2017"]]"""),
    (CODE, """assert (check[["diff_2023", "diff_2017"]] == 0).all().all()
units[["unit", "province", "pop", "urban_share", "literacy_female", "ses_index", "banks_2024", "mfb_2024",
       "branches_per_100k"]].sort_values("pop", ascending=False).head(8).round(1)"""),

    (MD, """## 2. The national picture

Branches per 100,000 people, recomputed from the district table. The province table in the pipeline must agree."""),
    (CODE, """by_province = units.groupby("province").agg(pop=("pop", "sum"), branches=("branches_2024", "sum"),
                                              rural_pop=("pop_rural", "sum"), rural_branches=("rural_branches_2024", "sum"))
by_province["per_100k"] = by_province["branches"] / by_province["pop"] * 1e5
by_province["rural_per_100k_rural"] = by_province["rural_branches"] / by_province["rural_pop"] * 1e5
assert np.allclose(by_province["per_100k"].sort_index(), r.provinces.set_index("province")["branches_per_100k"].sort_index())

total = units[["pop", "pop_rural", "branches_2024", "rural_branches_2024", "pop_urban", "urban_branches_2024"]].sum()
print(f"Rural: {total.pop_rural / total['pop']:.0%} of people, {total.rural_branches_2024 / total.branches_2024:.0%} of branches")
print(f"Per 100,000 rural people: {total.rural_branches_2024 / total.pop_rural * 1e5:.1f}; "
      f"per 100,000 urban people: {total.urban_branches_2024 / total.pop_urban * 1e5:.1f}")
by_province.sort_values("per_100k", ascending=False).round(1)"""),

    (MD, """## 3. Pakistan against other economies

Account ownership against income, for every economy with both. A straight line on the log of income gives the
account ownership that income would predict; the gap is Pakistan's shortfall."""),
    (CODE, """cc = r.cross
X = sm.add_constant(cc["gdp_pc_ppp"].map(np.log))
fit = sm.OLS(cc["account"], X).fit()
pak = cc[cc["country"] == "PAK"].iloc[0]
expected = fit.params.iloc[0] + fit.params.iloc[1] * np.log(pak["gdp_pc_ppp"])
assert abs(expected - pak["expected_account"]) < 0.01          # the pipeline's number

fig, ax = plt.subplots(figsize=(7.5, 4.6))
ax.scatter(cc["gdp_pc_ppp"], cc["account"], s=18, color=config.GREY, alpha=0.7, label="Other economies")
grid = np.linspace(cc["gdp_pc_ppp"].min(), cc["gdp_pc_ppp"].max(), 200)
ax.plot(grid, fit.params.iloc[0] + fit.params.iloc[1] * np.log(grid), color=config.NAVY, lw=2, label="Fitted on log income")
ax.scatter(pak["gdp_pc_ppp"], pak["account"], s=70, color=config.ORANGE, zorder=3, label="Pakistan")
ax.set_xscale("log")
ax.set_xlabel("GDP per person, PPP (log scale)")
ax.set_ylabel("Adults with an account (%)")
ax.set_title("Account ownership against income")
ax.legend(frameon=False)
plt.show()
print(f"Pakistan {pak['account']:.1f}% against {expected:.1f}% expected: a shortfall of {expected - pak['account']:.1f} points")
print(f"Rank from the lowest: {int((cc['account'] <= pak['account']).sum())} of {len(cc)}")"""),

    (MD, """## 4. Who is left out

Account ownership by group in the last two survey rounds, and the reasons adults give for having no bank account. The
reason labels are the World Bank's own wording."""),
    (CODE, """seg = r.segments[r.segments["year"].isin([2021, 2024])].pivot_table(index="segment", columns="year", values="value")
seg["change"] = seg[2024] - seg[2021]
seg.sort_values("change").round(1)"""),
    (CODE, """b = r.barriers.sort_values("share_of_unbanked")
fig, ax = plt.subplots(figsize=(7.5, 3.4))
ax.barh(b["reason"], b["share_of_unbanked"], color=[config.ORANGE if v == b["share_of_unbanked"].max() else config.NAVY
                                                    for v in b["share_of_unbanked"]])
for y, v in enumerate(b["share_of_unbanked"]):
    ax.text(v + 1, y, f"{v:.0f}%", va="center", fontsize=9)
ax.set_xlim(0, 80)
ax.set_xlabel("% of adults without a bank account (several reasons allowed)")
ax.set_title("Why adults have no bank account")
plt.show()"""),

    (MD, """## 5. Where the branches are

Branches per 100,000 people vary almost fifty-fold between districts. The districts below half the national average are the
"low-density" districts used throughout."""),
    (CODE, """national = units["branches_2024"].sum() / units["pop"].sum() * 1e5
low = units["branches_per_100k"] < config.LOW_DENSITY_SHARE_OF_AVERAGE * national
print(f"National: {national:.2f} per 100,000. Districts below half of it: {low.sum()} holding "
      f"{units.loc[low, 'pop'].sum() / units['pop'].sum():.1%} of people")
assert low.sum() == r.headline["units_below_half_average"]

best = units.nlargest(5, "branches_per_100k")[["unit", "province", "pop", "branches_2024", "branches_per_100k"]]
worst = units.nsmallest(5, "branches_per_100k")[["unit", "province", "pop", "branches_2024", "branches_per_100k"]]
pd.concat([best, worst]).round(1)"""),
    (CODE, """display(Image(filename=str(FIGURES / "06_map_branch_density.png"), width=620))"""),

    (MD, """## 6. How many branches should a district have?

A negative binomial model of branch counts on population, urban share and a development index. Each district's expected
count comes from a fit that leaves that district out, so a district never helps to predict itself. The notebook refits the
model from scratch and checks it against the pipeline."""),
    (CODE, """df = models.prepare(units.drop(columns=[c for c in units.columns if c in ("log_pop", "urban", "log_density", "log_branch_density")]))
y = df["branches_2024"].to_numpy(float)
Xm = sm.add_constant(df[models.MODEL_FEATURES]).to_numpy()
full = models._fit_nb(y, Xm)
names = ["intercept", *models.MODEL_FEATURES, "alpha"]
pd.DataFrame({"coef": full.params, "std err": full.bse, "p": full.pvalues}, index=names).round(3)"""),
    (CODE, """expected, failures = models._loo_predictions(y, Xm, full)
assert failures == 0
assert np.allclose(expected, units["expected_branches"], rtol=1e-6)
print("Leave-one-out expectations match the pipeline to 6 digits")

p_below, _ = models._nb_cdf(y, expected, float(full.params[-1]))
gap = pd.DataFrame({"unit": units["unit"], "branches": y, "expected": expected.round(0), "shortfall": (expected - y).round(0),
                    "chance_of_so_few": p_below.round(3)})
gap.sort_values("shortfall", ascending=False).head(8)"""),
    (CODE, """fig, ax = plt.subplots(figsize=(6.4, 5))
colour = np.where(units["robust_shortfall"], config.ORANGE, config.NAVY)
ax.scatter(expected, y, s=22, c=colour, alpha=0.8)
lim = [1, max(expected.max(), y.max()) * 1.3]
ax.plot(lim, lim, color=config.GREY, lw=1)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(lim); ax.set_ylim(lim)
for _, row in units[units["robust_shortfall"]].nlargest(5, "branch_gap").iterrows():
    ax.annotate(row["unit"], (row["expected_branches"], row["branches_2024"]), fontsize=8, xytext=(4, -9), textcoords="offset points")
ax.set_xlabel("Expected branches (leave one out)"); ax.set_ylabel("Actual branches")
ax.set_title("Orange: flagged as below expectation")
plt.show()
print(f"Total shortfall {np.maximum(expected - y, 0).sum():,.0f} branches; {int(units['robust_shortfall'].sum())} districts flagged for review")"""),

    (MD, """## 7. Types of district

K-means on four standardised variables gives four types. They form a continuum rather than sharp groups (silhouette about 0.3), so
the types are a summary, not a discovery."""),
    (CODE, """clustered, info = models.cluster_units(units.drop(columns=["cluster", "cluster_rank"]))
assert (clustered["cluster"].to_numpy() == units["cluster"].to_numpy()).all()
pd.DataFrame(info["profile"]).round(1)"""),
    (CODE, """fig, ax = plt.subplots(figsize=(6.8, 4.4))
palette = dict(zip(models.CLUSTER_NAMES, [config.ORANGE, config.AMBER, config.TEAL, config.NAVY]))
for name, g in units.groupby("cluster"):
    ax.scatter(g["ses_index"], g["branches_per_100k"], s=g["pop"] / 1.5e5 + 10, alpha=0.7, label=name, color=palette[name])
ax.set_yscale("symlog", linthresh=2)
ax.set_xlabel("Development index"); ax.set_ylabel("Branches per 100,000 people")
ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.set_title("District types (bubble size: population)")
plt.show()"""),

    (MD, """## 8. Inequality and catch-up

The Gini coefficient measures how unevenly branches are spread against population, and a regression asks whether districts that
started with fewer bank branches per person gained more between 2020 and 2024."""),
    (CODE, """x20, y20, g20 = models.lorenz(units["pop_2017"].to_numpy(float), units["banks_2020"].to_numpy(float))
x24, y24, g24 = models.lorenz(units["pop"].to_numpy(float), units["banks_2024"].to_numpy(float))
assert abs(g24 - r.summary["inequality"]["banks_2024"]["gini"]) < 1e-9
fig, ax = plt.subplots(figsize=(5.2, 5))
ax.plot([0, 1], [0, 1], color=config.GREY, lw=1)
ax.plot(x20, y20, color=config.AMBER, lw=2, label=f"2020 (Gini {g20:.3f})")
ax.plot(x24, y24, color=config.NAVY, lw=2, ls="--", label=f"2024 (Gini {g24:.3f})")
ax.set_xlabel("Cumulative share of people (fewest branches per person first)")
ax.set_ylabel("Cumulative share of bank branches")
ax.legend(frameon=False); ax.set_title("Lorenz curves of bank branches")
plt.show()"""),
    (CODE, """cx = sm.add_constant(units[["density_2020", "pop_growth_pct_pa"]])
conv = sm.OLS(units["density_change"], cx).fit(cov_type="HC3")
print(conv.summary().tables[1])
low_half = units["density_2020"] < units["density_2020"].median()
print(f"\\nDistricts that started in the lower half hold {units.loc[low_half, 'pop'].sum() / units['pop'].sum():.0%} of people and "
      f"received {units.loc[low_half, 'banks_change'].sum() / units['banks_change'].sum():.0%} of {units['banks_change'].sum():,} net new bank branches")"""),

    (MD, """## 9. A placement planner

If 1,000 new access points are added, where should they go? Three rules place them one at a time; each is judged on the same
five outcomes. The result that matters: **where points go decides who is reached**, and the rules disagree."""),
    (CODE, """k = r.scenario["default_k"]
rows = {"Today": models.outcomes(units)}
for name in models.STRATEGIES:
    rows[name] = models.outcomes(units, models.allocate(units, k, name))
planner = pd.DataFrame({k_: v.as_dict() for k_, v in rows.items()}).T.apply(pd.to_numeric)
planner["population_below_half"] = (planner["population_below_half"] * 100).round(1)
planner["gini"] = planner["gini"].round(3)
planner["share_to_low_female_literacy"] = (planner["share_to_low_female_literacy"] * 100).round(0)
saved = {s["strategy"]: s for s in r.summary["scenario_default"]}
assert planner.loc["equity", "units_below_half"] == saved["equity"]["units_below_half"]
assert abs(rows["equity"].gini - saved["equity"]["gini"]) < 1e-9
planner[["units_below_half", "population_below_half", "gini", "worst_people_per_branch", "placed", "share_to_low_female_literacy"]]"""),
    (CODE, """display(Image(filename=str(FIGURES / "14_planner_outcomes.png"), width=720))"""),

    (MD, """## 10. The digital layer

Wallet accounts and agents from the State Bank's quarterly statistics. Agents have grown, but a falling share is active."""),
    (CODE, """nat = r.bb_national.copy()
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
axes[0].plot(nat["quarter"], nat["agents"] / 1e3, marker="o", color=config.NAVY)
axes[0].set_title("Registered agents (thousand)")
axes[1].plot(nat["quarter"], nat["active_agent_share"], marker="o", color=config.ORANGE, label="Agents active")
axes[1].plot(nat["quarter"], nat["active_account_share"], marker="o", color=config.TEAL, label="Accounts active")
axes[1].set_title("Share that are active (%)"); axes[1].legend(frameon=False)
for ax in axes:
    ax.tick_params(axis="x", rotation=60)
plt.tight_layout(); plt.show()"""),

    (MD, """## 11. Conclusions

Every figure below is computed above, not typed."""),
    (CODE, """pak_row = r.summary["cross_country"]["pakistan"]
conv_p = conv.pvalues["density_2020"]
print(f"- Only {pak_row['account']:.0f}% of adults have an account: {pak_row['shortfall_pts']:.0f} points below the {pak_row['expected']:.0f}% that income predicts.")
print(f"- Women {pak_row['account_women']:.0f}% against men {pak_row['account_men']:.0f}%; phones {pak_row['phone_women']:.0f}% against {pak_row['phone_men']:.0f}%.")
print(f"- Rural Pakistan has {total.rural_branches_2024 / total.pop_rural * 1e5:.1f} branches per 100,000 against {total.urban_branches_2024 / total.pop_urban * 1e5:.1f} urban.")
print(f"- Districts that started behind did not catch up (slope {conv.params['density_2020']:.3f}, p = {conv_p:.2f}).")
print(f"- {k:,} new points placed to even out people per branch cut the Gini from {rows['Today'].gini:.3f} to {rows['equity'].gini:.3f}; "
      f"placed by the model gap they raise it to {rows['gap'].gini:.3f}.")"""),
]


def build(execute: bool = True) -> None:
    nb = new_notebook()
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.metadata["language_info"] = {"name": "python"}
    nb.cells = [new_markdown_cell(text) if kind == MD else new_code_cell(text) for kind, text in CELLS]
    path = NOTEBOOKS / "analysis.ipynb"
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    if execute:
        if sys.platform == "win32":  # pyzmq needs the selector loop; the default one only warns
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": str(NOTEBOOKS)}}).execute()
    nbformat.write(nb, path)
    print(f"[notebook] {len(nb.cells)} cells -> {path}")
