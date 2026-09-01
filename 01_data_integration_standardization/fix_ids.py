#!/usr/bin/env python3
"""
Fix incorrectly transformed IDs in data files:
- IDs with > 8 digits were incorrectly transformed (extra "5" prepended)
- Strip leading "5" from these IDs to restore correct 8-digit form
"""
import json
import os

DATA_DIR = r"f:\Study\科研任务\论文\评测集\Code\data"


def fix_id(val):
    """If ID has more than 8 digits, remove leading '5' chars until <= 8 digits."""
    s = str(val)
    while len(s) > 8 and s.startswith('5'):
        s = s[1:]  # strip one leading '5'
    return int(s)


def main():
    json_files = sorted([f for f in os.listdir(DATA_DIR) if f.endswith('.json')])
    total_fixed = 0

    for fname in json_files:
        fpath = os.path.join(DATA_DIR, fname)
        print(f"  {fname} ...", end=' ', flush=True)

        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        fixed = 0

        if isinstance(data, list):
            for rec in data:
                if isinstance(rec, dict) and '_meta_id' in rec:
                    old = rec['_meta_id']
                    if len(str(old)) > 8:
                        rec['_meta_id'] = fix_id(old)
                        fixed += 1

        elif isinstance(data, dict) and 'data' in data:
            for item in data['data']:
                if isinstance(item, dict) and 'meta' in item:
                    meta = item['meta']
                    if isinstance(meta, dict) and '数据ID' in meta:
                        old = meta['数据ID']
                        if len(str(old)) > 8:
                            meta['数据ID'] = fix_id(old)
                            fixed += 1

        print(f"{fixed} fixed")
        total_fixed += fixed

        if fixed > 0:
            with open(fpath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nTotal fixed: {total_fixed}")


if __name__ == '__main__':
    main()
