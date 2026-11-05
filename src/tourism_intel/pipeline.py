"""End to end rebuild from local files: ingest -> validate -> parquet -> DuckDB.

Run:  python -m tourism_intel.pipeline [--raw data/raw_local] [--db data/warehouse.duckdb]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import validate, warehouse
from .ingest import ROOT, load_config, run_ingest, write_manifest


def quality_checks(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    f: list[dict] = []

    def add(check, source, severity, detail):
        f.append({"check": check, "source": source, "severity": severity, "detail": detail})

    m = tables.get("monthly_arrivals")
    if m is not None:
        dup = validate.duplicate_keys(m, ["period_month"])
        add("duplicate_months", "monthly_arrivals", "error" if len(dup) else "ok",
            f"{len(dup)} duplicated rows")
        gaps = validate.missing_months(m["period_month"])
        add("missing_months", "monthly_arrivals", "warn" if gaps else "ok",
            ", ".join(d.strftime("%Y-%m") for d in gaps) or "none between first and last month")
        nulls = int(m["arrivals"].isna().sum())
        add("missing_values", "monthly_arrivals", "warn" if nulls else "ok",
            f"{nulls} months with blank arrivals (not interpolated)")
        neg = validate.negative_values(m.dropna(subset=["arrivals"]), "arrivals")
        add("negative_values", "monthly_arrivals", "error" if len(neg) else "ok",
            f"{len(neg)} rows")

    e = tables.get("entry_points")
    if e is not None:
        dup = validate.duplicate_keys(e, ["period_month", "entry_point"])
        add("duplicate_entry_rows", "entry_points", "error" if len(dup) else "ok",
            f"{len(dup)} duplicated rows")
        unk = sorted(e.loc[e["entry_type"] == "unclassified", "entry_point"].unique())
        add("unclassified_entry_points", "entry_points", "warn" if unk else "ok",
            ", ".join(unk) or "none")
        det = e[~e["is_total_row"]].groupby("period_month")["arrivals"].sum()
        tot = e[e["is_total_row"]].groupby("period_month")["arrivals"].sum()
        if len(tot):
            r = validate.reconcile(det, tot)
            bad = r[~r["ok"]]
            add("entry_total_reconciliation", "entry_points", "error" if len(bad) else "ok",
                f"{len(bad)} of {len(r)} months do not reconcile")
        else:
            add("entry_total_reconciliation", "entry_points", "warn", "no reported total rows")
        if m is not None and len(det):
            r = validate.reconcile(det, m.set_index("period_month")["arrivals"].dropna()
                                   .reindex(det.index))
            add("entry_vs_national_monthly", "entry_points+monthly_arrivals",
                "warn" if (~r["ok"]).any() else "ok",
                f"{int((~r['ok']).sum())} of {len(r)} months differ from national series")

    o = tables.get("origin_purpose")
    if o is not None:
        dup = validate.duplicate_keys(o, ["year", "residence", "purpose"])
        add("duplicate_origin_rows", "origin_purpose", "error" if len(dup) else "ok",
            f"{len(dup)} duplicated rows")
        c = o[o["level"] == "country"].groupby(["year", "purpose"])["visitors"].sum()
        r_ = o[o["level"] == "region"].groupby(["year", "purpose"])["visitors"].sum()
        if len(r_):
            rec = validate.reconcile(c, r_, tol_rel=0.001)
            add("country_vs_region_sum", "origin_purpose", "warn" if (~rec["ok"]).any() else "ok",
                f"{int((~rec['ok']).sum())} of {len(rec)} year/purpose cells differ >0.1%")
    if not f:
        add("no_data", "-", "warn", "no source files were found; nothing was validated")
    return pd.DataFrame(f)


def run(raw_dir: Path, db_path: Path, out_dir: Path) -> dict:
    cfg = load_config()
    tables, manifest, notes = run_ingest(raw_dir, cfg)
    quality = quality_checks(tables)
    out_dir.mkdir(parents=True, exist_ok=True)
    for kind, df in tables.items():
        df.to_parquet(out_dir / f"{kind}.parquet", index=False)
    write_manifest(manifest, out_dir / "manifest.json")
    warehouse.build(tables, db_path, synthetic=False, quality=quality)
    return {"tables": {k: len(v) for k, v in tables.items()}, "notes": notes,
            "quality": quality.to_dict("records")}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=ROOT / "data" / "raw_local")
    ap.add_argument("--db", type=Path, default=warehouse.DEFAULT_DB)
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "standardized")
    a = ap.parse_args()
    res = run(a.raw, a.db, a.out)
    print("rows per table:", res["tables"] or "none")
    for n in res["notes"]:
        print("NOTE", n)
    for q in res["quality"]:
        print(f"[{q['severity']}] {q['check']} ({q['source']}): {q['detail']}")


if __name__ == "__main__":
    main()
