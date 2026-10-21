"""Statistical models and decision-support calculations.

  * fit_access_model      negative binomial model: how many branches would a district of this size,
                          urbanisation and development level be expected to have?
  * cluster_units         district archetypes (k-means) with stability checks
  * inequality            Lorenz curve, Gini and Theil decomposition of branches against population
  * convergence           did low-density districts gain branches faster between 2020 and 2024?
  * cross_country         Pakistan against 139 economies, adjusted for income
  * allocate / outcomes   a planner that places new access points under three rules
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from . import config

_trapezoid = getattr(np, "trapezoid", None) or np.trapz

MODEL_FEATURES = ["log_pop", "urban", "ses_index"]
CANDIDATE_SPECS = {
    "population only": ["log_pop"],
    "population + urban share": ["log_pop", "urban"],
    "population + development": ["log_pop", "ses_index"],
    "population + urban share + development": ["log_pop", "urban", "ses_index"],
    "... + population density": ["log_pop", "urban", "ses_index", "log_density"],
    "... + population growth": ["log_pop", "urban", "ses_index", "pop_growth_pct_pa"],
}
SELECTED_SPEC = "population + urban share + development"


def prepare(units: pd.DataFrame) -> pd.DataFrame:
    """Add the transformed columns used by the models."""
    out = units.copy()
    out["log_pop"] = np.log(out["pop"])
    out["urban"] = out["urban_share"] / 100.0
    out["log_density"] = np.log(out["density_per_sqkm"])
    out["log_branch_density"] = np.log1p(out["branches_per_100k"])
    return out


# ---------------------------------------------------------------------------
# 1. Access-gap model
# ---------------------------------------------------------------------------
def _fit_nb(y: np.ndarray, X: np.ndarray, start: np.ndarray | None = None):
    return sm.NegativeBinomial(y, X).fit(disp=0, maxiter=300, start_params=start)


def _loo_predictions(y: np.ndarray, X: np.ndarray, full) -> tuple[np.ndarray, int]:
    """Leave-one-out predicted means. Falls back to the full-sample prediction if a refit fails."""
    pred = np.zeros(len(y))
    failures = 0
    for i in range(len(y)):
        mask = np.arange(len(y)) != i
        try:
            fit = _fit_nb(y[mask], X[mask], full.params)
            value = float(np.asarray(fit.predict(X[[i]]))[0])
            if not np.isfinite(value):
                raise ValueError
        except Exception:
            value = float(np.asarray(full.predict(X[[i]]))[0])
            failures += 1
        pred[i] = value
    return pred, failures


def _nb_cdf(y: np.ndarray, mu: np.ndarray, alpha: float) -> tuple[np.ndarray, np.ndarray]:
    """P(Y <= y) and P(Y >= y) under a negative binomial with mean mu and dispersion alpha."""
    n = 1.0 / alpha
    p = n / (n + mu)
    return stats.nbinom.cdf(y, n, p), stats.nbinom.sf(y - 1, n, p)


def compare_specs(df: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-out accuracy of each candidate specification against a proportional-to-population baseline."""
    y = df["branches_2024"].to_numpy(float)
    rows = []
    for name, cols in CANDIDATE_SPECS.items():
        X = sm.add_constant(df[cols]).to_numpy()
        full = _fit_nb(y, X)
        pred, _ = _loo_predictions(y, X, full)
        err = np.abs(pred - y)
        rows.append({"specification": name, "predictors": ", ".join(cols), "aic": float(full.aic),
                     "alpha": float(full.params[-1]), "loo_mae": float(err.mean()),
                     "loo_median_rel_error": float(np.median(err / np.maximum(y, 1)))})
    share = y.sum() / df["pop"].sum()
    base = np.abs(share * df["pop"].to_numpy() - y)
    rows.append({"specification": "baseline: proportional to population", "predictors": "population",
                 "aic": np.nan, "alpha": np.nan, "loo_mae": float(base.mean()),
                 "loo_median_rel_error": float(np.median(base / np.maximum(y, 1)))})
    return pd.DataFrame(rows)


def fit_access_model(units: pd.DataFrame, draws: int = config.BOOTSTRAP_DRAWS) -> tuple[pd.DataFrame, dict]:
    """Fit the selected model, add expected branches and gaps to the table, and summarise the fit.

    expected_branches is a leave-one-out prediction, so a district never helps to predict itself.
    The out-of-bag bootstrap gives a range for each prediction and for the total shortfall.
    """
    df = prepare(units)
    cols = MODEL_FEATURES
    y = df["branches_2024"].to_numpy(float)
    X = sm.add_constant(df[cols]).to_numpy()
    full = _fit_nb(y, X)
    alpha = float(full.params[-1])

    expected, failures = _loo_predictions(y, X, full)
    p_below, p_above = _nb_cdf(y, expected, alpha)

    # Out-of-bag bootstrap: refit on a resample, predict only the districts the resample left out.
    rng = np.random.default_rng(config.SEED)
    n = len(df)
    oob = [[] for _ in range(n)]
    totals = []
    for _ in range(draws):
        idx = rng.integers(0, n, n)
        out_of_bag = np.setdiff1d(np.arange(n), idx)
        if len(out_of_bag) < 10:
            continue
        try:
            fit = _fit_nb(y[idx], X[idx], full.params)
        except Exception:
            continue
        mu = np.asarray(fit.predict(X[out_of_bag]), dtype=float)
        if not np.all(np.isfinite(mu)):
            continue
        for j, value in zip(out_of_bag, mu):
            oob[j].append(value)
        totals.append(n / len(out_of_bag) * np.maximum(mu - y[out_of_bag], 0).sum())
    lo = np.array([np.percentile(v, 10) if len(v) >= 5 else np.nan for v in oob])
    hi = np.array([np.percentile(v, 90) if len(v) >= 5 else np.nan for v in oob])

    out = df.copy()
    out["expected_branches"] = expected
    out["expected_low"] = lo
    out["expected_high"] = hi
    out["branch_gap"] = expected - y
    out["gap_ratio"] = y / expected
    out["p_below_expected"] = p_below
    out["p_above_expected"] = p_above
    out["below_expected"] = out["p_below_expected"] < config.GAP_SIGNIFICANCE
    out["above_expected"] = out["p_above_expected"] < config.GAP_SIGNIFICANCE
    out["robust_shortfall"] = out["below_expected"] & (y < lo)
    out["people_per_branch"] = out["pop"] / out["branches_2024"].replace(0, np.nan)

    ci = full.conf_int()
    table = pd.DataFrame({
        "term": ["intercept"] + cols + ["alpha"],
        "coefficient": full.params, "std_error": full.bse, "p_value": full.pvalues,
        "ci_low": ci[:, 0], "ci_high": ci[:, 1],
    })
    table["rate_ratio"] = np.exp(table["coefficient"])
    table.loc[table["term"].isin(["intercept", "alpha"]), "rate_ratio"] = np.nan

    shortfall_point = float(np.maximum(out["branch_gap"], 0).sum())
    summary = {
        "formula": "branches_2024 ~ NegativeBinomial(log(population) + urban share + development index)",
        "n_units": int(n), "alpha": alpha, "aic": float(full.aic), "loo_failures": int(failures),
        "coefficients": table.replace({np.nan: None}).to_dict(orient="records"),
        "loo_mae": float(np.mean(np.abs(expected - y))),
        "baseline_mae": float(np.mean(np.abs(y.sum() / df["pop"].sum() * df["pop"].to_numpy() - y))),
        "loo_correlation": float(np.corrcoef(expected, y)[0, 1]),
        "spearman": float(stats.spearmanr(expected, y).statistic),
        "shortfall_total": shortfall_point,
        "shortfall_p05": float(np.percentile(totals, 5)), "shortfall_p95": float(np.percentile(totals, 95)),
        "bootstrap_draws_used": int(len(totals)),
        "units_below_expected": int(out["below_expected"].sum()),
        "units_above_expected": int(out["above_expected"].sum()),
        "units_robust_shortfall": int(out["robust_shortfall"].sum()),
        "specification_comparison": compare_specs(df).replace({np.nan: None}).to_dict(orient="records"),
    }
    summary["mae_reduction_vs_baseline"] = 1 - summary["loo_mae"] / summary["baseline_mae"]
    return out, summary


# ---------------------------------------------------------------------------
# 2. District archetypes
# ---------------------------------------------------------------------------
CLUSTER_FEATURES = ["log_pop", "urban_share", "ses_index", "log_branch_density"]
CLUSTER_NAMES = ["Frontier and remote", "Developing rural", "Established districts", "Metropolitan hubs"]
CLUSTER_K = 4


def cluster_units(units: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """K-means district types, named by their development level. Stability is the mean adjusted Rand index
    between the full-sample clusters and clusters from bootstrap resamples."""
    df = units.copy()
    Z = StandardScaler().fit_transform(df[CLUSTER_FEATURES])
    rng = np.random.default_rng(config.SEED)

    def stability(k: int, labels: np.ndarray) -> float:
        scores = []
        for _ in range(60):
            idx = rng.integers(0, len(Z), len(Z))
            boot = KMeans(n_clusters=k, n_init=10, random_state=int(rng.integers(1_000_000))).fit(Z[idx])
            scores.append(adjusted_rand_score(labels, boot.predict(Z)))
        return float(np.mean(scores))

    search = []
    for k in config.CLUSTER_K_RANGE:
        km = KMeans(n_clusters=k, n_init=30, random_state=config.SEED).fit(Z)
        search.append({"k": k, "silhouette": float(silhouette_score(Z, km.labels_)),
                       "stability_ari": stability(k, km.labels_)})

    km = KMeans(n_clusters=CLUSTER_K, n_init=30, random_state=config.SEED).fit(Z)
    df["_raw"] = km.labels_
    order = df.groupby("_raw")["ses_index"].mean().sort_values().index.tolist()
    names = {raw: CLUSTER_NAMES[rank] for rank, raw in enumerate(order)}
    df["cluster"] = df["_raw"].map(names)
    df["cluster_rank"] = df["_raw"].map({raw: rank for rank, raw in enumerate(order)})
    df = df.drop(columns="_raw")

    profile = (df.groupby("cluster").agg(
        units=("unit", "size"), population=("pop", "sum"), urban_share=("urban_share", "mean"),
        ses_index=("ses_index", "mean"), literacy_female=("literacy_female", "mean"),
        branches_per_100k=("branches_per_100k", "median"), mfb_share=("mfb_share", "mean"),
        rural_branch_share=("rural_branch_share", "mean"), cluster_rank=("cluster_rank", "first"))
        .sort_values("cluster_rank").reset_index())
    examples = (df.sort_values("pop", ascending=False).groupby("cluster")["unit"]
                  .apply(lambda s: ", ".join(s.head(4))).rename("largest_units"))
    profile = profile.merge(examples, on="cluster")
    info = {"k": CLUSTER_K, "features": CLUSTER_FEATURES,
            "selection_note": "k = 4 chosen for interpretability. Silhouette scores are flat across k = 3 to 6, "
                              "which means districts form a continuum rather than sharp groups.",
            "search": search, "profile": profile.to_dict(orient="records"),
            "silhouette_selected": float(silhouette_score(Z, km.labels_))}
    return df, info


# ---------------------------------------------------------------------------
# 3. Inequality
# ---------------------------------------------------------------------------
def lorenz(population: np.ndarray, counts: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Population-weighted Lorenz curve of branches, ordered from fewest to most branches per person."""
    order = np.argsort(counts / population)
    pop, cnt = population[order], counts[order]
    x = np.concatenate([[0], np.cumsum(pop) / pop.sum()])
    y = np.concatenate([[0], np.cumsum(cnt) / cnt.sum()])
    gini = 1 - 2 * _trapezoid(y, x)
    return x, y, float(gini)


def theil_decomposition(df: pd.DataFrame, count: str, pop: str, group: str) -> dict:
    """Theil T index of branches across districts, split into a between-province and a within-province part."""
    total_c, total_p = df[count].sum(), df[pop].sum()
    s, p = df[count] / total_c, df[pop] / total_p
    valid = s > 0
    theil = float((s[valid] * np.log(s[valid] / p[valid])).sum())
    between, within = 0.0, 0.0
    for _, g in df.groupby(group):
        S, P = g[count].sum() / total_c, g[pop].sum() / total_p
        if S > 0:
            between += S * np.log(S / P)
            gs, gp = g[count] / g[count].sum(), g[pop] / g[pop].sum()
            ok = gs > 0
            within += S * float((gs[ok] * np.log(gs[ok] / gp[ok])).sum())
    return {"theil": theil, "between": float(between), "within": float(within),
            "between_share": float(between / theil) if theil else float("nan")}


def inequality(units: pd.DataFrame) -> tuple[dict, dict]:
    """Gini and Theil for 2020 banks (2017 population) and 2024 banks and all branches (2023 population)."""
    spec = {
        "banks_2020": ("banks_2020", "pop_2017"),
        "banks_2024": ("banks_2024", "pop"),
        "branches_2024": ("branches_2024", "pop"),
    }
    summary, curves = {}, {}
    for name, (count, pop) in spec.items():
        x, y, g = lorenz(units[pop].to_numpy(float), units[count].to_numpy(float))
        summary[name] = {"gini": g, **theil_decomposition(units, count, pop, "province")}
        step = max(1, len(x) // 60)
        keep = sorted(set(range(0, len(x), step)) | {len(x) - 1})
        curves[name] = {"population_share": x[keep].tolist(), "branch_share": y[keep].tolist()}

    ordered = units.sort_values("branches_per_100k")
    pop_share = ordered["pop"].cumsum() / ordered["pop"].sum()
    bottom = ordered[pop_share <= 0.2]
    summary["bottom_20pct_population"] = {
        "units": int(len(bottom)), "population_share": float(bottom["pop"].sum() / units["pop"].sum()),
        "branch_share": float(bottom["branches_2024"].sum() / units["branches_2024"].sum())}
    top10 = units.nlargest(10, "branches_2024")
    summary["top10_by_branches"] = {
        "units": ", ".join(top10["unit"]), "branch_share": float(top10["branches_2024"].sum() / units["branches_2024"].sum()),
        "population_share": float(top10["pop"].sum() / units["pop"].sum())}
    return summary, curves


# ---------------------------------------------------------------------------
# 4. Convergence 2020 to 2024
# ---------------------------------------------------------------------------
def convergence(units: pd.DataFrame) -> dict:
    """Regress the change in bank branches per 100,000 people on the 2020 level (HC3 robust errors)."""
    df = units.copy()
    X = sm.add_constant(df[["density_2020", "pop_growth_pct_pa"]])
    fit = sm.OLS(df["density_change"], X).fit(cov_type="HC3")
    median_2020 = df["density_2020"].median()
    low = df[df["density_2020"] < median_2020]
    new_total = df["banks_change"].sum()
    return {
        "slope_initial_density": float(fit.params["density_2020"]),
        "slope_ci": [float(v) for v in fit.conf_int().loc["density_2020"]],
        "p_value": float(fit.pvalues["density_2020"]),
        "slope_population_growth": float(fit.params["pop_growth_pct_pa"]),
        "r_squared": float(fit.rsquared),
        "median_density_2020": float(median_2020),
        "net_new_banks": int(new_total),
        "low_density_units": int(len(low)),
        "low_density_share_of_new": float(low["banks_change"].sum() / new_total) if new_total else float("nan"),
        "low_density_share_of_population": float(low["pop"].sum() / df["pop"].sum()),
        "units_losing_branches": int((df["banks_change"] < 0).sum()),
        "interpretation": "A negative slope means districts that started with fewer branches per person gained more "
                          "per person (convergence)." }


# ---------------------------------------------------------------------------
# 5. Cross-country benchmark
# ---------------------------------------------------------------------------
def cross_country(cs: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Account ownership against income across economies, with Pakistan's shortfall and ranks."""
    df = cs.dropna(subset=["account", "log_gdp_pc"]).copy()
    X = sm.add_constant(df["log_gdp_pc"])
    fit = sm.OLS(df["account"], X).fit(cov_type="HC3")
    pred = fit.get_prediction(sm.add_constant(df["log_gdp_pc"])).summary_frame(alpha=0.10)
    df["expected_account"] = pred["mean"].to_numpy()
    df["account_residual"] = df["account"] - df["expected_account"]
    df["pred_low"] = pred["obs_ci_lower"].to_numpy()
    df["pred_high"] = pred["obs_ci_upper"].to_numpy()

    gap = df.dropna(subset=["account_gap"]).copy()
    phone = df.dropna(subset=["phone_gap"]).copy()
    pak = df[df["country"] == "PAK"].iloc[0]

    def rank(frame: pd.DataFrame, column: str, ascending: bool) -> tuple[int, int]:
        ordered = frame.sort_values(column, ascending=ascending)["country"].tolist()
        return ordered.index("PAK") + 1, len(ordered)

    south_asia = df[df["country"].isin(config.SOUTH_ASIA)][
        ["country", "name", "account", "account_women", "account_men", "account_gap", "phone_women", "phone_men",
         "phone_gap", "expected_account", "account_residual"]].sort_values("account", ascending=False)
    summary = {
        "year": config.FINDEX_YEAR, "n_economies": int(len(df)),
        "slope_per_log_point": float(fit.params["log_gdp_pc"]), "r_squared": float(fit.rsquared),
        "pakistan": {
            "account": float(pak["account"]), "expected": float(pak["expected_account"]),
            "shortfall_pts": float(pak["expected_account"] - pak["account"]),
            "prediction_interval_90": [float(pak["pred_low"]), float(pak["pred_high"])],
            "gdp_pc_ppp": float(pak["gdp_pc_ppp"]),
            "account_women": float(pak["account_women"]), "account_men": float(pak["account_men"]),
            "account_gap": float(pak["account_gap"]),
            "phone_women": float(pak["phone_women"]), "phone_men": float(pak["phone_men"]),
            "phone_gap": float(pak["phone_gap"]),
        },
        "rank_lowest_account": rank(df, "account", True),
        "rank_largest_account_gap": rank(gap, "account_gap", False),
        "rank_largest_phone_gap": rank(phone, "phone_gap", False),
        "rank_largest_shortfall": rank(df, "account_residual", True),
        "largest_account_gaps": gap.nlargest(5, "account_gap")[["name", "account_gap"]].to_dict(orient="records"),
        "largest_phone_gaps": phone.nlargest(5, "phone_gap")[["name", "phone_gap"]].to_dict(orient="records"),
        "south_asia": south_asia.round(2).to_dict(orient="records"),
    }
    return df, summary


# ---------------------------------------------------------------------------
# 6. Planner: where would new access points go?
# ---------------------------------------------------------------------------
STRATEGIES = {
    "equity": "Even out people per branch",
    "gap": "Close the peer-adjusted model gap first",
    "women": "Even out people per branch, weighted to districts where women are furthest behind",
}


def allocate(units: pd.DataFrame, k: int, strategy: str) -> pd.Series:
    """Give k new access points to districts, one at a time, under one of three rules.

    equity  next point goes to the district with the most people per (branch + 1)
    gap     next point goes to the district with the largest remaining shortfall against the model
    women   as 'equity', with each district's need multiplied by its literacy gap between men and women
            (relative to the average gap), so districts where women are furthest behind come first
    The gap rule places no point where the shortfall is already filled, so fewer than k may be placed.
    Returns the number added to each district, indexed like units.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy {strategy!r}")
    base = units["branches_2024"].to_numpy(float)
    pop = units["pop"].to_numpy(float)
    expected = units["expected_branches"].to_numpy(float)
    gap = units["literacy_gender_gap"].clip(lower=0).to_numpy(float)
    weight = gap / gap.mean() if gap.mean() > 0 else np.ones(len(units))
    added = np.zeros(len(units), dtype=int)

    def priority(i: int) -> float:
        if strategy == "gap":
            remaining = expected[i] - (base[i] + added[i])
            return remaining if remaining > 0 else -np.inf
        need = pop[i] / (base[i] + added[i] + 1)
        return need * weight[i] if strategy == "women" else need

    heap = [(-priority(i), i) for i in range(len(units))]
    heapq.heapify(heap)
    placed = 0
    while placed < k and heap:
        neg, i = heapq.heappop(heap)
        if neg == np.inf:      # the best remaining priority is -inf: nothing is left to fill
            break
        added[i] += 1
        placed += 1
        heapq.heappush(heap, (-priority(i), i))
    return pd.Series(added, index=units.index, name="added")


@dataclass
class Outcome:
    national_density: float
    units_below_half: int
    population_below_half: float
    gini: float
    worst_people_per_branch: float
    placed: int
    share_to_low_female_literacy: float

    def as_dict(self) -> dict:
        return self.__dict__.copy()


def outcomes(units: pd.DataFrame, added: pd.Series | None = None) -> Outcome:
    """Headline measures for the network, before (added=None) or after adding points."""
    extra = added if added is not None else pd.Series(0, index=units.index)
    total = units["branches_2024"] + extra
    density = total / units["pop"] * 1e5
    national = total.sum() / units["pop"].sum() * 1e5
    below = density < config.LOW_DENSITY_SHARE_OF_AVERAGE * national
    _, _, gini = lorenz(units["pop"].to_numpy(float), total.to_numpy(float))
    per_branch = (units["pop"] / total.replace(0, np.nan)).max()
    low_female = units["literacy_female"] < config.LOW_FEMALE_LITERACY
    placed = int(extra.sum())
    share = float(extra[low_female].sum() / placed) if placed else float("nan")
    return Outcome(float(national), int(below.sum()), float(units.loc[below, "pop"].sum() / units["pop"].sum()),
                   gini, float(per_branch), placed, share)


def scenario_table(units: pd.DataFrame, k: int) -> list[dict]:
    """Outcomes before and after k new points under each rule."""
    rows = [{"strategy": "before", "label": "Today", **outcomes(units).as_dict()}]
    for name, label in STRATEGIES.items():
        rows.append({"strategy": name, "label": label, **outcomes(units, allocate(units, k, name)).as_dict()})
    return rows
