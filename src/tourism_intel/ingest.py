"""Manual-import ingestion: read local files, record checksums, standardize.

Nothing here downloads data. Files are placed by hand in data/raw_local/<source_id>/.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import yaml

from .analytics import split_levels
from .dates import parse_month

ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path | None = None) -> dict:
    return yaml.safe_load((path or ROOT / "config" / "sources.yaml").read_text())


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_files(raw_dir: Path, source_id: str) -> list[Path]:
    d = raw_dir / source_id
    return sorted(p for p in d.glob("*") if p.suffix.lower() in {".csv", ".xlsx", ".xls"}) \
        if d.is_dir() else []


def read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=str)
    return pd.read_excel(path, dtype=str)


def manifest_entry(source_id: str, src: dict, path: Path) -> dict:
    return {"source_id": source_id, "owner": src.get("owner"), "url": src.get("url"),
            "file": path.name, "sha256": sha256(path), "bytes": path.stat().st_size,
            "ingested_at_utc": datetime.now(UTC).isoformat(timespec="seconds")}


def _to_int(s: pd.Series) -> pd.Series:
    cleaned = s.astype(str).str.replace(",", "", regex=False).str.strip()
    out = pd.to_numeric(cleaned, errors="coerce")
    bad = out.isna() & s.notna() & ~cleaned.isin(["", "nan", "-"])
    if bad.any():
        raise ValueError(f"non-numeric values: {s[bad].unique()[:5].tolist()}")
    return out


def _rename(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    inv = {v: k for k, v in mapping.items()}
    missing = [v for v in inv if v not in df.columns]
    if missing:
        raise KeyError(f"expected columns not found: {missing}; found {list(df.columns)}")
    return df.rename(columns=inv)[list(mapping)]


def standardize_monthly(df: pd.DataFrame, mapping: dict, source_id: str) -> pd.DataFrame:
    d = _rename(df, mapping)
    d["period_month"] = d["period"].map(parse_month)
    d["arrivals"] = _to_int(d["arrivals"])  # blank stays missing, never interpolated
    d["source_id"] = source_id
    return d[["period_month", "arrivals", "source_id"]]


def standardize_entry_points(df: pd.DataFrame, mapping: dict, source_id: str,
                             cfg: dict) -> pd.DataFrame:
    d = _rename(df, mapping)
    d["period_month"] = d["period"].map(parse_month)
    d["arrivals"] = _to_int(d["arrivals"])
    d["entry_point"] = d["entry_point"].str.strip()
    types = cfg.get("entry_point_types", {})
    totals = {t.lower() for t in cfg.get("total_labels", [])}
    d["is_total_row"] = d["entry_point"].str.lower().isin(totals)
    d["entry_type"] = d["entry_point"].map(types).fillna("unclassified")
    d.loc[d["is_total_row"], "entry_type"] = "total"
    d["source_id"] = source_id
    return d[["period_month", "entry_point", "entry_type", "is_total_row", "arrivals", "source_id"]]


def standardize_origin_purpose(df: pd.DataFrame, mapping: dict, source_id: str,
                               cfg: dict) -> pd.DataFrame:
    d = _rename(df, mapping)
    d["year"] = d["year"].astype(int)
    d["visitors"] = _to_int(d["visitors"])
    d["residence"] = d["residence"].str.strip()
    d["purpose"] = d["purpose"].str.strip()
    d = split_levels(d, "residence", cfg.get("region_labels", []), cfg.get("total_labels", []))
    d["source_id"] = source_id
    return d[["year", "residence", "level", "purpose", "visitors", "source_id"]]


def run_ingest(raw_dir: Path, cfg: dict) -> tuple[dict[str, pd.DataFrame], list[dict], list[str]]:
    """Return (standardized tables by kind, manifest, notes). Missing sources are noted."""
    parts: dict[str, list[pd.DataFrame]] = {}
    manifest: list[dict] = []
    notes: list[str] = []
    for sid, src in cfg["sources"].items():
        files = find_files(raw_dir, sid)
        if not files:
            notes.append(f"{sid}: no local file found in {raw_dir / sid}")
            continue
        for f in files:
            raw = read_table(f)
            kind = src["kind"]
            if kind == "monthly_arrivals":
                std = standardize_monthly(raw, src["columns"], sid)
            elif kind == "entry_points":
                std = standardize_entry_points(raw, src["columns"], sid, cfg)
            else:
                std = standardize_origin_purpose(raw, src["columns"], sid, cfg)
            parts.setdefault(kind, []).append(std)
            manifest.append(manifest_entry(sid, src, f) | {"rows": len(std)})
    tables = {k: pd.concat(v, ignore_index=True) for k, v in parts.items()}
    return tables, manifest, notes


def write_manifest(manifest: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2))
