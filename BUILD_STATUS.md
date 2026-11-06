# Build Status: Cambodia Tourism Intelligence

**Status: IN PROGRESS** (software scaffold done; no real data ingested)

This repository is an unnumbered addition to the owner's portfolio. It is **not** portfolio
Project 09 (that number belongs to the computer-vision project); the earlier "Project 09" label
in this file and in PR #1 was a numbering error, corrected on 2026-11-06.

| Area | State |
|---|---|
| Data access | Blocked in the cloud build (network policy). Both sites answered HTTP 200 from a local machine on 2026-11-06; datasets and terms not yet inspected |
| Licensing | Unresolved for all sources |
| Pipeline, validation, analytics, forecasting code | Implemented, tested on synthetic fixtures only |
| Dashboard (8 pages) | Runs; shows empty states without data |
| Research findings | None |
| Forecasts | None |
| Portfolio files (main portfolio BUILD_STATUS, PORTFOLIO_INDEX) | Updated locally on 2026-11-06 (recorded as an unnumbered project) |

## Log

- **2026-11-05 (cloud session):** pipeline, tests, dashboard and audit documents built; merged to
  `main` via PR #1. Default branch was left on the session branch `claude/zen-brahmagupta-801hxi`.
- **2026-11-06 (local):** README rewritten as a professional project report (no new claims;
  every technical statement checked against the code). Local re-run on Windows 11, Python
  3.12.5, pandas 3.1, DuckDB 2.0, Streamlit 1.66: `pytest` 36 passed, `ruff check .` clean.
  Reachability of data.mef.gov.kh and tourism.gov.kh confirmed (HTTP 200); no data downloaded.
  No code changed.
