"""Synthetic fixtures. Software tests only; never research evidence."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def monthly():
    idx = pd.date_range("2022-01-01", periods=60, freq="MS")
    season = np.tile(np.linspace(0.8, 1.2, 12), 5)
    vals = (100_000 * season * (1 + 0.01 * np.arange(60))).round()
    return pd.DataFrame({"period_month": idx, "arrivals": vals, "source_id": "synthetic"})


@pytest.fixture
def raw_dir(tmp_path, monthly):
    """A fake raw_local folder with CSVs shaped like config/sources.yaml expects."""
    d = tmp_path / "raw"
    (d / "monthly_arrivals").mkdir(parents=True)
    m = monthly.assign(period=monthly.period_month.dt.strftime("%Y-%m"))[["period", "arrivals"]]
    m.to_csv(d / "monthly_arrivals" / "m.csv", index=False)
    (d / "origins_2024").mkdir()
    pd.DataFrame({
        "year": [2024] * 6,
        "residence": ["China", "Vietnam", "ASEAN", "Total", "China", "Vietnam"],
        "purpose": ["Holiday"] * 4 + ["Business"] * 2,
        "visitors": ["600", "400", "1,000", "1,000", "50", "30"],
    }).to_csv(d / "origins_2024" / "o.csv", index=False)
    return d
