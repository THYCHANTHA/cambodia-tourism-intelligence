"""Cambodia Tourism Intelligence dashboard. Every figure comes from the local warehouse."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from tourism_intel import analytics, forecast  # noqa: E402
from tourism_intel.data_access import latest_period, load_warehouse  # noqa: E402
from tourism_intel.ingest import load_config  # noqa: E402

BLUE = ["#1f77b4", "#6baed6", "#9ecae1", "#08519c", "#4292c6", "#c6dbef"]
PAGES = ["Tourism Overview", "International Visitor Trends", "Visitor Origin & Market Intelligence",
         "Travel Purpose & Entry Points", "Domestic Tourism & Destinations",
         "Tourism Supply & Economic Indicators", "Forecasting & Scenario Analysis",
         "Data Quality & Methodology"]

st.set_page_config(page_title="Cambodia Tourism Intelligence", layout="wide")
st.markdown("""<style>
.block-container{padding-top:2rem} h1,h2,h3{color:#08519c}
div[data-testid="stMetric"]{background:#eaf4fb;border-radius:8px;padding:.6rem}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _load(path: str | None):
    return load_warehouse(path)


wh = _load(os.environ.get("TOURISM_DB"))
T = wh["tables"]
latest = latest_period(T)


def empty(what: str, need: str) -> None:
    st.info(f"No {what} loaded. {need} See Data Quality & Methodology for how to import files.")


def header(title: str) -> None:
    st.title(title)
    if wh["is_synthetic"]:
        st.error("SYNTHETIC TEST DATA. These numbers are not Cambodian tourism statistics.")
    st.caption(f"Latest actual reporting period in national monthly series: "
               f"**{latest or 'no data loaded'}**")


page = st.sidebar.radio("Navigate", PAGES)
header(page)
monthly = T.get("an_monthly_arrivals")
if monthly is not None:
    monthly = monthly.dropna(subset=["arrivals"]).sort_values("period_month")

if page == PAGES[0]:
    if monthly is None or monthly.empty:
        empty("monthly arrivals", "Place the MEF monthly arrivals file in data/raw_local/.")
    else:
        ann = analytics.annual_totals(monthly)
        last = ann.iloc[-1]
        c1, c2, c3 = st.columns(3)
        c1.metric("Months of data", len(monthly))
        c2.metric(f"{int(last.year)} arrivals" + ("" if last.is_complete else " (PARTIAL)"),
                  f"{int(last.total):,}")
        yoy = last.yoy_pct
        c3.metric("YoY (complete years only)", "n/a" if pd.isna(yoy) else f"{yoy:+.1f}%")
        st.plotly_chart(px.line(monthly, x="period_month", y="arrivals",
                                color_discrete_sequence=BLUE), use_container_width=True)

elif page == PAGES[1]:
    if monthly is None or monthly.empty:
        empty("monthly arrivals", "Place the MEF monthly arrivals file in data/raw_local/.")
    else:
        g = analytics.add_growth(monthly)
        st.plotly_chart(px.line(g, x="period_month", y=["arrivals", "rolling_12m"],
                                color_discrete_sequence=BLUE), use_container_width=True)
        st.plotly_chart(px.bar(g.dropna(subset=["yoy_pct"]), x="period_month", y="yoy_pct",
                               color_discrete_sequence=BLUE, title="Year-over-year change (%)"),
                        use_container_width=True)
        st.subheader("Annual totals")
        st.dataframe(analytics.annual_totals(monthly), hide_index=True)
        st.caption("Years with fewer than 12 months are flagged partial and get no YoY. "
                   "Trends are descriptive; no causes are tested here.")

elif page == PAGES[2]:
    o = T.get("an_origin_purpose")
    if o is None or o.empty:
        empty("visitor origin data", "Place the MEF origin files in data/raw_local/.")
    else:
        year = st.selectbox("Year", sorted(o["year"].unique()))
        level = st.radio("Level (never combined)", ["country", "region"], horizontal=True)
        d = o[(o.year == year) & (o.level == level)]
        purposes = sorted(d["purpose"].unique())
        pick = st.multiselect("Purpose", purposes, default=purposes)
        ms = analytics.market_share(d[d.purpose.isin(pick)], "residence", "visitors")
        if ms.empty:
            st.warning("No rows for this selection.")
        else:
            st.metric("HHI (0-10,000)", f"{analytics.hhi(ms.share_pct):,.0f}")
            st.plotly_chart(px.bar(ms.head(15), x="residence", y="share_pct",
                                   color_discrete_sequence=BLUE), use_container_width=True)
            st.caption("Country of residence, not nationality. Shares are within the chosen level.")

elif page == PAGES[3]:
    e, o = T.get("an_entry_detail"), T.get("an_origin_purpose")
    if e is None or e.empty:
        empty("entry-point data", "Place the MEF entry-point files in data/raw_local/.")
    else:
        comp = e.groupby([pd.to_datetime(e.period_month).dt.year.rename("year"), "entry_type"],
                         as_index=False)["arrivals"].sum()
        st.plotly_chart(px.bar(comp, x="year", y="arrivals", color="entry_type",
                               color_discrete_sequence=BLUE), use_container_width=True)
        st.caption("Detail rows only. Reported total rows are excluded to avoid double counting.")
    if o is not None and not o.empty:
        tot = o[o.level == "total"]
        if not tot.empty:
            st.plotly_chart(px.bar(tot, x="year", y="visitors", color="purpose",
                                   color_discrete_sequence=BLUE), use_container_width=True)

elif page == PAGES[4]:
    st.info("Domestic tourism is not loaded. The Ministry of Tourism publishes it in PDF reports "
            "and extraction has not been verified against the original tables. Domestic visits "
            "are never added to international arrivals.")

elif page == PAGES[5]:
    st.info("Receipts, occupancy, accommodation capacity, length of stay and GDP share are not "
            "loaded. They need verified extraction from the Ministry reports, and definitions "
            "may differ between years. No values are shown rather than guessed ones.")

elif page == PAGES[6]:
    if monthly is None or monthly.empty:
        empty("monthly arrivals", "Forecasting needs the national monthly series.")
    else:
        cov = load_config()["covid_window"]
        s = monthly.set_index("period_month")["arrivals"].astype(float)
        regime = st.radio("Regime", ["Post-COVID only (from window end)", "Pre-COVID only",
                                     "Full history (breaks ignored, for comparison)"])
        if regime.startswith("Post"):
            rs = forecast.regime_series(s, start=cov["end"])
        elif regime.startswith("Pre"):
            rs = forecast.regime_series(s, end=cov["start"])
        else:
            rs = s
        feas = forecast.assess_feasibility(rs)
        st.write(f"Months in regime: **{feas['n_months']}**. Gap-free: **{feas['gap_free']}**.")
        if not feas["feasible"]:
            st.warning(f"Backtest not run: {feas['reason']}. No forecast is produced.")
        else:
            bt = forecast.backtest(rs)
            summ = forecast.summarise(bt)
            st.dataframe(summ, hide_index=True)
            if "error" in bt:
                st.caption("Some model fits failed; see rows with an error in the backtest.")
            st.caption("Expanding-window backtest, chronological. Lower is better. A model is "
                       "only 'better' if it beats seasonal naive across origins. No forward "
                       "forecast is shown.")

else:
    q = T.get("quality_findings")
    if q is None:
        empty("quality findings", "Run python -m tourism_intel.pipeline.")
    else:
        st.dataframe(q, hide_index=True)
    st.markdown("See `docs/METHODOLOGY.md`, `docs/DATA_QUALITY_REPORT.md` and "
                "`docs/DATA_LICENSE_AUDIT.md`. Source files are imported manually and are not "
                "bundled because redistribution rights are unresolved.")
