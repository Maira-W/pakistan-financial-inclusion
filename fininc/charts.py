"""Static figures for the README, the notebook and the documents (matplotlib).

Run through the pipeline:  python -m fininc report
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon as MplPolygon

from . import config
from .paths import FIGURES
from .results import Results, load

NAVY, TEAL, ORANGE, AMBER, GREY, PURPLE = (config.NAVY, config.TEAL, config.ORANGE, config.AMBER, config.GREY,
                                           config.PURPLE)
CLUSTER_COLOURS = {"Frontier and remote": ORANGE, "Developing rural": AMBER,
                   "Established districts": TEAL, "Metropolitan hubs": NAVY}
PEER_COLOURS = {"Pakistan": ORANGE, "India": NAVY, "Bangladesh": TEAL, "Sri Lanka": GREY}

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 160, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left", "axes.grid": True,
    "grid.color": "#E6E9EE", "grid.linewidth": 0.8, "axes.axisbelow": True, "legend.frameon": False,
    "axes.edgecolor": "#AEB6C2", "xtick.color": "#444", "ytick.color": "#444", "axes.labelcolor": "#333",
})


def _save(fig: plt.Figure, name: str, source: str | None = None) -> None:
    if source:
        fig.text(0.01, -0.01, source, fontsize=7.5, color="#667", ha="left", va="top")
    fig.savefig(FIGURES / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def _title(ax, text: str, sub: str | None = None) -> None:
    ax.set_title(text, loc="left", pad=22 if sub else 8)
    if sub:
        ax.text(0, 1.015, sub, transform=ax.transAxes, fontsize=9, color="#556", va="bottom")


# ---------------------------------------------------------------------------
# maps
# ---------------------------------------------------------------------------
def _rings(geometry: dict):
    polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
    for polygon in polygons:
        yield polygon[0]


def _draw_map(ax, r: Results, colour_of, edge: str = "white", width: float = 0.35) -> None:
    patches, colours = [], []
    for feature in r.boundaries["features"]:
        colour = colour_of(feature["properties"]["unit_id"])
        for ring in _rings(feature["geometry"]):
            patches.append(MplPolygon(ring, closed=True))
            colours.append(colour)
    ax.add_collection(PatchCollection(patches, facecolor=colours, edgecolor=edge, linewidth=width))
    outline = [MplPolygon(ring, closed=True) for f in r.province_boundaries["features"]
               for ring in _rings(f["geometry"])]
    ax.add_collection(PatchCollection(outline, facecolor="none", edgecolor="#2B2F36", linewidth=0.9))
    ax.set_xlim(60.7, 77.2)
    ax.set_ylim(23.4, 37.3)
    ax.set_aspect(1 / np.cos(np.deg2rad(30)))
    ax.axis("off")
    ax.grid(False)


# ---------------------------------------------------------------------------
# 1-5: Findex and the cross-country picture
# ---------------------------------------------------------------------------
def fig_cross_country(r: Results) -> None:
    df = r.cross.dropna(subset=["account", "gdp_pc_ppp"]).sort_values("gdp_pc_ppp")
    pak = df[df["country"] == "PAK"].iloc[0]
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    ax.fill_between(df["gdp_pc_ppp"], df["pred_low"], df["pred_high"], color="#DDE6EE", alpha=0.7, lw=0,
                    label="90% prediction range")
    ax.plot(df["gdp_pc_ppp"], df["expected_account"], color="#5C6B7C", lw=1.6, label="Expected at this income")
    others = df[~df["country"].isin(config.SOUTH_ASIA)]
    ax.scatter(others["gdp_pc_ppp"], others["account"], s=22, color="#B8C2CE", edgecolor="white", lw=0.4, zorder=3)
    for code, colour in (("IND", NAVY), ("BGD", TEAL), ("LKA", GREY), ("NPL", "#6A994E")):
        row = df[df["country"] == code]
        if len(row):
            row = row.iloc[0]
            ax.scatter(row["gdp_pc_ppp"], row["account"], s=70, color=colour, edgecolor="white", lw=0.8, zorder=4)
            ax.annotate(row["name"], (row["gdp_pc_ppp"], row["account"]), xytext=(6, 5), textcoords="offset points",
                        fontsize=9, color=colour)
    ax.scatter(pak["gdp_pc_ppp"], pak["account"], s=150, color=ORANGE, edgecolor="white", lw=1.2, zorder=5)
    ax.annotate(f"Pakistan: {pak['account']:.0f}% have an account\nbut {pak['expected_account']:.0f}% expected at this income",
                (pak["gdp_pc_ppp"], pak["account"]), xytext=(18, -42), textcoords="offset points", fontsize=9.5,
                color=ORANGE, fontweight="bold", arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1))
    ax.set_xscale("log")
    ax.set_xticks([1000, 2000, 5000, 10000, 20000, 50000, 100000])
    ax.set_xticklabels(["1k", "2k", "5k", "10k", "20k", "50k", "100k"])
    ax.set_xlabel("GDP per capita, PPP (constant 2021 international $, log scale)")
    ax.set_ylabel("Adults with an account (%)")
    ax.set_ylim(0, 105)
    ax.legend(loc="lower right")
    _title(ax, "Pakistan is far below what its income would predict",
           f"Account ownership vs income across {len(df)} economies, Global Findex {config.FINDEX_YEAR}")
    _save(fig, "01_cross_country_account_vs_income.png",
          "Source: World Bank Global Findex 2025 and World Development Indicators. Line is an OLS fit on log income.")


def fig_gender_gaps(r: Results) -> None:
    names = {"PAK": "Pakistan", "IND": "India", "BGD": "Bangladesh", "LKA": "Sri Lanka"}
    cs = r.cross.set_index("country")
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.6), sharey=True)
    for ax, (women, men, title, sub) in zip(axes, (
            ("account_women", "account_men", "Having an account", "Share of adults with an account (%)"),
            ("phone_women", "phone_men", "Owning a mobile phone", "Share of adults who own a phone (%)"))):
        x = np.arange(len(names))
        w = [cs.loc[c, women] for c in names]
        m = [cs.loc[c, men] for c in names]
        ax.bar(x - 0.19, w, 0.38, color=ORANGE, label="Women")
        ax.bar(x + 0.19, m, 0.38, color=NAVY, label="Men")
        for i, (a, b) in enumerate(zip(w, m)):
            ax.text(i - 0.19, a + 1.5, f"{a:.0f}", ha="center", fontsize=8.5, color=ORANGE)
            ax.text(i + 0.19, b + 1.5, f"{b:.0f}", ha="center", fontsize=8.5, color=NAVY)
            gap = int(round(b - a))
            ax.text(i, -11, "no gap" if gap == 0 else f"gap {gap:+d}", ha="center", fontsize=8.5, color="#333",
                    fontweight="bold" if i == 0 else "normal")
        ax.set_xticks(x)
        ax.set_xticklabels(list(names.values()))
        ax.set_ylim(0, 108)
        _title(ax, title, sub)
    axes[0].legend(loc="upper right", ncol=2)
    axes[0].set_ylabel("%")
    pak = r.summary["cross_country"]["pakistan"]
    rank_a, n = r.summary["cross_country"]["rank_largest_account_gap"]
    rank_p, _ = r.summary["cross_country"]["rank_largest_phone_gap"]
    fig.suptitle(f"The phone gap comes first: {pak['phone_gap']:.0f} points between men and women "
                 f"(rank {rank_p} of {n}); account gap {pak['account_gap']:.0f} points (rank {rank_a})",
                 x=0.01, ha="left", fontsize=11.5, fontweight="bold", y=1.04)
    _save(fig, "02_gender_gaps_accounts_and_phones.png", f"Source: World Bank Global Findex {config.FINDEX_YEAR}.")


def fig_segments(r: Results) -> None:
    seg = r.segments.pivot_table(index=["group", "segment"], columns="year", values="value").reset_index()
    order = ["Women", "Men", "Poorest 40%", "Richest 60%", "Primary education or less",
             "Secondary education or more", "Out of the labour force", "In the labour force", "Rural", "Urban",
             "Young adults (15-24)", "Older adults (25+)"]
    seg = seg.set_index("segment").loc[order].reset_index()
    fig, ax = plt.subplots(figsize=(8.6, 5.6))
    y = np.arange(len(seg))[::-1]
    for i, row in seg.iterrows():
        yy = y[i]
        v21, v24 = row.get(2021, np.nan), row.get(2024, np.nan)
        colour = ORANGE if row["group"] in ("gender", "income", "labour") and row["segment"] in (
            "Women", "Poorest 40%", "Out of the labour force") else NAVY
        if not np.isnan(v21):
            ax.plot([v21, v24], [yy, yy], color="#C5CDD8", lw=3, zorder=1)
            ax.scatter(v21, yy, s=55, facecolor="white", edgecolor=colour, lw=1.6, zorder=3)
        ax.scatter(v24, yy, s=75, color=colour, zorder=4)
        right = max(v24, v21) if not np.isnan(v21) else v24
        ax.text(right + 1.6, yy, f"{v24:.0f}%", va="center", fontsize=9, color=colour, fontweight="bold")
        if not np.isnan(v21):
            change = v24 - v21
            ax.text(59, yy, f"{change:+.1f}", va="center", ha="right", fontsize=9, color=TEAL if change >= 0 else ORANGE)
    ax.set_yticks(y)
    ax.set_yticklabels(seg["segment"])
    ax.set_xlim(0, 60)
    ax.set_ylim(-0.7, len(seg) + 0.6)
    ax.set_xlabel("Adults with an account (%)")
    ax.text(59, len(seg) - 0.4, "Change in\npoints", fontsize=8.5, color="#556", ha="right", va="bottom")
    ax.legend(handles=[Line2D([], [], marker="o", color="w", markerfacecolor="white", markeredgecolor=NAVY,
                              markersize=8, label="2021"),
                       Line2D([], [], marker="o", color="w", markerfacecolor=NAVY, markersize=9, label="2024")],
              loc="upper center", bbox_to_anchor=(0.45, -0.1), ncol=2)
    _title(ax, "Gains went to groups that were already included",
           "Orange: women, the poorest 40% and adults outside the labour force lost ground between 2021 and 2024")
    _save(fig, "03_who_is_left_out.png",
          "Source: World Bank Global Findex. Rural and urban are published for 2024 only.")


def fig_barriers(r: Results) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 6.9), gridspec_kw={"height_ratios": [1.5, 1], "hspace": 0.62})
    b = r.barriers.sort_values("share_of_unbanked")
    colours = [ORANGE if v == b["share_of_unbanked"].max() else NAVY for v in b["share_of_unbanked"]]
    bars = axes[0].barh(b["reason"], b["share_of_unbanked"], color=colours)
    for bar, derived in zip(bars, b["derived"]):
        if derived:
            bar.set_hatch("///")
            bar.set_edgecolor("white")
    for bar, v in zip(bars, b["share_of_unbanked"]):
        axes[0].text(v + 1, bar.get_y() + bar.get_height() / 2, f"{v:.0f}%", va="center", fontsize=9)
    axes[0].set_xlim(0, 80)
    _title(axes[0], "Why adults have no bank account", "% of adults without a bank or similar account")
    m = r.mm_barriers.sort_values("value")
    bars = axes[1].barh(m["reason"], m["value"], color=TEAL)
    for bar, v in zip(bars, m["value"]):
        axes[1].text(v + 1, bar.get_y() + bar.get_height() / 2, f"{v:.0f}%", va="center", fontsize=9)
    axes[1].set_xlim(0, 65)
    _title(axes[1], "Why adults have no mobile money account", "% of all adults aged 15+, as published (not comparable with the top panel)")
    _save(fig, "04_barriers.png",
          "Source: World Bank Global Findex 2024. Hatched bar: documentation share derived from the all-adults figure.")


def fig_instruments(r: Results) -> None:
    panel = r.panel[r.panel["country"] == "PAK"]
    series = {"account.t.d": ("Any account", NAVY), "fiaccount.t.d": ("Bank or similar institution", GREY),
              "mobileaccount.t.d": ("Mobile money", TEAL), "g20.any": ("Made or received a digital payment", ORANGE)}
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    nudge = {"fiaccount.t.d": -0.9, "mobileaccount.t.d": 0.5}      # keeps the two end labels apart
    for ind, (label, colour) in series.items():
        s = panel[panel["indicator"] == ind].sort_values("year")
        ax.plot(s["year"], s["value"], marker="o", lw=2.4 if ind == "account.t.d" else 1.8, color=colour, label=label)
        ax.text(s["year"].iloc[-1] + 0.3, s["value"].iloc[-1] + nudge.get(ind, 0), f"{s['value'].iloc[-1]:.0f}%",
                va="center", fontsize=9, color=colour, fontweight="bold")
    ax.set_xticks([2011, 2014, 2017, 2021, 2024])
    ax.set_xlim(2010.5, 2025.6)
    ax.set_ylabel("Adults (%)")
    ax.legend(loc="upper left")
    fi21 = panel[(panel["indicator"] == "fiaccount.t.d") & (panel["year"] == 2021)]["value"].iloc[0]
    fi24 = panel[(panel["indicator"] == "fiaccount.t.d") & (panel["year"] == 2024)]["value"].iloc[0]
    mm21 = panel[(panel["indicator"] == "mobileaccount.t.d") & (panel["year"] == 2021)]["value"].iloc[0]
    mm24 = panel[(panel["indicator"] == "mobileaccount.t.d") & (panel["year"] == 2024)]["value"].iloc[0]
    _title(ax, "Mobile money has caught up with the bank account",
           f"Pakistan: mobile money rose from {mm21:.0f}% to {mm24:.0f}% of adults between 2021 and 2024, "
           f"bank accounts from {fi21:.0f}% to {fi24:.0f}%")
    _save(fig, "05_account_types.png", "Source: World Bank Global Findex.")


# ---------------------------------------------------------------------------
# 6-9: where branches are
# ---------------------------------------------------------------------------
def fig_map_density(r: Results) -> None:
    units = r.units.set_index("unit_id")
    bins = [0, 2, 4, 6, 9, 14, 40]
    colours = ["#7A1F0A", ORANGE, "#F4A582", "#CFE3E0", TEAL, NAVY]
    cmap, norm = ListedColormap(colours), BoundaryNorm(bins, len(colours))
    fig, ax = plt.subplots(figsize=(7.4, 6.8))
    _draw_map(ax, r, lambda uid: cmap(norm(units.loc[uid, "branches_per_100k"])))
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colours]
    labels = ["Under 2", "2 to 4", "4 to 6", "6 to 9", "9 to 14", "14 or more"]
    ax.legend(handles, labels, title="Bank and microfinance\nbranches per 100,000 people", loc="lower right",
              bbox_to_anchor=(1.02, 0.02), fontsize=9, title_fontsize=9)
    ax.set_ylim(23.4, 38.2)
    ax.text(0.0, 1.0, "Branches thin out away from the big cities", transform=ax.transAxes, fontsize=12.5,
            fontweight="bold", va="bottom")
    ax.text(0.0, 0.965, f"National average {r.headline['branches_per_100k']:.1f} per 100,000; "
            f"{r.headline['units_below_half_average']} of {r.headline['units']} districts are below half of it",
            transform=ax.transAxes, fontsize=9, color="#556", va="top")
    _save(fig, "06_map_branch_density.png",
          "Sources: SBP branch register, 31 Dec 2024; PBS Census 2023; geoBoundaries (WFP). AJK and Gilgit-Baltistan not covered.")


def fig_map_gap(r: Results) -> None:
    units = r.units.set_index("unit_id")
    ratio = (units["branches_2024"] / units["expected_branches"]).clip(0.4, 1.6)
    from matplotlib import cm
    from matplotlib.colors import TwoSlopeNorm
    cmap = cm.get_cmap("BrBG")
    norm = TwoSlopeNorm(vmin=0.4, vcenter=1.0, vmax=1.6)
    fig, ax = plt.subplots(figsize=(7.4, 6.8))
    _draw_map(ax, r, lambda uid: cmap(norm(ratio.loc[uid])))
    flagged = units[units["robust_shortfall"]]
    marked = [MplPolygon(ring, closed=True) for f in r.boundaries["features"]
              if f["properties"]["unit_id"] in set(flagged.index) for ring in _rings(f["geometry"])]
    ax.add_collection(PatchCollection(marked, facecolor="none", edgecolor="#111", linewidth=1.7))
    ax.set_ylim(23.4, 38.2)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, ax=ax, shrink=0.45, pad=0.0, location="bottom", aspect=28)
    cbar.set_label("Actual branches / expected branches (brown: fewer than expected)", fontsize=9)
    ax.text(0.0, 1.0, "Which districts have fewer branches than similar districts?", transform=ax.transAxes,
            fontsize=12.5, fontweight="bold", va="bottom")
    ax.text(0.0, 0.965, f"Black outline: {len(flagged)} districts flagged as short of branches, "
            "from central Punjab\nto small remote districts in Balochistan and Khyber Pakhtunkhwa",
            transform=ax.transAxes, fontsize=9, color="#556", va="top")
    _save(fig, "07_map_model_gap.png",
          "Model: negative binomial on population, urban share and development index; expected values are leave-one-out.")


def fig_province_access(r: Results) -> None:
    prov = r.provinces.copy()
    order = ["Balochistan", "Khyber Pakhtunkhwa", "Sindh", "Punjab", "Islamabad"]
    prov = prov.set_index("province").loc[order].reset_index()
    wal = r.bb_regions[r.bb_regions["quarter"] == r.bb_regions["quarter"].max()].set_index("region")
    region = {"Balochistan": "Balochistan", "Khyber Pakhtunkhwa": "Khyber Pakhtunkhwa", "Sindh": "Sindh",
              "Punjab": "Punjab (incl. Islamabad)", "Islamabad": "Punjab (incl. Islamabad)"}
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.4))
    y = np.arange(len(prov))
    axes[0].barh(y, prov["banks_per_100k"], color=NAVY, label="Banks")
    axes[0].barh(y, prov["mfb_per_100k"], left=prov["banks_per_100k"], color=TEAL, label="Microfinance banks")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(prov["province"])
    for i, v in enumerate(prov["branches_per_100k"]):
        axes[0].text(v + 0.5, i, f"{v:.1f}", va="center", fontsize=9)
    axes[0].legend(loc="lower right", fontsize=8.5)
    _title(axes[0], "Branches per 100,000 people", f"Dec {config.BRANCH_REGISTER_DATE[:4]}")
    # SBP reports Islamabad inside Punjab, so the wallet bars carry one Punjab (incl. Islamabad) value.
    skip = {"Islamabad"}
    agents = [np.nan if p in skip else wal.loc[region[p], "agents_per_100k_adults"] for p in prov["province"]]
    accounts = [np.nan if p in skip else wal.loc[region[p], "accounts_per_100_adults"] for p in prov["province"]]
    for ax, values, colour, offset, sub, title in (
            (axes[1], agents, ORANGE, 8, "Apr-Jun 2026; Punjab includes Islamabad", "Wallet agents per 100,000 adults"),
            (axes[2], accounts, PURPLE, 1.5, "Accounts, not people: many are dormant", "Wallet accounts per 100 adults")):
        ax.barh(y, np.nan_to_num(values), color=colour)
        ax.set_yticks(y)
        ax.set_yticklabels([])
        for i, v in enumerate(values):
            if np.isnan(v):
                ax.text(0.5, i, "included in Punjab", va="center", fontsize=8.5, color="#667", style="italic")
            else:
                ax.text(v + offset, i, f"{v:.0f}", va="center", fontsize=9)
        ax.set_xlim(0, np.nanmax(values) * 1.18)
        _title(ax, title, sub)
    fig.suptitle("The digital layer is much denser than branches, and follows the same geography",
                 x=0.01, ha="left", fontsize=12, fontweight="bold", y=1.06)
    _save(fig, "08_province_access_mix.png",
          "Sources: SBP branch register 2024; SBP branchless banking statistics Apr-Jun 2026; PBS Census 2023.")


def fig_rural_urban(r: Results) -> None:
    prov = r.provinces.set_index("province").loc[["Balochistan", "Khyber Pakhtunkhwa", "Sindh", "Punjab"]].reset_index()
    h = r.headline
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    x = np.arange(len(prov) + 1)
    rural = list(prov["rural_branches_per_100k_rural"]) + [h["rural_per_100k_rural"]]
    urban = list(prov["urban_branches_per_100k_urban"]) + [h["urban_per_100k_urban"]]
    ax.bar(x - 0.19, rural, 0.38, color=ORANGE, label="Per 100,000 rural residents")
    ax.bar(x + 0.19, urban, 0.38, color=NAVY, label="Per 100,000 urban residents")
    for i, (a, b) in enumerate(zip(rural, urban)):
        ax.text(i - 0.19, a + 0.4, f"{a:.1f}", ha="center", fontsize=8.5, color=ORANGE)
        ax.text(i + 0.19, b + 0.4, f"{b:.1f}", ha="center", fontsize=8.5, color=NAVY)
    ax.set_xticks(x)
    ax.set_xticklabels(["Balochistan", "Khyber\nPakhtunkhwa", "Sindh", "Punjab", "Pakistan"])
    ax.set_ylabel("Branches")
    ax.set_ylim(0, 25)
    ax.legend(loc="upper right")
    _title(ax, f"{h['rural_pop_share']:.0f}% of people live in rural areas but only {h['rural_branch_share']:.0f}% of branches do",
           "Branches per 100,000 residents, by where the branch is; Islamabad excluded from the provincial bars")
    _save(fig, "09_rural_urban_gap.png",
          "Rural/urban tags come from the SBP register and census respectively and are defined differently.")


# ---------------------------------------------------------------------------
# 10-11: inequality and change
# ---------------------------------------------------------------------------
def fig_lorenz(r: Results) -> None:
    ineq = r.summary["inequality"]
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    ax.plot([0, 1], [0, 1], color="#9AA5B1", lw=1, ls="--", label="Perfect equality")
    for key, colour, label, style, width in (
            ("banks_2020", ORANGE, "Banks, 2020", "-", 2.6),
            ("banks_2024", NAVY, "Banks, 2024", (0, (4, 2)), 1.8),
            ("branches_2024", TEAL, "Banks and microfinance, 2024", "-", 2.0)):
        c = r.lorenz[key]
        ax.plot(c["population_share"], c["branch_share"], color=colour, lw=width, ls=style,
                label=f"{label} (Gini {ineq[key]['gini']:.2f})")
    b = ineq["bottom_20pct_population"]
    ax.annotate(f"Least-served 20% of people\nhave {b['branch_share'] * 100:.0f}% of all branches",
                (0.2, b["branch_share"]), xytext=(0.30, 0.05), arrowprops=dict(arrowstyle="->", color="#333"),
                fontsize=9)
    ax.set_xlabel("Cumulative share of population (fewest branches per person first)")
    ax.set_ylabel("Cumulative share of branches")
    ax.set_aspect("equal")
    ax.legend(loc="upper left")
    _title(ax, "Bank branches are spread unevenly and the pattern has not changed",
           f"Top 10 districts hold {ineq['top10_by_branches']['branch_share'] * 100:.0f}% of branches "
           f"for {ineq['top10_by_branches']['population_share'] * 100:.0f}% of people")
    _save(fig, "10_lorenz_curve.png", "Sources: SBP; PBS. Districts on 2020 boundaries; 2020 uses 2017 census population.")


def fig_no_catch_up(r: Results) -> None:
    u = r.units
    conv = r.summary["convergence"]
    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    for province, g in u.groupby("province"):
        ax.scatter(g["density_2020"], g["density_change"], s=26, color=config.PROVINCE_COLOURS[province],
                   edgecolor="white", lw=0.4, label=province, alpha=0.9)
    x = np.linspace(0, u["density_2020"].max(), 50)
    intercept = u["density_change"].mean() - conv["slope_initial_density"] * u["density_2020"].mean()
    ax.plot(x, intercept + conv["slope_initial_density"] * x, color="#333", lw=1.4, ls="--")
    ax.axhline(0, color="#9AA5B1", lw=1)
    for _, row in u.nlargest(4, "density_change").iterrows():
        ax.annotate(row["unit"], (row["density_2020"], row["density_change"]), xytext=(5, 3), textcoords="offset points", fontsize=8.5)
    for _, row in u.nsmallest(3, "density_change").iterrows():
        ax.annotate(row["unit"], (row["density_2020"], row["density_change"]), xytext=(5, -9), textcoords="offset points", fontsize=8.5)
    ax.set_xlabel("Bank branches per 100,000 people in 2020")
    ax.set_ylabel("Change by 2024 (branches per 100,000)")
    ax.legend(loc="upper right", ncol=2, fontsize=8.5)
    low = conv["low_density_share_of_new"] * 100
    _title(ax, "New bank branches did not go where branches were scarce",
           f"Districts with fewer branches in 2020 (half of them, {conv['low_density_share_of_population'] * 100:.0f}% "
           f"of people) received {low:.0f}% of the {conv['net_new_banks']:,} net new branches")
    ax.text(0.02, 0.95, f"Fitted slope {conv['slope_initial_density']:+.2f} (p = {conv['p_value']:.2f}): "
            "no sign of catch-up", transform=ax.transAxes, fontsize=9, color="#333", va="top")
    _save(fig, "11_no_catch_up.png", "Sources: SBP 2020 appendix and 2024 register (banks only); PBS census 2017 and 2023.")


# ---------------------------------------------------------------------------
# 12-13: model and district types
# ---------------------------------------------------------------------------
def fig_model(r: Results) -> None:
    m = r.summary["access_model"]
    coef = pd.DataFrame(m["coefficients"])
    coef = coef[coef["term"].isin(["log_pop", "urban", "ses_index"])].copy()
    u = r.units
    fig, axes = plt.subplots(1, 2, figsize=(11.4, 4.9), gridspec_kw={"width_ratios": [0.8, 1.35]})
    names = {"log_pop": "Population\n(+1 log point)", "urban": "Urban share\n(0 to 100%)",
             "ses_index": "Development index\n(+1 SD)"}
    y = np.arange(len(coef))[::-1]
    for yy, (_, row) in zip(y, coef.iterrows()):
        axes[0].plot([np.exp(row["ci_low"]), np.exp(row["ci_high"])], [yy, yy], color=NAVY, lw=2)
        axes[0].scatter(np.exp(row["coefficient"]), yy, color=NAVY, s=55, zorder=3)
        axes[0].text(np.exp(row["coefficient"]), yy - 0.27, f"x{np.exp(row['coefficient']):.2f}", ha="center",
                     va="top", fontsize=9)
    axes[0].axvline(1, color="#9AA5B1", lw=1)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels([names[t] for t in coef["term"]])
    axes[0].set_ylim(-0.8, len(coef) - 0.4)
    axes[0].set_xlabel("Change in expected branches (rate ratio, 95% CI)")
    _title(axes[0], "What predicts branches", "Negative binomial model")
    axes[1].scatter(u["expected_branches"], u["branches_2024"], s=24, color="#9AA5B1", edgecolor="white", lw=0.4)
    lim = [0.8, 4000]
    axes[1].plot(lim, lim, color="#333", lw=1, ls="--")
    flagged = u[u["robust_shortfall"]]
    axes[1].scatter(flagged["expected_branches"], flagged["branches_2024"], s=40, color=ORANGE, edgecolor="white", lw=0.5,
                    label=f"Flagged as below expected ({len(flagged)})")
    offsets = {"Lahore": (-44, -13), "Karachi": (-46, 5), "Islamabad": (7, 2), "Multan": (-42, 6),
               "Gujranwala": (8, -4), "Hyderabad": (8, 8), "Sheikhupura": (8, -12)}
    for name, offset in offsets.items():
        row = u[u["unit"] == name]
        if len(row):
            row = row.iloc[0]
            axes[1].annotate(name, (row["expected_branches"], row["branches_2024"]), xytext=offset,
                             textcoords="offset points", fontsize=8.5)
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlim(lim)
    axes[1].set_ylim(lim)
    axes[1].set_xlabel("Expected branches (leave-one-out)")
    axes[1].set_ylabel("Actual branches")
    axes[1].legend(loc="upper left")
    _title(axes[1], "Actual vs expected branches, 120 districts",
           f"Error {(m['mae_reduction_vs_baseline'] * 100):.0f}% lower than a rule of branches proportional to population")
    _save(fig, "12_access_model.png",
          "Expected values come from refitting the model without the district being predicted (leave-one-out).")


def fig_district_types(r: Results) -> None:
    u = r.units
    info = r.summary["clusters"]
    profile = pd.DataFrame(info["profile"])
    fig = plt.figure(figsize=(12.0, 5.8))
    ax = fig.add_axes([0.0, 0.0, 0.5, 0.92])
    _draw_map(ax, r, lambda uid: CLUSTER_COLOURS[u.set_index("unit_id").loc[uid, "cluster"]])
    handles = [plt.Rectangle((0, 0), 1, 1, color=CLUSTER_COLOURS[c]) for c in profile["cluster"]]
    ax.legend(handles, profile["cluster"], loc="lower right", fontsize=9, bbox_to_anchor=(1.0, 0.02))
    ax.set_title("Four types of district", loc="left", fontsize=12.5, fontweight="bold")
    ax2 = fig.add_axes([0.58, 0.14, 0.41, 0.70])
    y = np.arange(len(profile))
    pop_share = profile["population"] / profile["population"].sum() * 100
    ax2.barh(y, pop_share, color=[CLUSTER_COLOURS[c] for c in profile["cluster"]])
    for i, row in profile.iterrows():
        ax2.text(pop_share[i] + 1, i, f"{pop_share[i]:.0f}% of people, {int(row['units'])} districts\n"
                 f"{row['branches_per_100k']:.1f} branches per 100k, microfinance {row['mfb_share']:.0f}%",
                 va="center", fontsize=8.5)
    ax2.set_yticks(y)
    ax2.set_yticklabels(profile["cluster"])
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Share of population (%)")
    ax2.set_title("What they look like", loc="left", fontsize=12.5, fontweight="bold")
    _save(fig, "13_district_types.png",
          f"K-means on population, urban share, development index and branch density (silhouette {info['silhouette_selected']:.2f}).")


# ---------------------------------------------------------------------------
# 14-15: planner and wallets
# ---------------------------------------------------------------------------
def fig_planner(r: Results) -> None:
    table = pd.DataFrame(r.scenario["table"])
    names = {"before": "Today", "equity": "Even out people per branch", "gap": "Close the model gap",
             "women": "Women-first equity"}
    colours = {"before": "#9AA5B1", "equity": TEAL, "gap": NAVY, "women": ORANGE}
    metrics = [("units_below_half", "Districts below half the average", "{:.0f}"),
               ("gini", "Gini of branches across people", "{:.3f}"),
               ("worst_people_per_branch", "Most people per branch (000s)", "{:.0f}"),
               ("share_to_low_female_literacy", "Share placed in low female-literacy districts", "{:.0%}")]
    fig, axes = plt.subplots(1, 4, figsize=(13.4, 3.5))
    order = list(table["strategy"])
    y = np.arange(len(order))[::-1]
    for ax, (col, title, fmt) in zip(axes, metrics):
        values = table[col].copy()
        if col == "worst_people_per_branch":
            values = values / 1000
        top = float(values.fillna(0).max())
        ax.barh(y, values.fillna(0), color=[colours[s] for s in order], height=0.62)
        for yy, v in zip(y, values):
            if pd.isna(v):
                ax.text(0, yy, " n/a", va="center", fontsize=9, color="#667")
            else:
                ax.text(v, yy, " " + fmt.format(v), va="center", fontsize=9)
        ax.set_xlim(0, top * 1.3 if top > 0 else 1)
        ax.set_title(title, loc="left", fontsize=10)
        ax.set_yticks(y)
        ax.set_yticklabels([names[s] for s in order] if col == metrics[0][0] else [])
        ax.grid(axis="y", visible=False)
        if "%" in fmt:
            ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    k = r.scenario["default_k"]
    fig.suptitle(f"What {k:,} new branches or agent points would do under three placement rules "
                 f"(network today: {r.scenario['network_size']:,})", x=0.01, ha="left", fontsize=12, fontweight="bold", y=1.05)
    _save(fig, "14_planner_outcomes.png", "Planner rules are described in docs/methodology.md. Not a forecast of demand or cost.")


def fig_wallets(r: Results) -> None:
    bb = r.bb_regions
    nat = r.bb_national
    quarters = list(nat["quarter"])
    labels = [config.BB_QUARTER_LABELS[q].replace(" ", "\n", 1) for q in quarters]
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.2))
    palette = {"Balochistan": AMBER, "Khyber Pakhtunkhwa": ORANGE, "Sindh": TEAL, "Punjab (incl. Islamabad)": NAVY}
    for region, colour in palette.items():
        s = bb[bb["region"] == region].set_index("quarter").loc[quarters]
        ok = ~s["flag_accounts"].to_numpy()
        xs = np.arange(len(quarters))[ok]
        axes[0].plot(xs, s["accounts_per_100_adults"].to_numpy()[ok], color=colour, lw=2, marker="o", ms=3.5, label=region)
        axes[0].text(len(quarters) - 0.8, s["accounts_per_100_adults"].iloc[-1], f"{s['accounts_per_100_adults'].iloc[-1]:.0f}",
                     fontsize=8.5, color=colour, va="center")
    axes[0].set_xticks(range(0, len(quarters), 2))
    axes[0].set_xticklabels([labels[i] for i in range(0, len(quarters), 2)], fontsize=8)
    axes[0].legend(fontsize=8, loc="upper left")
    _title(axes[0], "Wallet accounts per 100 adults", "Accounts, not unique people")
    for region, colour in palette.items():
        s = bb[bb["region"] == region].set_index("quarter").loc[quarters]
        ok = ~(s["flag_accounts"] | s["flag_female"]).to_numpy()
        xs = np.arange(len(quarters))[ok]
        axes[1].plot(xs, s["female_share"].to_numpy()[ok], color=colour, lw=2, marker="o", ms=3.5)
        last = s["female_share"].iloc[-1]
        nudge = {"Punjab (incl. Islamabad)": 0.5, "Sindh": -0.5, "Khyber Pakhtunkhwa": 0.4, "Balochistan": -0.4}[region]
        axes[1].text(len(quarters) - 0.8, last + nudge, f"{last:.0f}%", fontsize=8.5, color=colour, va="center")
    axes[1].set_xticks(range(0, len(quarters), 2))
    axes[1].set_xticklabels([labels[i] for i in range(0, len(quarters), 2)], fontsize=8)
    axes[1].set_ylim(18, 38)
    _title(axes[1], "Women's share of wallet accounts", "%")
    ax = axes[2]
    ax.bar(range(len(quarters)), nat["agents"] / 1000, color="#C8D1DC", label="All agents")
    ax.bar(range(len(quarters)), nat["active_agents"] / 1000, color=TEAL, label="Active agents")
    for i, share in enumerate(nat["active_agent_share"]):
        if i in (0, len(quarters) - 1):
            ax.text(i, nat["agents"].iloc[i] / 1000 + 12, f"{share:.0f}%\nactive", ha="center", fontsize=8.5)
    ax.set_xticks(range(0, len(quarters), 2))
    ax.set_xticklabels([labels[i] for i in range(0, len(quarters), 2)], fontsize=8)
    ax.set_ylim(0, 1000)
    ax.legend(loc="upper left", fontsize=8.5)
    _title(ax, "Agents (thousands)", "The network grew, the active share fell")
    _save(fig, "15_wallets_and_agents.png",
          "Source: SBP branchless banking statistics, Apr-Jun 2024 to Apr-Jun 2026. Provincial points that are out of line "
          "with neighbouring quarters in the SBP tables are left out (Balochistan Oct-Dec 2024 and Jan-Mar 2026).")


def make_all() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    r = load()
    for fn in (fig_cross_country, fig_gender_gaps, fig_segments, fig_barriers, fig_instruments, fig_map_density,
               fig_map_gap, fig_province_access, fig_rural_urban, fig_lorenz, fig_no_catch_up, fig_model,
               fig_district_types, fig_planner, fig_wallets):
        fn(r)
