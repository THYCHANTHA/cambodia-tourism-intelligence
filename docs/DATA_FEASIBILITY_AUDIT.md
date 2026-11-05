# Data Feasibility Audit

**Status: BLOCKED. No source could be accessed, so nothing below is verified.**

Audit date: 2026-11-05. Environment: Claude Code cloud session.

## Access attempts

| Host | Result | Cause |
|---|---|---|
| data.mef.gov.kh | `CONNECT tunnel failed, response 403`; WebFetch `ENOTFOUND` | Cloud network policy (proxy refuses the tunnel). Not an upstream HTTP 403. |
| tourism.gov.kh | same | same |
| www.nis.gov.kh, api.worldbank.org, data.opendevelopmentmekong.net, www.tourismcambodia.org | same | same |

No retry loops, TLS bypasses, or unofficial mirrors were used. Only pypi, npm and github.com
were reachable. To continue, add `data.mef.gov.kh` and `tourism.gov.kh` to the environment's
allowed domains, or commit the files under `data/raw_local/` (they stay git-ignored).

## Per-source table

For every field below the honest answer is "not inspected".

| Field | A Monthly arrivals | B Entry pts 2024 | C Entry pts 2025 | D Origin/purpose 2024, 2025 | E MoT reports |
|---|---|---|---|---|---|
| Source | MEF Data EF (intended) | MEF | MEF | MEF | Ministry of Tourism |
| URL | pd_67f64166dbc953000126f580 | pd_6a855873911be0000713a2c3 | pd_6a8555f7911be0000713a2c1 | pd_6a94e5649db1ac00079f7f84, pd_685d0de81b4d5f0001c68176 | tourism.gov.kh/statistics-v2; pd_6a8280c3911be0000713a250 |
| Coverage | not inspected | not inspected | not inspected | not inspected | not inspected |
| Frequency | not inspected | not inspected | not inspected | not inspected | not inspected |
| Units / definitions | not inspected | not inspected | not inspected | not inspected | not inspected |
| Missingness | not inspected | not inspected | not inspected | not inspected | not inspected |
| License | unresolved | unresolved | unresolved | unresolved | unresolved |
| Access method | unknown | unknown | unknown | unknown | PDF suspected, unverified |

The brief's claims (e.g. 2019 to 2025 coverage) are the user's description, not findings.

## The seven questions

1. **Useful datasets?** Unknown. Not assessable.
2. **Complete monthly observations?** Unknown. Software counts them once a file is imported
   (`validate.missing_months`).
3. **Independent dimensions?** Unknown. The pipeline is built to keep time, entry point, and
   origin/purpose as separate tables.
4. **Overlapping totals?** Unknown. The pipeline tags total and regional rows (`is_total_row`,
   `level`) so they are never summed with detail rows.
5. **Reconcilable values?** Unknown. Reconciliation checks exist (entry detail vs reported total,
   entry vs national monthly, countries vs regions) and have only run on synthetic fixtures.
6. **Answerable research questions?** None answered. RQ1 to RQ4 and RQ6 need sources A to D.
   RQ5 needs verified extraction from source E.
7. **Is forecasting reasonable?** Undecided. `forecast.assess_feasibility` requires a gap-free
   regime with at least 48 months. Excluding the COVID window (2020-03 to 2022-12, configurable) from
   a 2019 to 2025 series would leave roughly 12 months before and 36 months after, so
   a seasonal backtest on a single post-COVID regime would likely be too short. This is an
   expectation from the brief's stated coverage, not a result.

## Placeholders in the code

`config/sources.yaml` column mappings are guesses. Expect to edit them against the real files.
