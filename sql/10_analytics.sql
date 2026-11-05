-- Grain: one row per calendar month. Key: period_month.
CREATE TABLE an_monthly_arrivals AS
SELECT period_month, arrivals, source_id
FROM std_monthly_arrivals;

-- Grain: one row per (period_month, entry_point), detail rows only (totals excluded).
CREATE TABLE an_entry_detail AS
SELECT period_month, entry_point, entry_type, arrivals
FROM std_entry_points
WHERE NOT is_total_row;

-- Grain: one row per period_month, reported total row of the entry-point file.
CREATE TABLE an_entry_reported_total AS
SELECT period_month, SUM(arrivals) AS reported_total
FROM std_entry_points
WHERE is_total_row
GROUP BY period_month;

-- Grain: one row per (year, residence, purpose); level says country / region / total.
-- Never sum across levels.
CREATE TABLE an_origin_purpose AS
SELECT year, residence, level, purpose, visitors
FROM std_origin_purpose;
