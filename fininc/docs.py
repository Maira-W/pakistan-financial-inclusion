"""Render README.md and the documents in docs/ from templates, so every number in them comes from the results.

A template is plain Markdown with {{name}} or {{name:format}} placeholders (the format is a Python format spec, for
example {{rural_pop_share:.0f}}). Rendering fails if a template asks for a value that does not exist, so a renamed
result cannot leave a stale number behind. `python -m fininc report` writes the documents; a test checks that the
committed files are what the templates and the data produce.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter

from . import config
from .paths import DOCS, MANIFEST, ROOT, TEMPLATES
from .powerbi.measures import MEASURES
from .results import Results, load
from .text import largest_phrase, ordinal
from .units import SBP_ALIASES

TEMPLATE_DIR = TEMPLATES / "docs"
OUTPUTS = {
    "readme.md": ROOT / "README.md",
    "memo.md": DOCS / "recommendation_memo.md",
    "methodology.md": DOCS / "methodology.md",
    "data_sources.md": DOCS / "data_sources.md",
    "powerbi.md": DOCS / "powerbi.md",
}
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::([^{}]*?))?\s*\}\}")


def render(template: str, values: dict) -> str:
    def fill(match: re.Match) -> str:
        name, spec = match.group(1), match.group(2) or ""
        if name not in values:
            raise KeyError(f"A template uses {{{{{name}}}}} but no such value exists")
        return format(values[name], spec)
    return PLACEHOLDER.sub(fill, template)


def _table(header: list[str], rows: list[list], align: str = "") -> str:
    """A GitHub Markdown table. `align` gives one of l, r, c per column (default left, numbers right)."""
    aligns = align or "".join("l" if isinstance(v, str) else "r" for v in rows[0])
    rule = {"l": "---", "r": "---:", "c": ":---:"}
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(rule[a] for a in aligns) + " |"]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in rows]
    return "\n".join(lines)


def _int(x) -> str:
    return f"{x:,.0f}"


# ---------------------------------------------------------------------------
# tables that appear in more than one document
# ---------------------------------------------------------------------------
def province_table(r: Results) -> str:
    p = r.provinces.sort_values("branches_per_100k", ascending=False)
    rows = [[row.province, _int(row.pop), f"{row.urban_share:.0f}%", _int(row.branches_2024),
             f"{row.branches_per_100k:.1f}", f"{row.rural_branches_per_100k_rural:.1f}",
             f"{row.urban_branches_per_100k_urban:.1f}", f"{row.banks_growth_pct:.0f}%"] for row in p.itertuples()]
    return _table(["Province", "People", "Urban", "Branches", "Per 100,000 people", "Per 100,000 rural",
                   "Per 100,000 urban", "Bank growth 2020-24"], rows, "lrrrrrrr")


def shortfall_table(r: Results, n: int = 10) -> str:
    u = r.units.sort_values("branch_gap", ascending=False).head(n)
    rows = [[row.unit, row.province, _int(row.pop), _int(row.branches_2024), f"{row.expected_branches:,.0f}",
             f"{row.branch_gap:,.0f}", f"{row.p_below_expected:.3f}"] for row in u.itertuples()]
    return _table(["District", "Province", "People", "Branches", "Expected", "Shortfall", "Chance of so few"], rows, "llrrrrr")


def cluster_table(r: Results) -> str:
    rows = [[c["cluster"], c["units"], f"{c['population'] / 1e6:.1f}", f"{c['urban_share']:.0f}%",
             f"{c['ses_index']:+.2f}", f"{c['literacy_female']:.0f}%", f"{c['branches_per_100k']:.1f}",
             f"{c['rural_branch_share']:.0f}%", c["largest_units"]] for c in r.summary["clusters"]["profile"]]
    return _table(["Type", "Districts", "People (m)", "Urban", "Development index", "Women literate",
                   "Branches per 100,000 (median)", "Rural share of branches", "Largest districts"], rows, "lrrrrrrrl")


def specification_table(r: Results) -> str:
    rows = []
    for s in r.summary["access_model"]["specification_comparison"]:
        aic = "n/a" if s["aic"] is None else f"{s['aic']:.1f}"
        rows.append([s["specification"], aic, f"{s['loo_mae']:.1f}", f"{s['loo_median_rel_error'] * 100:.0f}%"])
    return _table(["Model", "AIC", "Leave-one-out error (branches)", "Median relative error"], rows, "lrrr")


def coefficient_table(r: Results) -> str:
    names = {"intercept": "Intercept", "log_pop": "log(population)", "urban": "Urban share (0 to 1)",
             "ses_index": "Development index (1 sd)", "alpha": "Dispersion (alpha)"}
    rows = []
    for c in r.summary["access_model"]["coefficients"]:
        rr = "" if c["rate_ratio"] is None else f"{c['rate_ratio']:.2f}"
        rows.append([names[c["term"]], f"{c['coefficient']:.3f}", f"{c['std_error']:.3f}", f"{c['p_value']:.3g}", rr])
    return _table(["Term", "Coefficient", "Std. error", "p-value", "Rate ratio"], rows, "lrrrr")


def scenario_table(r: Results) -> str:
    rows = []
    for s in r.summary["scenario_default"]:
        rows.append([s["label"], s["units_below_half"], f"{s['population_below_half'] * 100:.1f}%", f"{s['gini']:.3f}",
                     _int(s["worst_people_per_branch"]),
                     "" if s["strategy"] == "before" else f"{s['share_to_low_female_literacy'] * 100:.0f}%"])
    return _table(["Rule", "Districts below half the average", "People in them", "Gini", "People per branch, worst district",
                   "Points to districts where under 40% of women read"], rows, "lrrrrr")


def source_table() -> str:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    groups: dict[str, list[dict]] = {}
    for path, meta in manifest.items():
        groups.setdefault(path.split("/")[0] + "/" + path.split("/")[1] if path.count("/") > 1 else path.split("/")[0], []).append(meta)
    rows = []
    for folder, metas in sorted(groups.items()):
        rows.append([f"`data/raw/{folder}`", len(metas), _int(sum(m["bytes"] for m in metas)),
                     metas[0]["licence"].split(";")[0]])
    return _table(["Folder", "Files", "Bytes", "Terms"], rows, "lrrl")


def powerbi_pages_table() -> str:
    from .powerbi import report
    plural = {"card": "card", "slicer": "slicer", "lineChart": "line chart", "clusteredBarChart": "bar chart",
              "scatterChart": "scatter chart", "tableEx": "table"}
    rows = []
    for i, (page_id, display, builder) in enumerate(report.PAGES, start=1):
        visuals = builder()
        kinds = Counter(v["type"] for v in visuals)
        parts = [f"{n} {plural[t]}{'s' if n > 1 else ''}" for t, n in sorted(kinds.items(), key=lambda kv: -kv[1])]
        rows.append([i, f"**{display}**", report.PAGE_NOTES[page_id], len(visuals), ", ".join(parts)])
    return _table(["#", "Page", "What it shows", "Visuals", "Made of"], rows, "rllrl")


def powerbi_gallery(prefix: str, page_ids: tuple[str, ...] | None = None, columns: int = 2) -> str:
    """Screenshots of Power BI pages as an HTML table. The images are saved from Power BI Desktop by hand, one per page,
    named `<page number>_<page id>.png`; a test fails if one is missing."""
    from .powerbi import report
    cells = []
    for i, (page_id, display, _) in enumerate(report.PAGES, start=1):
        if page_ids is not None and page_id not in page_ids:
            continue
        src = f"{prefix}/{i:02d}_{page_id}.png"
        cells.append(f'<td width="{100 // columns}%"><a href="{src}"><img src="{src}" alt="Power BI report, page {i}: {display}">'
                     f"</a><br><sub>Page {i}: {display}</sub></td>")
    rows = ["<tr>\n" + "\n".join(cells[k:k + columns]) + "\n</tr>" for k in range(0, len(cells), columns)]
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def powerbi_tables_table(r: Results) -> str:
    from .powerbi import tables as pbi_tables
    rows = [[f"`{name}`", len(df), len(df.columns), pbi_tables.TABLE_NOTES[name]]
            for name, df in pbi_tables.make_tables(r).items()]
    return _table(["Table", "Rows", "Columns", "Role"], rows, "lrrl")


def powerbi_measures_table() -> str:
    folders: dict[str, list[str]] = {}
    for m in MEASURES:
        folders.setdefault(m.folder, []).append(m.name)
    rows = [[folder, len(names), ", ".join(f"`{n}`" for n in names[:4]) + (", ..." if len(names) > 4 else "")]
            for folder, names in folders.items()]
    return _table(["Folder", "Measures", "Examples"], rows, "lrl")


# ---------------------------------------------------------------------------
# the values templates can use
# ---------------------------------------------------------------------------
def _seg(r: Results, segment: str, year: int) -> float:
    s = r.segments
    return float(s[(s["segment"] == segment) & (s["year"] == year)]["value"].iloc[0])


def _series(r: Results, indicator: str, country: str, year: int) -> float:
    p = r.panel
    return float(p[(p["indicator"] == indicator) & (p["country"] == country) & (p["year"] == year)]["value"].iloc[0])


def context(r: Results) -> dict:
    h, s = r.headline, r.summary
    cc, pak = s["cross_country"], s["cross_country"]["pakistan"]
    model, conv, ineq, quality = s["access_model"], s["convergence"], s["inequality"], s["quality"]
    scen = {row["strategy"]: row for row in s["scenario_default"]}
    barriers = r.barriers.set_index("indicator")["share_of_unbanked"]
    mm = r.mm_barriers.set_index("indicator")["value"]
    coef = {c["term"]: c for c in model["coefficients"]}
    bb, nat = r.bb_regions, r.bb_national.set_index("quarter")
    first_q, last_q = bb["quarter"].min(), bb["quarter"].max()
    wallet = bb[bb["quarter"] == last_q].set_index("region")
    units = r.units
    profile = {c["cluster"]: c for c in s["clusters"]["profile"]}
    search = {row["k"]: row for row in s["clusters"]["search"]}
    k4 = search[4]
    top = units.sort_values("branch_gap", ascending=False)
    robust = units[units["robust_shortfall"]]
    sizes = {int(k): {row["strategy"]: row for row in rows} for k, rows in r.scenario["sizes"].items()}
    register, sbp20 = quality["register_2024"], quality["sbp_2020"]
    checks = quality["external_checks"]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]

    values = {
        # scale
        "population_m": h["population"] / 1e6, "n_units": h["units"], "n_census_districts": int(units["n_districts"].sum()),
        "branches": h["branches_2024"], "banks_2024": h["banks_2024"], "mfb_2024": h["mfb_2024"],
        "banks_2020": h["banks_2020"], "bank_growth": h["banks_growth_pct"], "branches_per_100k": h["branches_per_100k"],
        "banks_per_100k_adults": h["banks_per_100k_adults"], "islamic_share": h["islamic_share_of_banks"],
        # rural against urban
        "rural_pop_share": h["rural_pop_share"], "rural_branch_share": h["rural_branch_share"],
        "rural_per_100k": h["rural_per_100k_rural"], "urban_per_100k": h["urban_per_100k_urban"],
        "urban_rural_ratio": h["urban_per_100k_urban"] / h["rural_per_100k_rural"],
        "mfb_rural_share": h["mfb_rural_share"], "bank_rural_share": h["bank_rural_share"],
        "units_below_half": h["units_below_half_average"], "pop_below_half": h["population_below_half_average"] * 100,
        "zero_branch_units": h["units_zero_branches"],
        # Findex
        "acct": pak["account"], "acct_women": pak["account_women"], "acct_men": pak["account_men"],
        "acct_gap": pak["account_gap"], "phone_women": pak["phone_women"], "phone_men": pak["phone_men"],
        "phone_gap": pak["phone_gap"], "expected_acct": pak["expected"], "shortfall_pts": pak["shortfall_pts"],
        "pi_low": pak["prediction_interval_90"][0], "pi_high": pak["prediction_interval_90"][1],
        "gdp_pc": pak["gdp_pc_ppp"], "rank_lowest": cc["rank_lowest_account"][0], "n_economies": cc["n_economies"],
        "rank_acct_gap": cc["rank_largest_account_gap"][0], "rank_acct_gap_n": cc["rank_largest_account_gap"][1],
        "rank_phone_gap": cc["rank_largest_phone_gap"][0], "rank_phone_gap_n": cc["rank_largest_phone_gap"][1],
        "rank_lowest_ord": ordinal(cc["rank_lowest_account"][0]),
        "phone_gap_phrase": largest_phrase(*cc["rank_largest_phone_gap"]),
        "acct_gap_phrase": largest_phrase(*cc["rank_largest_account_gap"]),
        "income_slope": cc["slope_per_log_point"], "income_r2": cc["r_squared"],
        "income_doubling": cc["slope_per_log_point"] * math.log(2),
        "women_2021": _seg(r, "Women", 2021), "women_2024": _seg(r, "Women", 2024),
        "men_2021": _seg(r, "Men", 2021), "men_2024": _seg(r, "Men", 2024),
        "poor_2021": _seg(r, "Poorest 40%", 2021), "poor_2024": _seg(r, "Poorest 40%", 2024),
        "rich_2021": _seg(r, "Richest 60%", 2021), "rich_2024": _seg(r, "Richest 60%", 2024),
        "rural_acct_2024": _seg(r, "Rural", 2024), "urban_acct_2024": _seg(r, "Urban", 2024),
        "young_2024": _seg(r, "Young adults (15-24)", 2024), "older_2024": _seg(r, "Older adults (25+)", 2024),
        "men_gain": _seg(r, "Men", 2024) - _seg(r, "Men", 2021), "rich_gain": _seg(r, "Richest 60%", 2024) - _seg(r, "Richest 60%", 2021),
        "women_loss": _seg(r, "Women", 2021) - _seg(r, "Women", 2024), "poor_loss": _seg(r, "Poorest 40%", 2021) - _seg(r, "Poorest 40%", 2024),
        "fi_2021": _series(r, "fiaccount.t.d", "PAK", 2021), "fi_2024": _series(r, "fiaccount.t.d", "PAK", 2024),
        "mm_2021": _series(r, "mobileaccount.t.d", "PAK", 2021), "mm_2024": _series(r, "mobileaccount.t.d", "PAK", 2024),
        "acct_2021": _series(r, "account.t.d", "PAK", 2021),
        "digital_2024": _series(r, "g20.any", "PAK", 2024),
        "b_money": barriers["fin11d.s"], "b_cost": barriers["fin11b.s"], "b_distance": barriers["fin11a.s"],
        "b_docs": barriers["fin11c"], "b_trust": barriers["fin11f.s"], "b_family": barriers["fin11e.s"],
        "mm_money": mm["fin14d"], "mm_cost": mm["fin14b"], "mm_docs": mm["fin14c"], "mm_distance": mm["fin14a"],
        # models
        "alpha": model["alpha"], "aic": model["aic"], "loo_mae": model["loo_mae"], "baseline_mae": model["baseline_mae"],
        "mae_cut": model["mae_reduction_vs_baseline"] * 100, "loo_corr": model["loo_correlation"],
        "spearman": model["spearman"], "shortfall_total": model["shortfall_total"],
        "shortfall_lo": model["shortfall_p05"], "shortfall_hi": model["shortfall_p95"],
        "n_below_expected": model["units_below_expected"], "n_above_expected": model["units_above_expected"],
        "n_robust": model["units_robust_shortfall"], "boot_draws": model["bootstrap_draws_used"],
        "rr_pop": coef["log_pop"]["rate_ratio"], "rr_pop_double": 2 ** coef["log_pop"]["coefficient"], "rr_urban": coef["urban"]["rate_ratio"], "rr_ses": coef["ses_index"]["rate_ratio"],
        "p_pop": coef["log_pop"]["p_value"], "p_urban": coef["urban"]["p_value"], "p_ses": coef["ses_index"]["p_value"],
        "ses_var": h["ses_explained_variance"] * 100,
        "loading_min": min(quality["ses_index"]["loadings"].values()), "loading_max": max(quality["ses_index"]["loadings"].values()),
        "silhouette_4": k4["silhouette"], "stability_4": k4["stability_ari"],
        "silhouette_min": min(v["silhouette"] for v in search.values()), "silhouette_max": max(v["silhouette"] for v in search.values()),
        "n_frontier": profile["Frontier and remote"]["units"], "frontier_pop": profile["Frontier and remote"]["population"] / 1e6,
        "frontier_density": profile["Frontier and remote"]["branches_per_100k"],
        "metro_density": profile["Metropolitan hubs"]["branches_per_100k"],
        "frontier_women_literate": profile["Frontier and remote"]["literacy_female"],
        "robust_names": ", ".join(robust.sort_values("branch_gap", ascending=False)["unit"].head(6)),
        "robust_3": ", ".join(robust.sort_values("branch_gap", ascending=False)["unit"].head(3)),
        "top3_names": f"{top.iloc[0]['unit']}, {top.iloc[1]['unit']} and {top.iloc[2]['unit']}",
        "n_measures": len(MEASURES), "n_aliases": len(SBP_ALIASES), "n_others": h["units"] - 1,
        "chance_flags": config.GAP_SIGNIFICANCE * h["units"],
        "detailed_cover": units["age_all"].sum() / units["pop"].sum() * 100,
        "detailed_gap_max": (1 - units["age_all"] / units["pop"]).max() * 100,
        "n_merged_districts": int(units.loc[units["n_districts"] > 1, "n_districts"].sum()),
        "n_merged_units": int((units["n_districts"] > 1).sum()),
        "top1": top.iloc[0]["unit"], "top1_gap": top.iloc[0]["branch_gap"], "top1_branches": top.iloc[0]["branches_2024"],
        "top1_expected": top.iloc[0]["expected_branches"],
        "top2": top.iloc[1]["unit"], "top2_gap": top.iloc[1]["branch_gap"],
        "top3": top.iloc[2]["unit"], "top3_gap": top.iloc[2]["branch_gap"],
        "top5_gap_share": top.head(5)["branch_gap"].sum() / model["shortfall_total"] * 100,
        # inequality and catch-up
        "gini_2020": ineq["banks_2020"]["gini"], "gini_2024": ineq["banks_2024"]["gini"], "gini_all": ineq["branches_2024"]["gini"],
        "theil_between_share": ineq["banks_2024"]["between_share"] * 100,
        "bottom20_units": ineq["bottom_20pct_population"]["units"],
        "bottom20_pop": ineq["bottom_20pct_population"]["population_share"] * 100,
        "bottom20_branches": ineq["bottom_20pct_population"]["branch_share"] * 100,
        "top10_branch_share": ineq["top10_by_branches"]["branch_share"] * 100, "top10_pop_share": ineq["top10_by_branches"]["population_share"] * 100,
        "top10_names": ineq["top10_by_branches"]["units"],
        "conv_slope": conv["slope_initial_density"], "conv_lo": conv["slope_ci"][0], "conv_hi": conv["slope_ci"][1],
        "conv_p": conv["p_value"], "conv_r2": conv["r_squared"], "net_new": conv["net_new_banks"],
        "low_new_share": conv["low_density_share_of_new"] * 100, "low_pop_share": conv["low_density_share_of_population"] * 100,
        "units_losing": conv["units_losing_branches"], "low_units": conv["low_density_units"],
        "median_density_2020": conv["median_density_2020"],
        # planner
        "k_default": r.scenario["default_k"], "network": r.scenario["network_size"],
        "k_share": r.scenario["default_k"] / r.scenario["network_size"] * 100,
        "plan_units_before": scen["before"]["units_below_half"], "plan_pop_before": scen["before"]["population_below_half"] * 100,
        "plan_gini_before": scen["before"]["gini"], "plan_worst_before": scen["before"]["worst_people_per_branch"],
        "plan_gini_cut": (1 - scen["equity"]["gini"] / scen["before"]["gini"]) * 100,
        "plan_gini_equity": scen["equity"]["gini"], "plan_gini_gap": scen["gap"]["gini"], "plan_gini_women": scen["women"]["gini"],
        "plan_units_equity": scen["equity"]["units_below_half"], "plan_units_gap": scen["gap"]["units_below_half"],
        "plan_units_women": scen["women"]["units_below_half"],
        "plan_worst_equity": scen["equity"]["worst_people_per_branch"], "plan_worst_gap": scen["gap"]["worst_people_per_branch"],
        "plan_placed_gap": scen["gap"]["placed"],
        "plan_female_equity": scen["equity"]["share_to_low_female_literacy"] * 100,
        "plan_female_gap": scen["gap"]["share_to_low_female_literacy"] * 100,
        "plan_female_women": scen["women"]["share_to_low_female_literacy"] * 100,
        "plan_low_female_units": int((units["literacy_female"] < config.LOW_FEMALE_LITERACY).sum()),
        "plan_gini_equity_4000": sizes[4000]["equity"]["gini"], "plan_units_equity_500": sizes[500]["equity"]["units_below_half"],
        # branchless banking
        "wallet_first": config.BB_QUARTER_LABELS[min(config.BB_FILES)], "wallet_last": config.BB_QUARTER_LABELS[max(config.BB_FILES)],
        "wallet_quarters": len(config.BB_FILES),
        "wallet_accounts_m": nat.loc[last_q, "accounts"] / 1e6, "wallet_accounts_first_m": nat.loc[first_q, "accounts"] / 1e6,
        "wallet_agents_k": nat.loc[last_q, "agents"] / 1e3, "wallet_agents_first_k": nat.loc[first_q, "agents"] / 1e3,
        "agents_growth": (nat.loc[last_q, "agents"] / nat.loc[first_q, "agents"] - 1) * 100,
        "accounts_growth": (nat.loc[last_q, "accounts"] / nat.loc[first_q, "accounts"] - 1) * 100,
        "active_agents_first": nat.loc[first_q, "active_agent_share"], "active_agents_last": nat.loc[last_q, "active_agent_share"],
        "active_accounts_last": nat.loc[last_q, "active_account_share"],
        "wallet_deposits_bn": nat.loc[last_q, "deposits_pkr_mn"] / 1e3,
        "agents_punjab": wallet.loc["Punjab (incl. Islamabad)", "agents_per_100k_adults"],
        "agents_baloch": wallet.loc["Balochistan", "agents_per_100k_adults"],
        "agents_kp": wallet.loc["Khyber Pakhtunkhwa", "agents_per_100k_adults"],
        "agents_sindh": wallet.loc["Sindh", "agents_per_100k_adults"],
        "women_kp": wallet.loc["Khyber Pakhtunkhwa", "female_share"], "women_punjab": wallet.loc["Punjab (incl. Islamabad)", "female_share"],
        "wallet_flags": len(quality["wallet_irregularities"]),
        # data checks
        "register_rows": register["rows"], "register_banks": register["banks"], "register_mfb": register["mfb_dfi"],
        "register_in": register["in_scope"], "register_out": register["outside_coverage"],
        "register_mismatches": sum(m["branches"] for m in register["province_mismatches"]),
        "sbp20_total": sbp20["grand_total"], "sbp20_in": sbp20["in_scope"], "sbp20_out": sbp20["outside_coverage"],
        "sbp20_districts": sbp20["districts"],
        "wdi_2024": checks["banks_per_100k_adults_2024"]["world_bank_wdi"], "mine_2024": checks["banks_per_100k_adults_2024"]["this_project"],
        "wdi_2020": checks["banks_per_100k_adults_2020"]["world_bank_wdi"], "mine_2020": checks["banks_per_100k_adults_2020"]["this_project"],
        "census_total": h["population"], "n_raw_files": len(manifest),
        "register_date": config.BRANCH_REGISTER_DATE, "baseline_date": config.BRANCH_BASELINE_DATE,
        "census_year": config.CENSUS_YEAR, "findex_year": config.FINDEX_YEAR,
        "seed": config.SEED, "bootstrap_draws": config.BOOTSTRAP_DRAWS,
        "low_share_of_avg": config.LOW_DENSITY_SHARE_OF_AVERAGE, "gap_significance": config.GAP_SIGNIFICANCE,
        "low_female_literacy": config.LOW_FEMALE_LITERACY, "n_findex_rows": len(r.panel),
        "n_findex_indicators": r.panel["indicator"].nunique(),
        # tables
        "table_provinces": province_table(r), "table_shortfalls": shortfall_table(r), "table_clusters": cluster_table(r),
        "table_specs": specification_table(r), "table_coefficients": coefficient_table(r),
        "table_scenarios": scenario_table(r), "table_sources": source_table(),
        "table_pbi_pages": powerbi_pages_table(), "table_pbi_tables": powerbi_tables_table(r),
        "table_pbi_measures": powerbi_measures_table(), "n_pbi_pages": len(report_pages()),
        "pbi_gallery_readme": powerbi_gallery("docs/powerbi_pages", ("overview", "where", "gaps", "planner")),
        "pbi_gallery_all": powerbi_gallery("powerbi_pages"),
    }
    return values


def report_pages() -> list:
    from .powerbi import report
    return report.PAGES


def render_all(r: Results | None = None) -> dict:
    """Every document as text, keyed by its output path."""
    r = r or load()
    values = context(r)
    return {path: render((TEMPLATE_DIR / name).read_text(encoding="utf-8"), values) for name, path in OUTPUTS.items()}


def build() -> None:
    for path, text in render_all().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
