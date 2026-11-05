"""Data quality checks. Each returns findings; nothing is silently repaired."""

from __future__ import annotations

import pandas as pd


def missing_months(months: pd.Series) -> list[pd.Timestamp]:
    """Months absent between the first and last observed month."""
    m = pd.DatetimeIndex(pd.to_datetime(months)).unique().sort_values()
    if len(m) == 0:
        return []
    full = pd.date_range(m.min(), m.max(), freq="MS")
    return list(full.difference(m))


def duplicate_keys(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return df[df.duplicated(keys, keep=False)].sort_values(keys)


def negative_values(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df[df[col] < 0]


def reconcile(detail_sum: pd.Series, reported_total: pd.Series, tol_abs: float = 0,
              tol_rel: float = 0.0) -> pd.DataFrame:
    """Compare summed detail rows with a reported total, per key. Indexes are the keys.
    A key present on one side only is reported as a failure, not dropped."""
    out = pd.concat({"detail_sum": detail_sum, "reported_total": reported_total}, axis=1)
    out["diff"] = out["detail_sum"] - out["reported_total"]
    allowed = (out["reported_total"].abs() * tol_rel).fillna(0).clip(lower=tol_abs)
    out["ok"] = out["diff"].abs().le(allowed) & out["diff"].notna()
    return out


def complete_years(monthly: pd.DataFrame, date_col: str = "period_month") -> pd.Series:
    """Year -> True if all 12 distinct months are present."""
    d = pd.to_datetime(monthly[date_col])
    return d.groupby(d.dt.year).nunique().eq(12)
