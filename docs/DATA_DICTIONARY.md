# Data Dictionary (target schema)

These are the designed tables. They have only been exercised with synthetic test fixtures.

## Standardized layer (`std_*`)

| Table | Grain | Key | Columns |
|---|---|---|---|
| std_monthly_arrivals | month x source file | (period_month, source_id) | period_month (first day), arrivals (int, NULL if blank), source_id |
| std_entry_points | month x entry point row | (period_month, entry_point, source_id) | entry_type (air/land/water/total/unclassified), is_total_row, arrivals |
| std_origin_purpose | year x residence x purpose | (year, residence, purpose, source_id) | level (country/region/total), visitors |

## Analytics layer (`an_*`, built by `sql/10_analytics.sql`)

| Table | Grain | Notes |
|---|---|---|
| an_monthly_arrivals | one row per month | national series |
| an_entry_detail | month x entry point | detail rows only, totals removed |
| an_entry_reported_total | month | reported total rows, kept only for reconciliation |
| an_origin_purpose | year x residence x purpose | never sum across `level` |
| quality_findings | one row per check | check, source, severity, detail |
| meta | key | `is_synthetic` flag shown by the dashboard |

Units: arrivals and visitors are counts of people as reported. Whether they count
arrivals or unique visitors, and the exact residence definition, are **unverified**.
Not modelled: domestic tourism, receipts, occupancy, accommodation, length of stay, GDP share.
