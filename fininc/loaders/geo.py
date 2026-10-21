"""District boundaries for the maps.

Source: geoBoundaries gbHumanitarian ADM2 for Pakistan (2022, from the World Food Programme via HDX, CC BY 3.0 IGO).
The polygons follow the 2022 district structure, so several are merged here to match the analysis units.
"""

from __future__ import annotations

import json

import pandas as pd
import shapely
from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from .. import units as U
from ..paths import RAW

GEO_FILE = RAW / "geo" / "pak_adm2_humanitarian_2022_simplified.geojson"

# Polygon names that differ from the census names.
ALIASES = {
    "Central Karachi": "KARACHI CENTRAL", "East Karachi": "KARACHI EAST", "South Karachi": "KARACHI SOUTH",
    "West Karachi": "KARACHI WEST", "Korangi Karachi": "KORANGI", "Malir Karachi": "MALIR",
    "Chitral Lower": "LOWER CHITRAL", "Chitral Upper": "UPPER CHITRAL",
    "Kohistan Lower": "LOWER KOHISTAN", "Kohistan Upper": "UPPER KOHISTAN",
    "D. I. Khan": "DERA ISMAIL KHAN", "Leiah": "LAYYAH", "Shaheed Benazir Abad": "SHAHEED BENAZIRABAD",
    # Polygons for areas that the census lists inside a larger district:
    "Lehri": "SIBI",                    # southern tehsil of Sibi
    "Shaheed Sikandarabad": "KALAT",    # carved out of Kalat
}

# Azad Jammu & Kashmir and Gilgit-Baltistan: not covered by the census district tables.
OUTSIDE_COVERAGE = {
    "Bagh", "Bhimber", "Haveli", "Jhelum Valley", "Kotli", "Mirpur", "Muzaffarabad", "Neelum", "Poonch", "Sudhnoti",
    "Astore", "Darel", "Diamir", "Ghanche", "Ghizer", "Gilgit", "Gupis-Yasin", "Hunza", "Kharmang", "Nagar",
    "Rondu", "Shigar", "Skardu", "Tangir",
}

SIMPLIFY_DEGREES = 0.004   # about 400 m
GRID = 0.0001              # coordinates are rounded to about 11 m


def build_unit_geojson(districts: pd.DataFrame, units: pd.DataFrame) -> tuple[dict, dict]:
    """Merge the 2022 polygons into one polygon per analysis unit.

    Returns (units_geojson, provinces_geojson). Raises if a polygon cannot be placed or a unit has none.
    """
    census_names = {U.key(n): n for n in districts["district"]}
    members: dict[str, list] = {}
    for feature in json.loads(GEO_FILE.read_text(encoding="utf-8"))["features"]:
        name = feature["properties"]["shapeName"]
        if name in OUTSIDE_COVERAGE:
            continue
        district = ALIASES.get(name) or census_names.get(U.key(name))
        if district is None:
            raise KeyError(f"No analysis unit for boundary polygon {name!r}")
        members.setdefault(U.unit_for_census_district(district), []).append(shapely.make_valid(shape(feature["geometry"])))

    missing = set(units["unit"]) - members.keys()
    if missing:
        raise ValueError(f"Units without a boundary polygon: {sorted(missing)}")

    by_unit = units.set_index("unit")
    features, by_province = [], {}
    for unit, parts in sorted(members.items()):
        geom = unary_union(parts).simplify(SIMPLIFY_DEGREES, preserve_topology=True)
        geom = shapely.set_precision(geom, GRID)
        row = by_unit.loc[unit]
        features.append({"type": "Feature",
                         "properties": {"unit_id": row["unit_id"], "unit": unit, "province": row["province"]},
                         "geometry": mapping(geom)})
        by_province.setdefault(row["province"], []).append(geom)

    prov_features = []
    for province, parts in sorted(by_province.items()):
        geom = shapely.set_precision(unary_union(parts).simplify(SIMPLIFY_DEGREES, preserve_topology=True), GRID)
        prov_features.append({"type": "Feature", "properties": {"province": province}, "geometry": mapping(geom)})

    return ({"type": "FeatureCollection", "features": features},
            {"type": "FeatureCollection", "features": prov_features})
