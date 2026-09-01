#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Re-replace and re-run the 3 still-empty entries (34, 37, 149).
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
TARGET_IDS = {34, 37, 149}


def convert_value(val):
    if isinstance(val, Decimal):
        return float(val) if val % 1 != 0 else int(val)
    if isinstance(val, bytes):
        return val.decode('utf-8', errors='replace')
    if isinstance(val, datetime):
        return val.isoformat()
    return val


def main():
    print(f"[{datetime.now()}] Loading files...")
    with open(RESULT_FILE, 'r', encoding='utf-8') as f:
        result_data = json.load(f)
    with open(COPY_FILE, 'r', encoding='utf-8') as f:
        copy_data = json.load(f)

    copy_lookup = {e['sample_id']: e for e in copy_data}

    # ---- Step 1: Replace ----
    print(f"[{datetime.now()}] Replacing entries {list(TARGET_IDS)} from copy file...")
    for i, entry in enumerate(result_data):
        sid = entry['sample_id']
        if sid in TARGET_IDS and sid in copy_lookup:
            ce = copy_lookup[sid]
            old_nl = entry['natural_language']
            old_sql = entry['sql']
            entry['sql'] = ce['sql']
            entry['natural_language'] = ce['natural_language']
            if 'result_data' in ce:
                entry['result_data'] = ce['result_data']
            entry['result'] = []
            print(f"  sample_id={sid}")
            print(f"    OLD NL: {old_nl[:80]}...")
            print(f"    NEW NL: {ce['natural_language'][:80]}...")

    # ---- Step 2: Re-run ----
    print(f"[{datetime.now()}] Connecting to MySQL...")
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    for entry in result_data:
        sid = entry['sample_id']
        if sid not in TARGET_IDS:
            continue
        sql = entry['sql']
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
            status = f"{len(result)} rows" if result else "EMPTY"
            print(f"  sample_id={sid}: {status}")
        except Exception as e:
            print(f"  sample_id={sid}: SQL ERROR: {e}")

    cursor.close()
    conn.close()

    # ---- Step 3: Save ----
    print(f"[{datetime.now()}] Saving...")
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    # Final check
    empty_left = [e['sample_id'] for e in result_data if not e['result']]
    print(f"\n=== DONE ===")
    print(f"Still empty: {empty_left}")
    print(f"Output: {RESULT_FILE}")


if __name__ == '__main__':
    main()
