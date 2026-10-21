"""Build the interactive dashboard: one self-contained HTML page.

The page template (templates/dashboard.html) and script (templates/dashboard.js) are filled with a single JSON
object of results, so every number on the page comes from the pipeline. Charts are drawn in the browser with
Plotly.js, which is loaded from a CDN.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from plotly.offline import get_plotlyjs_version

from . import config, narrative
from .paths import DASHBOARD, ROOT, TEMPLATES
from .results import Results, load

UNIT_FIELDS = {
    "id": "unit_id", "name": "unit", "province": "province", "pop": "pop", "adults": "adults_15plus",
    "urban": "urban_share", "growth": "pop_growth_pct_pa", "lit": "literacy", "litF": "literacy_female",
    "litM": "literacy_male", "litGap": "literacy_gender_gap", "ses": "ses_index", "femaleOwner": "female_owner_share",
    "banks": "banks_2024", "mfb": "mfb_2024", "branches": "branches_2024", "ruralBranches": "rural_branches_2024",
    "per100k": "branches_per_100k", "banksPer100k": "banks_per_100k", "mfbShare": "mfb_share",
    "ruralShare": "rural_branch_share", "ruralPopShare": "rural_pop_share", "islamicShare": "islamic_share",
    "nBanks": "n_banks", "topBank": "top_bank_share", "banks2020": "banks_2020", "d2020": "density_2020",
    "dChange": "density_change", "bChange": "banks_change", "expected": "expected_branches",
    "expLo": "expected_low", "expHi": "expected_high", "gap": "branch_gap", "ratio": "gap_ratio",
    "pBelow": "p_below_expected", "below": "below_expected", "above": "above_expected",
    "robust": "robust_shortfall", "cluster": "cluster", "ppb": "people_per_branch",
}


def _clean(value):
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return None if np.isnan(value) else round(float(value), 4)
    return value


def _records(df: pd.DataFrame, columns: dict[str, str] | list[str]) -> list[dict]:
    mapping = columns if isinstance(columns, dict) else {c: c for c in columns}
    out = []
    for row in df.to_dict(orient="records"):
        out.append({new: _clean(row[old]) for new, old in mapping.items()})
    return out


def build_data(r: Results) -> dict:
    units = r.units.copy()
    cross = r.cross

    findex_series = {}
    for indicator, group in r.panel.groupby("indicator"):
        findex_series[indicator] = {
            "label": group["label"].iloc[0],
            "values": {c: sorted([[int(y), round(float(v), 3)] for y, v in zip(g["year"], g["value"])])
                       for c, g in group.groupby("country")}}

    bb_cols = ["region", "quarter", "label", "accounts", "agents", "accounts_per_100_adults", "agents_per_100k_adults",
               "female_share", "flag_accounts", "flag_female", "pop", "adults_15plus"]
    bb = r.bb_regions[bb_cols].copy()

    provinces_cols = ["province", "units", "pop", "urban_share", "banks_2020", "banks_2024", "mfb_2024",
                      "branches_2024", "branches_per_100k", "banks_per_100k", "mfb_per_100k",
                      "rural_branches_per_100k_rural", "urban_branches_per_100k_urban", "rural_branch_share",
                      "mfb_share", "density_2020", "density_2024_banks", "banks_growth_pct"]

    quality = r.summary["quality"]
    return {
        "meta": {
            "plotly": get_plotlyjs_version(), "units": int(len(units)),
            "vintages": {"branches": config.BRANCH_REGISTER_DATE, "baseline": config.BRANCH_BASELINE_DATE,
                         "census": config.CENSUS_YEAR, "findex": config.FINDEX_YEAR,
                         "wallet_first": config.BB_QUARTER_LABELS[min(config.BB_FILES)],
                         "wallet_last": config.BB_QUARTER_LABELS[max(config.BB_FILES)]},
            "lowDensityShare": config.LOW_DENSITY_SHARE_OF_AVERAGE, "lowFemaleLiteracy": config.LOW_FEMALE_LITERACY,
        },
        "headline": r.headline,
        "findings": narrative.findings(r),
        "units": _records(units, UNIT_FIELDS),
        "geo": r.boundaries,
        "provinceGeo": r.province_boundaries,
        "provinces": _records(r.provinces, provinces_cols),
        "wallet": {"regions": _records(bb, list(bb.columns)),
                   "national": _records(r.bb_national, ["quarter", "label", "agents", "active_agents", "accounts",
                                                         "active_accounts", "deposits_pkr_mn", "active_account_share",
                                                         "active_agent_share"])},
        "findex": {
            "series": findex_series,
            "segments": _records(r.segments, ["segment", "group", "year", "value"]),
            "barriers": _records(r.barriers, ["reason", "share_of_unbanked", "derived"]),
            "mmBarriers": _records(r.mm_barriers, ["reason", "value"]),
        },
        "cross": _records(cross, ["country", "name", "region", "income", "account", "account_women", "account_men",
                                  "account_gap", "phone_women", "phone_men", "phone_gap", "gdp_pc_ppp",
                                  "expected_account", "account_residual", "pred_low", "pred_high"]),
        "crossSummary": r.summary["cross_country"],
        "model": r.summary["access_model"],
        "clusters": r.summary["clusters"],
        "inequality": r.summary["inequality"],
        "lorenz": r.lorenz,
        "convergence": r.summary["convergence"],
        "scenario": r.scenario,
        "quality": {
            "census": quality["census_official_check"], "external": quality["external_checks"],
            "register": quality["register_2024"], "sbp2020": quality["sbp_2020"],
            "wallet": quality["wallet_irregularities"], "notes": quality["census_notes"],
            "ses": quality["ses_index"],
        },
    }


# A tiny page at the repository root so the GitHub Pages address opens the dashboard.
REDIRECT_PAGE = ('<!doctype html><html lang="en"><meta charset="utf-8">'
                 '<meta http-equiv="refresh" content="0; url=dashboard/dashboard.html">'
                 '<title>Financial inclusion in Pakistan</title>'
                 '<p><a href="dashboard/dashboard.html">Open the dashboard</a></p></html>\n')


def render(r: Results | None = None) -> str:
    """The dashboard page as text: the template with the results, the script and the plotting library address filled in."""
    data = build_data(r or load())
    html = (TEMPLATES / "dashboard.html").read_text(encoding="utf-8")
    script = (TEMPLATES / "dashboard.js").read_text(encoding="utf-8")
    payload = json.dumps(data, separators=(",", ":"), ensure_ascii=True)
    for token, value in (("__PLOTLY_URL__", f"https://cdn.plot.ly/plotly-{data['meta']['plotly']}.min.js"),
                         ("__DASHBOARD_JS__", script), ("__DATA__", payload)):
        if token not in html:
            raise ValueError(f"Template is missing {token}")
        html = html.replace(token, value)
    return html


def build() -> None:
    DASHBOARD.mkdir(parents=True, exist_ok=True)
    (DASHBOARD / "dashboard.html").write_text(render(), encoding="utf-8")
    (ROOT / "index.html").write_text(REDIRECT_PAGE, encoding="utf-8")
