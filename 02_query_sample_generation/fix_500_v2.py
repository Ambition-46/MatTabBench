# -*- coding: utf-8 -*-
"""
Fix sql_nl_test_samples_500.json comprehensively.
1. smart_mged -> smart_small
2. Delete duplicate-SQL samples (keep the best NL match)
3. Fix 0-threshold queries
4. Regenerate results from smart_small database
"""
import json, re, pymysql
from collections import defaultdict
from decimal import Decimal

JSON_PATH = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500.json'

MYSQL_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': '123456',
    'database': 'smart_small', 'charset': 'utf8mb4'
}

def to_serializable(obj):
    """Convert Decimal and other non-JSON types."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    return obj

# ── Load ──
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'Loaded {len(data)} samples')

# ═══════════════════════════════════════
# STEP 1: smart_mged -> smart_small
# ═══════════════════════════════════════
for item in data:
    item['sql'] = item['sql'].replace('smart_mged', 'smart_small')
print('1. Schema: smart_mged -> smart_small  [OK]')

# ═══════════════════════════════════════
# STEP 2: Handle duplicate SQL
# ═══════════════════════════════════════
sql_map = defaultdict(list)
for item in data:
    norm = ' '.join(item['sql'].split()).strip()
    sql_map[norm].append(item)

dup_groups = {k: v for k, v in sql_map.items() if len(v) > 1}
print(f'2. Found {len(dup_groups)} duplicate SQL groups ({sum(len(v) for v in dup_groups.values())} samples)')

samples_to_delete = set()

for sql_norm, group in dup_groups.items():
    # Score each NL against SQL: count how many threshold numbers appear in NL
    # Extract all numbers from SQL
    sql_nums = set()
    for m in re.finditer(r'(\d+\.?\d*)', sql_norm):
        n = float(m.group(1))
        if n > 0.01 and n < 1000000:
            sql_nums.add(n)

    # Check for string equality in SQL
    str_match = re.search(r"v2?\.value\s*=\s*'([^']+)'", sql_norm)

    scores = []
    for s in group:
        nl = s['natural_language']
        score = 0
        for n in sql_nums:
            n_str = str(int(n)) if n == int(n) else f'{n:.1f}' if n == round(n, 1) else f'{n:.2f}'
            if n_str in nl:
                score += 3
        if str_match:
            if str_match.group(1) in nl:
                score += 5
        # Check operator keyword match
        if 'BETWEEN' in sql_norm.upper():
            if '之间' in nl or '到' in nl:
                score += 2
        scores.append((score, s['sample_id'], nl[:60]))

    scores.sort(reverse=True)
    best_score = scores[0][0]

    # Keep all with best_score; delete the rest
    best_ids = {s[1] for s in scores if s[0] == best_score}
    # BUT: if best_score is 0 (no numbers matched), keep only first, delete rest
    if best_score == 0 and len(best_ids) > 1:
        best_ids = {scores[0][1]}

    for sc, sid, nl in scores:
        if sid not in best_ids:
            samples_to_delete.add(sid)

    if len(group) - len(best_ids) > 0:
        print(f'  Group {[s["sample_id"] for s in group]}: keep={best_ids}, del={len(group)-len(best_ids)}')

data = [item for item in data if item['sample_id'] not in samples_to_delete]
print(f'   Deleted {len(samples_to_delete)}, remaining {len(data)}')

# Re-index
for i, item in enumerate(data, 1):
    item['sample_id'] = i

# ═══════════════════════════════════════
# STEP 3: Fix 0-threshold queries
# ═══════════════════════════════════════
fixed_zero = 0
for item in data:
    sql = item['sql']
    # Find exact 0.0 thresholds in CAST comparisons (not part of BETWEEN or larger numbers)
    # Pattern: CAST(...) > 0.0  or CAST(...) < 0.0 etc.
    new_sql = re.sub(
        r"(CAST\(v2?\.value\s+AS\s+DECIMAL\(\d+,\s*\d+\)\)\s*[><]\s*)0\.0\b",
        r"\g<1>0.1",
        sql
    )
    if new_sql != sql:
        item['sql'] = new_sql
        fixed_zero += 1

print(f'3. Fixed {fixed_zero} zero-threshold queries  [OK]')

# ═══════════════════════════════════════
# STEP 4: Regenerate results from smart_small
# ═══════════════════════════════════════
print(f'4. Regenerating results ({len(data)} samples)...')
conn = pymysql.connect(**MYSQL_CONFIG)
cur = conn.cursor()

for idx, item in enumerate(data):
    sql = item['sql']
    try:
        cur.execute(sql)
        results = [int(r[0]) for r in cur.fetchall()]
        item['result'] = results

        # Build result_data (limit 50)
        result_data = []
        for did in results[:50]:
            cur.execute('SELECT title FROM entity_table WHERE data_id = %s', (did,))
            trow = cur.fetchone()
            title = str(trow[0]) if trow else ''

            cur.execute(
                'SELECT property_name, value FROM value_table WHERE data_id = %s',
                (did,))
            props = cur.fetchall()

            entry = {'_meta_id': int(did), 'title': title, 'data': {}}
            for pname, pval in props:
                try:
                    pv = float(pval)
                except (ValueError, TypeError):
                    pv = str(pval) if pval is not None else ''
                entry['data'][str(pname)] = pv
            result_data.append(entry)

        item['result_data'] = result_data

        if (idx + 1) % 100 == 0:
            print(f'  {idx+1}/{len(data)}')

    except Exception as e:
        print(f'  ERROR #{item["sample_id"]}: {e}')
        item['result'] = []
        item['result_data'] = []

conn.close()
print(f'  Regenerated all {len(data)} samples  [OK]')

# ═══════════════════════════════════════
# STEP 5: Final save with Decimal-safe serialization
# ═══════════════════════════════════════
# Pre-process: walk through data and convert any remaining Decimal objects
def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(v) for v in obj]
    elif isinstance(obj, bytes):
        return obj.decode('utf-8', errors='replace')
    return obj

data = convert_decimals(data)

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'\n5. Saved {len(data)} samples to sql_nl_test_samples_500.json  [DONE]')
print(f'   Deleted duplicates: {len(samples_to_delete)}')
print(f'   Zero-thresholds fixed: {fixed_zero}')
