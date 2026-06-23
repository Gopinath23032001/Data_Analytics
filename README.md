# ⚡ India Power Outage Pattern & Grid Reliability Tracker

A full-stack data analytics project that monitors India's thermal and nuclear
grid reliability by combining daily CEA outage reports with real-time weather
data, producing a composite risk score per state updated with each new report.

---

## The Problem

India's electricity distribution companies (discoms) do not publish outage data
publicly. Residents, businesses, and researchers have no systematic way to
understand which states are chronically unreliable or what conditions drive
grid stress. This project builds that visibility from publicly available
central-level data.

---

## What It Does

| Layer | Tool | What it produces |
|---|---|---|
| Data extraction | Python + xlrd | Parses CEA Sub-Report 10 (XLS) into structured records |
| Storage | PostgreSQL (Supabase) | Normalized star schema — dim/fact tables |
| Weather enrichment | Open-Meteo API | Daily max temp + rainfall per state |
| Analysis | SQL (PostgreSQL) | Correlation, ranking, trend, root-cause queries |
| Risk scoring | Python (rule-based) | Composite outage risk score per state per day |
| Dashboard | Streamlit + Plotly | 4-page interactive app with live DB connection |
| Report | Power BI | Static trend and root-cause report |

---

## The Problem

Live Dashboard Link : https://gopinath-ipop.streamlit.app/

## Key Findings

**1. Uttar Pradesh and Bihar carry the highest outage risk**
On the latest report date, UP scored 0.720 (High) and Bihar 0.700 (High),
driven by 100% forced-outage load ratios combined with temperatures above 38°C.

**2. Temperature correlates positively with outage severity**
States with max temperatures above 40°C averaged significantly higher forced
outage MW than cooler states on the same date — consistent with the known
mechanism of cooling-system stress in thermal plants during heatwaves.

**3. India's grid always has some units under forced outage**
The CEA daily report tracks all *currently open* outages, not just new ones.
85%+ of entries are chronic outages (units offline for months or years) with
identical MW values across dates. This is a real data-quality finding, not a
pipeline error — and it drove the decision to use rule-based risk scoring
rather than supervised ML (see Methodology section).

**4. Mechanical failures dominate forced outages**
Root-cause breakdown from reason-text categorisation:
Mechanical (38%) > Grid/Other (26%) > Fuel (15%) > Electrical (6%) > Unknown (16%)

---

## Architecture

```
npp.gov.in (manual download)          Open-Meteo API (automated)
        │                                      │
        ▼                                      ▼
 parse_report10.py                    fetch_weather.py
        │                                      │
        └──────────────┬────────────────────────┘
                       ▼
              load_report10.py / batch_load.py
                       │
                       ▼
         PostgreSQL on Supabase
         ┌─────────────────────────────┐
         │  dim_state  dim_station     │
         │  fact_outage_event          │
         │  fact_weather_event         │
         │  fact_risk_scores           │
         └─────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
   risk_model.py              Streamlit App
   (rule-based scorer)        (4 pages)
                                    │
                              Power BI Report
```

---

## Database Schema

```sql
dim_state        — 36 states/UTs with region classification
dim_station      — 82 power stations (auto-populated from reports)
fact_outage_event  — unit-level daily outage records (station, MW, reason, timestamps)
fact_weather_event — daily weather per state (temp, rainfall, source)
fact_risk_scores   — composite risk score per state per day
v_outage_duration  — view: computed outage duration in hours
```

---

## Risk Score Formula

```
Risk Score = 0.50 × Outage Load + 0.30 × Heat Stress + 0.20 × Rain Stress
```

| Component | Definition |
|---|---|
| Outage Load | Forced MW ÷ Total MW under maintenance (normalised 0–1) |
| Heat Stress | Max daily temperature, capped at 45°C (normalised 0–1) |
| Rain Stress | Daily rainfall in mm, capped at 100 mm (normalised 0–1) |

Labels: High (>0.66) / Medium (0.33–0.66) / Low (<0.33)

---

## Methodology & Honest Caveats

**Why rule-based scoring instead of ML:**
Supervised ML requires a target variable with meaningful class variation.
The CEA report's cumulative tracking of all open outages (including units
offline since 2004) makes forced-event counts essentially constant per state
across dates — producing 100% positive rate for any binary target. Rule-based
scoring is more appropriate here and is standard in operational risk contexts.

**Why manual download for CEA reports:**
npp.gov.in's robots.txt explicitly disallows automated access. Reports are
downloaded manually 2–3 times per week. Open-Meteo (which explicitly supports
programmatic use) is fetched automatically.

**State-capital coordinates:**
Weather data uses each state capital's coordinates as a proxy. Sub-state
variation is not captured in v1.

**Coverage:**
This tool covers inter-state and large-capacity thermal/nuclear units (≥25 MW)
monitored by CEA. Local distribution-level outages (discoms) are not included
as no public API exists for this data.

---

## Tech Stack

```
Python 3.12       pandas, psycopg2-binary, xlrd, requests, scikit-learn
PostgreSQL 16     Supabase (free tier)
Streamlit         Plotly, deployed on Streamlit Community Cloud
Power BI Desktop  Direct PostgreSQL connection
Open-Meteo API    Historical weather archive (free, no key required)
```

---

## Project Structure

```
power-outage-tracker/
├── extract/
│   ├── parse_report10.py     # XLS → DataFrame extractor
│   ├── load_report10.py      # DataFrame → PostgreSQL loader
│   ├── batch_load.py         # Multi-file batch loader
│   ├── fetch_weather.py      # Open-Meteo API → PostgreSQL
│   └── risk_model.py         # Rule-based risk scorer
├── sql/
│   ├── 01_schema.sql         # Table definitions
│   ├── 02_seed_states.sql    # 36 states/UTs seed data
│   ├── 03_add_constraints.sql
│   ├── 04_weather_constraints.sql
│   └── 05_analysis.sql       # Core analysis queries
├── streamlit_app/
│   ├── app.py                # 4-page Streamlit dashboard
│   └── requirements.txt
└── data/                     # Downloaded XLS files (gitignored)
```

---

## Setup

```bash
# 1. Clone and create environment
git clone https://github.com/yourusername/power-outage-tracker
cd power-outage-tracker
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -r streamlit_app/requirements.txt

# 2. Set up database
# Run sql/01_schema.sql through 04_weather_constraints.sql in Supabase SQL Editor

# 3. Load data
DATABASE_URL="your-connection-string" python extract/batch_load.py data/
DATABASE_URL="your-connection-string" python extract/fetch_weather.py 2026-05-01 2026-06-22
DATABASE_URL="your-connection-string" python extract/risk_model.py

# 4. Run dashboard
set DATABASE_URL=your-connection-string
streamlit run streamlit_app/app.py
```

---

## Author

**Gopinath Arumugam** — Data Analytics Professional, Tamil Nadu
[LinkedIn](https://www.linkedin.com/in/gopinath-mdu/) |
[Portfolio](https://gopinatharumugam.netlify.app)
