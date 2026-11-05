# Data Provenance

No source was downloaded, so there are no download dates, checksums, or verified units to record.

## Intended sources (URLs from the brief)

| ID | URL | Owner | Retrieved | SHA-256 | Units | Period |
|---|---|---|---|---|---|---|
| monthly_arrivals | https://data.mef.gov.kh/datasets/pd_67f64166dbc953000126f580 | MEF | never | n/a | unverified | unverified |
| entry_points_2024 | https://data.mef.gov.kh/datasets/pd_6a855873911be0000713a2c3 | MEF | never | n/a | unverified | unverified |
| entry_points_2025 | https://data.mef.gov.kh/datasets/pd_6a8555f7911be0000713a2c1 | MEF | never | n/a | unverified | unverified |
| origins_2024 | https://data.mef.gov.kh/datasets/pd_6a94e5649db1ac00079f7f84 | MEF | never | n/a | unverified | unverified |
| origins_2025 | https://data.mef.gov.kh/datasets/pd_685d0de81b4d5f0001c68176 | MEF | never | n/a | unverified | unverified |
| mot_report_2025 | https://data.mef.gov.kh/datasets/pd_6a8280c3911be0000713a250 | MoT | never | n/a | unverified | unverified |
| mot_statistics | https://tourism.gov.kh/statistics-v2 | MoT | never | n/a | unverified | unverified |

## What the pipeline records once files exist

`python -m tourism_intel.pipeline` writes `data/standardized/manifest.json` with, per file:
source id, owner, URL, file name, SHA-256, byte size, UTC ingest time, and row count.
The retrieval date of the download itself must be noted by the person who downloaded it.
