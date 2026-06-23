import os
import re
import sys
from datetime import datetime

import pandas as pd
import psycopg2
import psycopg2.extras

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Parse_report10 import parse_report10

STATE_NAME_FIXES = {
    'Chhatisgarh': 'Chhattisgarh',
}


def get_report_date(filepath: str) -> datetime.date:
    """Extract YYYY-MM-DD from a filename like dgr10-2026-06-18.xls."""
    match = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(filepath))
    if not match:
        raise ValueError(f"Could not find a date in filename: {filepath}")
    return datetime.strptime(match.group(1), '%Y-%m-%d').date()


def load(filepath: str, database_url: str):
    df = parse_report10(filepath)
    report_date = get_report_date(filepath)
    df['state'] = df['state'].replace(STATE_NAME_FIXES)

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    cur.execute("SELECT state_id, state_name FROM dim_state;")
    state_lookup = {name: sid for sid, name in cur.fetchall()}

    unmatched_states = set(df['state'].unique()) - set(state_lookup.keys())
    if unmatched_states:
        print(f"WARNING: {len(unmatched_states)} state name(s) did not match dim_state, "
              f"skipping their rows: {unmatched_states}")
        print("Add these to STATE_NAME_FIXES once you confirm the correct spelling.")
        df = df[~df['state'].isin(unmatched_states)]

    df['state_id'] = df['state'].map(state_lookup)


    stations = df[['station_name', 'state_id']].drop_duplicates()
    station_records = list(stations.itertuples(index=False, name=None))
    psycopg2.extras.execute_values(
        cur,
        """INSERT INTO dim_station (station_name, state_id)
           VALUES %s
           ON CONFLICT (station_name, state_id) DO NOTHING""",
        station_records
    )

    cur.execute("SELECT station_id, station_name, state_id FROM dim_station;")
    station_lookup = {(name, sid): pid for pid, name, sid in cur.fetchall()}
    df['station_id'] = df.apply(
        lambda r: station_lookup.get((r['station_name'], r['state_id'])), axis=1
    )

    def none_if_na(val):
        return None if pd.isna(val) else val

    event_records = [
        (
            row.station_id, row.state_id, row.unit_no, row.outage_category,
            row.outage_mw, row.start_ts, none_if_na(row.expected_return_ts),
            row.reason_raw, row.reason_category, report_date
        )
        for row in df.itertuples(index=False)
        if row.station_id is not None and pd.notna(row.start_ts)
    ]

    psycopg2.extras.execute_values(
        cur,
        """INSERT INTO fact_outage_event
           (station_id, state_id, unit_no, outage_category, outage_mw,
            start_ts, expected_return_ts, reason_raw, reason_category, report_date)
           VALUES %s
           ON CONFLICT (station_id, unit_no, start_ts, report_date)
            DO UPDATE SET
           expected_return_ts = EXCLUDED.expected_return_ts""",
        event_records
    )

    conn.commit()
    print(f"Loaded {len(event_records)} events for report_date={report_date}")
    print(f"({len(df) - len(event_records)} rows skipped — missing station_id or start_ts)")

    cur.close()
    conn.close()


if __name__ == '__main__':
    filepath = sys.argv[1]
    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/power_outage_tracker')
    load(filepath, db_url)