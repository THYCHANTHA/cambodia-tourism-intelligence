import pandas as pd
import pytest

from tourism_intel.analytics import (
    add_growth,
    annual_totals,
    hhi,
    market_share,
    seasonal_index,
    split_levels,
)


def test_yoy_matches_manual_and_gap_gives_nan(monthly):
    g = add_growth(monthly)
    row = g.iloc[12]
    assert row.yoy_pct == pytest.approx((monthly.arrivals[12] / monthly.arrivals[0] - 1) * 100)
    assert g.iloc[:12].yoy_pct.isna().all()
    gap = add_growth(monthly.drop(index=0))  # Jan 2022 missing -> Jan 2023 has no base
    assert pd.isna(gap[gap.period_month == "2023-01-01"].yoy_pct.iloc[0])


def test_annual_totals_flags_partial_and_skips_yoy(monthly):
    a = annual_totals(monthly.iloc[:50])
    assert a.set_index("year").loc[2026, "is_complete"] is False or not a.iloc[-1].is_complete
    assert a.iloc[-1].n_months == 2 and pd.isna(a.iloc[-1].yoy_pct)
    assert a.iloc[1].total == monthly.arrivals[12:24].sum()
    assert a.iloc[1].yoy_pct == pytest.approx((a.iloc[1].total / a.iloc[0].total - 1) * 100)


def test_seasonal_index_requires_complete_years(monthly):
    si = seasonal_index(monthly, [2022, 2023])
    assert len(si) == 12
    with pytest.raises(ValueError):
        seasonal_index(monthly.iloc[:50], [2022, 2026])


def test_market_share_and_hhi():
    df = pd.DataFrame({"c": ["A", "B", "A", "C"], "v": [50, 30, 10, 10]})
    ms = market_share(df, "c", "v")
    assert ms.share_pct.sum() == pytest.approx(100)
    assert ms.iloc[0].c == "A" and ms.iloc[0].share_pct == pytest.approx(60)
    assert hhi(ms.share_pct) == pytest.approx(60**2 + 30**2 + 10**2)
    assert hhi([100]) == 10_000
    with pytest.raises(ValueError):
        hhi([50, 20])
    with pytest.raises(ValueError):
        hhi([120, -20])


def test_split_levels_keeps_levels_apart():
    df = pd.DataFrame({"r": ["China", " asean ", "Total", "Laos"], "v": [1, 2, 3, 4]})
    out = split_levels(df, "r", ["ASEAN"], ["Total"])
    assert out.level.tolist() == ["country", "region", "total", "country"]
    assert out[out.level == "country"].v.sum() == 5  # regions and totals excluded
