# -*- coding: utf-8 -*-
"""
Fix result_data with 3-tier lookup:
1. data/*.json files (primary source)
2. Backup's result_data (for IDs not in data/)
3. MySQL (final fallback)
Handle aggregation queries separately.
"""
import json, os, glob, re, pymysql
from decimal import Decimal

FIXED_PATH   = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500.json'
BACKUP_PATH  = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500_backup.json'
DATA_DIR     = r'f:\Study\科研任务\论文\评测集\Code\data'

MYSQL_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': '123456',
    'database': 'smart_small', 'charset': 'utf8mb4'
}

def is_aggregation(sql):
    return bool(re.search(r'\b(MIN|MAX|AVG|COUNT|SUM)\s*\(', sql.upper()))

# ── Tier 1: data/*.json files ──
print('[1/3] Scanning data/*.json...')
tier1 = {}
for fpath in glob.glob(os.path.join(DATA_DIR, '*.json')):
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = json.load(f)
        if isinstance(content, dict) and ('template' in content or 'dataset' in content):
            continue
        records = content if isinstance(content, list) else [content]
        for rec in records:
            if not isinstance(rec, dict): continue
            mid = rec.get('_meta_id')
            if mid is not None and mid not in tier1:
                tier1[mid] = rec
    except: pass
print(f'  Tier 1 (data/): {len(tier1)} entries')

# ── Tier 2: Backup ──
print('[2/3] Loading backup...')
with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
    backup = json.load(f)
tier2 = {}
for s in backup:
    for rd in s.get('result_data', []):
        mid = rd.get('_meta_id')
        if mid is not None and mid not in tier1 and mid not in tier2:
            tier2[mid] = rd
print(f'  Tier 2 (backup): {len(tier2)} entries (not in data/)')

# ── Tier 3: MySQL ──
# We'll build this on-demand for missing IDs later

# ── Load fixed file ──
with open(FIXED_PATH, 'r', encoding='utf-8') as f:
    fixed = json.load(f)
print(f'\n  Fixed samples: {len(fixed)}')

# ── Identify remaining missing IDs ──
all_ids = set()
for s in fixed:
    if not is_aggregation(s['sql']):
        all_ids.update(s.get('result', []))

found_t1 = all_ids & set(tier1.keys())
found_t2 = all_ids & set(tier2.keys())
still_missing = all_ids - set(tier1.keys()) - set(tier2.keys())
# Filter out aggregation scalar values (< 1000)
real_missing = [m for m in still_missing if m > 1000]

print(f'  Total IDs: {len(all_ids)}')
print(f'  Tier 1 hits: {len(found_t1)}')
print(f'  Tier 2 hits: {len(found_t2)}')
print(f'  Still missing (>1000): {len(real_missing)}')

# ── Tier 3: MySQL for remaining missing ──
tier3 = {}
if real_missing:
    print(f'[3/3] MySQL lookup for {len(real_missing)} missing IDs...')
    conn = pymysql.connect(**MYSQL_CONFIG)
    cur = conn.cursor()
    for i, did in enumerate(real_missing):
        try:
            cur.execute('SELECT title FROM entity_table WHERE data_id = %s', (did,))
            trow = cur.fetchone()
            title = str(trow[0]) if trow else ''
            cur.execute('SELECT property_name, value FROM value_table WHERE data_id = %s', (did,))
            props = cur.fetchall()
            data_obj = {}
            for pname, pval in props:
                try: pv = float(pval)
                except: pv = str(pval) if pval is not None else ''
                data_obj[str(pname)] = pv
            tier3[did] = {
                '_meta_id': int(did), '_id': f'mysql_{did}',
                '_tid': 0, 'data': data_obj, 'title': title
            }
        except Exception as e:
            tier3[did] = {
                '_meta_id': int(did), '_id': f'mysql_{did}',
                '_tid': 0, 'data': {}, 'title': ''
            }
        if (i+1) % 100 == 0:
            print(f'  {i+1}/{len(real_missing)}')
    conn.close()
    print(f'  Tier 3 (MySQL): {len(tier3)} entries')

# ── Combine all tiers ──
full_lookup = {}
full_lookup.update(tier1)
full_lookup.update(tier2)
full_lookup.update(tier3)

# ── Rebuild result_data ──
print(f'\nRebuilding result_data...')
agg = 0
stats = {'tier1': 0, 'tier2': 0, 'tier3': 0, 'miss': 0}

for s in fixed:
    if is_aggregation(s['sql']):
        s['result_data'] = []
        agg += 1
    else:
        new_rd = []
        for did in s.get('result', []):
            if did in tier1:
                new_rd.append(tier1[did]); stats['tier1'] += 1
            elif did in tier2:
                new_rd.append(tier2[did]); stats['tier2'] += 1
            elif did in tier3:
                new_rd.append(tier3[did]); stats['tier3'] += 1
            else:
                stats['miss'] += 1
        s['result_data'] = new_rd

print(f'  Aggregation: {agg} samples (no result_data)')
print(f'  Tier 1 (data/):  {stats["tier1"]} entries')
print(f'  Tier 2 (backup): {stats["tier2"]} entries')
print(f'  Tier 3 (MySQL):  {stats["tier3"]} entries')
print(f'  Not found:       {stats["miss"]} entries')

# ── Convert & Save ──
def convert(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: convert(v) for k,v in obj.items()}
    if isinstance(obj, list): return [convert(v) for v in obj]
    return obj

fixed = convert(fixed)
with open(FIXED_PATH, 'w', encoding='utf-8') as f:
    json.dump(fixed, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(fixed)} samples!')
