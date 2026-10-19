"""Analysis and charts for the Pakistan financial inclusion project.

Reads the clean tables in data/clean/ and writes:
  - dashboard/*.png           static charts for the README and memo
  - dashboard/dashboard.html  interactive dashboard (filters, toggles, searchable table)

The dashboard page is built from scripts/dashboard_template.html. The data is embedded as JSON
and the charts are drawn in the browser with Plotly.js, so the page works offline once loaded.

Run from the project root, after scripts/build_clean_data.py:
  python scripts/analysis.py
"""

import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from plotly.offline import get_plotlyjs_version

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "dashboard"
TEMPLATE = Path(__file__).resolve().parent / "dashboard_template.html"
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
        "lowest_district": matched.sort_values("branches_per_100k").iloc[0][["unit", "province", "branches_per_100k"]].to_dict(),
        "highest_district": matched.sort_values("branches_per_100k").iloc[-1][["unit", "province", "branches_per_100k"]].to_dict(),
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


def _records(df: pd.DataFrame, columns: list[str]) -> list[dict]:
    """Rows as plain dicts, with NaN turned into None so the JSON is valid."""
    out = []
    for row in df[columns].itertuples(index=False):
        out.append({c: (None if pd.isna(v) else (v.item() if hasattr(v, "item") else v))
                    for c, v in zip(columns, row)})
    return out


def build_dashboard_page(findex, density, province, headline, path):
    """Fill the HTML template with the data and write the dashboard page."""
    wide = findex_series(findex, "total")
    years = [int(y) for y in wide.index]
    series = {c: [None if pd.isna(v) else round(float(v), 2) for v in wide[c]] for c in wide.columns}

    gender = findex[findex["country"] == "Pakistan"].pivot(index="year", columns="measure", values="pct_age_15_plus")
    latest = findex["year"].max()
    pak_2024 = wide.loc[latest, "Pakistan"]
    men_2024 = gender.loc[latest, "male"]
    women_2024 = gender.loc[latest, "female"]

    kpis = {
        "pak_2024": round(float(pak_2024), 1),
        "india_2024": round(float(wide.loc[latest, "India"]), 1),
        "men_2024": round(float(men_2024), 1),
        "women_2024": round(float(women_2024), 1),
        "gender_gap_2024": round(float(men_2024 - women_2024), 1),
        "national_density": headline["national_branches_per_100k"],
        "below_half_count": headline["districts_below_half_avg"],
        "matched_count": headline["matched_districts"],
        "pop_share_low": headline["pop_share_in_low_density_districts"],
    }

    data = {
        "kpis": kpis,
        "findex": {
            "years": years,
            "series": series,
            "male": [round(float(v), 2) for v in gender["male"]],
            "female": [round(float(v), 2) for v in gender["female"]],
        },
        "provinces": _records(province, ["province", "population_2023", "branches_total", "branches_per_100k"]),
        "districts": _records(density, ["unit", "province", "population_2023", "branches_total",
                                        "branches_per_100k"]),
    }
    # Blank rows (districts created after 2020) carry no branch figures.
    for row in data["districts"]:
        if row["branches_per_100k"] is not None and row["branches_total"] is not None:
            row["branches_total"] = int(row["branches_total"])
        row["population_2023"] = int(row["population_2023"])

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__PLOTLY_URL__", f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js")
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    path.write_text(html, encoding="utf-8")


def main():
    findex, density, province = load()
    headline = headline_numbers(density)

    chart_peer_benchmark(findex, OUT / "01_peer_benchmark.png")
    chart_gender_gap(findex, OUT / "02_gender_gap.png")
    chart_province(province, OUT / "03_province_branch_density.png")
    chart_districts(density, OUT / "04_district_extremes.png")
    chart_scatter(density, OUT / "05_population_vs_branches.png")
    build_dashboard_page(findex, density, province, headline, OUT / "dashboard.html")

    print("Headline numbers:")
    for k, v in headline.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
