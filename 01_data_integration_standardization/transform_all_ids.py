#!/usr/bin/env python3
"""
Transform ALL data IDs in both data directory and sample queries:
Prepend '5' and pad with zeros to make exactly 8 digits.

- Array-type files: transform _meta_id
- Dict-type files (with dataset/template/data): transform meta.数据ID
- Sample queries: transform data_id in result arrays

Rule: "5" + "0"*(7 - len(str(id))) + str(id)
Example: 2305 -> 50002305, 331752 -> 50331752, 5205678 -> 55205678
"""
import json
import os

DATA_DIR = r"f:\Study\科研任务\论文\评测集\Code\data"
SAMPLE_FILE = r"f:\Study\科研任务\论文\评测集\Code\sample\sample_queries_with_sql_100_new.json"
SAMPLE_OUTPUT = r"f:\Study\科研任务\论文\评测集\Code\sample\sample_queries_with_sql_100_new.json"


def transform_id(old_id):
    """Prepend '5' and pad with zeros to 8 digits.
    Only transforms IDs shorter than 8 digits (idempotent)."""
    s = str(old_id)
    if len(s) >= 8:
        return old_id  # already transformed
    padding = 7 - len(s)  # 7 because first digit is always 5
    new_id_str = "5" + "0" * padding + s
    return int(new_id_str)


def main():
    json_files = sorted([
        f for f in os.listdir(DATA_DIR) if f.endswith('.json')
    ])

    total_transformed = 0

    # Step 1: Transform all data files
    print("=" * 60)
    print("STEP 1: Transform data files")
    print("=" * 60)
    for fname in json_files:
        fpath = os.path.join(DATA_DIR, fname)
        print(f"  {fname} ...", end=' ', flush=True)

        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        changed = 0

        if isinstance(data, list):
            for rec in data:
                if isinstance(rec, dict) and '_meta_id' in rec:
                    rec['_meta_id'] = transform_id(rec['_meta_id'])
                    changed += 1
            print(f"{changed} _meta_id [array-type]")

        elif isinstance(data, dict) and 'data' in data:
            for item in data['data']:
                if isinstance(item, dict) and 'meta' in item:
                    meta = item['meta']
                    if isinstance(meta, dict) and '数据ID' in meta:
                        meta['数据ID'] = transform_id(meta['数据ID'])
                        changed += 1
            print(f"{changed} 数据ID [dict-type]")
        else:
            print(f"skip (unknown format)")

        total_transformed += changed

        if changed > 0:
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Data files transformed: {total_transformed} records")

    # Step 2: Transform sample query result IDs
    print(f"\n{'=' * 60}")
    print("STEP 2: Transform sample query result IDs")
    print("=" * 60)
    with open(SAMPLE_FILE, 'r', encoding='utf-8') as f:
        samples = json.load(f)

    sample_changes = 0
    for sample in samples:
        for i, data_id in enumerate(sample.get('result', [])):
            # Only transform IDs that are less than 8 digits
            # (8-digit IDs starting with 5xx are already transformed)
            if len(str(data_id)) < 8:
                new_id = transform_id(data_id)
                sample['result'][i] = new_id
                sample_changes += 1

    print(f"  Sample result IDs transformed: {sample_changes}")

    # Try primary path first, fall back to alternative
    output_path = SAMPLE_FILE
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)
    except PermissionError:
        output_path = SAMPLE_FILE.replace('.json', '_transformed.json')
        print(f"  Primary path locked, writing to: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(samples, f, ensure_ascii=False, indent=2)

    print(f"  Sample file written to: {output_path}")


if __name__ == '__main__':
    main()
