import numpy as np
import pandas as pd
import pytest

from tourism_intel import forecast as f


def test_metrics():
    assert f.mae([1, 2], [2, 4]) == 1.5
    assert f.rmse([0, 0], [3, 4]) == pytest.approx(np.sqrt(12.5))
    assert f.smape([100], [100]) == 0
    assert f.smape([0], [0]) != f.smape([0], [0])  # nan, not a crash
    assert f.smape([100], [50]) == pytest.approx(66.667, rel=1e-3)


def test_baselines(monthly):
    s = monthly.set_index("period_month").arrivals
    assert (f.naive(s, 3) == s.iloc[-1]).all()
    sn = f.seasonal_naive(s, 14)
    assert sn[0] == s.iloc[-12] and sn[12] == s.iloc[-12]
    with pytest.raises(ValueError):
        f.seasonal_naive(s.iloc[:5], 3)


def test_splits_are_chronological_and_never_leak():
    sp = list(f.expanding_splits(20, min_train=10, horizon=3, step=2))
    assert sp[0] == (10, 13)
    assert all(tr < te <= 20 for tr, te in sp)
    assert sp[-1][1] <= 20
    assert list(f.expanding_splits(10, 10, 3)) == []
    with pytest.raises(ValueError):
        list(f.expanding_splits(10, 0, 3))


def test_backtest_uses_only_past_data(monthly):
    s = monthly.set_index("period_month").arrivals
    bt = f.backtest(s, horizon=3, step=6, min_train=24, models=["naive", "seasonal_naive"])
    assert (bt.target > bt.origin).all()
    # naive forecast at each origin equals the last training value, i.e. the value AT origin
    n = bt[bt.model == "naive"]
    assert (n.forecast.values == s.loc[n.origin].values).all()
    summ = f.summarise(bt)
    assert set(summ.model) == {"naive", "seasonal_naive"}
    # clean seasonal data with mild trend: seasonal naive should beat naive
    assert summ.iloc[0].model == "seasonal_naive"


def test_backtest_rejects_unsorted(monthly):
    s = monthly.set_index("period_month").arrivals.iloc[::-1]
    with pytest.raises(ValueError):
        f.backtest(s)


def test_ets_and_sarima_run(monthly):
    s = monthly.set_index("period_month").arrivals
    for m in (f.ets, f.sarima):
        out = m(s, 6)
        assert len(out) == 6 and np.isfinite(out).all()


def test_regime_and_feasibility(monthly):
    s = monthly.set_index("period_month").arrivals
    post = f.regime_series(s, start="2024-01-01")
    assert post.index.min() == pd.Timestamp("2024-01-01")
    assert f.assess_feasibility(post)["feasible"] is True or len(post) < 48
    assert not f.assess_feasibility(s.iloc[:20])["feasible"]
    gappy = s.drop(s.index[10])
    assert f.assess_feasibility(gappy)["reason"] == "series has gaps"
    with pytest.raises(ValueError):
        f.regime_series(s, exclude=("2023-01-01", "2023-06-01"))
