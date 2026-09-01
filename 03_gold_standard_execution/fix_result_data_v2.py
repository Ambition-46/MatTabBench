# -*- coding: utf-8 -*-
"""
Fix result_data: look up data_id in data/*.json files to get original documents.
"""
import json, os, glob
from decimal import Decimal

FIXED_PATH = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500.json'
DATA_DIR   = r'f:\Study\科研任务\论文\评测集\Code\data'

# ── 1. Build global lookup from all data/*.json files ──
print('Scanning data directory...')
global_lookup = {}
file_stats = {}

for fpath in glob.glob(os.path.join(DATA_DIR, '*.json')):
    fname = os.path.basename(fpath)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            records = json.load(f)
        count = 0
        for rec in records:
            mid = rec.get('_meta_id')
            if mid is not None:
                if mid not in global_lookup:
                    global_lookup[mid] = rec
                    count += 1
        file_stats[fname] = count
    except Exception as e:
        print(f'  ERROR reading {fname}: {e}')

print(f'  {len(file_stats)} files processed')
print(f'  {len(global_lookup)} unique _meta_id -> document mappings')
print(f'  Top files by records:')
for fname, cnt in sorted(file_stats.items(), key=lambda x: -x[1])[:10]:
    print(f'    {fname}: {cnt}')

# ── 2. Load fixed file ──
with open(FIXED_PATH, 'r', encoding='utf-8') as f:
    fixed = json.load(f)
print(f'\n  {len(fixed)} samples in fixed file')

# ── 3. Check coverage ──
all_ids = set()
for s in fixed:
    all_ids.update(s.get('result', []))

found = all_ids & set(global_lookup.keys())
missing = all_ids - set(global_lookup.keys())

print(f'  {len(all_ids)} total unique result data_ids')
print(f'  {len(found)} found in data/ files ({100*len(found)/len(all_ids):.1f}%)')
print(f'  {len(missing)} missing')
if missing:
    print(f'  First 10 missing IDs: {sorted(list(missing))[:10]}')

# ── 4. Rebuild result_data ──
print(f'\nRebuilding result_data...')
total = 0
found_count = 0
miss_count = 0

for s in fixed:
    new_rd = []
    for did in s.get('result', []):
        total += 1
        if did in global_lookup:
            new_rd.append(global_lookup[did])
            found_count += 1
        else:
            miss_count += 1
    s['result_data'] = new_rd

print(f'  Total entries: {total}')
print(f'  Found in data/: {found_count} ({100*found_count/total:.1f}%)')
print(f'  Missing: {miss_count}')

# ── 5. Convert Decimals for JSON ──
def convert(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: convert(v) for k,v in obj.items()}
    if isinstance(obj, list): return [convert(v) for v in obj]
    return obj

fixed = convert(fixed)

# ── 6. Save ──
with open(FIXED_PATH, 'w', encoding='utf-8') as f:
    json.dump(fixed, f, ensure_ascii=False, indent=2)

print(f'\nSaved {len(fixed)} samples to sql_nl_test_samples_500.json')
