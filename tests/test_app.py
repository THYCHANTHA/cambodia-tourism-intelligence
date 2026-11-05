"""Run every dashboard page against a SYNTHETIC warehouse and against no data."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tourism_intel import pipeline, warehouse
from tourism_intel.ingest import run_ingest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


def _pages(at):
    return at.sidebar.radio[0].options


@pytest.fixture
def synthetic_db(raw_dir, tmp_path, monkeypatch):
    cfg = pipeline.load_config()
    tables, _, _ = run_ingest(raw_dir, cfg)
    db = tmp_path / "syn.duckdb"
    warehouse.build(tables, db, synthetic=True, quality=pipeline.quality_checks(tables))
    monkeypatch.setenv("TOURISM_DB", str(db))
    return db


def test_all_pages_with_synthetic_data_are_labelled(synthetic_db):
    at = AppTest.from_file(APP, default_timeout=60).run()
    for p in _pages(at):
        at.sidebar.radio[0].set_value(p).run()
        assert not at.exception, (p, at.exception)
        assert any("SYNTHETIC" in e.value for e in at.error), p


def test_all_pages_without_data_show_empty_states(tmp_path, monkeypatch):
    monkeypatch.setenv("TOURISM_DB", str(tmp_path / "none.duckdb"))
    at = AppTest.from_file(APP, default_timeout=60).run()
    for p in _pages(at):
        at.sidebar.radio[0].set_value(p).run()
        assert not at.exception, (p, at.exception)
        assert at.info or at.dataframe, p
    assert os.environ["TOURISM_DB"].endswith("none.duckdb")
