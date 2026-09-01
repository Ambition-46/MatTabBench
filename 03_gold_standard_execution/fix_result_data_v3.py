# -*- coding: utf-8 -*-
"""
Fix result_data: look up data_id in data/*.json for original documents.
Handle aggregation queries (MIN/MAX/AVG/COUNT) separately.
"""
import json, os, glob, re
from decimal import Decimal

FIXED_PATH = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500.json'
DATA_DIR   = r'f:\Study\科研任务\论文\评测集\Code\data'

def is_aggregation(sql):
    """Check if SQL is an aggregation query (returns scalar, not data_ids)."""
    upper = sql.upper()
    return bool(re.search(r'\b(MIN|MAX|AVG|COUNT|SUM)\s*\(', upper))

# ── 1. Build global lookup from data/*.json files ──
print('Scanning data directory...')
global_lookup = {}

for fpath in glob.glob(os.path.join(DATA_DIR, '*.json')):
    fname = os.path.basename(fpath)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = json.load(f)

        # Support both array-of-records and single-object formats
        if isinstance(content, list):
            records = content
        elif isinstance(content, dict):
            # Template/schema files (no _meta_id) - skip
            if 'template' in content or 'dataset' in content:
                continue
            # Single record
            records = [content]
        else:
            continue

        for rec in records:
            if not isinstance(rec, dict):
                continue
            mid = rec.get('_meta_id')
            if mid is not None and mid not in global_lookup:
                global_lookup[mid] = rec

    except Exception as e:
        print(f'  WARN {fname}: {e}')

print(f'  {len(global_lookup)} unique _meta_id -> document mappings')

# ── 2. Load fixed file ──
with open(FIXED_PATH, 'r', encoding='utf-8') as f:
    fixed = json.load(f)
print(f'  {len(fixed)} samples')

# ── 3. Fix result_data for each sample ──
agg_count = 0
lookup_hit = 0
lookup_miss = 0
total_entries = 0

for s in fixed:
    sql = s['sql']
    result = s.get('result', [])

    if is_aggregation(sql):
        # Aggregation query: result contains scalar value, no result_data
        s['result_data'] = []
        agg_count += 1
    else:
        # Regular query: result contains data_ids, look up in data/*.json
        new_rd = []
        for did in result:
            total_entries += 1
            if did in global_lookup:
                new_rd.append(global_lookup[did])
                lookup_hit += 1
            else:
                lookup_miss += 1
        s['result_data'] = new_rd

print(f'\n  Aggregation queries (no result_data): {agg_count}')
print(f'  Regular queries: {len(fixed) - agg_count}')
print(f'  data_id lookups: {total_entries} total, {lookup_hit} hit ({100*lookup_hit/total_entries:.1f}%), {lookup_miss} miss')

if lookup_miss > 0:
    # Show some missing IDs
    all_ids = set()
    for s in fixed:
        if not is_aggregation(s['sql']):
            all_ids.update(s.get('result', []))
    missing_ids = all_ids - set(global_lookup.keys())
    # Filter out small IDs (likely scalar results misclassified)
    real_missing = [m for m in missing_ids if m > 1000]
    print(f'  Missing IDs (not in any data file): {len(real_missing)} (excluding <1000)')
    if real_missing:
        print(f'  First 10 real missing: {sorted(real_missing)[:10]}')

# ── 4. Convert Decimals ──
def convert(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: convert(v) for k,v in obj.items()}
    if isinstance(obj, list): return [convert(v) for v in obj]
    return obj

fixed = convert(fixed)

# ── 5. Save ──
with open(FIXED_PATH, 'w', encoding='utf-8') as f:
    json.dump(fixed, f, ensure_ascii=False, indent=2)

print(f'\nSaved {len(fixed)} samples!')
