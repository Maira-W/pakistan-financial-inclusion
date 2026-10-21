"""The dashboard is one HTML file built from the results; its data must agree with them."""

import json
import re

import pytest

from fininc import dashboard, paths


@pytest.fixture(scope="module")
def data(results):
    return dashboard.build_data(results)


def test_every_district_is_in_the_dashboard(data, results):
    assert len(data["units"]) == 120
    assert {u["name"] for u in data["units"]} == set(results.units["unit"])
    features = data["geo"]["features"]
    assert {f["properties"]["unit_id"] for f in features} == set(results.units["unit_id"])


def test_headline_numbers_are_the_pipeline_numbers(data, results):
    assert data["headline"]["branches_2024"] == int(results.units["branches_2024"].sum())
    assert data["model"]["units_robust_shortfall"] == int(results.units["robust_shortfall"].sum())
    assert data["meta"]["units"] == 120


def test_the_data_is_plain_json(data):
    """NaN or infinity would break the page's script; json.dumps refuses them."""
    json.dumps(data, allow_nan=False)


def test_the_planner_inputs_are_complete(data):
    for unit in data["units"]:
        for field in ("pop", "banks", "branches", "expected", "gap", "litGap", "litF"):
            assert unit[field] is not None or field == "litGap", (unit["name"], field)


def test_the_page_has_no_unfilled_placeholder(results):
    html = dashboard.render(results)
    assert not re.search(r"__[A-Z_]+__", html)
    assert "<script" in html and "plotly" in html.lower()


def test_the_committed_dashboard_is_what_the_results_produce(results):
    committed = (paths.DASHBOARD / "dashboard.html").read_text(encoding="utf-8")
    assert committed == dashboard.render(results)


def test_the_root_page_points_at_the_dashboard():
    root_page = (paths.ROOT / "index.html").read_text(encoding="utf-8")
    assert root_page == dashboard.REDIRECT_PAGE
    assert (paths.DASHBOARD / "dashboard.html").exists()
