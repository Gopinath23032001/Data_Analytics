import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import psycopg2
import psycopg2.extras

DB_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:postgres@localhost/power_outage_tracker'
)

def load_data(conn):
    outage_q = """
        SELECT oe.state_id, s.state_name, s.region,
               oe.report_date AS date,
               oe.outage_category, oe.outage_mw
        FROM fact_outage_event oe
        JOIN dim_state s ON s.state_id = oe.state_id
        ORDER BY oe.report_date, oe.state_id
    """
    weather_q = """
        SELECT state_id, event_date AS date, max_temp_c, rainfall_mm
        FROM fact_weather_event
        WHERE source = 'OpenMeteo'
        ORDER BY event_date, state_id
    """
    df_o = pd.read_sql(outage_q, conn, parse_dates=['date'])
    df_w = pd.read_sql(weather_q, conn, parse_dates=['date'])
    return df_o, df_w

def aggregate(df_o):
    agg = (df_o.groupby(['state_id', 'state_name', 'region', 'date'])
               .agg(
                   total_mw=('outage_mw', 'sum'),
                   forced_mw=('outage_mw',
                               lambda x: x[df_o.loc[x.index, 'outage_category']
                                            .str.startswith('Forced')].sum()),
               )
               .reset_index())
    agg['forced_pct'] = (agg['forced_mw'] / agg['total_mw'].replace(0, np.nan)).fillna(0)
    return agg.sort_values(['state_id', 'date'])

def normalise(series):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)

def compute_risk(df):
    df = df.copy()
    df['score_outage'] = normalise(df['forced_pct'])
    df['temp_capped']  = df['max_temp_c'].clip(upper=45)
    df['score_heat']   = normalise(df['temp_capped'].fillna(df['temp_capped'].median()))
    df['rain_capped']  = df['rainfall_mm'].clip(upper=100)
    df['score_rain']   = normalise(df['rain_capped'].fillna(0))
    df['risk_score']   = (
        0.50 * df['score_outage'] +
        0.30 * df['score_heat']   +
        0.20 * df['score_rain']
    ).round(4)
    df['risk_label'] = pd.cut(
        df['risk_score'],
        bins=[0, 0.33, 0.66, 1.01],
        labels=['Low', 'Medium', 'High'],
        include_lowest=True
    )
    return df

def save_scores(df, conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS fact_risk_scores (
            state_id      INT REFERENCES dim_state(state_id),
            score_date    DATE NOT NULL,
            risk_score    NUMERIC(5,4),
            risk_label    VARCHAR(10),
            score_outage  NUMERIC(5,4),
            score_heat    NUMERIC(5,4),
            score_rain    NUMERIC(5,4),
            model_version VARCHAR(30) DEFAULT 'v1-rule-based',
            scored_at     TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (state_id, score_date)
        )
    """)
    records = [
        (int(r.state_id), r.date.date(),
         float(r.risk_score), str(r.risk_label),
         float(r.score_outage), float(r.score_heat), float(r.score_rain))
        for r in df.itertuples()
        if pd.notna(r.risk_score)
    ]
    psycopg2.extras.execute_values(
        cur,
        """INSERT INTO fact_risk_scores
           (state_id, score_date, risk_score, risk_label,
            score_outage, score_heat, score_rain)
           VALUES %s
           ON CONFLICT (state_id, score_date) DO UPDATE SET
               risk_score   = EXCLUDED.risk_score,
               risk_label   = EXCLUDED.risk_label,
               score_outage = EXCLUDED.score_outage,
               score_heat   = EXCLUDED.score_heat,
               score_rain   = EXCLUDED.score_rain,
               scored_at    = NOW()""",
        records
    )
    conn.commit()
    cur.close()
    print(f"Saved {len(records)} risk scores to fact_risk_scores")

def print_report(df):
    latest = df['date'].max()
    today  = df[df['date'] == latest].sort_values('risk_score', ascending=False)
    print(f"\n{'='*60}")
    print(f" OUTAGE RISK REPORT — {latest.date()}")
    print(f"{'='*60}")
    print(f"{'State':<30} {'Score':>6}  {'Label':<8} {'Outage%':>8} {'Temp C':>7} {'Rain mm':>8}")
    print('-' * 75)
    for r in today.itertuples():
        temp  = f"{r.max_temp_c:.1f}" if pd.notna(r.max_temp_c) else "N/A"
        rain  = f"{r.rainfall_mm:.1f}" if pd.notna(r.rainfall_mm) else "N/A"
        print(f"{r.state_name:<30} {r.risk_score:>6.3f}  {str(r.risk_label):<8} "
              f"{r.forced_pct:>7.1%} {temp:>7} {rain:>8}")
    print(f"\n── Label breakdown ──")
    print(today['risk_label'].value_counts().to_string())
    print(f"\n── Top 5 highest-risk states ──")
    for r in today.head(5).itertuples():
        print(f"  {r.state_name}: {r.risk_score:.3f} ({r.risk_label})")
    print(f"\n── Score weights ──")
    print("  50% Outage load  (forced MW as % of total MW under maintenance)")
    print("  30% Heat stress  (normalised max temp, capped at 45C)")
    print("  20% Rain stress  (normalised rainfall, capped at 100mm)")

def main():
    conn = psycopg2.connect(DB_URL)
    print("Connected to database.")
    df_o, df_w = load_data(conn)
    print(f"Loaded {len(df_o)} outage rows across {df_o['date'].nunique()} dates, "
          f"{df_o['state_id'].nunique()} states")
    print(f"Loaded {len(df_w)} weather rows across {df_w['date'].nunique()} dates")
    agg    = aggregate(df_o)
    joined = pd.merge(agg, df_w, on=['state_id', 'date'], how='left')
    scored = compute_risk(joined)
    print_report(scored)
    save_scores(scored, conn)
    conn.close()

if __name__ == '__main__':
    main()