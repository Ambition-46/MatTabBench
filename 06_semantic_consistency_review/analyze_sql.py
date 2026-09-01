# -*- coding: utf-8 -*-
"""Analyze NL-SQL consistency for all 100 samples."""
import json, re, sys

with open(r'f:\Study\科研任务\论文\评测集\Code\sample\sample_queries_with_sql_100_new_with_data.json',
          'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    sid = item['sample_id']
    nl = item['natural_language']
    nle = item['natural_language_en']
    sql = item['sql']

    # Extract conditions from SQL
    conditions = []
    parts = sql.split('property_id = ')
    for part in parts[1:]:
        pid = re.match(r'(\d+)', part).group(1)
        # Find CAST and comparison
        m = re.search(
            r"CAST\(v2?\.value\s+AS\s+DECIMAL\(\d+,\s*\d+\)\)\s*"
            r"(BETWEEN\s+([\d.]+)\s+AND\s+([\d.]+)"
            r"|([<>=!]+)\s*([\d.-]+))",
            part
        )
        if m:
            if m.group(1) and 'BETWEEN' in str(m.group(1)):
                conditions.append((pid, 'BETWEEN', float(m.group(2)), float(m.group(3))))
            else:
                op = m.group(4).strip()
                val = float(m.group(5))
                conditions.append((pid, op, val, None))

    print(f'#{sid}: {nl}')
    print(f'  EN: {nle}')
    for c in conditions:
        if c[1] == 'BETWEEN':
            print(f'  pid={c[0]} BETWEEN {c[2]} AND {c[3]}')
        else:
            print(f'  pid={c[0]} {c[1]} {c[2]}')
    print()
