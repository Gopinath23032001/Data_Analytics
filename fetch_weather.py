import os
import sys

import psycopg2
import psycopg2.extras
import requests

STATE_COORDS = {
    'Jammu and Kashmir': (34.0837, 74.7973),
    'Ladakh': (34.1526, 77.5771),
    'Himachal Pradesh': (31.1048, 77.1734),
    'Punjab': (30.7333, 76.7794),
    'Haryana': (30.7333, 76.7794),
    'Delhi': (28.6139, 77.2090),
    'Uttarakhand': (30.3165, 78.0322),
    'Uttar Pradesh': (26.8467, 80.9462),
    'Chandigarh': (30.7333, 76.7794),
    'Rajasthan': (26.9124, 75.7873),
    'Gujarat': (23.2156, 72.6369),
    'Maharashtra': (19.0760, 72.8777),
    'Goa': (15.4909, 73.8278),
    'Dadra and Nagar Haveli and Daman and Diu': (20.3974, 72.8328),
    'Karnataka': (12.9716, 77.5946),
    'Kerala': (8.5241, 76.9366),
    'Tamil Nadu': (13.0827, 80.2707),
    'Andhra Pradesh': (16.5062, 80.6480),
    'Telangana': (17.3850, 78.4867),
    'Puducherry': (11.9416, 79.8083),
    'Lakshadweep': (10.5593, 72.6358),
    'Andaman and Nicobar Islands': (11.6234, 92.7265),
    'West Bengal': (22.5726, 88.3639),
    'Odisha': (20.2961, 85.8245),
    'Bihar': (25.5941, 85.1376),
    'Jharkhand': (23.3441, 85.3096),
    'Madhya Pradesh': (23.2599, 77.4126),
    'Chhattisgarh': (21.2514, 81.6296),
    'Assam': (26.1445, 91.7362),
    'Arunachal Pradesh': (27.0844, 93.6053),
    'Manipur': (24.8170, 93.9368),
    'Meghalaya': (25.5788, 91.8933),
    'Mizoram': (23.7271, 92.7176),
    'Nagaland': (25.6751, 94.1086),
    'Sikkim': (27.3389, 88.6065),
    'Tripura': (23.8315, 91.2868),
}

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_state_weather(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "Asia/Kolkata",
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()["daily"]


def load_weather(start_date: str, end_date: str, database_url: str):
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    cur.execute("SELECT state_id, state_name FROM dim_state;")
    state_lookup = {name: sid for sid, name in cur.fetchall()}

    total_rows = 0
    for state_name, (lat, lon) in STATE_COORDS.items():
        state_id = state_lookup.get(state_name)
        if state_id is None:
            print(f"WARNING: '{state_name}' not found in dim_state, skipping")
            continue

        try:
            daily = fetch_state_weather(lat, lon, start_date, end_date)
        except requests.RequestException as e:
            print(f"FAILED to fetch weather for {state_name}: {e}")
            continue

        records = []
        for i, date in enumerate(daily["time"]):
            tmax = daily["temperature_2m_max"][i]
            tmin = daily["temperature_2m_min"][i]
            rain = daily["precipitation_sum"][i]
            records.append((state_id, 'DailyObservation', date, None, tmax, rain, 'OpenMeteo'))

        psycopg2.extras.execute_values(
            cur,
            """INSERT INTO fact_weather_event
               (state_id, event_type, event_date, severity, max_temp_c, rainfall_mm, source)
               VALUES %s
               ON CONFLICT DO NOTHING""",
            records
        )
        conn.commit()
        total_rows += len(records)
        print(f"{state_name}: loaded {len(records)} days")

    print(f"\nTotal weather rows loaded: {total_rows}")
    cur.close()
    conn.close()


if __name__ == '__main__':
    start_date, end_date = sys.argv[1], sys.argv[2]
    db_url = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost/power_outage_tracker'
    )
    load_weather(start_date, end_date, db_url)