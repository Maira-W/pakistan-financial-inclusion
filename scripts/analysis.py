"""Analysis and charts for the Pakistan financial inclusion project.

Reads the clean tables in data/clean/ and writes:
  - dashboard/*.png           static charts for the README and memo
  - dashboard/dashboard.html  one interactive page (Plotly), open in any browser

Run from the project root, after scripts/build_clean_data.py:
  python scripts/analysis.py
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "dashboard"
OUT.mkdir(parents=True, exist_ok=True)

NAVY = "#1F3B57"
TEAL = "#2A9D8F"
ORANGE = "#E76F51"
GREY = "#8D99AE"

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False})


def load():
    findex = pd.read_csv(CLEAN / "findex_account_ownership.csv")
    density = pd.read_csv(CLEAN / "branch_density_district.csv")
    province = pd.read_csv(CLEAN / "branch_density_province.csv")
    return findex, density, province


def headline_numbers(density: pd.DataFrame) -> dict:
    """Numbers quoted in the README and memo. Computed here so they can be checked."""
    matched = density[density["branch_data_found"]].copy()
    national_rate = matched["branches_total"].sum() / matched["population_2023"].sum() * 100_000
    matched["below_half_avg"] = matched["branches_per_100k"] < national_rate / 2
    share_pop_low = matched.loc[matched["below_half_avg"], "population_2023"].sum() / matched["population_2023"].sum()
    return {
        "matched_districts": int(len(matched)),
        "national_branches_per_100k": round(national_rate, 2),
        "districts_below_half_avg": int(matched["below_half_avg"].sum()),
        "pop_share_in_low_density_districts": round(share_pop_low * 100, 1),
        "lowest_district": matched.iloc[0][["unit", "province", "branches_per_100k"]].to_dict(),
        "highest_district": matched.iloc[-1][["unit", "province", "branches_per_100k"]].to_dict(),
    }


def findex_series(findex: pd.DataFrame, measure: str) -> pd.DataFrame:
    return findex[findex["measure"] == measure].pivot(index="year", columns="country", values="pct_age_15_plus")


def chart_peer_benchmark(findex, path):
    wide = findex_series(findex, "total")
    fig, ax = plt.subplots(figsize=(7, 4.4))
    colors = {"Pakistan": ORANGE, "India": NAVY, "Bangladesh": TEAL, "Sri Lanka": GREY}
    for country in ["India", "Bangladesh", "Sri Lanka", "Pakistan"]:
        ax.plot(wide.index, wide[country], marker="o", lw=3 if country == "Pakistan" else 1.6,
                color=colors[country], label=country, zorder=3 if country == "Pakistan" else 2)
    ax.set_title("Account ownership, adults 15+ (%)", loc="left", fontweight="bold")
    ax.set_ylabel("% of adults with an account")
    ax.set_xticks(wide.index)
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.1))
    fig.text(0.01, 0.01, "Source: World Bank Global Findex (via World Bank API).", fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def chart_gender_gap(findex, path):
    p = findex[findex["country"] == "Pakistan"].pivot(index="year", columns="measure", values="pct_age_15_plus")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(p.index, p["male"], marker="o", color=NAVY, lw=2, label="Men")
    ax.plot(p.index, p["female"], marker="o", color=ORANGE, lw=2, label="Women")
    for year in p.index:
        gap = p.loc[year, "male"] - p.loc[year, "female"]
        ax.annotate(f"gap {gap:.1f} pts", (year, p.loc[year, "male"]), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=8, color="#333")
    ax.set_title("Pakistan: account ownership by gender (%)", loc="left", fontweight="bold")
    ax.set_xticks(p.index)
    ax.set_ylabel("% of adults 15+")
    ax.set_ylim(0, 55)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def chart_province(province, path):
    p = province.sort_values("branches_per_100k")
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.barh(p["province"].str.title(), p["branches_per_100k"],
                   color=[ORANGE if v < 5 else TEAL for v in p["branches_per_100k"]])
    for bar, v in zip(bars, p["branches_per_100k"]):
        ax.text(v + 0.2, bar.get_y() + bar.get_height() / 2, f"{v:.1f}", va="center", fontsize=9)
    ax.set_title("Bank branches per 100,000 people, by province", loc="left", fontweight="bold")
    ax.set_xlabel("Branches per 100,000 (SBP Dec 2020 / PBS Census 2023)")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def chart_districts(density, path, n=12):
    d = density.dropna(subset=["branches_per_100k"]).sort_values("branches_per_100k")
    low = d.head(n)
    high = d.tail(n)
    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    for ax, data, title, color in [(axes[0], low, f"Lowest {n} districts", ORANGE),
                                   (axes[1], high, f"Highest {n} districts", TEAL)]:
        ax.barh(data["unit"].str.title(), data["branches_per_100k"], color=color)
        for i, v in enumerate(data["branches_per_100k"]):
            ax.text(v, i, f" {v:.1f}", va="center", fontsize=8)
        ax.set_title(title, loc="left", fontweight="bold")
        ax.set_xlabel("Branches per 100,000 people")
        ax.tick_params(axis="y", labelsize=8)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def chart_scatter(density, path):
    d = density.dropna(subset=["branches_per_100k"])
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(d["population_2023"] / 1e6, d["branches_total"], s=18, color=NAVY, alpha=0.6)
    labelled = pd.concat([d.nlargest(4, "population_2023"), d[d["unit"] == "ISLAMABAD"]])
    for _, row in labelled.iterrows():
        ax.annotate(row["unit"].title(), (row["population_2023"] / 1e6, row["branches_total"]),
                    xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.set_xlabel("Population 2023 (millions)")
    ax.set_ylabel("Bank branches (Dec 2020)")
    ax.set_title("Branches vs population, by district (119 matched districts)",
                 loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def interactive_dashboard(findex, density, province, headline, path):
    wide = findex_series(findex, "total")
    p = findex[findex["country"] == "Pakistan"].pivot(index="year", columns="measure", values="pct_age_15_plus")
    matched = density.dropna(subset=["branches_per_100k"]).sort_values("branches_per_100k")

    fig = make_subplots(
        rows=3, cols=2,
        specs=[[{"type": "xy"}, {"type": "xy"}],
               [{"type": "xy"}, {"type": "xy"}],
               [{"type": "xy", "colspan": 2}, None]],
        subplot_titles=(
            "Account ownership, adults 15+ (%)",
            "Pakistan: men vs women (%)",
            "Branches per 100,000 by province",
            "Branches per 100,000 by district (all matched)",
            "Districts sorted by branches per 100,000 (lowest first)",
        ),
        vertical_spacing=0.12, horizontal_spacing=0.08,
    )
    for country, color in [("India", GREY), ("Bangladesh", "#B8C0CC"), ("Sri Lanka", "#5C677D"),
                           ("Pakistan", ORANGE)]:
        fig.add_trace(go.Scatter(x=wide.index, y=wide[country], mode="lines+markers", name=country,
                                 line=dict(color=color, width=3 if country == "Pakistan" else 2)),
                      row=1, col=1)
    fig.add_trace(go.Scatter(x=p.index, y=p["male"], mode="lines+markers", name="Men",
                             line=dict(color=NAVY, width=2)), row=1, col=2)
    fig.add_trace(go.Scatter(x=p.index, y=p["female"], mode="lines+markers", name="Women",
                             line=dict(color=ORANGE, width=2)), row=1, col=2)

    prov = province.sort_values("branches_per_100k")
    fig.add_trace(go.Bar(x=prov["branches_per_100k"], y=prov["province"].str.title(), orientation="h",
                         marker_color=TEAL, name="Province", showlegend=False), row=2, col=1)

    fig.add_trace(go.Scatter(x=matched["population_2023"] / 1e6, y=matched["branches_per_100k"],
                             mode="markers", text=matched["unit"].str.title(), name="Districts",
                             marker=dict(color=NAVY, size=7, opacity=0.6), showlegend=False,
                             hovertemplate="%{text}<br>%{y:.1f} per 100k<br>%{x:.2f}M people<extra></extra>"),
                  row=2, col=2)

    fig.add_trace(go.Bar(x=matched["unit"].str.title(), y=matched["branches_per_100k"],
                         marker_color=[ORANGE if v < headline["national_branches_per_100k"] / 2 else TEAL
                                       for v in matched["branches_per_100k"]],
                         name="Districts", showlegend=False,
                         hovertemplate="%{x}<br>%{y:.1f} per 100k<extra></extra>"),
                  row=3, col=1)

    fig.update_layout(
        height=1100, width=1100, template="plotly_white",
        title=dict(text="Financial Inclusion Gap in Pakistan", x=0.02, font=dict(size=22)),
        legend=dict(orientation="h", y=1.04, x=0),
        margin=dict(t=110),
    )
    fig.update_xaxes(showgrid=False, tickangle=0)
    fig.update_xaxes(tickangle=-60, tickfont=dict(size=7), row=3, col=1)
    fig.update_yaxes(gridcolor="#eee")
    fig.update_xaxes(title_text="Population 2023 (millions)", row=2, col=2)
    fig.update_yaxes(title_text="Branches per 100k", row=2, col=2)
    fig.write_html(path, include_plotlyjs="cdn")


def main():
    findex, density, province = load()
    headline = headline_numbers(density)

    chart_peer_benchmark(findex, OUT / "01_peer_benchmark.png")
    chart_gender_gap(findex, OUT / "02_gender_gap.png")
    chart_province(province, OUT / "03_province_branch_density.png")
    chart_districts(density, OUT / "04_district_extremes.png")
    chart_scatter(density, OUT / "05_population_vs_branches.png")
    interactive_dashboard(findex, density, province, headline, OUT / "dashboard.html")

    print("Headline numbers:")
    for k, v in headline.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
