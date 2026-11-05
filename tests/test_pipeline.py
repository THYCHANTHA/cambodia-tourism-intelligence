import duckdb
import pandas as pd
import pytest

from tourism_intel import ingest, pipeline
from tourism_intel.data_access import latest_period, load_warehouse
from tourism_intel.pipeline import quality_checks


def test_standardize_blank_not_interpolated():
    df = pd.DataFrame({"period": ["2024-01", "2024-02"], "arrivals": ["1,000", ""]})
    out = ingest.standardize_monthly(df, {"period": "period", "arrivals": "arrivals"}, "s")
    assert out.arrivals.iloc[0] == 1000 and pd.isna(out.arrivals.iloc[1])


def test_non_numeric_and_missing_column_fail_loudly():
    with pytest.raises(ValueError):
        ingest.standardize_monthly(pd.DataFrame({"period": ["2024-01"], "arrivals": ["abc"]}),
                                   {"period": "period", "arrivals": "arrivals"}, "s")
    with pytest.raises(KeyError):
        ingest.standardize_monthly(pd.DataFrame({"x": [1]}),
                                   {"period": "period", "arrivals": "arrivals"}, "s")


def test_entry_point_total_rows_flagged_and_reconciled():
    cfg = ingest.load_config()
    raw = pd.DataFrame({"period": ["2024-01"] * 4,
                        "entry_point": ["Phnom Penh International Airport", "Land", "Waterway",
                                        "Total"],
                        "arrivals": ["60", "30", "10", "100"]})
    std = ingest.standardize_entry_points(raw, cfg["sources"]["entry_points_2024"]["columns"],
                                          "x", cfg)
    assert std.is_total_row.tolist() == [False, False, False, True]
    assert std.entry_type.tolist() == ["air", "land", "water", "total"]
    q = quality_checks({"entry_points": std}).set_index("check")
    assert q.loc["entry_total_reconciliation", "severity"] == "ok"
    std.loc[0, "arrivals"] = 50
    q = quality_checks({"entry_points": std}).set_index("check")
    assert q.loc["entry_total_reconciliation", "severity"] == "error"


def test_unknown_entry_point_is_flagged_not_guessed():
    cfg = ingest.load_config()
    raw = pd.DataFrame({"period": ["2024-01"], "entry_point": ["Mystery Gate"],
                        "arrivals": ["5"]})
    std = ingest.standardize_entry_points(raw, {"period": "period", "entry_point": "entry_point",
                                                "arrivals": "arrivals"}, "x", cfg)
    assert std.entry_type.iloc[0] == "unclassified"


def test_offline_rebuild_and_reproducible(raw_dir, tmp_path):
    r1 = pipeline.run(raw_dir, tmp_path / "a.duckdb", tmp_path / "o1")
    r2 = pipeline.run(raw_dir, tmp_path / "b.duckdb", tmp_path / "o2")
    assert r1["tables"] == r2["tables"] == {"monthly_arrivals": 60, "origin_purpose": 6}
    assert any("entry_points_2024" in n for n in r1["notes"])  # missing source is reported
    assert (tmp_path / "o1" / "manifest.json").exists()
    a = duckdb.connect(str(tmp_path / "a.duckdb"), read_only=True)
    b = duckdb.connect(str(tmp_path / "b.duckdb"), read_only=True)
    q = "SELECT * FROM an_monthly_arrivals ORDER BY period_month"
    assert a.execute(q).df().equals(b.execute(q).df())
    # country rows never summed with regional / total rows
    lv = a.execute("SELECT level, SUM(visitors) v FROM an_origin_purpose WHERE purpose='Holiday' "
                   "GROUP BY level ORDER BY level").fetchall()
    assert lv == [("country", 1000), ("region", 1000), ("total", 1000)]


def test_dashboard_loading(raw_dir, tmp_path):
    empty = load_warehouse(tmp_path / "missing.duckdb")
    assert not empty["available"] and latest_period(empty["tables"]) is None
    pipeline.run(raw_dir, tmp_path / "w.duckdb", tmp_path / "o")
    wh = load_warehouse(tmp_path / "w.duckdb")
    assert wh["available"] and not wh["is_synthetic"]
    assert latest_period(wh["tables"]) == "2026-12"


def test_checksums_recorded(raw_dir):
    cfg = ingest.load_config()
    _, manifest, _ = ingest.run_ingest(raw_dir, cfg)
    assert all(len(m["sha256"]) == 64 for m in manifest) and len(manifest) == 2
