"""District harmonisation: names from different sources must land on the same analysis unit."""

import pandas as pd
import pytest

from fininc import units as U


@pytest.fixture(scope="module")
def unit_table():
    districts = pd.DataFrame({
        "district": ["LAHORE", "KARACHI CENTRAL", "KARACHI EAST", "UPPER CHITRAL", "LOWER CHITRAL", "TANK",
                     "DERA ISMAIL KHAN", "QUETTA"],
        "province": ["Punjab", "Sindh", "Sindh", "Khyber Pakhtunkhwa", "Khyber Pakhtunkhwa", "Khyber Pakhtunkhwa",
                     "Khyber Pakhtunkhwa", "Balochistan"],
    })
    return U.build_units(districts)


def test_key_ignores_case_and_punctuation():
    assert U.key("D.G.Khan") == U.key("D G KHAN") == "DGKHAN"


def test_slug_is_stable_and_safe():
    assert U.slug("Dera Ismail Khan") == "dera_ismail_khan"
    assert U.slug("Tharparkar (Mithi)") == "tharparkar_mithi"


def test_new_districts_fold_into_their_parent():
    assert U.unit_for_census_district("karachi east") == "Karachi"
    assert U.unit_for_census_district("UPPER CHITRAL") == "Chitral"
    assert U.unit_for_census_district("Tank") == "Dera Ismail Khan"
    assert U.unit_for_census_district("LAHORE") == "Lahore"


def test_units_group_member_districts(unit_table):
    by_unit = unit_table.set_index("unit")
    assert by_unit.loc["Karachi", "n_districts"] == 2
    assert by_unit.loc["Chitral", "members"] == ["LOWER CHITRAL", "UPPER CHITRAL"]
    assert by_unit.loc["Dera Ismail Khan", "n_districts"] == 2
    assert len(unit_table) == 5
    assert unit_table["unit_id"].is_unique


def test_a_unit_cannot_span_two_provinces():
    districts = pd.DataFrame({"district": ["KARACHI EAST", "KARACHI WEST"], "province": ["Sindh", "Punjab"]})
    with pytest.raises(ValueError, match="more than one province"):
        U.build_units(districts)


def test_resolver_maps_sbp_spellings(unit_table):
    resolver = U.UnitResolver(unit_table)
    assert resolver.resolve("Karachi") == "Karachi"
    assert resolver.resolve("D.I.Khan") == "Dera Ismail Khan"      # alias
    assert resolver.resolve("Tank") == "Dera Ismail Khan"          # created after 2020, listed on its own
    assert resolver.resolve("QUETTA") == "Quetta"                  # case-insensitive match on the letters


def test_resolver_sends_districts_outside_coverage_to_none(unit_table):
    resolver = U.UnitResolver(unit_table)
    assert resolver.resolve("Gilgit") is None
    assert resolver.resolve("Muzaffarabad") is None


def test_resolver_refuses_unknown_names(unit_table):
    resolver = U.UnitResolver(unit_table)
    with pytest.raises(KeyError, match="No analysis unit"):
        resolver.resolve("Atlantis")


def test_register_tehsil_override(unit_table):
    resolver = U.UnitResolver(unit_table)
    assert U.REGISTER_TEHSIL_OVERRIDES[("Sibi", "Gandawah")] == "Jhal Magsi"
    assert resolver.resolve("Sibi", "Gandawah") == "Jhal Magsi"
