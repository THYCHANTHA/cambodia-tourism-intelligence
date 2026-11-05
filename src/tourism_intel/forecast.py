"""Forecasting with chronological, expanding-window backtests. No random splits."""

from __future__ import annotations

import warnings
from collections.abc import Callable

import numpy as np
import pandas as pd

Model = Callable[[pd.Series, int], np.ndarray]


def mae(y, f) -> float:
    return float(np.mean(np.abs(np.asarray(y, float) - np.asarray(f, float))))


def rmse(y, f) -> float:
    return float(np.sqrt(np.mean((np.asarray(y, float) - np.asarray(f, float)) ** 2)))


def smape(y, f) -> float:
    """Symmetric MAPE in percent. Points where both actual and forecast are 0 are skipped."""
    y, f = np.asarray(y, float), np.asarray(f, float)
    denom = (np.abs(y) + np.abs(f)) / 2
    ok = denom > 0
    return float(np.mean(np.abs(y - f)[ok] / denom[ok]) * 100) if ok.any() else float("nan")


def naive(train: pd.Series, h: int) -> np.ndarray:
    return np.repeat(train.iloc[-1], h).astype(float)


def seasonal_naive(train: pd.Series, h: int, m: int = 12) -> np.ndarray:
    if len(train) < m:
        raise ValueError("need at least one full season")
    last = train.iloc[-m:].to_numpy(float)
    return np.array([last[i % m] for i in range(h)])


def ets(train: pd.Series, h: int) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = ExponentialSmoothing(train.to_numpy(float), trend="add", damped_trend=True,
                                   seasonal="add", seasonal_periods=12).fit()
    return np.asarray(fit.forecast(h))


def sarima(train: pd.Series, h: int) -> np.ndarray:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = SARIMAX(train.to_numpy(float), order=(1, 1, 1), seasonal_order=(0, 1, 1, 12),
                      enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    return np.asarray(fit.forecast(h))


MODELS: dict[str, Model] = {"naive": naive, "seasonal_naive": seasonal_naive,
                            "ets": ets, "sarima": sarima}
MIN_TRAIN = {"naive": 1, "seasonal_naive": 12, "ets": 24, "sarima": 36}


def expanding_splits(n: int, min_train: int, horizon: int, step: int = 1):
    """Yield (train_end_exclusive, test_end_exclusive). Train always precedes test."""
    if min_train < 1 or horizon < 1 or step < 1:
        raise ValueError("min_train, horizon and step must be >= 1")
    end = min_train
    while end + horizon <= n:
        yield end, end + horizon
        end += step


def regime_series(s: pd.Series, start: str | None = None, end: str | None = None,
                  exclude: tuple[str, str] | None = None) -> pd.Series:
    """Slice a monthly series to a regime. `exclude` removes a window (e.g. COVID); the
    result must stay contiguous, so exclude is only allowed at the edges of the slice."""
    out = s
    if start:
        out = out[out.index >= pd.Timestamp(start)]
    if end:
        out = out[out.index <= pd.Timestamp(end)]
    if exclude:
        lo, hi = map(pd.Timestamp, exclude)
        inside = (out.index >= lo) & (out.index <= hi)
        kept = out[~inside]
        if inside.any() and (kept.index.min() < lo) and (kept.index.max() > hi):
            raise ValueError("excluding an interior window would break the series")
        out = kept
    return out


def assess_feasibility(s: pd.Series, min_months: int = 48) -> dict:
    """Is a seasonal backtest defensible? Needs a gap-free monthly series in the regime."""
    s = s.dropna()
    n = len(s)
    gap_free = n > 0 and len(pd.date_range(s.index.min(), s.index.max(), freq="MS")) == n
    ok = gap_free and n >= min_months
    reason = ("ok" if ok else
              "series has gaps" if not gap_free else
              f"only {n} months in regime, need {min_months}")
    return {"n_months": n, "gap_free": bool(gap_free), "feasible": bool(ok), "reason": reason}


def backtest(s: pd.Series, horizon: int = 6, step: int = 3, min_train: int = 36,
             models: list[str] | None = None) -> pd.DataFrame:
    """Expanding-window backtest. Returns one row per (model, origin, step_ahead)."""
    if not s.index.is_monotonic_increasing:
        raise ValueError("series must be sorted chronologically")
    rows = []
    for name in models or list(MODELS):
        need = max(min_train, MIN_TRAIN[name])
        for tr_end, te_end in expanding_splits(len(s), need, horizon, step):
            train, test = s.iloc[:tr_end], s.iloc[tr_end:te_end]
            try:
                fc = MODELS[name](train, horizon)
            except Exception as exc:  # model failed to fit: record, do not hide
                rows.append({"model": name, "origin": train.index[-1], "error": str(exc)})
                continue
            for i, (d, y) in enumerate(test.items(), 1):
                rows.append({"model": name, "origin": train.index[-1], "target": d, "h": i,
                             "actual": float(y), "forecast": float(fc[i - 1])})
    return pd.DataFrame(rows)


def summarise(bt: pd.DataFrame) -> pd.DataFrame:
    ok = bt.dropna(subset=["actual"]) if "actual" in bt else bt.iloc[0:0]
    if ok.empty:
        return pd.DataFrame(columns=["model", "n_origins", "mae", "rmse", "smape_pct"])
    g = ok.groupby("model")
    out = g.apply(lambda d: pd.Series({
        "n_origins": d["origin"].nunique(), "mae": mae(d.actual, d.forecast),
        "rmse": rmse(d.actual, d.forecast), "smape_pct": smape(d.actual, d.forecast)}),
        include_groups=False)
    return out.sort_values("mae").reset_index()
