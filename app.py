import os
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import psycopg2
import psycopg2.extras


st.set_page_config(
    page_title="India Grid Reliability Tracker",
    page_icon="⚡",
    layout="wide",
)

INDIA_GEOJSON_URL = (
    "https://raw.githubusercontent.com/geohacker/india/"
    "master/state/india_all.geojson"
)

RISK_COLORS = {"High": "#e63946", "Medium": "#f4a261", "Low": "#2a9d8f"}

GEOJSON_NAME_MAP = {
    "Arunanchal Pradesh": "Arunachal Pradesh",
    "Chattisgarh": "Chhattisgarh",
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Dadara & Nagar Havelli": "Dadra and Nagar Haveli and Daman and Diu",
    "Daman & Diu": "Dadra and Nagar Haveli and Daman and Diu",
    "Andaman & Nicobar Island": "Andaman and Nicobar Islands",
}


@st.cache_resource
def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        try:
            db_url = st.secrets["DATABASE_URL"]
        except Exception:
            db_url = ""
    if not db_url:
        st.error("DATABASE_URL not set. Add it to .streamlit/secrets.toml or your environment.")
        st.stop()
    return psycopg2.connect(db_url)


@st.cache_data(ttl=3600)
def load_risk_scores():
    conn = get_connection()
    return pd.read_sql("""
        SELECT rs.state_id, s.state_name, s.region,
               rs.score_date, rs.risk_score, rs.risk_label,
               rs.score_outage, rs.score_heat, rs.score_rain
        FROM fact_risk_scores rs
        JOIN dim_state s ON s.state_id = rs.state_id
        ORDER BY rs.score_date, rs.risk_score DESC
    """, conn, parse_dates=["score_date"])


@st.cache_data(ttl=3600)
def load_outage_trend():
    conn = get_connection()
    return pd.read_sql("""
        SELECT report_date,
               COUNT(*) FILTER (WHERE outage_category LIKE 'Forced%%') AS forced_events,
               COALESCE(SUM(outage_mw) FILTER (WHERE outage_category LIKE 'Forced%%'), 0)
                   AS forced_mw
        FROM fact_outage_event
        GROUP BY report_date
        ORDER BY report_date
    """, conn, parse_dates=["report_date"])


@st.cache_data(ttl=3600)
def load_state_outage_detail(state_name: str):
    conn = get_connection()
    return pd.read_sql("""
        SELECT oe.report_date, oe.outage_category, oe.outage_mw,
               oe.reason_category, st.station_name
        FROM fact_outage_event oe
        JOIN dim_state s  ON s.state_id  = oe.state_id
        JOIN dim_station st ON st.station_id = oe.station_id
        WHERE s.state_name = %(state)s
        ORDER BY oe.report_date
    """, conn, params={"state": state_name}, parse_dates=["report_date"])


@st.cache_data(ttl=3600)
def load_weather_for_state(state_name: str):
    conn = get_connection()
    return pd.read_sql("""
        SELECT w.event_date, w.max_temp_c, w.rainfall_mm
        FROM fact_weather_event w
        JOIN dim_state s ON s.state_id = w.state_id
        WHERE s.state_name = %(state)s AND w.source = 'OpenMeteo'
        ORDER BY w.event_date
    """, conn, params={"state": state_name}, parse_dates=["event_date"])


@st.cache_data(ttl=3600)
def load_reason_breakdown():
    conn = get_connection()
    return pd.read_sql("""
        SELECT reason_category,
               COUNT(*) AS events,
               SUM(outage_mw) AS total_mw
        FROM fact_outage_event
        WHERE outage_category LIKE 'Forced%%'
        GROUP BY reason_category
        ORDER BY events DESC
    """, conn)


@st.cache_data(ttl=86400)
def load_geojson():
    try:
        r = requests.get(INDIA_GEOJSON_URL, timeout=10)
        r.raise_for_status()
        gj = r.json()
        # normalise state names inside the GeoJSON
        for feature in gj["features"]:
            name = feature["properties"].get("NAME_1", "")
            feature["properties"]["NAME_1"] = GEOJSON_NAME_MAP.get(name, name)
        return gj
    except Exception:
        return None



def risk_badge(label: str) -> str:
    colors = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
    return f"{colors.get(label, '⚪')} {label}"


def kpi_row(scores_today: pd.DataFrame, trend: pd.DataFrame):
    high_count  = (scores_today["risk_label"] == "High").sum()
    total_mw    = trend.sort_values("report_date").iloc[-1]["forced_mw"] \
                  if not trend.empty else 0
    top_state   = scores_today.iloc[0]["state_name"] if not scores_today.empty else "—"
    avg_score   = scores_today["risk_score"].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 High-Risk States",    f"{high_count}",
              help="States scoring above 0.66 today")
    c2.metric("⚡ Forced MW (latest)",  f"{total_mw:,.0f} MW",
              help="Total forced outage capacity in latest report")
    c3.metric("📍 Highest-Risk State",  top_state,
              help="State with highest composite risk score today")
    c4.metric("📊 Avg Risk Score",      f"{avg_score:.3f}",
              help="Average composite risk score across all states today")


def page_overview():
    st.title("⚡ India Grid Reliability — National Overview")

    scores  = load_risk_scores()
    trend   = load_outage_trend()
    geojson = load_geojson()

    latest_date  = scores["score_date"].max()
    scores_today = scores[scores["score_date"] == latest_date].copy()

    st.caption(f"Latest data: **{latest_date.date()}**  |  "
               f"{len(scores_today)} states scored")

    kpi_row(scores_today, trend)
    st.divider()

    col_map, col_bar = st.columns([3, 2])

    with col_map:
        st.subheader("Risk Score by State")
        if geojson:
            fig = px.choropleth(
                scores_today,
                geojson=geojson,
                locations="state_name",
                featureidkey="properties.NAME_1",
                color="risk_score",
                color_continuous_scale=["#2a9d8f", "#f4a261", "#e63946"],
                range_color=[0, 1],
                hover_name="state_name",
                hover_data={
                    "risk_score": ":.3f",
                    "risk_label": True,
                    "score_outage": ":.3f",
                    "score_heat": ":.3f",
                    "score_rain": ":.3f",
                },
                labels={
                    "risk_score": "Risk Score",
                    "risk_label": "Label",
                    "score_outage": "Outage Component",
                    "score_heat": "Heat Component",
                    "score_rain": "Rain Component",
                },
            )
            fig.update_geos(
                fitbounds="locations", visible=False,
                bgcolor="rgba(0,0,0,0)"
            )
            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                coloraxis_colorbar=dict(title="Risk Score"),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not load India GeoJSON — showing bar chart instead.")
            fig = px.bar(
                scores_today.sort_values("risk_score", ascending=True),
                x="risk_score", y="state_name", orientation="h",
                color="risk_label",
                color_discrete_map=RISK_COLORS,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_bar:
        st.subheader("States Ranked by Risk")
        for _, row in scores_today.iterrows():
            label = str(row["risk_label"])
            col_a, col_b, col_c = st.columns([3, 1, 1])
            col_a.write(row["state_name"])
            col_b.write(risk_badge(label))
            col_c.write(f"{row['risk_score']:.3f}")

    st.divider()
    st.subheader("Forced Outage Trend — All India")

    if not trend.empty:
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=trend["report_date"], y=trend["forced_mw"],
            mode="lines+markers", name="Forced MW",
            line=dict(color="#e63946", width=2),
            fill="tozeroy", fillcolor="rgba(230,57,70,0.1)",
        ))
        fig2.update_layout(
            xaxis_title="Date", yaxis_title="Forced MW",
            hovermode="x unified",
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)


def page_state():
    st.title("🔍 State Drill-Down")

    scores  = load_risk_scores()
    states  = sorted(scores["state_name"].unique())
    state   = st.selectbox("Select a state", states, index=states.index("Uttar Pradesh"))

    state_scores  = scores[scores["state_name"] == state].sort_values("score_date")
    outage_detail = load_state_outage_detail(state)
    weather       = load_weather_for_state(state)

    latest = state_scores.iloc[-1] if not state_scores.empty else None
    if latest is not None:
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Risk Score", f"{latest['risk_score']:.3f}",
                  delta=risk_badge(str(latest["risk_label"])))
        c2.metric("Outage Component",   f"{latest['score_outage']:.3f}")
        c3.metric("Heat + Rain",
                  f"{latest['score_heat']:.3f} / {latest['score_rain']:.3f}")

    st.divider()

  
    st.subheader(f"Risk Score Trend — {state}")
    if not state_scores.empty:
        fig = px.line(
            state_scores, x="score_date", y="risk_score",
            markers=True,
            color_discrete_sequence=["#e63946"],
        )
        fig.add_hrect(y0=0.66, y1=1.0,  fillcolor="#e63946", opacity=0.08,
                      annotation_text="High")
        fig.add_hrect(y0=0.33, y1=0.66, fillcolor="#f4a261", opacity=0.08,
                      annotation_text="Medium")
        fig.add_hrect(y0=0,    y1=0.33, fillcolor="#2a9d8f", opacity=0.08,
                      annotation_text="Low")
        fig.update_layout(
            yaxis=dict(range=[0, 1]), xaxis_title="Date",
            yaxis_title="Risk Score",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=10, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Forced Outage by Category")
        if not outage_detail.empty:
            forced = outage_detail[
                outage_detail["outage_category"].str.startswith("Forced")
            ]
            if not forced.empty:
                cat_counts = (forced.groupby("reason_category")["outage_mw"]
                                    .sum().reset_index())
                fig2 = px.pie(
                    cat_counts, names="reason_category", values="outage_mw",
                    color_discrete_sequence=px.colors.qualitative.Set2,
                    hole=0.4,
                )
                fig2.update_layout(
                    margin=dict(l=0, r=0, t=10, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No forced outages recorded for this state.")

    with col_right:
        st.subheader("Temperature & Rainfall Overlay")
        if not weather.empty:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=weather["event_date"], y=weather["max_temp_c"],
                name="Max Temp (°C)", yaxis="y1",
                line=dict(color="#e63946"),
            ))
            fig3.add_trace(go.Bar(
                x=weather["event_date"], y=weather["rainfall_mm"],
                name="Rainfall (mm)", yaxis="y2",
                marker_color="#4895ef", opacity=0.5,
            ))
            fig3.update_layout(
                yaxis=dict(title="Temp °C", side="left"),
                yaxis2=dict(title="Rainfall mm", side="right",
                            overlaying="y", showgrid=False),
                hovermode="x unified",
                legend=dict(orientation="h", y=-0.2),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Station-Level Detail")
    if not outage_detail.empty:
        summary = (outage_detail[
                       outage_detail["outage_category"].str.startswith("Forced")]
                   .groupby("station_name")
                   .agg(
                       appearances=("report_date", "nunique"),
                       avg_mw=("outage_mw", "mean"),
                       top_reason=("reason_category",
                                   lambda x: x.value_counts().index[0])
                   )
                   .reset_index()
                   .sort_values("avg_mw", ascending=False))
        st.dataframe(summary, use_container_width=True, hide_index=True)



def page_scoreboard():
    st.title("📊 Risk Scoreboard")
    scores = load_risk_scores()

    dates = sorted(scores["score_date"].unique(), reverse=True)
    selected_date = st.selectbox(
        "Select date",
        dates,
        format_func=lambda d: str(d.date()),
    )

    day_scores = scores[scores["score_date"] == selected_date].copy()
    day_scores  = day_scores.sort_values("risk_score", ascending=False).reset_index(drop=True)
    day_scores["rank"] = day_scores.index + 1

    col_high, col_med, col_low = st.columns(3)
    col_high.metric("🔴 High Risk",   (day_scores["risk_label"] == "High").sum())
    col_med.metric("🟡 Medium Risk",  (day_scores["risk_label"] == "Medium").sum())
    col_low.metric("🟢 Low Risk",     (day_scores["risk_label"] == "Low").sum())

    st.divider()

    # Horizontal bar chart
    fig = px.bar(
        day_scores.sort_values("risk_score"),
        x="risk_score", y="state_name",
        orientation="h",
        color="risk_label",
        color_discrete_map=RISK_COLORS,
        text="risk_score",
        labels={"risk_score": "Risk Score", "state_name": "State",
                "risk_label": "Risk Level"},
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside")
    fig.add_vline(x=0.33, line_dash="dot", line_color="gray")
    fig.add_vline(x=0.66, line_dash="dot", line_color="gray")
    fig.update_layout(
        xaxis=dict(range=[0, 1.05]),
        showlegend=True,
        margin=dict(l=0, r=60, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=500,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Score Component Breakdown")
    display_cols = ["rank", "state_name", "risk_label",
                    "risk_score", "score_outage", "score_heat", "score_rain"]
    display = day_scores[display_cols].copy()
    display.columns = ["#", "State", "Label", "Composite", "Outage", "Heat", "Rain"]

    def color_label(val):
        colors = {"High": "background-color:#ffd6d6",
                  "Medium": "background-color:#fff3cd",
                  "Low": "background-color:#d4edda"}
        return colors.get(val, "")

    styled = display.style\
        .map(color_label, subset=["Label"])\
        .format({"Composite": "{:.3f}", "Outage": "{:.3f}",
                 "Heat": "{:.3f}", "Rain": "{:.3f}"})
    st.dataframe(styled, use_container_width=True, hide_index=True)

    # All-time trend heatmap
    st.subheader("Risk Score Heatmap — All Dates")
    pivot = scores.pivot_table(
        index="state_name", columns="score_date",
        values="risk_score", aggfunc="mean"
    )
    pivot.columns = [str(c.date()) for c in pivot.columns]

    fig2 = px.imshow(
        pivot,
        color_continuous_scale=["#2a9d8f", "#f4a261", "#e63946"],
        zmin=0, zmax=1,
        aspect="auto",
        labels={"color": "Risk Score"},
    )
    fig2.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        height=500,
        xaxis_title="", yaxis_title="",
    )
    st.plotly_chart(fig2, use_container_width=True)



def page_methodology():
    st.title("📋 Methodology & Findings")

    st.subheader("What this tool does")
    st.write("""
    This tracker monitors India's thermal and nuclear grid reliability by
    combining daily outage data from CEA's reports with weather observations
    from the Open-Meteo API. It produces a composite risk score for each
    state, updated each time new report data is loaded.
    """)

    st.subheader("Data Sources")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Outage Data**
        - Source: CEA Daily Maintenance Report (Sub-Report 10)
        - Portal: npp.gov.in/publishedReports
        - Frequency: Daily (manually downloaded; site disallows automation)
        - Coverage: Thermal and nuclear units ≥ 25 MW
        """)
    with col2:
        st.markdown("""
        **Weather Data**
        - Source: Open-Meteo Historical Weather API
        - Endpoint: archive-api.open-meteo.com
        - Frequency: Automated daily fetch
        - Metrics: Max temperature, min temperature, rainfall (mm)
        """)

    st.subheader("Risk Score Formula")
    st.latex(r"""
    \text{Risk Score} =
    0.50 \times \text{Outage Load} +
    0.30 \times \text{Heat Stress} +
    0.20 \times \text{Rain Stress}
    """)
    st.markdown("""
    Each component is normalised to [0, 1] across all state-days in the
    loaded data. A higher value means a worse-than-average condition
    relative to the observed historical range.

    | Component | Definition |
    |---|---|
    | Outage Load | Forced MW ÷ Total MW under maintenance |
    | Heat Stress | Max daily temperature (capped at 45°C) |
    | Rain Stress | Daily rainfall in mm (capped at 100 mm) |
    """)

    st.subheader("Key Finding — Chronic Outage Entries")
    st.info("""
    **Finding:** India's daily CEA maintenance report tracks all *currently
    open* outages — not just new ones. This means units that have been
    offline for years (some since 2004) appear in every single daily report
    with identical MW values. This "chronic outage stock" accounts for 85%+
    of entries and means outage *counts* do not vary meaningfully between
    dates. As a result, the risk model was redesigned from a supervised ML
    approach to a transparent rule-based scoring system, which is more
    appropriate for this data structure and is standard in operational risk
    contexts (grid operations, credit risk, infrastructure monitoring).

    This is documented here rather than hidden — understanding the shape
    of your data is as important as the analysis itself.
    """)

    st.subheader("Limitations")
    st.warning("""
    - **No real-time discom data:** Individual state electricity distribution
      companies (discoms) do not expose public APIs for local outage events.
      This tool uses CEA's central monitoring data, which covers inter-state
      and large-capacity units only.
    - **State-capital coordinates:** Weather data uses each state capital's
      coordinates as a proxy for the whole state. Sub-state variation
      (e.g., coastal vs inland Andhra Pradesh) is not captured.
    - **Small backfill window:** Risk scores are normalised within the loaded
      date range. A longer history (12+ months) would produce more stable
      and meaningful scores.
    - **Risk score ≠ outage prediction:** The composite score indicates
      relative stress conditions, not a deterministic forecast of outages.
    """)

    st.subheader("Tech Stack")
    st.code("""
Python       — ETL pipeline, feature engineering, risk scoring
PostgreSQL   — Supabase-hosted database (schema: dim + fact tables)
Open-Meteo   — Weather API (automated daily fetch)
Streamlit    — This interactive dashboard
Power BI     — Static trend report (see portfolio)
    """, language="text")



def main():
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/"
                 "Flag_of_India.svg/320px-Flag_of_India.svg.png", width=80)
        st.title("Grid Tracker")
        st.caption("India Power Outage & Reliability Tracker")
        st.divider()
        page = st.radio(
            "Navigate",
            ["🗺️ National Overview",
             "🔍 State Drill-Down",
             "📊 Risk Scoreboard",
             "📋 Methodology"],
        )
        st.divider()
        st.caption("Data: CEA + Open-Meteo  |  Built with Python & Streamlit")

    if page == "🗺️ National Overview":
        page_overview()
    elif page == "🔍 State Drill-Down":
        page_state()
    elif page == "📊 Risk Scoreboard":
        page_scoreboard()
    elif page == "📋 Methodology":
        page_methodology()


if __name__ == "__main__":
    main()