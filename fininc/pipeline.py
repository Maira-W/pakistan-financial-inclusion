"""Pipeline stages.

    build    raw files            -> data/interim   (clean, validated tables)
    analyze  data/interim         -> data/processed (models, rankings, summaries)
    report   data/processed       -> docs/figures, dashboard/, powerbi/

Each stage reads only the output of the stage before it, so any stage can be rerun on its own.
No timestamps are written, so rerunning on unchanged data reproduces the same files.
"""

from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd

from . import config, features, ingest, models, paths
from .loaders import census, findex, geo

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload, indent=1, ensure_ascii=False, default=_json_default) + "\n",
                    encoding="utf-8")


def _write_compact(path, payload) -> None:
    """GeoJSON without extra whitespace: the file is embedded in the dashboard."""
    path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")


def _json_default(value):
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if np.isnan(value) else float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Cannot serialise {type(value)}")


def _read_json(path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _save(df: pd.DataFrame, path, digits: int = 4) -> None:
    df.round(digits).to_csv(path, index=False)


# ---------------------------------------------------------------------------
# build: raw -> interim
# ---------------------------------------------------------------------------
def external_checks(units: pd.DataFrame) -> dict:
    """Compare totals with independent published figures."""
    wdi = findex.load_wdi_branches()
    pak = wdi[(wdi["country"] == "PAK") & (wdi["indicator"] == "FB.CBK.BRCH.P5")].set_index("year")["value"]
    adults_2023 = float(units["adults_15plus"].sum())
    adult_share = adults_2023 / float(units["pop"].sum())
    # 2020 adults: interpolate the census population to 2020 and keep the 2023 adult share (approximate).
    pop_2020 = float((units["pop_2017"] * (units["pop"] / units["pop_2017"]) ** 0.5).sum())
    return {
        "banks_per_100k_adults_2024": {"this_project": float(units["banks_2024"].sum() / adults_2023 * 1e5),
                                       "world_bank_wdi": float(pak.get(2024, np.nan))},
        "banks_per_100k_adults_2020": {"this_project": float(units["banks_2020"].sum() / (pop_2020 * adult_share) * 1e5),
                                       "world_bank_wdi": float(pak.get(2020, np.nan))},
        "note": "This project excludes Azad Jammu & Kashmir and Gilgit-Baltistan on both sides of the ratio and "
                "uses census age shares; the World Bank figure comes from the IMF Financial Access Survey.",
    }


def build() -> None:
    paths.ensure_dirs()
    units, quality = features.build_unit_table()
    provinces = features.province_table(units)
    bb_regions, bb_national = features.bb_region_table(units)
    panel = findex.load_panel()
    cross = findex.load_cross_section()
    quality["external_checks"] = external_checks(units)
    flagged = bb_regions[bb_regions["flag_accounts"] | bb_regions["flag_female"]]
    quality["wallet_irregularities"] = [
        {"region": r.region, "quarter": r.quarter, "what": ("accounts" if r.flag_accounts else "women's share"),
         "accounts_vs_neighbouring_quarters_pct": None if pd.isna(r.accounts_vs_neighbours_pct) else round(float(r.accounts_vs_neighbours_pct), 1),
         "female_share": None if pd.isna(r.female_share) else round(float(r.female_share), 1)}
        for r in flagged.itertuples()]
    quality["data_vintages"] = {
        "branch_register": config.BRANCH_REGISTER_DATE, "branch_baseline": config.BRANCH_BASELINE_DATE,
        "census": config.CENSUS_YEAR, "findex": config.FINDEX_YEAR,
        "wallet_statistics": [config.BB_QUARTER_LABELS[q] for q in config.BB_FILES][::len(config.BB_FILES) - 1]}

    units_out = units.copy()
    units_out["members"] = units_out["members"].map("; ".join)
    _save(units_out, paths.INTERIM / "unit_features.csv", 6)
    _save(provinces, paths.INTERIM / "provinces.csv", 6)
    _save(bb_regions, paths.INTERIM / "bb_regions_quarterly.csv", 6)
    _save(bb_national, paths.INTERIM / "bb_national_quarterly.csv", 6)
    _save(panel, paths.INTERIM / "findex_panel.csv", 6)
    _save(cross, paths.INTERIM / "findex_cross_section.csv", 6)
    _write_json(paths.INTERIM / "data_quality.json", quality)
    print(f"[build] {len(units)} units, {len(panel)} Findex rows, {len(cross)} economies")


# ---------------------------------------------------------------------------
# analyze: interim -> processed
# ---------------------------------------------------------------------------
def analyze() -> None:
    paths.ensure_dirs()
    units = pd.read_csv(paths.INTERIM / "unit_features.csv")
    panel = pd.read_csv(paths.INTERIM / "findex_panel.csv")
    cross_section = pd.read_csv(paths.INTERIM / "findex_cross_section.csv")

    # 1. Access-gap model, district types, inequality, convergence
    modelled, model_summary = models.fit_access_model(units)
    clustered, cluster_info = models.cluster_units(modelled)
    inequality_summary, curves = models.inequality(clustered)
    convergence_summary = models.convergence(clustered)

    # 2. Cross-country benchmark
    cross_df, cross_summary = models.cross_country(cross_section)

    # 3. Planner results at a default size and across sizes
    default_k = 1000
    scenario = {"default_k": default_k, "network_size": int(clustered["branches_2024"].sum()),
                "table": models.scenario_table(clustered, default_k),
                "sizes": {str(k): models.scenario_table(clustered, k) for k in (250, 500, 1000, 2000, 4000)},
                "strategies": models.STRATEGIES}
    curve = models.scenario_curve(clustered, [0] + list(range(250, 4001, 250)))

    # 4. National headline numbers used in the documents and the dashboard
    adults = float(clustered["adults_15plus"].sum())
    headline = {
        "population": int(clustered["pop"].sum()),
        "units": int(len(clustered)),
        "banks_2024": int(clustered["banks_2024"].sum()), "mfb_2024": int(clustered["mfb_2024"].sum()),
        "branches_2024": int(clustered["branches_2024"].sum()),
        "banks_2020": int(clustered["banks_2020"].sum()),
        "banks_growth_pct": float((clustered["banks_2024"].sum() / clustered["banks_2020"].sum() - 1) * 100),
        "branches_per_100k": float(clustered["branches_2024"].sum() / clustered["pop"].sum() * 1e5),
        "banks_per_100k_adults": float(clustered["banks_2024"].sum() / adults * 1e5),
        "rural_branch_share": float(clustered["rural_branches_2024"].sum() / clustered["branches_2024"].sum() * 100),
        "rural_pop_share": float(clustered["pop_rural"].sum() / clustered["pop"].sum() * 100),
        "rural_per_100k_rural": float(clustered["rural_branches_2024"].sum() / clustered["pop_rural"].sum() * 1e5),
        "urban_per_100k_urban": float(clustered["urban_branches_2024"].sum() / clustered["pop_urban"].sum() * 1e5),
        "mfb_rural_share": float(clustered["rural_mfb_2024"].sum() / clustered["mfb_2024"].sum() * 100),
        "bank_rural_share": float(clustered["rural_banks_2024"].sum() / clustered["banks_2024"].sum() * 100),
        "islamic_share_of_banks": float(clustered["islamic_banks_2024"].sum() / clustered["banks_2024"].sum() * 100),
        "units_below_half_average": int(scenario["table"][0]["units_below_half"]),
        "population_below_half_average": float(scenario["table"][0]["population_below_half"]),
        "units_zero_branches": int((clustered["branches_2024"] == 0).sum()),
        "ses_explained_variance": None,
    }
    quality = _read_json(paths.INTERIM / "data_quality.json")
    headline["ses_explained_variance"] = quality["ses_index"]["explained_variance"]

    # 5. Findex tables for Pakistan
    segments = findex.segment_table(panel)
    barriers = findex.barrier_table(panel)
    mm_barriers = findex.mobile_money_barriers(panel)

    # District boundaries merged to the analysis units
    districts, _ = census.load_districts()
    units_for_geo = clustered[["unit_id", "unit", "province"]]
    unit_geo, province_geo = geo.build_unit_geojson(districts, units_for_geo)
    _write_compact(paths.PROCESSED / "unit_boundaries.geojson", unit_geo)
    _write_compact(paths.PROCESSED / "province_boundaries.geojson", province_geo)

    # Write outputs
    clustered_out = clustered.copy()
    _save(clustered_out, paths.PROCESSED / "units.csv", 6)
    _save(segments, paths.PROCESSED / "findex_segments.csv", 4)
    _save(barriers, paths.PROCESSED / "findex_barriers.csv", 4)
    _save(mm_barriers, paths.PROCESSED / "findex_mobile_money_barriers.csv", 4)
    cross_cols = ["country", "name", "region", "income", "account", "account_women", "account_men", "account_gap",
                  "phone", "phone_women", "phone_men", "phone_gap", "mobile_money", "fi_account", "digital_payment",
                  "gdp_pc_ppp", "gdp_year", "expected_account", "account_residual", "pred_low", "pred_high"]
    _save(cross_df[cross_cols], paths.PROCESSED / "cross_country.csv", 3)
    _save(curve, paths.PROCESSED / "scenario_curve.csv", 4)

    summary = {
        "headline": headline, "quality": quality, "access_model": model_summary, "clusters": cluster_info,
        "inequality": inequality_summary, "convergence": convergence_summary, "cross_country": cross_summary,
        "scenario_default": scenario["table"],
    }
    _write_json(paths.PROCESSED / "summary.json", summary)
    _write_json(paths.PROCESSED / "lorenz_curves.json", curves)
    _write_json(paths.PROCESSED / "scenario.json", scenario)
    print(f"[analyze] shortfall {model_summary['shortfall_total']:.0f} branches "
          f"(90% range {model_summary['shortfall_p05']:.0f}-{model_summary['shortfall_p95']:.0f}); "
          f"Pakistan account shortfall vs income {cross_summary['pakistan']['shortfall_pts']:.1f} pts")


# ---------------------------------------------------------------------------
# report: processed -> figures, dashboard, Power BI
# ---------------------------------------------------------------------------
def report() -> None:
    from . import charts, dashboard, dictionary, docs, powerbi

    paths.ensure_dirs()
    charts.make_all()
    dashboard.build()
    powerbi.build()
    (paths.DOCS / "data_dictionary.md").write_text(dictionary.render_markdown(), encoding="utf-8")
    docs.build()
    print("[report] figures, dashboard, Power BI project, data dictionary and documents written")


def all() -> None:  # noqa: A001 - matches the command name
    build()
    analyze()
    report()


def verify_raw() -> list[str]:
    return ingest.verify()
