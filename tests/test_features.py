"""The district table: invariants that must hold whatever the data, and agreement with the sources' totals."""

import numpy as np
import pandas as pd
import pytest

from fininc import config, features, paths


def test_one_row_per_district_with_a_unique_id(units):
    assert len(units) == 120
    assert units["unit"].is_unique and units["unit_id"].is_unique
    assert set(units["province"]) == set(config.CENSUS_PROVINCE_FILES)


def test_population_and_branch_totals_match_the_sources(units, results):
    quality = results.summary["quality"]
    assert units["pop"].sum() == config.OFFICIAL_CENSUS_TOTALS["Pakistan"]["2023"]
    assert units["branches_2024"].sum() == quality["register_2024"]["in_scope"] == 18_322
    assert units["banks_2020"].sum() == quality["sbp_2020"]["in_scope"] == 14_211
    assert units["banks_2024"].sum() + units["mfb_2024"].sum() == units["branches_2024"].sum()


def test_branch_parts_are_consistent(units):
    assert (units["rural_branches_2024"] <= units["branches_2024"]).all()
    assert (units["urban_branches_2024"] == units["branches_2024"] - units["rural_branches_2024"]).all()
    assert (units["rural_banks_2024"] <= units["banks_2024"]).all() and (units["islamic_banks_2024"] <= units["banks_2024"]).all()
    assert (units["branches_2024"] >= 0).all() and (units["banks_2020"] >= 0).all()


def test_shares_are_percentages(units):
    for column in [c for c in units.columns if c.endswith("_share") and c not in ("top_bank_share",)] + ["literacy"]:
        values = units[column].dropna()
        assert values.between(0, 100).all(), column


def test_branch_density_is_branches_over_population(units):
    expected = units["branches_2024"] / units["pop"] * 1e5
    assert np.allclose(units["branches_per_100k"], expected, atol=2e-6)        # the file keeps six decimals
    assert np.allclose(units["density_change"], units["density_2024_banks"] - units["density_2020"], atol=2e-6)


def test_development_index_is_standardised_and_points_the_right_way(units):
    assert units["ses_index"].mean() == pytest.approx(0, abs=1e-6)
    assert units["ses_index"].std(ddof=0) == pytest.approx(1, abs=1e-6)
    assert units["ses_index"].corr(units["literacy"]) > 0.8


def test_only_one_district_has_no_branch_and_it_is_documented(units, results):
    assert (units["branches_2024"] == 0).sum() == results.headline["units_zero_branches"] == 1
    assert units["people_per_branch"].isna().sum() == 1


def test_model_columns_are_complete(units):
    for column in ["expected_branches", "expected_low", "expected_high", "branch_gap", "p_below_expected", "cluster"]:
        assert units[column].notna().all(), column
    assert (units["expected_low"] <= units["expected_high"]).all()
    assert ((units["p_below_expected"] >= 0) & (units["p_below_expected"] <= 1)).all()
    assert (units["robust_shortfall"] <= units["below_expected"]).all()


def test_provinces_are_the_sum_of_their_districts(units, results):
    by_province = units.groupby("province")[["pop", "branches_2024", "rural_branches_2024"]].sum()
    table = results.provinces.set_index("province")
    assert (by_province["pop"] == table["pop"]).all()
    assert (by_province["branches_2024"] == table["branches_2024"]).all()


# --------------------------------------------------------------------------- helper functions
def test_jump_detector_flags_the_worst_point_and_not_its_neighbours():
    series = pd.Series([100.0, 102.0, 400.0, 106.0, 108.0])
    flagged = features._flag_jumps(series, 25.0, relative=True)
    assert flagged.tolist() == [False, False, True, False, False]


def test_jump_detector_leaves_a_smooth_series_alone():
    assert not features._flag_jumps(pd.Series([10.0, 11.0, 12.5, 14.0, 15.0]), 25.0, relative=True).any()


def test_jump_detector_can_measure_in_points():
    series = pd.Series([30.0, 30.5, 22.0, 31.0, 30.2])
    assert features._flag_jumps(series, 4.0, relative=False).tolist() == [False, False, True, False, False]


def test_development_index_flips_sign_if_needed():
    rng = np.random.default_rng(5)
    base = rng.normal(0, 1, 40)
    table = pd.DataFrame({c: base * k + rng.normal(0, 0.1, 40) + 50 for c, k in zip(features.SES_COLUMNS, [-3, -3, -2, -2, -1, -1, -2])})
    out, info = features.add_ses_index(table)
    assert out["ses_index"].corr(out["literacy"]) > 0.9
    assert info["explained_variance"] > 0.9


def test_wallet_regions_cover_every_quarter(results):
    bb = results.bb_regions
    assert bb["quarter"].nunique() == len(config.BB_FILES)
    assert set(bb["region"]) >= {"Punjab (incl. Islamabad)", "Sindh", "Khyber Pakhtunkhwa", "Balochistan"}
    assert bb.loc[bb["region"] == "Azad Kashmir", "accounts_per_100_adults"].isna().all()


@pytest.mark.slow
def test_district_table_is_rebuilt_from_the_raw_files():
    """The slow check: the committed table is what the raw files produce today."""
    rebuilt, _ = features.build_unit_table()
    rebuilt["members"] = rebuilt["members"].map("; ".join)
    committed = pd.read_csv(paths.INTERIM / "unit_features.csv")
    assert list(rebuilt.columns) == list(committed.columns)
    for column in rebuilt.columns:
        if pd.api.types.is_numeric_dtype(committed[column]):
            assert np.allclose(rebuilt[column].astype(float).round(6), committed[column], rtol=1e-6, equal_nan=True), column
        else:
            assert (rebuilt[column].astype(str) == committed[column].astype(str)).all(), column
