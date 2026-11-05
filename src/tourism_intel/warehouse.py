"""DuckDB warehouse: standardized tables -> analytics tables via SQL."""

from __future__ import annotations

import re
from pathlib import Path

import duckdb
import pandas as pd

from .ingest import ROOT

DEFAULT_DB = ROOT / "data" / "warehouse.duckdb"
SQL_DIR = ROOT / "sql"


def build(tables: dict[str, pd.DataFrame], db_path: Path, synthetic: bool = False,
          quality: pd.DataFrame | None = None) -> None:
    """Rebuild the warehouse from scratch. `synthetic` is stored so the app can warn."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    try:
        for kind, df in tables.items():
            if not re.fullmatch(r"[a-z_]+", kind):
                raise ValueError(f"unsafe table kind: {kind!r}")
            con.register("_df", df)
            con.execute(f"CREATE TABLE std_{kind} AS SELECT * FROM _df")  # nosec B608
            con.unregister("_df")
        con.execute("CREATE TABLE meta (key VARCHAR PRIMARY KEY, value VARCHAR)")
        con.execute("INSERT INTO meta VALUES ('is_synthetic', ?)", [str(synthetic).lower()])
        if quality is not None:
            con.register("_q", quality)
            con.execute("CREATE TABLE quality_findings AS SELECT * FROM _q")
            con.unregister("_q")
        for f in sorted(SQL_DIR.glob("*.sql")):
            sql = "\n".join(ln for ln in f.read_text().splitlines()
                            if not ln.strip().startswith("--"))
            for stmt in (s.strip() for s in sql.split(";")):
                if stmt:
                    _run_if_ready(con, stmt)
    finally:
        con.close()


def _run_if_ready(con, stmt: str) -> None:
    """Run an analytics statement only when the std_ tables it reads exist."""
    needed = {w for w in stmt.replace("\n", " ").split() if w.startswith("std_")}
    have = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
    if needed <= have:
        con.execute(stmt)
