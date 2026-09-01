#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1. Replace 39 empty-result entries in result file with entries from copy file
2. Re-run those 39 SQL queries against MySQL
3. Update the result file with actual results
Only modifies: sql_nl_test_samples_500(7)_replaced_result.json
"""

import json
import pymysql
from datetime import datetime
from decimal import Decimal

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'smart_small',
    'charset': 'utf8mb4',
}

RESULT_FILE = '评测集修改/500/sql_nl_test_samples_500(7)_replaced_result.json'
COPY_FILE = '评测集修改/500/sql_nl_test_samples_500(7)_replaced copy.json'

# IDs with empty results from the first run
EMPTY_IDS = [34, 35, 37, 39, 90, 92, 137, 141, 145, 149, 153, 157, 160, 164,
             172, 175, 176, 180, 184, 256, 257, 260, 264, 306, 313, 338, 352,
             356, 360, 361, 403, 441, 443, 445, 451, 457, 458, 475, 497]
EMPTY_SET = set(EMPTY_IDS)


def convert_value(val):
    """Convert MySQL types to JSON-serializable Python types."""
    if isinstance(val, Decimal):
        return float(val) if val % 1 != 0 else int(val)
    if isinstance(val, bytes):
        return val.decode('utf-8', errors='replace')
    if isinstance(val, datetime):
        return val.isoformat()
    return val


def main():
    # ---- Step 1: Load both files ----
    print(f"[{datetime.now()}] Step 1: Loading files...")
    with open(RESULT_FILE, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    with open(COPY_FILE, 'r', encoding='utf-8') as f:
        copy_data = json.load(f)

    # Build lookup from copy file by sample_id
    copy_lookup = {e['sample_id']: e for e in copy_data}
    print(f"  Result file: {len(result_data)} entries")
    print(f"  Copy file: {len(copy_data)} entries")

    # ---- Step 2: Replace empty entries with copy file entries ----
    print(f"[{datetime.now()}] Step 2: Replacing {len(EMPTY_IDS)} empty entries from copy file...")
    replaced_count = 0
    for i, entry in enumerate(result_data):
        sid = entry['sample_id']
        if sid in EMPTY_SET and sid in copy_lookup:
            # Replace sql and natural_language from copy file
            copy_entry = copy_lookup[sid]
            entry['sql'] = copy_entry['sql']
            entry['natural_language'] = copy_entry['natural_language']
            # Also replace result_data if present in copy
            if 'result_data' in copy_entry:
                entry['result_data'] = copy_entry['result_data']
            # Keep result as empty for now - will be filled by SQL execution
            entry['result'] = []
            replaced_count += 1
            print(f"  Replaced sample_id={sid}: {entry['natural_language'][:60]}...")

    print(f"  Total replaced: {replaced_count}")

    # Save intermediate result
    print(f"[{datetime.now()}] Saving intermediate result file...")
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    print(f"  Intermediate file saved.")

    # ---- Step 3: Re-run the 39 SQL queries ----
    print(f"[{datetime.now()}] Step 3: Connecting to MySQL and re-running {len(EMPTY_IDS)} queries...")
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    print(f"  Connected successfully.")

    success = 0
    errors = 0
    still_empty = 0

    try:
        for i, entry in enumerate(result_data):
            sid = entry['sample_id']
            if sid not in EMPTY_SET:
                continue

            sql = entry.get('sql', '')
            if not sql:
                print(f"  sample_id={sid}: SKIP (empty SQL)")
                errors += 1
                continue

            try:
                cursor.execute(sql)
                rows = cursor.fetchall()

                if rows:
                    if len(rows[0]) == 1:
                        result = [convert_value(row[0]) for row in rows]
                    else:
                        result = [[convert_value(v) for v in row] for row in rows]
                else:
                    result = []

                entry['result'] = result
                success += 1
                if not result:
                    still_empty += 1
                    print(f"  sample_id={sid}: EMPTY result | {entry['natural_language'][:50]}...")
                else:
                    print(f"  sample_id={sid}: {len(result)} rows | {entry['natural_language'][:50]}...")

            except Exception as e:
                print(f"  sample_id={sid}: SQL ERROR: {e}")
                errors += 1

    finally:
        cursor.close()
        conn.close()
        print(f"  MySQL connection closed.")

    # ---- Step 4: Save final result ----
    print(f"[{datetime.now()}] Step 4: Saving final result file...")
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    print(f"\n=== SUMMARY ===")
    print(f"Replaced entries: {replaced_count}")
    print(f"Re-run successful: {success}")
    print(f"Re-run errors: {errors}")
    print(f"Still empty after re-run: {still_empty}")
    print(f"Output: {RESULT_FILE}")


if __name__ == '__main__':
    main()
