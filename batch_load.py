import glob
import os
import sys

from load_report10 import load, get_report_date


def batch_load(folder: str, database_url: str):
    files = sorted(
        glob.glob(os.path.join(folder, 'dgr10-*.xls')),
        key=lambda f: get_report_date(f)
    )

    if not files:
        print(f"No dgr10-*.xls files found in {folder}")
        return

    print(f"Found {len(files)} files to load\n")

    results = []
    for filepath in files:
        report_date = get_report_date(filepath)
        try:
            load(filepath, database_url)
            results.append((report_date, 'OK', None))
        except Exception as e:
            print(f"FAILED on {os.path.basename(filepath)}: {e}")
            results.append((report_date, 'FAILED', str(e)))
        print('-' * 50)

    print("\n=== Batch Summary ===")
    ok_count = sum(1 for _, status, _ in results if status == 'OK')
    print(f"Loaded successfully: {ok_count}/{len(results)}")
    for date, status, err in results:
        if status == 'FAILED':
            print(f"  FAILED: {date} — {err}")


if __name__ == '__main__':
    folder = sys.argv[1] if len(sys.argv) > 1 else '.'
    db_url = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost/power_outage_tracker'
    )
    batch_load(folder, db_url)