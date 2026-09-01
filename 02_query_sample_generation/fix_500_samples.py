# -*- coding: utf-8 -*-
"""
Fix sql_nl_test_samples_500.json:
1. smart_mged -> smart_small
2. Fix 0-threshold queries (> 0.0 / < 0.0 -> meaningful thresholds)
3. Handle duplicate SQL (delete mismatched NL queries, keep best match)
4. Regenerate results from smart_small database
"""
import json, re, pymysql
from collections import defaultdict, Counter
from difflib import SequenceMatcher

JSON_PATH = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500.json'
BACKUP_PATH = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500_backup.json'

MYSQL_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': '123456',
    'database': 'smart_small', 'charset': 'utf8mb4'
}

# ── STEP 0: Load & Backup ──
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'Loaded {len(data)} samples')

# Backup
import shutil
shutil.copy(JSON_PATH, BACKUP_PATH)
print(f'Backup saved to {BACKUP_PATH}')

# ── STEP 1: smart_mged -> smart_small ──
for item in data:
    item['sql'] = item['sql'].replace('smart_mged', 'smart_small')
print('STEP 1: smart_mged -> smart_small: DONE')

# ── STEP 2: Analyze duplicate SQL groups ──
sql_map = defaultdict(list)
for item in data:
    norm = ' '.join(item['sql'].split()).strip()
    sql_map[norm].append(item['sample_id'])

dup_groups = {k: v for k, v in sql_map.items() if len(v) > 1}
print(f'\nSTEP 2: Found {len(dup_groups)} duplicate SQL groups ({sum(len(v) for v in dup_groups.values())} samples)')

# For each duplicate group, determine which sample to keep
# Strategy: keep the sample whose NL query best matches the SQL semantics
# We'll use heuristics based on keyword matching

def get_sql_semantic(sql):
    """Extract key semantic features from SQL."""
    features = {'pids': [], 'operators': [], 'thresholds': []}
    parts = sql.split('property_id = ')
    for p in parts[1:]:
        m = re.match(r'(\d+)', p)
        if not m: continue
        pid = int(m.group(1))
        features['pids'].append(pid)
        cm = re.search(
            r"CAST\(v2?\.value\s+AS\s+DECIMAL\(\d+,\s*\d+\)\)\s*"
            r"(BETWEEN\s+([\d.]+)\s+AND\s+([\d.]+)"
            r"|([<>=!]+)\s*([\d.-]+))", p)
        if cm:
            if cm.group(1) and 'BETWEEN' in str(cm.group(1)):
                features['operators'].append('BETWEEN')
                features['thresholds'].extend([float(cm.group(2)), float(cm.group(3))])
            else:
                features['operators'].append(cm.group(4).strip())
                features['thresholds'].append(float(cm.group(5)))
    # Check for string equality
    str_matches = re.findall(r"v2?\.value\s*=\s*'([^']+)'", sql)
    if str_matches:
        features['string_val'] = str_matches[0]
    return features

# Process duplicates
samples_to_delete = set()
samples_fixed_sql = {}  # sid -> new SQL

for sql_norm, ids in dup_groups.items():
    # Get all samples in this group
    group_samples = [item for item in data if item['sample_id'] in ids]
    sql_sem = get_sql_semantic(sql_norm)

    # Score each NL query against the SQL semantics
    scores = []
    for s in group_samples:
        nl = s['natural_language']
        score = 0
        # Check if NL mentions threshold numbers
        for t in sql_sem['thresholds']:
            if str(int(t) if t == int(t) else t) in nl or f'{t:.1f}' in nl or f'{t:.2f}' in nl:
                score += 5
        # Check if NL matches the operator direction
        if 'BETWEEN' in sql_sem['operators'] or 'BETWEEN' in sql_norm.upper():
            if '之间' in nl or '到' in nl:
                score += 3
        elif '>' in sql_sem['operators']:
            if any(w in nl for w in ['大于', '超过', '以上', '高于']):
                score += 3
        elif '<' in sql_sem['operators']:
            if any(w in nl for w in ['小于', '低于', '不到', '以下']):
                score += 3
        elif '=' in sql_sem['operators']:
            if any(w in nl for w in ['等于', '刚好', '为', '是']):
                score += 3
        # Check string match
        if 'string_val' in sql_sem:
            if sql_sem['string_val'] in nl:
                score += 5
        scores.append((score, s['sample_id'], nl[:60]))

    scores.sort(reverse=True)
    best_score = scores[0][0]

    # If multiple samples have the same best score, keep all (they're likely legitimate variants)
    best_ids = [s[1] for s in scores if s[0] == best_score]
    delete_ids = [s[1] for s in scores if s[0] < best_score]

    if delete_ids:
        print(f'\n  Group {ids}:')
        print(f'  SQL: pid={sql_sem["pids"]}, ops={sql_sem["operators"]}, thresh={sql_sem["thresholds"]}')
        for sc, sid, nl in scores:
            mark = ' [KEEP]' if sid in best_ids else ' [DELETE]'
            print(f'    #{sid} (score={sc}): {nl}{mark}')
        samples_to_delete.update(delete_ids)

print(f'\n  Total samples to DELETE: {len(samples_to_delete)}')
print(f'  Remaining after dedup: {len(data) - len(samples_to_delete)}')

# ── STEP 3: Fix 0-thresholds in remaining samples ──
zero_fixes = {}
for item in data:
    if item['sample_id'] in samples_to_delete:
        continue

    sql = item['sql']
    nl = item['natural_language']

    # Find CAST conditions with threshold == 0
    matches = re.findall(
        r'(CAST\(v2?\.value\s+AS\s+DECIMAL\(\d+,\s*\d+\)\)\s*)(>|<|>=|<=)\s*(-?0\.0)',
        sql)

    for cast_prefix, op, val in matches:
        # Determine appropriate replacement threshold
        if op == '>':
            new_val = '0.1'  # default: change > 0 to > 0.1
        elif op == '<':
            new_val = '0.1'  # default: change < 0 to < 0.1
        elif op == '>=':
            new_val = '0.1'
        elif op == '<=':
            new_val = '0.1'
        else:
            continue

        old_pattern = cast_prefix + op + ' ' + val
        new_pattern = cast_prefix + op + ' ' + new_val
        sql = sql.replace(old_pattern, new_pattern)

        # Update NL query too - replace "大于0" style patterns
        if float(val) == 0.0:
            # Try to update NL
            if '大于0' in nl:
                nl = nl.replace('大于0', f'大于{new_val}')
            elif '小于0' in nl:
                nl = nl.replace('小于0', f'小于{new_val}')
            elif '>0' in nl:
                nl = nl.replace('>0', f'>{new_val}')

        zero_fixes[item['sample_id']] = (val, new_val)

    item['sql'] = sql
    item['natural_language'] = nl

print(f'\nSTEP 3: Fixed {len(zero_fixes)} zero-threshold queries')
for sid, (old, new) in list(zero_fixes.items())[:10]:
    print(f'  #{sid}: {old} -> {new}')
if len(zero_fixes) > 10:
    print(f'  ... and {len(zero_fixes)-10} more')

# ── STEP 4: Delete duplicate samples ──
data = [item for item in data if item['sample_id'] not in samples_to_delete]
print(f'\nSTEP 4: Deleted {len(samples_to_delete)} duplicate samples, {len(data)} remaining')

# Re-index sample_ids sequentially
for i, item in enumerate(data, 1):
    item['sample_id'] = i
print(f'  Re-indexed sample_ids 1..{len(data)}')

# ── STEP 5: Save intermediate result ──
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'\nSTEP 5: Saved {len(data)} samples to {JSON_PATH}')

# ── STEP 6: Regenerate results from database ──
print('\nSTEP 6: Regenerating results from smart_small...')
conn = pymysql.connect(**MYSQL_CONFIG)
cur = conn.cursor()

regenerated = 0
for item in data:
    # Only regenerate if result is empty OR SQL was modified
    sid = item['sample_id']
    sql = item['sql']

    try:
        cur.execute(sql)
        results = [r[0] for r in cur.fetchall()]
        item['result'] = results

        # Build result_data (limit to 50 entries)
        max_data = min(len(results), 50)
        result_data = []
        for did in results[:max_data]:
            cur.execute('SELECT title FROM entity_table WHERE data_id = %s', (did,))
            title_row = cur.fetchone()
            title = str(title_row[0]) if title_row else ''

            cur.execute(
                'SELECT property_name, value FROM value_table WHERE data_id = %s',
                (did,))
            props = cur.fetchall()

            entry = {'_meta_id': int(did), 'title': title, 'data': {}}
            for pname, pval in props:
                # Convert Decimal/bytes to string
                try:
                    pv = float(pval) if pval is not None else ''
                except (ValueError, TypeError):
                    pv = str(pval) if pval else ''
                entry['data'][str(pname)] = pv
            result_data.append(entry)

        item['result_data'] = result_data
        regenerated += 1

        if regenerated % 50 == 0:
            print(f'  Progress: {regenerated}/{len(data)}')

    except Exception as e:
        print(f'  ERROR #{sid}: {e}')
        item['result'] = []
        item['result_data'] = []

conn.close()
print(f'  Regenerated {regenerated}/{len(data)} samples')

# ── STEP 7: Final save ──
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'\nSTEP 7: Final save complete!')
print(f'  Total samples: {len(data)}')
print(f'  Deleted duplicates: {len(samples_to_delete)}')
print(f'  Zero-thresholds fixed: {len(zero_fixes)}')
print(f'  Results regenerated: {regenerated}')
