#!/usr/bin/env python3
"""
Match data_id from sample JSON result arrays to _meta_id (or meta.数据ID) in data directory files,
and add result_data field containing the full matched records.
"""
import json
import os
import sys

SAMPLE_FILE = r"f:\Study\科研任务\论文\评测集\Code\sample\sample_queries_with_sql_100_new_transformed.json"
DATA_DIR = r"f:\Study\科研任务\论文\评测集\Code\data"
OUTPUT_FILE = r"f:\Study\科研任务\论文\评测集\Code\sample\sample_queries_with_sql_100_new_with_data.json"

def process_list_file(records, needed_ids):
    """Process array-type files: index by _meta_id."""
    found = {}
    count = 0
    for rec in records:
        count += 1
        if not isinstance(rec, dict):
            continue
        meta_id = rec.get('_meta_id')
        if meta_id is not None and meta_id in needed_ids:
            found[meta_id] = rec
    return found, count

def process_dict_file(data, needed_ids):
    """Process dict-type files (with dataset/template/data): index by meta.数据ID."""
    found = {}
    count = 0
    if 'data' not in data or not isinstance(data['data'], list):
        return found, 0
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
    return found, count

def main():
    # Step 1: Collect all unique data_ids needed from the sample file
    print("Loading sample file...")
    with open(SAMPLE_FILE, 'r', encoding='utf-8') as f:
        samples = json.load(f)

    needed_ids = set()
    for sample in samples:
        for data_id in sample.get('result', []):
            needed_ids.add(data_id)

    print(f"Total samples: {len(samples)}")
    print(f"Unique data_ids needed: {len(needed_ids)}")

    # Step 2: Scan all data files and build lookup for needed IDs
    data_files = sorted([
        f for f in os.listdir(DATA_DIR)
        if f.endswith('.json')
    ])
    print(f"Data files found: {len(data_files)}")

    lookup = {}
    total_records = 0

    for fname in data_files:
        fpath = os.path.join(DATA_DIR, fname)
        print(f"  Scanning: {fname} ...", end=' ', flush=True)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                # Array-type: index by _meta_id
                found, count = process_list_file(data, needed_ids)
                total_records += count
                print(f"{count} records, {len(found)} matched [via _meta_id]")
                lookup.update(found)
            elif isinstance(data, dict) and 'data' in data:
                # Dict-type (template format): index by meta.数据ID
                found, count = process_dict_file(data, needed_ids)
                total_records += count
                if count > 0:
                    print(f"{count} records, {len(found)} matched [via meta.数据ID]")
                else:
                    print(f"SKIP (no data array)")
                lookup.update(found)
            else:
                print(f"SKIP (unrecognized format, type={type(data).__name__})")
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\nTotal records scanned: {total_records}")
    print(f"Matched records: {len(lookup)} / {len(needed_ids)}")

    # Step 3: Report missing IDs
    missing = needed_ids - set(lookup.keys())
    if missing:
        print(f"\nWARNING: {len(missing)} data_ids not found in data files:")
        for mid in sorted(missing):
            print(f"  - {mid}")

    # Step 4: Add result_data to each sample
    print("\nAdding result_data to samples...")
    for sample in samples:
        result_data_list = []
        for data_id in sample.get('result', []):
            if data_id in lookup:
                result_data_list.append(lookup[data_id])
            else:
                result_data_list.append(None)  # placeholder for not found
        sample['result_data'] = result_data_list

    # Step 5: Write output
    print(f"Writing output to: {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)

    print("Done!")

if __name__ == '__main__':
    main()
