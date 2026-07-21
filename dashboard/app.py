"""
Ethiopia Financial Inclusion — Stakeholder Dashboard (Task 5)

Run with:
    streamlit run dashboard/app.py

Reads the tracked, enriched dataset (data/raw/ethiopia_fi_unified_data.csv) and the
Task 3/4 outputs already saved to data/processed/ -- it does not re-run any modeling
itself, so it stays fast and always reflects exactly what the notebooks produced.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import (
    load_unified_data, load_reference_codes, get_observations, get_events,
    get_targets, get_indicator_coverage,
)

st.set_page_config(page_title="Ethiopia Financial Inclusion Dashboard", layout="wide", page_icon="🇪🇹")

st.markdown("""
<style>
    /*  overall spacing -- Streamlit's default padding is generous */
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    div[data-testid="stVerticalBlock"] > div { gap: 0.6rem; }
    h1 { margin-bottom: 0.2rem !important; padding-top: 0 !important; }
    h2, h3 { margin-top: 0.8rem !important; margin-bottom: 0.4rem !important; }
    hr { margin: 0.6rem 0 !important; }

    /* Cream / whitish palette */
    .stApp { background-color: #FAF7F0; }
    section[data-testid="stSidebar"] { background-color: #F0EAD8; }
    div[data-testid="stMetric"] {
        background-color: #FFFDF8;
        border: 1px solid #E5DEC8;
        border-radius: 8px;
        padding: 0.7rem 0.9rem;
    }
    div[data-testid="stMetricLabel"] { color: #6B6355; }
    .stAlert { border-radius: 8px; }
    div[data-testid="stDataFrame"] { background-color: #FFFDF8; }
</style>
""", unsafe_allow_html=True)

PROCESSED_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"

# Human-readable labels for the indicator codes used throughout the dashboard
INDICATOR_LABELS = {
    "ACC_OWNERSHIP": "Account Ownership (Access)",
    "ACC_MM_ACCOUNT": "Mobile Money Account Penetration",
    "ACC_MM_REGISTERED": "Registered Mobile Money Accounts",
    "ACC_AGENT_COUNT": "Mobile Money Agent Count",
    "ACC_4G_COV": "4G Population Coverage",
    "ACC_SMARTPHONE_PEN": "Smartphone Penetration",
    "ACC_PHONE_OWNERSHIP": "Mobile Phone Ownership",
    "USG_DIGITAL_PAYMENT": "Digital Payment Adoption (Usage)",
    "USG_P2P_COUNT": "P2P Transaction Count",
    "USG_P2P_VALUE": "P2P Transaction Value",
    "USG_ATM_COUNT": "ATM Transaction Count",
    "USG_ATM_VALUE": "ATM Transaction Value",
    "USG_TELEBIRR_USERS": "Telebirr Users",
    "USG_MPESA_USERS": "M-Pesa Users",
    "USG_MPESA_ACTIVE": "M-Pesa 90-Day Active Rate",
    "GEN_GAP_ACC": "Gender Gap in Access (pp)",
}


# --------------------------------------------------------------------------- data loading
@st.cache_data
def load_data():
    df = load_unified_data()
    reference = load_reference_codes()
    return df, reference


@st.cache_data
def load_processed():
    forecast = pd.read_csv(PROCESSED_DIR / "forecast_2025_2027.csv")
    assoc_matrix = pd.read_csv(PROCESSED_DIR / "event_indicator_association_matrix_refined.csv", index_col=0)
    calibration = pd.read_csv(PROCESSED_DIR / "impact_model_calibration.csv")
    return forecast, assoc_matrix, calibration


df, reference = load_data()
forecast_df, assoc_matrix, calibration_df = load_processed()
obs = get_observations(df)


def _national_rows(rows: pd.DataFrame, gender: str | None):
    """
    Restrict to national/aggregate rows. Many indicators (especially ones added in Task 1
    enrichment) were never gender-disaggregated at all, so their `gender` field is NaN
    rather than the literal string 'all' -- both mean "not broken out by gender" and
    should be treated the same. Only an explicit 'male'/'female' value should be excluded
    when the caller asks for the aggregate.
    """
    if gender is None or "gender" not in rows.columns:
        return rows
    return rows[(rows["gender"] == gender) | (rows["gender"].isna())] if gender == "all" else rows[rows["gender"] == gender]


def latest_value(indicator_code: str, gender: str | None = "all"):
    rows = obs[obs["indicator_code"] == indicator_code]
    rows = _national_rows(rows, gender)
    if rows.empty:
        return None, None
    rows = rows.sort_values("observation_date")
    last = rows.iloc[-1]
    return last["value_numeric"], last["observation_date"]


def value_at_or_before(indicator_code: str, cutoff: pd.Timestamp, gender: str | None = "all"):
    rows = obs[obs["indicator_code"] == indicator_code]
    rows = _national_rows(rows, gender)
    rows = rows[rows["observation_date"] <= cutoff].sort_values("observation_date")
    if rows.empty:
        return None
    return rows.iloc[-1]["value_numeric"]


def style_fig(fig, height=420):
    """Apply the dashboard's cream palette and tighter margins to any Plotly figure."""
    fig.update_layout(
        paper_bgcolor="#FAF7F0",
        plot_bgcolor="#FFFDF8",
        font_color="#3A3A3A",
        margin=dict(l=40, r=20, t=50, b=40),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    fig.update_xaxes(gridcolor="#EDE6D6")
    fig.update_yaxes(gridcolor="#EDE6D6")
    return fig


# --------------------------------------------------------------------------- sidebar nav
st.sidebar.title("🇪🇹 Ethiopia FI Dashboard")
page = st.sidebar.radio("Navigate", ["Overview", "Trends", "Forecasts", "Inclusion Projections"])
st.sidebar.markdown("---")
st.sidebar.caption(
    f"Dataset: {len(df)} records "
    f"({(df['record_type']=='observation').sum()} observations, "
    f"{(df['record_type']=='event').sum()} events, "
    f"{(df['record_type']=='impact_link').sum()} impact_links)"
)
st.sidebar.caption("Two data-quality conflicts are flagged, not silently resolved — see `reports/data_enrichment_log.md`.")


# =============================================================================================
# OVERVIEW PAGE
# =============================================================================================
if page == "Overview":
    st.title("Overview")
    st.caption("Ethiopia's financial inclusion at a glance, per the Global Findex framework.")

    acc_val, acc_date = latest_value("ACC_OWNERSHIP")
    acc_prev = value_at_or_before("ACC_OWNERSHIP", pd.Timestamp("2021-12-31"))
    usg_val, usg_date = latest_value("USG_DIGITAL_PAYMENT")
    usg_prev = value_at_or_before("USG_DIGITAL_PAYMENT", pd.Timestamp("2021-12-31"))
    mm_val, mm_date = latest_value("ACC_MM_ACCOUNT")
    mm_prev = value_at_or_before("ACC_MM_ACCOUNT", pd.Timestamp("2021-12-31"))
    crossover_val, crossover_date = latest_value("USG_CROSSOVER", gender=None)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Account Ownership (Access)", f"{acc_val:.0f}%",
                f"{acc_val - acc_prev:+.0f}pp since 2021" if acc_prev else None)
    col2.metric("Digital Payment Adoption (Usage)", f"{usg_val:.0f}%",
                f"{usg_val - usg_prev:+.0f}pp since 2021" if usg_prev else None,
                delta_color="inverse" if (usg_prev and usg_val < usg_prev) else "normal")
    col3.metric("Mobile Money Account Penetration", f"{mm_val:.1f}%",
                f"{mm_val - mm_prev:+.1f}pp since 2021" if mm_prev else None)
    if crossover_val is not None:
        col4.metric("P2P / ATM Crossover Ratio", f"{crossover_val:.2f}x",
                    "P2P transfers exceed ATM withdrawals" if crossover_val > 1 else "ATM still leads")

    st.caption(
        f"Latest Access figure: {acc_date.date() if acc_date is not None else 'n/a'}. "
        f"Latest Usage figure: {usg_date.date() if usg_date is not None else 'n/a'} "
        "(this figure conflicts with an alternate ~35% estimate — see `reports/data_enrichment_log.md`)."
    )

    st.subheader("Growth Rate Highlights")
    st.caption("Percentage-point change in Account Ownership between each Findex survey round.")

    acc_series = obs[(obs["indicator_code"] == "ACC_OWNERSHIP") & (obs["gender"] == "all")].sort_values("observation_date")
    acc_series = acc_series.reset_index(drop=True)
    acc_series["pp_change"] = acc_series["value_numeric"].diff()
    growth_labels = [
        f"{acc_series['observation_date'].dt.year.iloc[i-1]}→{acc_series['observation_date'].dt.year.iloc[i]}"
        for i in range(1, len(acc_series))
    ]
    growth_fig = px.bar(
        x=growth_labels, y=acc_series["pp_change"].dropna(),
        labels={"x": "Survey round", "y": "Percentage points gained"},
        title="Account Ownership Growth Between Survey Rounds",
        text=acc_series["pp_change"].dropna().apply(lambda v: f"+{v:.0f}pp"),
    )
    growth_fig.update_traces(marker_color="#4c72b0", textposition="outside")
    st.plotly_chart(style_fig(growth_fig), use_container_width=True)
    st.info(
        "The 2021→2024 round grew only **+3pp**, the smallest jump on record, despite Telebirr "
        "and M-Pesa launching in between. See the Inclusion Projections page for the "
        "registered-vs-active gap that best explains this slowdown."
    )


# =============================================================================================
# TRENDS PAGE
# =============================================================================================
elif page == "Trends":
    st.title("Trends")
    st.caption("Explore how any combination of indicators has moved over time.")

    min_year = int(obs["observation_date"].dt.year.min())
    max_year = int(obs["observation_date"].dt.year.max())
    year_range = st.slider("Date range", min_year, max_year, (min_year, max_year))

    available_codes = sorted(obs["indicator_code"].dropna().unique())
    default_codes = [c for c in ["ACC_OWNERSHIP", "ACC_MM_ACCOUNT", "USG_DIGITAL_PAYMENT"] if c in available_codes]
    selected_codes = st.multiselect(
        "Compare indicators (channel comparison)",
        options=available_codes,
        default=default_codes,
        format_func=lambda c: INDICATOR_LABELS.get(c, c),
    )

    filtered = obs[
        (obs["observation_date"].dt.year >= year_range[0])
        & (obs["observation_date"].dt.year <= year_range[1])
        & (obs["indicator_code"].isin(selected_codes))
    ].copy()
    if "gender" in filtered.columns:
        filtered = filtered[(filtered["gender"] == "all") | (filtered["gender"].isna())]
    filtered["label"] = filtered["indicator_code"].map(lambda c: INDICATOR_LABELS.get(c, c))

    if filtered.empty:
        st.warning("No data for this selection — widen the date range or pick different indicators.")
    else:
        trend_fig = px.line(
            filtered.sort_values("observation_date"), x="observation_date", y="value_numeric",
            color="label", markers=True,
            labels={"observation_date": "Date", "value_numeric": "Value", "label": "Indicator"},
            title="Indicator Trends",
        )
        st.plotly_chart(style_fig(trend_fig), use_container_width=True)

        st.subheader("Underlying data")
        display_cols = ["record_id", "label", "value_numeric", "unit", "observation_date", "source_name", "confidence"]
        display_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(filtered[display_cols].sort_values("observation_date"), use_container_width=True)

        st.download_button(
            "Download this data as CSV",
            data=filtered[display_cols].to_csv(index=False).encode("utf-8"),
            file_name="ethiopia_fi_trends_export.csv",
            mime="text/csv",
        )


# =============================================================================================
# FORECASTS PAGE
# =============================================================================================
elif page == "Forecasts":
    st.title("Forecasts")
    st.caption("2025-2027 projections for Ethiopia's two headline Findex indicators.")

    indicator_choice = st.selectbox(
        "Indicator", ["ACC_OWNERSHIP", "USG_DIGITAL_PAYMENT"],
        format_func=lambda c: INDICATOR_LABELS.get(c, c),
    )
    model_choice = st.radio(
        "Model",
        ["Trend regression (statistical CI)", "Event-augmented (scenario range)"],
        help="Trend regression is a pure statistical fit. Event-augmented layers Task 3's "
             "calibrated event-impact model on top of it. USG_DIGITAL_PAYMENT has only 2 "
             "historical points, so its statistical CI is undefined (NaN) by design — not a bug.",
    )

    hist = obs[obs["indicator_code"] == indicator_choice]
    if "gender" in hist.columns:
        hist = hist[(hist["gender"] == "all") | (hist["gender"].isna())]
    hist = hist.sort_values("observation_date")

    fc = forecast_df[forecast_df["indicator"] == indicator_choice].sort_values("year")
    forecast_dates = pd.to_datetime(fc["year"].astype(str) + "-12-31")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist["observation_date"], y=hist["value_numeric"],
                              mode="lines+markers", name="Actual", line=dict(color="black", width=3)))

    if model_choice.startswith("Trend"):
        fig.add_trace(go.Scatter(x=forecast_dates, y=fc["trend_forecast"], mode="lines+markers",
                                  name="Trend forecast", line=dict(color="#4c72b0", dash="dash")))
        if fc["ci_lower"].notna().all():
            fig.add_trace(go.Scatter(x=list(forecast_dates) + list(forecast_dates[::-1]),
                                      y=list(fc["ci_upper"]) + list(fc["ci_lower"][::-1]),
                                      fill="toself", fillcolor="rgba(76,114,176,0.2)",
                                      line=dict(color="rgba(255,255,255,0)"), name="95% CI"))
        else:
            st.warning(
                f"{INDICATOR_LABELS.get(indicator_choice, indicator_choice)} has too few historical "
                "points for a statistically meaningful confidence interval (shown as undefined, "
                "not plotted) — see the scenario range under the event-augmented model instead."
            )
    else:
        fig.add_trace(go.Scatter(x=forecast_dates, y=fc["base"], mode="lines+markers",
                                  name="Base case", line=dict(color="#4c72b0", dash="dash")))
        fig.add_trace(go.Scatter(x=list(forecast_dates) + list(forecast_dates[::-1]),
                                  y=list(fc["optimistic"]) + list(fc["pessimistic"][::-1]),
                                  fill="toself", fillcolor="rgba(76,114,176,0.2)",
                                  line=dict(color="rgba(255,255,255,0)"), name="Scenario range"))

    fig.update_layout(title=f"{INDICATOR_LABELS.get(indicator_choice, indicator_choice)} — Forecast to 2027",
                       yaxis_title="%", xaxis_title="Date")
    st.plotly_chart(style_fig(fig), use_container_width=True)

    st.subheader("Key projected milestones")
    last_actual_val = hist["value_numeric"].iloc[-1]
    last_actual_year = hist["observation_date"].iloc[-1].year
    forecast_2027 = fc[fc["year"] == 2027]["base"].values[0] if model_choice.startswith("Event") else fc[fc["year"] == 2027]["trend_forecast"].values[0]
    st.markdown(
        f"- **{last_actual_year}** (last actual): {last_actual_val:.1f}%\n"
        f"- **2027** (projected, {'base case' if model_choice.startswith('Event') else 'trend'}): {forecast_2027:.1f}%\n"
        f"- Implied change: **{forecast_2027 - last_actual_val:+.1f}pp** over {2027 - last_actual_year} years"
    )

    st.subheader("Event-Indicator Association Matrix (refined, calibrated)")
    st.caption("From Task 3 — estimated effect (pp) of each cataloged event on key indicators.")
    st.dataframe(assoc_matrix.style.background_gradient(cmap="RdYlGn", axis=None, vmin=-10, vmax=10),
                 use_container_width=True)
    st.download_button(
        "Download forecast table as CSV",
        data=forecast_df.to_csv(index=False).encode("utf-8"),
        file_name="ethiopia_fi_forecast_2025_2027.csv",
        mime="text/csv",
    )


# =============================================================================================
# INCLUSION PROJECTIONS PAGE
# =============================================================================================
elif page == "Inclusion Projections":
    st.title("Inclusion Projections")
    st.caption("Progress toward official targets, and direct answers to the consortium's key questions.")

    scenario = st.radio("Scenario", ["pessimistic", "base", "optimistic"], index=1, horizontal=True)

    acc_targets = get_targets(df)
    acc_target_row = acc_targets[acc_targets["indicator"] == "Account Ownership Rate"]
    official_target = acc_target_row["value_numeric"].values[0] if not acc_target_row.empty else 70.0
    official_target_date = acc_target_row["observation_date"].values[0] if not acc_target_row.empty else None

    acc_fc = forecast_df[forecast_df["indicator"] == "ACC_OWNERSHIP"].sort_values("year")
    current_val = obs[(obs["indicator_code"] == "ACC_OWNERSHIP") & (obs["gender"] == "all")].sort_values("observation_date").iloc[-1]["value_numeric"]
    projected_2027 = acc_fc[acc_fc["year"] == 2027][scenario].values[0]

    st.markdown(
        f"**Note on targets**: the project brief references a 60% Access milestone; this "
        f"dataset's own official target (NFIS-II, sourced from the National Bank of Ethiopia) "
        f"is **{official_target:.0f}%** by "
        f"{pd.Timestamp(official_target_date).year if official_target_date is not None else 'end-2025'}. "
        "Both are shown below rather than silently picking one."
    )

    gauge_fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=projected_2027,
        delta={"reference": current_val, "increasing": {"color": "green"}},
        title={"text": f"Account Ownership — {scenario.title()} scenario, projected 2027"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#4c72b0"},
            "steps": [
                {"range": [0, 60], "color": "#fde0dd"},
                {"range": [60, 70], "color": "#fee8c8"},
                {"range": [70, 100], "color": "#e5f5e0"},
            ],
            "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.9, "value": official_target},
        },
    ))
    st.plotly_chart(style_fig(gauge_fig, height=380), use_container_width=True)
    st.caption("Red line = official NFIS-II target (70%). Shaded bands mark 60% (brief's reference milestone) and the 60-70% gap.")

    # Simple linear extrapolation (using the scenario's own 2026->2027 slope) to estimate
    # when each scenario would cross the official target, if not already within the forecast window.
    def project_year_to_reach(target, y2026, y2027, start_year=2027):
        slope = y2027 - y2026
        if slope <= 0:
            return None
        years_needed = (target - y2027) / slope
        return start_year + years_needed

    st.subheader("Projected year to reach official 70% target, by scenario")
    milestone_rows = []
    for s in ["pessimistic", "base", "optimistic"]:
        y2026 = acc_fc[acc_fc["year"] == 2026][s].values[0]
        y2027 = acc_fc[acc_fc["year"] == 2027][s].values[0]
        year_reached = project_year_to_reach(official_target, y2026, y2027)
        milestone_rows.append({
            "scenario": s, "2027 projected": f"{y2027:.1f}%",
            "estimated year to reach 70%": f"~{year_reached:.0f}" if year_reached else "beyond projection horizon",
        })
    st.table(pd.DataFrame(milestone_rows))
    st.caption(
        "Linear extrapolation beyond 2027 using each scenario's own 2026→2027 slope — a rough "
        "guide, not a precise date. All three scenarios cluster closely because, per Task 4, "
        "the event-driven component is nearly fully realized by 2025 in this model; the "
        "trend slope (not the event model) dominates further out."
    )

  #  st.subheader("Answers to the Consortium's Key Questions")
  