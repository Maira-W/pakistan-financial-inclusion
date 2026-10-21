"""The statistical and planning functions, checked on small examples whose answers are known."""

import numpy as np
import pandas as pd
import pytest

from fininc import config, models


# --------------------------------------------------------------------------- inequality
def test_gini_is_zero_when_branches_follow_population():
    pop = np.array([100.0, 300.0, 600.0])
    _, _, gini = models.lorenz(pop, pop * 0.01)
    assert gini == pytest.approx(0.0, abs=1e-12)


def test_gini_when_one_of_n_equal_districts_has_everything():
    n = 5
    counts = np.zeros(n)
    counts[-1] = 10
    _, _, gini = models.lorenz(np.ones(n), counts)
    assert gini == pytest.approx(1 - 1 / n)


def test_lorenz_curve_runs_from_zero_to_one_and_never_exceeds_the_diagonal():
    rng = np.random.default_rng(1)
    pop = rng.uniform(1, 10, 30)
    counts = rng.integers(0, 50, 30).astype(float)
    x, y, _ = models.lorenz(pop, counts)
    assert x[0] == y[0] == 0 and x[-1] == pytest.approx(1) and y[-1] == pytest.approx(1)
    assert (y <= x + 1e-12).all()


def test_theil_parts_add_up():
    rng = np.random.default_rng(2)
    df = pd.DataFrame({"count": rng.integers(1, 80, 24).astype(float), "pop": rng.uniform(1, 9, 24),
                       "group": np.repeat(list("abcd"), 6)})
    t = models.theil_decomposition(df, "count", "pop", "group")
    assert t["between"] + t["within"] == pytest.approx(t["theil"])
    assert 0 <= t["between_share"] <= 1


def test_theil_is_zero_when_branches_follow_population():
    df = pd.DataFrame({"count": [10.0, 20.0, 30.0, 40.0], "pop": [1.0, 2.0, 3.0, 4.0], "group": list("aabb")})
    assert models.theil_decomposition(df, "count", "pop", "group")["theil"] == pytest.approx(0.0, abs=1e-12)


# --------------------------------------------------------------------------- negative binomial tail probabilities
def test_nb_tail_probabilities_bracket_one():
    y = np.array([0, 3, 10, 40])
    mu = np.array([5.0, 5.0, 5.0, 5.0])
    below, above = models._nb_cdf(y, mu, alpha=0.2)
    assert ((below >= 0) & (below <= 1) & (above >= 0) & (above <= 1)).all()
    assert (below + above >= 1 - 1e-12).all()          # P(Y <= y) + P(Y >= y) = 1 + P(Y = y)
    assert np.all(np.diff(below) >= 0) and np.all(np.diff(above) <= 0)


def test_a_count_far_below_the_mean_is_unlikely():
    below, _ = models._nb_cdf(np.array([2]), np.array([100.0]), alpha=0.1)
    assert below[0] < 1e-6


# --------------------------------------------------------------------------- planner
@pytest.fixture()
def towns():
    return pd.DataFrame({
        "pop": [1_000_000.0, 400_000.0, 250_000.0, 100_000.0, 50_000.0],
        "branches_2024": [40, 12, 2, 1, 0],
        "expected_branches": [30.0, 10.0, 6.0, 2.0, 3.0],
        "literacy_gender_gap": [5.0, 10.0, 25.0, 30.0, 20.0],
        "literacy_female": [70.0, 55.0, 30.0, 25.0, 35.0],
    })


@pytest.mark.parametrize("strategy", ["equity", "women"])
def test_planner_places_exactly_the_points_it_is_given(towns, strategy):
    for k in (0, 1, 7, 100):
        assert models.allocate(towns, k, strategy).sum() == k


def test_equity_rule_evens_out_people_per_branch(towns):
    before = (towns["pop"] / (towns["branches_2024"] + 1)).max()
    added = models.allocate(towns, 30, "equity")
    after = (towns["pop"] / (towns["branches_2024"] + added + 1)).max()
    assert after < before
    assert added.iloc[-1] > 0           # the district with no branch gets some


def test_gap_rule_never_overfills_a_shortfall(towns):
    added = models.allocate(towns, 1000, "gap")
    shortfall = (towns["expected_branches"] - towns["branches_2024"]).clip(lower=0)
    assert (added <= np.ceil(shortfall)).all()
    assert added.sum() < 1000                          # it stops once every shortfall is filled


def test_planner_rejects_unknown_rules(towns):
    with pytest.raises(ValueError, match="Unknown strategy"):
        models.allocate(towns, 5, "random")


def test_outcomes_improve_when_points_go_where_people_per_branch_is_highest(towns):
    before = models.outcomes(towns)
    after = models.outcomes(towns, models.allocate(towns, 20, "equity"))
    assert after.worst_people_per_branch < before.worst_people_per_branch
    assert after.gini < before.gini
    assert after.national_density > before.national_density
    assert after.placed == 20


def test_a_district_without_branches_counts_as_one_person_per_branch_unit(towns):
    # The worst-served figure treats zero branches as one branch, so it stays finite.
    assert np.isfinite(models.outcomes(towns).worst_people_per_branch)


def test_scenario_curve_starts_from_the_same_point_under_every_rule(towns):
    curve = models.scenario_curve(towns, [0, 5, 10])
    start = curve[curve["points_requested"] == 0]
    assert len(start) == len(models.STRATEGIES)
    assert start["gini"].nunique() == 1
    assert set(curve["strategy"]) == set(models.STRATEGIES)


# --------------------------------------------------------------------------- cross-country benchmark
def test_benchmark_recovers_a_known_income_slope():
    rng = np.random.default_rng(3)
    n = 60
    income = rng.uniform(3, 11, n)
    df = pd.DataFrame({
        "country": [f"C{i:02d}" for i in range(n)], "name": [f"Country {i}" for i in range(n)],
        "log_gdp_pc": income, "account": 10 * income - 30 + rng.normal(0, 3, n),
        "account_gap": rng.uniform(0, 20, n), "phone_gap": rng.uniform(0, 20, n),
        "account_women": 40.0, "account_men": 50.0, "phone_women": 70.0, "phone_men": 80.0,
        "gdp_pc_ppp": np.exp(income),
    })
    df.loc[0, "country"] = "PAK"
    out, summary = models.cross_country(df)
    assert summary["slope_per_log_point"] == pytest.approx(10, abs=1.0)
    assert summary["n_economies"] == n
    assert {"expected_account", "account_residual", "pred_low", "pred_high"} <= set(out.columns)
    assert (out["pred_low"] < out["expected_account"]).all() and (out["expected_account"] < out["pred_high"]).all()


# --------------------------------------------------------------------------- access model, on a small synthetic country
def test_access_model_finds_the_district_that_is_short_of_branches():
    rng = np.random.default_rng(4)
    n = 40
    pop = rng.uniform(2e5, 4e6, n)
    urban = rng.uniform(0.05, 0.9, n)
    ses = rng.normal(0, 1, n)
    mean = np.exp(-9.0 + 0.9 * np.log(pop) + 0.8 * urban + 0.2 * ses)
    branches = rng.poisson(mean).astype(int)
    branches[0] = 0                                    # a large district with no branch at all
    pop[0] = pop.max() * 1.1
    df = pd.DataFrame({"unit": [f"U{i}" for i in range(n)], "pop": pop, "urban_share": urban * 100, "ses_index": ses,
                       "branches_2024": branches, "density_per_sqkm": rng.uniform(10, 500, n),
                       "pop_growth_pct_pa": rng.uniform(1, 3, n), "branches_per_100k": branches / pop * 1e5})
    out, summary = models.fit_access_model(df, draws=20)
    assert out.loc[0, "branch_gap"] > 0
    assert out.loc[0, "p_below_expected"] < config.GAP_SIGNIFICANCE
    assert summary["n_units"] == n and summary["alpha"] > 0
    assert summary["loo_mae"] < summary["baseline_mae"]
    assert summary["shortfall_p05"] <= summary["shortfall_p95"]


# --------------------------------------------------------------------------- committed outputs
def test_committed_district_types_are_reproduced_from_the_committed_table(units):
    from sklearn.metrics import adjusted_rand_score

    again, info = models.cluster_units(units.drop(columns=["cluster", "cluster_rank"]))
    # k-means can differ in a borderline district between machines; the grouping must be essentially the same.
    assert adjusted_rand_score(units["cluster"], again["cluster"]) > 0.95
    assert info["k"] == 4
    assert list(again.groupby("cluster")["ses_index"].mean().sort_values().index) == models.CLUSTER_NAMES


@pytest.mark.slow
def test_models_are_rerun_from_the_committed_feature_table():
    """The slow check: fitting the access model again on the stage-one table gives the committed expectations."""
    from fininc import paths

    features = pd.read_csv(paths.INTERIM / "unit_features.csv")
    modelled, summary = models.fit_access_model(features)
    committed = pd.read_csv(paths.PROCESSED / "units.csv")
    for column in ("expected_branches", "branch_gap", "p_below_expected", "expected_low", "expected_high"):
        assert np.allclose(modelled[column], committed[column], rtol=1e-4, atol=1e-5), column
    assert (modelled["robust_shortfall"].to_numpy() == committed["robust_shortfall"].to_numpy()).all()
    assert summary["shortfall_total"] == pytest.approx(
        float(np.maximum(committed["branch_gap"], 0).sum()), rel=1e-4)
