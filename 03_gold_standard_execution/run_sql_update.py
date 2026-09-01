#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Execute SQL queries from sql_nl_test_samples_500(7)_replaced.json
against MySQL and update the 'result' field with actual query results.
"""

import json
import sys
import pymysql
from datetime import datetime
from decimal import Decimal


def convert_value(val):
    """Convert MySQL types to JSON-serializable Python types."""
    if isinstance(val, Decimal):
        return float(val) if val % 1 != 0 else int(val)
    if isinstance(val, bytes):
        return val.decode('utf-8', errors='replace')
    if isinstance(val, datetime):
        return val.isoformat()
    return val


MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'smart_small',
    'charset': 'utf8mb4',
}

INPUT_FILE = '评测集修改/500/sql_nl_test_samples_500(7)_replaced.json'
OUTPUT_FILE = '评测集修改/500/sql_nl_test_samples_500(7)_replaced_result.json'


def main():
    # Load JSON data
    print(f"[{datetime.now()}] Loading: {INPUT_FILE}")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"[{datetime.now()}] Total entries: {len(data)}")

    # Connect to MySQL
    print(f"[{datetime.now()}] Connecting to MySQL...")
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print(f"[{datetime.now()}] Connected successfully.")
    except Exception as e:
        print(f"ERROR: Failed to connect to MySQL: {e}")
        sys.exit(1)

    success_count = 0
    error_count = 0
    empty_count = 0

    try:
        for i, entry in enumerate(data):
            sample_id = entry.get('sample_id', i + 1)
            sql = entry.get('sql', '')

            if not sql:
                print(f"[{i+1}/{len(data)}] sample_id={sample_id}: SKIP (empty SQL)")
                error_count += 1
                continue

            try:
                cursor.execute(sql)
                rows = cursor.fetchall()
                # Extract results - if single column, extract values from tuples
                if rows:
                    if len(rows[0]) == 1:
                        # Single column: flatten tuple list to value list
                        result = [convert_value(row[0]) for row in rows]
                    else:
                        # Multi-column: keep as list of lists
                        result = [[convert_value(v) for v in row] for row in rows]
                else:
                    result = []

                entry['result'] = result

                if not result:
                    empty_count += 1

                success_count += 1

            except Exception as e:
                print(f"[{i+1}/{len(data)}] sample_id={sample_id}: SQL ERROR: {e}")
                # Keep the original result on error
                error_count += 1

            # Progress indicator every 50 entries
            if (i + 1) % 50 == 0:
                print(f"[{datetime.now()}] Progress: {i+1}/{len(data)} "
                      f"(success: {success_count}, errors: {error_count}, empty: {empty_count})")

    finally:
        cursor.close()
        conn.close()
        print(f"[{datetime.now()}] MySQL connection closed.")

    # Write output
    print(f"[{datetime.now()}] Writing: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== SUMMARY ===")
    print(f"Total entries: {len(data)}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Empty results: {empty_count}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
