import pandas as pd
import pytest

from tourism_intel.dates import parse_month
from tourism_intel.validate import (
    complete_years,
    duplicate_keys,
    missing_months,
    negative_values,
    reconcile,
)


@pytest.mark.parametrize("v", ["2024-03", "Mar 2024", "March-2024", "2024-03-15", "2024/3",
                               pd.Timestamp("2024-03-20")])
def test_parse_month_formats(v):
    assert parse_month(v) == pd.Timestamp("2024-03-01")


@pytest.mark.parametrize("v", ["2024-13", "hello", "", None, "Foo 2024"])
def test_parse_month_rejects(v):
    with pytest.raises(ValueError):
        parse_month(v)


def test_missing_months_detects_gap(monthly):
    m = monthly.drop(index=[5, 6])
    assert [d.strftime("%Y-%m") for d in missing_months(m.period_month)] == ["2022-06", "2022-07"]
    assert missing_months(monthly.period_month) == []
    assert missing_months(pd.Series([], dtype="datetime64[ns]")) == []


def test_duplicates_and_negatives(monthly):
    d = pd.concat([monthly, monthly.iloc[[0]]])
    assert len(duplicate_keys(d, ["period_month"])) == 2
    bad = monthly.copy()
    bad.loc[0, "arrivals"] = -1
    assert len(negative_values(bad, "arrivals")) == 1


def test_reconcile_flags_mismatch_and_one_sided_keys():
    det = pd.Series({"a": 10, "b": 20})
    tot = pd.Series({"a": 10, "b": 25, "c": 5})
    r = reconcile(det, tot)
    assert r.loc["a", "ok"] and not r.loc["b", "ok"] and not r.loc["c", "ok"]
    assert reconcile(det, pd.Series({"a": 10, "b": 20.5}), tol_abs=1)["ok"].all()


def test_complete_years(monthly):
    assert complete_years(monthly.iloc[:50]).to_dict() == {2022: True, 2023: True, 2024: True,
                                                          2025: True, 2026: False}
