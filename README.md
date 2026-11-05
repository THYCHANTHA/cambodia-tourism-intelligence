# Cambodia Tourism Intelligence & Demand Analytics

*Understanding Cambodia's Tourism Industry Through Data Engineering, Market Intelligence, and Statistical Forecasting.*

> **Status: IN PROGRESS. No Cambodian data has been analysed yet.** The official sources
> (data.mef.gov.kh, tourism.gov.kh) were blocked from the build environment, so this repo contains
> the pipeline, tests and dashboard, but no findings. See `docs/DATA_FEASIBILITY_AUDIT.md`.

## Research question
How can public tourism statistics help us understand Cambodia's tourism trends, visitor markets,
travel patterns, supply and possible future demand? Sub-questions RQ1 to RQ6 are open.

## Data coverage
None loaded. Intended sources: MEF Data EF monthly arrivals, entry points 2024 and 2025,
origin and purpose 2024 and 2025, and Ministry of Tourism reports. Licensing is unresolved,
so no data is bundled. Files are imported by hand into `data/raw_local/<source_id>/`
(git-ignored).

## Architecture
manual files -> ingest (checksums, strict parsing) -> validate -> standardized Parquet ->
DuckDB (`sql/`) -> analytics -> Streamlit.

```
src/tourism_intel/  dates, ingest, validate, analytics, forecast, warehouse, pipeline, data_access
app/streamlit_app.py   8 pages, localhost only
config/sources.yaml    source registry and column mappings (placeholders, unverified)
sql/                   analytics tables with documented grain
tests/                 synthetic fixtures only
```

## Run it
```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
python -m tourism_intel.pipeline      # after placing files in data/raw_local/
streamlit run app/streamlit_app.py    # http://127.0.0.1:8501
pytest && ruff check .
```

## Dashboard pages
Overview, International Visitor Trends, Visitor Origin & Market Intelligence, Travel Purpose &
Entry Points, Domestic Tourism, Supply & Economic Indicators, Forecasting, Data Quality &
Methodology. Domestic and supply pages are explanatory placeholders: PDF extraction is not
built. Screenshots in `docs/screenshots/` show empty states only.

## Forecasting
Naive, seasonal naive, ETS and SARIMA with expanding-window backtests by regime. Not run on real
data. No forward forecast is produced by design.

## Validation actually run (2026-11-05, cloud session)
- `ruff check .`: pass
- `pytest`: 36 passed (synthetic fixtures, incl. Streamlit AppTest on all pages)
- `bandit -r src app`: no reported issues after fixes (two B608 table-name warnings handled)
- `pip-audit -r requirements.txt`: no known vulnerabilities
- Dashboard started on 127.0.0.1:8599, health endpoint returned 200
- Pipeline run with no data: completes and reports every source as missing
- Fresh-clone install: see PR description

## Limitations
No real data, unverified column mappings, unresolved licensing, no portfolio file updates.
Software license not yet chosen. Dataset licenses are separate from software license.
