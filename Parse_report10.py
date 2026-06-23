"""
Phase 2 proof-of-concept extractor for NPP Sub-Report-10:
'Daily Maintenance Report (Coal, Lignite and Nuclear)'

Input:  raw .xls file as downloaded from npp.gov.in
Output: clean DataFrame matching the fact_outage_event schema
"""
import pandas as pd
import re

REGIONS = {'Northern', 'Western', 'Southern', 'Eastern', 'North Eastern', 'NorthEastern'}
SKIP_PREFIXES = ('Total', 'Note', 'Report Version')
SKIP_EXACT = {'State/System', '1'}

REASON_MAP = {
    'Mechanical': ['fan', 'bearing', 'turbine', 'boiler', 'tube lkg', 'tube leak', 'drum', 'water wall'],
    'Electrical': ['electrical', 'generator', 'transformer', 'h.t.', 'l.t.', 'c&i', 'earth fault'],
    'Fuel':       ['fuel', 'coal', 'gas supply', 'linkage', 'ash handling', 'coal feeding'],
    'Grid/Other': ['grid', 'frequency', 'merit order', 'scrapped', 'rsd', 'reserve shut down',
                   'standby', 'overhauling', 'annual maintenance', 'instrument air'],
}

def categorize(reason_text: str) -> str:
    text = (reason_text or '').lower()
    for category, keywords in REASON_MAP.items():
        if any(k in text for k in keywords):
            return category
    return 'Unknown'

def derive_outage_category(row) -> tuple[str, float]:
    """Return (outage_category, outage_mw) from the four MW columns."""
    options = [
        ('Planned', row['planned_mw']),
        ('Forced-Major', row['forced_major_mw']),
        ('Forced-Minor', row['forced_minor_mw']),
        ('Other', row['others_mw']),
    ]
    # pick whichever column is non-zero (reports use one active column per row)
    for category, mw in options:
        if pd.notna(mw) and mw != 0:
            return category, float(mw)
    return 'Unknown', 0.0

def parse_report10(filepath: str) -> pd.DataFrame:
    raw = pd.read_excel(r'C:\Users\Lucky Dell\Desktop\Data Analytics\Portfolio gopi\swiggy\power-outage-tracker\dgr10-2026-06-18.xls', sheet_name=0, header=None)

    records = []
    current_region = None

    for _, row in raw.iterrows():
        col0 = row[0]
        station = row[2]

        if pd.isna(col0):
            continue
        col0_str = str(col0).strip()

        if col0_str in REGIONS:
            current_region = col0_str
            continue
        if col0_str.startswith(SKIP_PREFIXES) or col0_str in SKIP_EXACT:
            continue
        if pd.isna(station):
            continue

        records.append({
            'region': current_region,
            'state': col0_str,
            'station_name': str(station).strip(),
            'unit_no': row[3],
            'planned_mw': row[4],
            'forced_major_mw': row[5],
            'forced_minor_mw': row[6],
            'others_mw': row[7],
            'maint_start_raw': row[8],
            'expected_return_raw': row[9],
            'reason_raw': row[10],
        })

    df = pd.DataFrame(records)

    # derive outage_category + outage_mw
    df[['outage_category', 'outage_mw']] = df.apply(
        lambda r: pd.Series(derive_outage_category(r)), axis=1
    )

    # parse timestamps (format: DD/MM/YYYY HH24:MM)
    df['start_ts'] = pd.to_datetime(df['maint_start_raw'], format='%d/%m/%Y %H:%M', errors='coerce')
    df['expected_return_ts'] = pd.to_datetime(df['expected_return_raw'], format='%d/%m/%Y %H:%M', errors='coerce')

    # categorize reason text
    df['reason_category'] = df['reason_raw'].apply(categorize)

    final_cols = [
        'region', 'state', 'station_name', 'unit_no', 'outage_category', 'outage_mw',
        'start_ts', 'expected_return_ts', 'reason_raw', 'reason_category'
    ]
    return df[final_cols]


if __name__ == '__main__':
    import sys
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'dgr10-2026-06-18.xls'
    result = parse_report10(filepath)
    print(f"Extracted {len(result)} outage events\n")
    print(result.head(20).to_string())
    print(f"\nReason category breakdown:\n{result['reason_category'].value_counts()}")
    print(f"\nOutage category breakdown:\n{result['outage_category'].value_counts()}")