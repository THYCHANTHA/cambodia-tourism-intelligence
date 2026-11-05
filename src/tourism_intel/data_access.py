"""Dashboard data loading. Returns empty results, not placeholders, when data is absent."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from .warehouse import DEFAULT_DB

TABLES = ["an_monthly_arrivals", "an_entry_detail", "an_entry_reported_total",
          "an_origin_purpose", "quality_findings"]


def load_warehouse(db_path: Path | str | None = None) -> dict:
    """{'tables': {name: df}, 'is_synthetic': bool, 'available': bool}."""
    path = Path(db_path) if db_path else DEFAULT_DB
    if not path.exists():
        return {"tables": {}, "is_synthetic": False, "available": False}
    con = duckdb.connect(str(path), read_only=True)
    try:
        have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        # table names come from the constant TABLES list, never from user input
        tables = {t: con.execute(f"SELECT * FROM {t}").df()  # nosec B608
                  for t in TABLES if t in have}
        syn = False
        if "meta" in have:
            row = con.execute("SELECT value FROM meta WHERE key='is_synthetic'").fetchone()
            syn = bool(row and row[0] == "true")
    finally:
        con.close()
    return {"tables": tables, "is_synthetic": syn, "available": bool(tables)}


def latest_period(tables: dict[str, pd.DataFrame]) -> str | None:
    """Latest month with a non-blank national arrival value, or None."""
    m = tables.get("an_monthly_arrivals")
    if m is None or m.empty:
        return None
    v = m.dropna(subset=["arrivals"])
    return None if v.empty else pd.Timestamp(v["period_month"].max()).strftime("%Y-%m")
