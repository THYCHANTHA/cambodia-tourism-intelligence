"""Descriptive analytics. All functions are pure."""

from __future__ import annotations

import pandas as pd


def add_growth(monthly: pd.DataFrame, value: str = "arrivals", window: int = 12) -> pd.DataFrame:
    """Add mom_pct, yoy_pct and a trailing rolling mean. Growth uses the calendar month 12
    months earlier, so a gap gives NaN rather than a wrong comparison."""
    df = monthly.sort_values("period_month").copy()
    s = df.set_index("period_month")[value]
    full = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="MS"))
    mom = full.pct_change(1, fill_method=None) * 100
    yoy = full.pct_change(12, fill_method=None) * 100
    roll = full.rolling(window, min_periods=window).mean()
    df["mom_pct"] = df["period_month"].map(mom)
    df["yoy_pct"] = df["period_month"].map(yoy)
    df[f"rolling_{window}m"] = df["period_month"].map(roll)
    return df


def annual_totals(monthly: pd.DataFrame, value: str = "arrivals") -> pd.DataFrame:
    """Annual sums with n_months and is_complete so partial years are never mistaken for full."""
    d = monthly.assign(year=pd.to_datetime(monthly["period_month"]).dt.year)
    g = d.groupby("year").agg(total=(value, "sum"), n_months=("period_month", "nunique"))
    g["is_complete"] = g["n_months"].eq(12)
    g["yoy_pct"] = None
    prev = g["total"].shift(1)
    comparable = g["is_complete"] & g["is_complete"].shift(1, fill_value=False)
    g.loc[comparable, "yoy_pct"] = (g["total"] / prev - 1) * 100
    g["yoy_pct"] = g["yoy_pct"].astype(float)
    return g.reset_index()


def seasonal_index(monthly: pd.DataFrame, years: list[int], value: str = "arrivals") -> pd.Series:
    """Mean of month value / that year's monthly mean, over the chosen complete years.
    Raises if a chosen year is incomplete."""
    d = monthly.assign(y=monthly["period_month"].dt.year, m=monthly["period_month"].dt.month)
    d = d[d["y"].isin(years)]
    counts = d.groupby("y")["m"].nunique()
    bad = [y for y in years if counts.get(y, 0) != 12]
    if bad:
        raise ValueError(f"incomplete years: {bad}")
    d["rel"] = d[value] / d.groupby("y")[value].transform("mean")
    return d.groupby("m")["rel"].mean()


def market_share(df: pd.DataFrame, key: str, value: str) -> pd.DataFrame:
    """Share (%) of each key in the sum of df. Caller must pass one level only
    (countries OR regions, no totals)."""
    out = df.groupby(key, as_index=False)[value].sum()
    total = out[value].sum()
    out["share_pct"] = out[value] / total * 100 if total else float("nan")
    return out.sort_values(value, ascending=False).reset_index(drop=True)


def hhi(shares_pct) -> float:
    """Herfindahl-Hirschman index on 0-10000 scale from shares in percent."""
    s = pd.Series(shares_pct, dtype=float)
    if (s < 0).any():
        raise ValueError("negative share")
    if abs(s.sum() - 100) > 0.5:
        raise ValueError(f"shares sum to {s.sum():.2f}, expected 100")
    return float((s**2).sum())


def split_levels(df: pd.DataFrame, label_col: str, region_labels: list[str],
                 total_labels: list[str]) -> pd.DataFrame:
    """Tag rows as country, region or total so overlapping levels are never summed together.
    Matching is case-insensitive on stripped labels. Anything not listed as region or total
    is called country, so the label lists must be reviewed against real files."""
    reg = {x.strip().lower() for x in region_labels}
    tot = {x.strip().lower() for x in total_labels}
    lab = df[label_col].astype(str).str.strip().str.lower()
    level = pd.Series("country", index=df.index)
    level[lab.isin(reg)] = "region"
    level[lab.isin(tot)] = "total"
    return df.assign(level=level)
