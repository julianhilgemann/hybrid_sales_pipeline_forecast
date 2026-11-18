#!/usr/bin/env python3
"""Build the data bundle that every animation clip reads.

Runs the real forecast pipeline in the README-chart configuration
(as-of 2025-05-01, 15 business-day horizon, max age 45) into a temporary
directory and distils everything the animation needs into
``animation/data/model_data.json``.

Run with the *project* interpreter (needs duckdb / pandas), from anywhere:

    .venv/bin/python animation/build_data.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO))

from pipeline_lib import Config, run_pipeline  # noqa: E402
from pipeline_lib.overview.transforms import (  # noqa: E402
    build_arrivals_surface,
    smooth_matrix,
    smooth_series,
)

AS_OF = "2025-05-01"
HORIZON = 15
MAX_AGE = 45
TRAINING_WINDOW = 60
SMOOTHING_ALPHA = 0.25  # additive smoothing used in estimate_kernel_from_training
N_SIMS = 400
MC_SEED = 7


def r(arr, nd: int = 6):
    """Round an array-like to a JSON-friendly nested list."""
    return np.round(np.asarray(arr, dtype=float), nd).tolist()


def simulate_system(N, k, loss, S, arrivals, rng, detail: bool = False):
    """One forward realisation of the stochastic system the model takes the mean of.

    Stock: an opp of age ``a`` wins on forecast day ``d`` (1..H) w.p. k(a+d)/S(a),
    is lost w.p. loss(a+d)/S(a), otherwise stays open through the horizon.
    Arrivals: Poisson(A_hat(t)) opps arrive on day ``t``; each wins at age ``j``
    w.p. k(j) (on day t+j), is lost w.p. loss(j), otherwise stays open.
    """
    H = len(arrivals)
    wins_stock = np.zeros(H)
    wins_arr = np.zeros(H)
    particles = []

    for a in range(len(N)):
        n = int(N[a])
        if n == 0 or S[a] <= 1e-12:
            continue
        idx = [a + d for d in range(1, H + 1) if a + d <= MAX_AGE]
        pw = np.array([k[i] for i in idx]) / S[a]
        pl = np.array([loss[i] for i in idx]) / S[a]
        probs = np.concatenate([pw, pl, [max(0.0, 1.0 - pw.sum() - pl.sum())]])
        probs = probs / probs.sum()
        draws = rng.choice(len(probs), size=n, p=probs)
        for dr in draws:
            if dr < len(idx):
                d = int(dr) + 1
                wins_stock[d - 1] += 1
                outcome, day = "won", d
            elif dr < 2 * len(idx):
                outcome, day = "lost", int(dr) - len(idx) + 1
            else:
                outcome, day = "open", None
            if detail:
                particles.append({"kind": "stock", "age0": a, "t": 0, "outcome": outcome, "day": day})

    for t in range(1, H + 1):
        n = int(rng.poisson(arrivals[t - 1]))
        ages = list(range(0, H - t + 1))
        pw = np.array([k[j] for j in ages])
        pl = np.array([loss[j] for j in ages])
        probs = np.concatenate([pw, pl, [max(0.0, 1.0 - pw.sum() - pl.sum())]])
        probs = probs / probs.sum()
        draws = rng.choice(len(probs), size=n, p=probs) if n else []
        for dr in draws:
            if dr < len(ages):
                d = t + int(dr)
                wins_arr[d - 1] += 1
                outcome, day = "won", d
            elif dr < 2 * len(ages):
                outcome, day = "lost", t + int(dr) - len(ages)
            else:
                outcome, day = "open", None
            if detail:
                particles.append({"kind": "arrival", "age0": 0, "t": t, "outcome": outcome, "day": day})

    return wins_stock, wins_arr, particles


def cohort_of_100(k, loss, rng):
    """A cohort of 100 brand-new opportunities that follows the real hazards on
    average: cumulative wins/losses by age are rounded expected counts, so the
    piles end at round(100*P(win)), round(100*P(loss)), and the rest stays open.
    Dots are assigned to events in a shuffled order so the grid looks random."""
    won_cum = np.round(100 * np.cumsum(k)).astype(int)
    lost_cum = np.round(100 * np.cumsum(loss)).astype(int)
    won_at = np.diff(np.concatenate([[0], won_cum]))
    lost_at = np.diff(np.concatenate([[0], lost_cum]))
    open_at = 100 - np.concatenate([[0], np.cumsum(won_at + lost_at)[:-1]])  # open at start of age a
    order = rng.permutation(100)
    dots = [{"slot": int(s), "outcome": "open", "age": None} for s in range(100)]
    pos = 0
    for a in range(len(k)):
        for _ in range(int(won_at[a])):
            dots[int(order[pos])].update(outcome="won", age=a)
            pos += 1
        for _ in range(int(lost_at[a])):
            dots[int(order[pos])].update(outcome="lost", age=a)
            pos += 1
    return won_at, lost_at, open_at, dots


def training_sample(lifelines, n_won=12, n_lost=14, n_open=10, seed=3):
    """Real lifelines created inside the training window, as known on the as-of
    date: an event at age ttc if it closed by then, otherwise open (censored) at
    its current age. A stratified sample, sorted by creation day."""
    rng = np.random.default_rng(seed)
    rows = []
    for row in lifelines:
        c = row["created_rel"]
        if not (-TRAINING_WINDOW + 1 <= c <= 0):
            continue
        if row["closed_rel"] is not None and row["closed_rel"] <= 0 and row["outcome"] in ("won", "lost"):
            rows.append({"created_rel": c, "end_age": int(row["ttc"]), "status": row["outcome"]})
        else:
            rows.append({"created_rel": c, "end_age": int(-c), "status": "open"})
    pick = []
    for status, n in (("won", n_won), ("lost", n_lost), ("open", n_open)):
        pool = [r for r in rows if r["status"] == status and r["end_age"] <= MAX_AGE]
        idx = rng.choice(len(pool), size=n, replace=False)
        pick += [pool[i] for i in idx]
    pick.sort(key=lambda r: (r["created_rel"], r["end_age"]))
    counts = {s: sum(1 for r in rows if r["status"] == s) for s in ("won", "lost", "open")}
    return pick, counts


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="pipeline_anim_") as tmp:
        cfg = Config(
            training_window_bdays=TRAINING_WINDOW,
            horizon_bdays=HORIZON,
            max_age_bdays=MAX_AGE,
            output_dir=tmp,
        )
        run = run_pipeline(cfg, as_of_date=AS_OF)
        res = run["result"]
        as_of_idx = int(res["as_of_idx"])

        kernel = res["kernel"]
        pred = res["pred_by_day"].sort_values("day_offset")
        arrivals_fc = res["arrivals_fc"].sort_values("day_offset")
        stock_surface = np.asarray(res["stock_surface"], dtype=float)  # (MAX_AGE+1, H)

        con = duckdb.connect(str(run["db_path"]), read_only=True)
        try:
            lifelines = con.execute(
                """
                SELECT o.opp_id,
                       o.created_biz_day_index - ? AS created_rel,
                       e.outcome,
                       e.time_to_close_biz_days AS ttc,
                       e.closed_biz_day_index - ? AS closed_rel
                FROM fct_opportunity o
                JOIN fct_opportunity_event e USING (opp_id)
                WHERE o.created_biz_day_index BETWEEN ? AND ?
                ORDER BY o.created_biz_day_index, o.opp_id
                """,
                [as_of_idx, as_of_idx, as_of_idx - TRAINING_WINDOW + 1, as_of_idx + HORIZON],
            ).df()
            hist = con.execute(
                """
                WITH arr AS (
                    SELECT created_date AS date, COUNT(*) AS arrivals
                    FROM fct_opportunity GROUP BY created_date
                )
                SELECT c.date, c.dow, c.is_business_day, c.is_holiday,
                       c.biz_day_index - ? AS rel, COALESCE(a.arrivals, 0) AS arrivals
                FROM dim_calendar c LEFT JOIN arr a ON c.date = a.date
                WHERE c.date <= CAST(? AS DATE)
                ORDER BY c.date
                """,
                [as_of_idx, AS_OF],
            ).df()
        finally:
            con.close()

    # ---- kernel -----------------------------------------------------------
    k = kernel["win_kernel_mass"].to_numpy(dtype=float)
    loss = kernel["loss_kernel_mass"].to_numpy(dtype=float)
    S = kernel["survival_to_age"].to_numpy(dtype=float)
    k_smooth = smooth_series(k, window=11, sigma=2.2)
    k_smooth = k_smooth * (k.sum() / k_smooth.sum())

    # ---- stock ------------------------------------------------------------
    N = np.zeros(MAX_AGE + 1)
    for row in res["active_age"].itertuples(index=False):
        if 0 <= int(row.age_biz_days) <= MAX_AGE:
            N[int(row.age_biz_days)] = float(row.active_count)

    # ---- arrivals ---------------------------------------------------------
    A = arrivals_fc["forecast_arrivals"].to_numpy(dtype=float)[:HORIZON]
    arr_surface = build_arrivals_surface(arrivals_fc, kernel, HORIZON)  # (H, H) [t-1, d-1]
    recent = hist.tail(180)
    biz_recent = recent[recent["is_business_day"]]
    dow_means = biz_recent.groupby("dow")["arrivals"].mean()
    hist_biz = hist[hist["is_business_day"]].tail(60)

    # ---- forecast ---------------------------------------------------------
    w_stock = pred["expected_wins_stock"].to_numpy(dtype=float)
    w_arr = pred["expected_wins_arrivals"].to_numpy(dtype=float)
    w_total = w_stock + w_arr
    assert np.allclose(stock_surface.sum(axis=0), w_stock)
    assert np.allclose(arr_surface.sum(axis=0), w_arr)

    # ---- the stochastic system (Monte Carlo of what the model averages) ----
    rng = np.random.default_rng(MC_SEED)
    sims_stock, sims_arr = [], []
    for _ in range(N_SIMS):
        ws, wa, _p = simulate_system(N, k, loss, S, A, rng)
        sims_stock.append(ws)
        sims_arr.append(wa)
    sims_stock = np.array(sims_stock)
    sims_arr = np.array(sims_arr)
    sims_total = sims_stock + sims_arr
    _ws, _wa, particles = simulate_system(N, k, loss, S, A, np.random.default_rng(MC_SEED + 1), detail=True)

    lifelines["ttc"] = lifelines["ttc"].astype("Int64")
    lifelines["closed_rel"] = lifelines["closed_rel"].astype("Int64")
    life_rows = [
        {
            "created_rel": int(row.created_rel),
            "outcome": str(row.outcome),
            "ttc": None if pd.isna(row.ttc) else int(row.ttc),
            "closed_rel": None if pd.isna(row.closed_rel) else int(row.closed_rel),
        }
        for row in lifelines.itertuples(index=False)
    ]


    # ---- didactic extras: a cohort of 100, a conditional example, training lifelines
    won_at, lost_at, open_at, dots = cohort_of_100(k, loss, np.random.default_rng(11))
    assert won_at.sum() == round(100 * k.sum()) and lost_at.sum() == round(100 * loss.sum())
    assert np.all(np.abs(open_at - 100 * S) <= 1.5), "cohort drifts from S(a)"
    A0 = 8
    cond = np.array([k[A0 + d] / S[A0] for d in range(1, HORIZON + 1)])
    assert np.allclose(N[A0] * cond, stock_surface[A0]), "conditional row != stock surface row"
    cond_matrix = np.zeros((MAX_AGE + 1, HORIZON))
    for a in range(MAX_AGE + 1):
        for d in range(1, HORIZON + 1):
            if a + d <= MAX_AGE and S[a] > 1e-12:
                cond_matrix[a, d - 1] = k[a + d] / S[a]
    assert np.allclose(N[:, None] * cond_matrix, stock_surface)
    sample, window_counts = training_sample(life_rows)

    bundle = {
        "meta": {
            "as_of_date": AS_OF,
            "horizon": HORIZON,
            "max_age": MAX_AGE,
            "training_window": TRAINING_WINDOW,
            "smoothing_alpha": SMOOTHING_ALPHA,
            "note": (
                "d and t are 1-indexed forecast business days (1 = first day after as-of). "
                "Age index 45 pools every opportunity aged 45+; the model projects no wins from it."
            ),
        },
        "kernel": {
            "age": list(range(MAX_AGE + 1)),
            "at_risk": r(kernel["at_risk_count"], 1),
            "wins": r(kernel["wins_at_age"], 1),
            "losses": r(kernel["losses_at_age"], 1),
            "win_hazard": r(kernel["win_hazard"]),
            "loss_hazard": r(kernel["loss_hazard"]),
            "survival": r(S),
            "win_mass": r(k),
            "loss_mass": r(loss),
            "win_mass_smooth": r(k_smooth),
            "p_win_total": round(float(k.sum()), 6),
            "p_loss_total": round(float(loss.sum()), 6),
        },
        "stock": {
            "N": r(N, 1),
            "total_active": float(N.sum()),
            "surface": r(stock_surface),
            "surface_smooth": r(smooth_matrix(stock_surface, passes=1)),
            "by_day": r(w_stock),
            "by_age": r(stock_surface.sum(axis=1)),
        },
        "arrivals": {
            "forecast": r(A, 4),
            "forecast_dow": [int(v) for v in arrivals_fc["dow"]] if "dow" in arrivals_fc else None,
            "forecast_dates": [str(v) for v in arrivals_fc["date"]][:HORIZON],
            "dow_means": {str(int(d)): round(float(v), 4) for d, v in dow_means.items()},
            "history": [
                {"rel": int(row.rel), "date": str(row.date), "dow": int(row.dow), "arrivals": int(row.arrivals)}
                for row in hist_biz.itertuples(index=False)
            ],
            "surface": r(arr_surface),
            "surface_smooth": r(smooth_matrix(arr_surface, passes=1)),
            "by_day": r(w_arr),
            "by_origin": r(arr_surface.sum(axis=1)),
        },
        "forecast": {
            "day": list(range(1, HORIZON + 1)),
            "stock": r(w_stock),
            "arrivals": r(w_arr),
            "total": r(w_total),
            "total_smooth": r(smooth_series(w_total, window=7, sigma=1.6)),
            "actual": r(pred["actual_wins"], 1),
        },
        "monte_carlo": {
            "n_sims": N_SIMS,
            "stock": sims_stock.astype(int).tolist(),
            "arrivals": sims_arr.astype(int).tolist(),
            "total": sims_total.astype(int).tolist(),
            "mean_total": r(sims_total.mean(axis=0), 4),
            "q05_total": r(np.quantile(sims_total, 0.05, axis=0), 2),
            "q25_total": r(np.quantile(sims_total, 0.25, axis=0), 2),
            "q75_total": r(np.quantile(sims_total, 0.75, axis=0), 2),
            "q95_total": r(np.quantile(sims_total, 0.95, axis=0), 2),
            "particles": particles,
        },
        "cohort": {
            "size": 100,
            "won_at_age": won_at.astype(int).tolist(),
            "lost_at_age": lost_at.astype(int).tolist(),
            "open_at_age": open_at.astype(int).tolist(),
            "won_total": int(won_at.sum()),
            "lost_total": int(lost_at.sum()),
            "open_end": int(100 - won_at.sum() - lost_at.sum()),
            "dots": dots,
        },
        "conditional": {
            "a0": A0,
            "N_a0": float(N[A0]),
            "S_a0": round(float(S[A0]), 6),
            "cond_prob": r(cond),
            "cond_total": round(float(cond.sum()), 6),
            "row": r(stock_surface[A0]),
            "row_total": round(float(stock_surface[A0].sum()), 6),
            "matrix": r(cond_matrix),
        },
        "training": {
            "window_start_rel": -TRAINING_WINDOW + 1,
            "window_end_rel": 0,
            "sample": sample,
            "window_counts": window_counts,
        },
        "lifelines": life_rows,
    }
    if bundle["arrivals"]["forecast_dow"] is None:
        bundle["arrivals"]["forecast_dow"] = [
            int(pd.Timestamp(d).dayofweek) for d in bundle["arrivals"]["forecast_dates"]
        ]

    out = HERE / "data" / "model_data.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} kB)")
    print(f"  P(win)={k.sum():.3f}  P(loss)={loss.sum():.3f}  active stock={N.sum():.0f}")
    print(f"  expected wins over horizon: stock={w_stock.sum():.2f} arrivals={w_arr.sum():.2f}")
    print(f"  MC mean total / model total: {sims_total.mean(axis=0).sum():.2f} / {w_total.sum():.2f}")
    print(f"  lifelines={len(life_rows)}  particles={len(particles)}")
    print(f"  cohort: won={won_at.sum()} lost={lost_at.sum()} open={100 - won_at.sum() - lost_at.sum()}; open at age {A0}: {open_at[A0]}")
    print(f"  conditional a0={A0}: N={N[A0]:.0f} S={S[A0]:.3f} sum p={cond.sum():.3f} expected wins={stock_surface[A0].sum():.2f}")
    print(f"  training window counts {window_counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
