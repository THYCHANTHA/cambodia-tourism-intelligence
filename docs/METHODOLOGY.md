# Methodology

All methods are implemented and unit-tested on synthetic data only. No empirical result exists yet.

- **Ingestion**: manual files only. Dates parse strictly (`dates.parse_month`); bad values raise.
  Blank counts stay NULL and are never interpolated.
- **Validation**: duplicates, missing months, negatives, entry detail vs reported total, entry
  vs national monthly, country sum vs regional sum (0.1% tolerance).
- **Growth**: YoY compares the same month 12 months earlier, so a gap yields NaN. Annual YoY is
  only computed between two complete 12-month years.
- **Markets**: shares inside one `level` only. HHI = sum of squared percent shares (0 to 10,000).
  Country of residence is not nationality.
- **Forecasting**: models are naive, seasonal naive, damped additive Holt-Winters (ETS) and
  SARIMA(1,1,1)(0,1,1)12. Validation is expanding-window and chronological; metrics are MAE,
  RMSE, sMAPE. Regimes (pre-COVID, post-COVID, full) are chosen explicitly and the COVID window
  is configurable. A backtest runs only when the regime is gap-free and has at least 48 months.
  No forward forecast is produced. A model counts as better only if it beats seasonal naive.
- **ML models** (Random Forest, gradient boosting) were not implemented: a few dozen monthly
  points do not justify them.
- Trends are descriptive. No causal claim is made about COVID or anything else.
