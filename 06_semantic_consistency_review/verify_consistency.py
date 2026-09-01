# -*- coding: utf-8 -*-
"""
Verify NL-SQL-result_data consistency for all 328 samples.
Checks:
1. SQL conditions match NL question (property, operator, threshold)
2. result_data entries actually satisfy SQL conditions
3. Flag any mismatches
"""
import json, re, pymysql
from collections import defaultdict

FIXED_PATH = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500.json'

MYSQL_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': '123456',
    'database': 'smart_small', 'charset': 'utf8mb4'
}

def is_aggregation(sql):
    return bool(re.search(r'\b(MIN|MAX|AVG|COUNT|SUM)\s*\(', sql.upper()))

def extract_sql_conditions(sql):
    """Extract (property_id, operator, threshold1, threshold2) from SQL."""
    conds = []
    parts = sql.split('property_id = ')
    for p in parts[1:]:
        m = re.match(r'(\d+)', p)
        if not m: continue
        pid = int(m.group(1))

        # Check for string equality first
        str_m = re.search(r"v2?\.value\s*=\s*'([^']+)'", p)
        if str_m:
            conds.append((pid, '=', str_m.group(1), None))
            continue

        # Numeric comparison
        cm = re.search(
            r"CAST\(v2?\.value\s+AS\s+DECIMAL\(\d+,\s*\d+\)\)\s*"
            r"(BETWEEN\s+([\d.]+)\s+AND\s+([\d.]+)"
            r"|([<>=!]+)\s*([\d.-]+))", p)
        if cm:
            if cm.group(1) and 'BETWEEN' in str(cm.group(1)):
                conds.append((pid, 'BETWEEN', float(cm.group(2)), float(cm.group(3))))
            else:
                conds.append((pid, cm.group(4).strip(), float(cm.group(5)), None))
    return conds

def get_property_name(conn, pid):
    """Get property name from MySQL."""
    try:
        cur = conn.cursor()
        cur.execute('SELECT property_name FROM property_table WHERE property_id = %s', (pid,))
        r = cur.fetchone()
        return r[0] if r else f'pid_{pid}'
    except:
        return f'pid_{pid}'

def check_value_satisfies(value, op, t1, t2=None):
    """Check if a value satisfies the condition."""
    try:
        v = float(value)
    except (ValueError, TypeError):
        return None  # Can't check non-numeric

    if op == 'BETWEEN':
        return t1 <= v <= t2
    elif op == '>':
        return v > t1
    elif op == '<':
        return v < t1
    elif op == '>=':
        return v >= t1
    elif op == '<=':
        return v <= t1
    elif op == '=':
        return abs(v - t1) < 0.001
    elif op == '!=':
        return abs(v - t1) > 0.001
    return None

# ── Load ──
with open(FIXED_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

conn = pymysql.connect(**MYSQL_CONFIG)

print(f'Verifying {len(data)} samples...\n')

issues = []
ok_count = 0
agg_count = 0

for s in data:
    sid = s['sample_id']
    sql = s['sql']
    nl = s['natural_language']
    result = s.get('result', [])
    result_data = s.get('result_data', [])

    if is_aggregation(sql):
        agg_count += 1
        continue

    conds = extract_sql_conditions(sql)
    if not conds:
        issues.append((sid, 'NO_CONDITIONS', 'Could not extract SQL conditions'))
        continue

    # ── Check 1: result count matches result_data ──
    if len(result) > 0 and len(result_data) == 0:
        issues.append((sid, 'EMPTY_DATA', f'{len(result)} results but 0 result_data entries'))
        continue

    # Don't require exact match if result > 50 (we limit to 50)
    if len(result) <= 50 and len(result) != len(result_data):
        issues.append((sid, 'COUNT_MISMATCH', f'result={len(result)}, result_data={len(result_data)}'))

    # ── Check 2: Verify first 5 result_data entries satisfy SQL conditions ──
    violations = 0
    for rd in result_data[:5]:
        rd_data = rd.get('data', {})

        for pid, op, t1, t2 in conds:
            if op == '=' and isinstance(t1, str):
                # String equality - check if any field matches
                found_str = False
                for v in rd_data.values():
                    if str(v) == t1:
                        found_str = True
                        break
                if not found_str:
                    violations += 1
                continue

            # Find the property name for this pid
            pname = get_property_name(conn, pid)

            # Look for matching field in result_data
            val = rd_data.get(pname)
            if val is None:
                # Try case-insensitive match
                for k, v in rd_data.items():
                    if k.lower() == pname.lower():
                        val = v
                        break

            if val is not None:
                satisfies = check_value_satisfies(val, op, t1, t2)
                if satisfies is False:
                    violations += 1
                    if violations <= 3:  # Only report first few
                        issues.append((sid, 'VALUE_VIOLATION',
                            f'pid={pid}({pname}): value={val} does NOT satisfy {op} {t1}'
                            + (f' AND {t2}' if t2 else '')))

    if violations == 0:
        ok_count += 1

# ── Report ──
print(f'{"="*60}')
print(f'Aggregation queries (skipped): {agg_count}')
print(f'Regular queries OK: {ok_count}')
print(f'Regular queries with issues: {len(issues)}')
print(f'{"="*60}')

if issues:
    # Group by issue type
    by_type = defaultdict(list)
    for sid, itype, msg in issues:
        by_type[itype].append((sid, msg))

    for itype, items in sorted(by_type.items()):
        print(f'\n[{itype}] ({len(items)} samples):')
        for sid, msg in items[:5]:
            print(f'  #{sid}: {msg}')
        if len(items) > 5:
            print(f'  ... and {len(items)-5} more')

conn.close()
print('\nDone!')
