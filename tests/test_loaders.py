"""The loaders turn messy public files into tables, and each one must reconcile to a published total."""

import json

import pandas as pd
import pytest

from fininc import config, ingest, paths
from fininc.loaders import census, sbp_bb, sbp_branches

pytestmark = pytest.mark.skipif(not (paths.RAW / "MANIFEST.json").exists(), reason="raw data not downloaded")


# --------------------------------------------------------------------------- provenance
def test_raw_files_match_the_manifest():
    assert ingest.verify() == []


def test_every_raw_file_has_a_source_and_a_licence():
    manifest = json.loads(paths.MANIFEST.read_text(encoding="utf-8"))["files"]
    assert manifest
    for name, meta in manifest.items():
        assert meta["source"].startswith("http"), name
        assert meta["licence"], name
        assert len(meta["sha256"]) == 64, name


# --------------------------------------------------------------------------- census
@pytest.fixture(scope="module")
def districts():
    return census.load_districts()[0]


def test_census_has_one_row_per_district(districts):
    assert len(districts) == 136
    assert districts["district"].is_unique
    assert not districts.isna().any().any()


def test_census_matches_the_official_provincial_totals_exactly(districts):
    check = census.check_against_official(districts)
    assert (check[["diff_2023", "diff_2017"]] == 0).all().all()
    assert districts["pop"].sum() == config.OFFICIAL_CENSUS_TOTALS["Pakistan"]["2023"]
    assert districts["pop_2017"].sum() == config.OFFICIAL_CENSUS_TOTALS["Pakistan"]["2017"]


def test_urban_and_rural_add_up_to_the_total(districts):
    gap = (districts["pop_urban"] + districts["pop_rural"] - districts["pop"]).abs() / districts["pop"]
    assert (gap <= 0.005).all()


def test_housing_table_total_equals_the_household_count(districts):
    # Table 20 carries its own TOTAL row; adding every row once halved the pakka share in an early version.
    assert ((districts["hh_housing_total"] - districts["hh_total"]).abs() <= 0.005 * districts["hh_total"]).all()
    assert (districts["hh_pakka"] <= districts["hh_housing_total"]).all()
    assert (districts["hh_pakka"] / districts["hh_housing_total"]).max() <= 1.0


def test_literate_people_cannot_exceed_the_people_asked(districts):
    assert (districts["lit10"] <= districts["pop10"]).all()
    assert (districts["lit10_f"] + districts["lit10_m"] <= districts["pop10"] * 1.001).all()


# --------------------------------------------------------------------------- State Bank
def test_2020_appendix_adds_up_to_its_grand_total():
    appendix, total = sbp_branches.load_2020_districts()
    assert total == 14_849
    assert int(appendix["branches"].sum()) == total
    assert len(appendix) == 134
    assert (appendix["islamic"] <= appendix["branches"]).all()


def test_register_rows_are_all_classified():
    register = sbp_branches.load_register()
    assert len(register) == 19_115
    assert set(register["kind"]) == {"Bank", "MFB/DFI"}
    assert register["rural"].isin([True, False]).all() and register["islamic"].isin([True, False]).all()
    assert register["district_reg"].notna().all()


def test_wallet_province_tables_add_up_to_the_national_totals():
    national, provinces = sbp_bb.load_all()
    assert national["quarter"].nunique() == len(config.BB_FILES)
    totals = national.set_index("quarter")
    for quarter, group in provinces.groupby("quarter"):
        assert group["accounts"].sum() == pytest.approx(totals.loc[quarter, "accounts"], rel=0.01)
        assert group["agents"].sum() == pytest.approx(totals.loc[quarter, "agents"], rel=0.01)


# --------------------------------------------------------------------------- Global Findex
def test_reason_codes_carry_the_meaning_the_world_bank_gives_them():
    """The labels were checked against the API names after three were found wrong; this pins them."""
    meaning = {"fin11a.s": "far", "fin11b.s": "expensive", "fin11d.s": "funds", "fin11e.s": "family",
               "fin11f.s": "trust"}
    for code, word in meaning.items():
        assert word in config.BARRIER_INDICATORS[code][0].lower(), code
    mobile = {"fin14a": "far", "fin14b": "expensive", "fin14c": "documentation", "fin14d": "money"}
    for code, word in mobile.items():
        assert word in config.MOBILE_MONEY_BARRIERS[code][0].lower(), code


def test_group_codes_carry_the_right_group():
    expected = {"account.t.d.1": "women", "account.t.d.2": "men", "account.t.d.7": "poorest", "account.t.d.8": "richest",
                "account.t.d.9": "rural", "account.t.d.10": "urban", "con1.1": "women", "con1.2": "men"}
    for code, word in expected.items():
        assert word in config.FINDEX_CATALOGUE[code][0].lower(), code


def test_documentation_barrier_is_converted_to_a_share_of_adults_without_an_account():
    panel = pd.read_csv(paths.INTERIM / "findex_panel.csv")
    barriers = pd.read_csv(paths.PROCESSED / "findex_barriers.csv").set_index("indicator")
    pak = panel[(panel["country"] == "PAK") & (panel["year"] == config.FINDEX_YEAR)].set_index("indicator")["value"]
    expected = pak[config.DOCUMENTATION_BARRIER] / (1 - pak["fiaccount.t.d"] / 100)
    assert barriers.loc[config.DOCUMENTATION_BARRIER, "share_of_unbanked"] == pytest.approx(expected, abs=1e-3)
    assert barriers.loc[config.DOCUMENTATION_BARRIER, "derived"]
    assert not barriers.drop(config.DOCUMENTATION_BARRIER)["derived"].any()


def test_shares_of_adults_stay_between_zero_and_one_hundred():
    panel = pd.read_csv(paths.INTERIM / "findex_panel.csv")
    assert panel["value"].between(0, 100).all()
    assert panel["year"].isin([2011, 2014, 2017, 2021, 2024]).all()
