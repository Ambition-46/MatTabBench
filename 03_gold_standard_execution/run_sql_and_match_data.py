#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Step 1: Run all SQL queries from question files against MySQL smart_small and update 'result'.
Step 2: For non-aggregation questions (simple + complex), match result data_ids with data/ JSON files
        (via _meta_id or meta.数据ID) and update 'result_data'.
"""

import json
import os
import sys
import pymysql
from datetime import datetime
from decimal import Decimal


# ============================================================
# Config
# ============================================================

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'smart_small',
    'charset': 'utf8mb4',
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Directories to process (each with simple_questions.json, complex_questions.json, aggregated_questions.json)
QUESTION_DIRS = {
    'questions': os.path.join(BASE_DIR, 'questions'),
    'pos': os.path.join(BASE_DIR, 'pos'),
}

# Build QUESTION_FILES and OUTPUT_FILES dynamically
QUESTION_FILES = {}
OUTPUT_FILES = {}
for dir_key, dir_path in QUESTION_DIRS.items():
    for qtype in ['simple', 'complex', 'aggregated']:
        key = f'{dir_key}/{qtype}'
        fpath = os.path.join(dir_path, f'{qtype}_questions.json')
        QUESTION_FILES[key] = fpath
        OUTPUT_FILES[key] = fpath

# Non-aggregation question types get result_data populated
NON_AGG_TYPES = {'simple', 'complex'}


# ============================================================
# Helpers
# ============================================================

def convert_value(val):
    """Convert MySQL types to JSON-serializable Python types."""
    if isinstance(val, Decimal):
        return float(val) if val % 1 != 0 else int(val)
    if isinstance(val, bytes):
        return val.decode('utf-8', errors='replace')
    if isinstance(val, datetime):
        return val.isoformat()
    return val


def run_sql(cursor, sql):
    """Execute one SQL query and return the result rows."""
    cursor.execute(sql)
    rows = cursor.fetchall()
    if rows:
        if len(rows[0]) == 1:
            return [convert_value(row[0]) for row in rows]
        else:
            return [[convert_value(v) for v in row] for row in rows]
    return []


# ============================================================
# Step 1: Run SQL queries and update 'result'
# ============================================================

def step1_run_sql():
    """Run all SQL queries and update the result field in-place."""
    print("=" * 60)
    print("STEP 1: Running SQL queries against MySQL")
    print("=" * 60)

    # Load all question files
    all_data = {}
    for qtype, fpath in QUESTION_FILES.items():
        print(f"\nLoading: {fpath}")
        with open(fpath, 'r', encoding='utf-8') as f:
            all_data[qtype] = json.load(f)
        print(f"  {len(all_data[qtype])} entries")

    # Connect to MySQL
    print(f"\n[{datetime.now()}] Connecting to MySQL...")
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        print(f"[{datetime.now()}] Connected successfully.")
    except Exception as e:
        print(f"ERROR: Failed to connect to MySQL: {e}")
        sys.exit(1)

    total = sum(len(v) for v in all_data.values())
    current = 0
    stats = {'success': 0, 'error': 0, 'empty': 0}

    try:
        for qtype, entries in all_data.items():
            print(f"\n--- Processing {qtype} ({len(entries)} entries) ---")
            for entry in entries:
                sample_id = entry.get('sample_id', '?')
                sql = entry.get('sql', '')

                if not sql:
                    print(f"  [{sample_id}] SKIP: empty SQL")
                    stats['error'] += 1
                    current += 1
                    continue

                try:
                    result = run_sql(cursor, sql)
                    entry['result'] = result
                    stats['success'] += 1
                    if not result:
                        stats['empty'] += 1

                except Exception as e:
                    print(f"  [{sample_id}] SQL ERROR: {e}")
                    stats['error'] += 1

                current += 1
                if current % 100 == 0:
                    print(f"  Progress: {current}/{total} (success={stats['success']}, "
                          f"error={stats['error']}, empty={stats['empty']})")

    finally:
        cursor.close()
        conn.close()
        print(f"\n[{datetime.now()}] MySQL connection closed.")

    print(f"\nStep 1 Summary: total={total}, success={stats['success']}, "
          f"error={stats['error']}, empty={stats['empty']}")

    return all_data


# ============================================================
# Step 2: Match result data with data/ files and update result_data
# ============================================================

def scan_data_files(needed_ids):
    """Scan all JSON files in data/ directory and build lookup for needed IDs."""
    print("\n" + "=" * 60)
    print("STEP 2: Matching result data with data/ directory files")
    print("=" * 60)

    data_files = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.endswith('.json') and not f.endswith('.bak')
    ])
    print(f"\nData files found: {len(data_files)}")

    lookup = {}          # data_id -> record
    total_records = 0

    for fname in data_files:
        fpath = os.path.join(DATA_DIR, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            found = {}
            count = 0

            if isinstance(data, list):
                # Array-type: index by _meta_id
                for rec in data:
                    count += 1
                    if not isinstance(rec, dict):
                        continue
                    meta_id = rec.get('_meta_id')
                    if meta_id is not None and meta_id in needed_ids:
                        found[meta_id] = rec
                via = '_meta_id'

            elif isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                # Dict-type: index by meta.数据ID
                for item in data['data']:
                    count += 1
                    if not isinstance(item, dict):
                        continue
                    meta = item.get('meta', {})
                    if not isinstance(meta, dict):
                        continue
                    data_id = meta.get('数据ID')
                    if data_id is not None and data_id in needed_ids:
                        found[data_id] = item
                via = 'meta.数据ID'

            else:
                continue

            total_records += count
            if found:
                print(f"  {fname}: {count} records, {len(found)} matched via {via}")
            lookup.update(found)

        except Exception as e:
            print(f"  {fname}: ERROR - {e}")

    print(f"\nTotal records scanned: {total_records}")
    print(f"Matched IDs: {len(lookup)} / {len(needed_ids)}")

    # Report missing
    missing = needed_ids - set(lookup.keys())
    if missing:
        print(f"\nWARNING: {len(missing)} data_ids not found:")
        for mid in sorted(missing)[:20]:
            print(f"  - {mid}")
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")

    return lookup


def step2_match_data(all_data):
    """For non-aggregation questions, match result data with data/ files."""
    # Collect all unique data_ids needed
    needed_ids = set()
    for key, entries in all_data.items():
        # key format: 'questions/simple', 'pos/complex', etc.
        qtype = key.split('/')[-1]  # 'simple', 'complex', 'aggregated'
        if qtype in NON_AGG_TYPES:
            for entry in entries:
                for data_id in entry.get('result', []):
                    needed_ids.add(data_id)

    print(f"\nNon-aggregation question types: {NON_AGG_TYPES}")
    print(f"Unique data_ids needed: {len(needed_ids)}")

    if not needed_ids:
        print("No data_ids to match (empty results).")
        return

    # Scan data files
    lookup = scan_data_files(needed_ids)

    # Update result_data
    print("\n--- Adding result_data to non-aggregation questions ---")
    for key, entries in all_data.items():
        qtype = key.split('/')[-1]
        if qtype not in NON_AGG_TYPES:
            continue
        empty_rd = 0
        partial_rd = 0
        full_rd = 0
        for entry in entries:
            result_ids = entry.get('result', [])
            result_data_list = []
            for data_id in result_ids:
                if data_id in lookup:
                    result_data_list.append(lookup[data_id])
                else:
                    result_data_list.append(None)  # placeholder
            entry['result_data'] = result_data_list

            if not result_data_list:
                empty_rd += 1
            elif any(r is None for r in result_data_list):
                partial_rd += 1
            else:
                full_rd += 1

        print(f"  {key}: {full_rd} full, {partial_rd} partial, {empty_rd} empty")


# ============================================================
# Step 3: Save output
# ============================================================

def step3_save(all_data):
    """Save updated data to output files."""
    print("\n" + "=" * 60)
    print("STEP 3: Saving output files")
    print("=" * 60)

    for qtype, fpath in OUTPUT_FILES.items():
        print(f"\nWriting: {fpath}")
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(all_data[qtype], f, ensure_ascii=False, indent=2)
        print(f"  {len(all_data[qtype])} entries written")


# ============================================================
# Main
# ============================================================

def main():
    print(f"[{datetime.now()}] Starting...")
    print(f"Question dirs: {list(QUESTION_DIRS.keys())}")
    print(f"Data dir: {DATA_DIR}")

    # Step 1: Run SQL queries
    all_data = step1_run_sql()

    # Step 2: Match result data for non-aggregation questions
    step2_match_data(all_data)

    # Step 3: Save output files
    step3_save(all_data)

    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    for key, entries in sorted(all_data.items()):
        has_result = sum(1 for e in entries if e.get('result'))
        has_rd = sum(1 for e in entries if 'result_data' in e)
        empty_result = sum(1 for e in entries if not e.get('result'))
        print(f"  {key}: {len(entries)} entries, "
              f"{has_result} with results, {empty_result} empty, "
              f"{has_rd} with result_data")

    print(f"\n[{datetime.now()}] Done!")


if __name__ == '__main__':
    main()
