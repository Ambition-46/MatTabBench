# -*- coding: utf-8 -*-
"""
Fix result_data: use original data from backup whenever possible,
fall back to MySQL for new data_ids.
"""
import json, pymysql
from collections import defaultdict
from decimal import Decimal

BACKUP_PATH = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500_backup.json'
FIXED_PATH  = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500.json'

MYSQL_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': '123456',
    'database': 'smart_small', 'charset': 'utf8mb4'
}

# ── 1. Build global lookup from backup ──
print('Loading backup...')
with open(BACKUP_PATH, 'r', encoding='utf-8') as f:
    backup = json.load(f)

global_lookup = {}
for s in backup:
    for rd in s.get('result_data', []):
        did = rd.get('_meta_id')
        if did and did not in global_lookup:
            global_lookup[did] = rd

print(f'  {len(global_lookup)} unique data_id -> result_data entries from backup')

# ── 2. Load fixed file ──
with open(FIXED_PATH, 'r', encoding='utf-8') as f:
    fixed = json.load(f)
print(f'  {len(fixed)} samples in fixed file')

# ── 3. Check coverage ──
all_ids = set()
for s in fixed:
    all_ids.update(s.get('result', []))

found = all_ids & set(global_lookup.keys())
missing = all_ids - set(global_lookup.keys())
print(f'  {len(all_ids)} total result data_ids')
print(f'  {len(found)} found in backup')
print(f'  {len(missing)} need MySQL lookup')

# ── 4. For missing IDs, build result_data from MySQL ──
mysql_lookup = {}
if missing:
    print(f'\nBuilding MySQL lookup for {len(missing)} missing data_ids...')
    conn = pymysql.connect(**MYSQL_CONFIG)
    cur = conn.cursor()

    batch = list(missing)
    for i, did in enumerate(batch):
        try:
            cur.execute('SELECT title FROM entity_table WHERE data_id = %s', (did,))
            trow = cur.fetchone()
            title = str(trow[0]) if trow else ''

            cur.execute(
                'SELECT property_name, value FROM value_table WHERE data_id = %s',
                (did,))
            props = cur.fetchall()

            data_obj = {}
            for pname, pval in props:
                try:
                    pv = float(pval)
                except (ValueError, TypeError):
                    pv = str(pval) if pval is not None else ''
                data_obj[str(pname)] = pv

            mysql_lookup[did] = {
                '_meta_id': int(did),
                '_id': f'mysql_{did}',
                '_tid': 0,
                'data': data_obj,
                'title': title
            }

        except Exception as e:
            print(f'  ERROR for data_id {did}: {e}')
            mysql_lookup[did] = {
                '_meta_id': int(did),
                '_id': f'mysql_{did}',
                '_tid': 0,
                'data': {},
                'title': ''
            }

        if (i+1) % 200 == 0:
            print(f'  {i+1}/{len(missing)}')

    conn.close()
    print(f'  Built {len(mysql_lookup)} entries from MySQL')

# ── 5. Combine lookups ──
full_lookup = {}
full_lookup.update(global_lookup)
full_lookup.update(mysql_lookup)

# ── 6. Rebuild result_data for each sample ──
print(f'\nRebuilding result_data for {len(fixed)} samples...')
from_backup = 0
from_mysql = 0
not_found = 0

for s in fixed:
    result_ids = s.get('result', [])
    new_result_data = []
    for did in result_ids:
        if did in global_lookup:
            new_result_data.append(global_lookup[did])
            from_backup += 1
        elif did in mysql_lookup:
            new_result_data.append(mysql_lookup[did])
            from_mysql += 1
        else:
            not_found += 1

    s['result_data'] = new_result_data

print(f'  From backup: {from_backup}')
print(f'  From MySQL:  {from_mysql}')
print(f'  Not found:   {not_found}')

# ── 7. Save ──
def convert(obj):
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, dict): return {k: convert(v) for k,v in obj.items()}
    if isinstance(obj, list): return [convert(v) for v in obj]
    return obj

fixed = convert(fixed)

with open(FIXED_PATH, 'w', encoding='utf-8') as f:
    json.dump(fixed, f, ensure_ascii=False, indent=2)

print(f'\nSaved {len(fixed)} samples!')
