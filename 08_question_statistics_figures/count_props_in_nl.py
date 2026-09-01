# -*- coding: utf-8 -*-
import json, re, os, pymysql
from collections import defaultdict

MYSQL_CONFIG = {'host':'127.0.0.1','port':3306,'user':'root','password':os.getenv('MYSQL_PASSWORD','12345678'),'database':'smart_small','charset':'utf8mb4'}

s=json.load(open('sql_nl_test_samples_500.json',encoding='utf-8'))
prop_ids=set()
for item in s:
    sql=item.get('sql','')
    prop_ids.update(re.findall(r'property_id\s*=\s*(\d+)', sql))
prop_ids = sorted(int(x) for x in prop_ids)

# fetch property names
conn = pymysql.connect(**MYSQL_CONFIG)
try:
    cur = conn.cursor()
    q = 'SELECT property_id, property_name FROM smart_small.property_table WHERE property_id IN (%s)' % ','.join(['%s']*len(prop_ids))
    cur.execute(q, prop_ids)
    rows = cur.fetchall()
    prop_map = {int(r[0]): (r[1] or '').strip() for r in rows}
finally:
    conn.close()

found=set()
prop_usage=defaultdict(list)
for item in s:
    nl = item.get('natural_language','') or ''
    for pid, pname in prop_map.items():
        if pname and pname in nl:
            found.add(pid)
            prop_usage[pid].append(item['sample_id'])

print(len(found))
# print sorted list of property names
for pid in sorted(found):
    print(pid, prop_map.get(pid,''))

# also print unmatched ids count
unmatched = [pid for pid in prop_ids if pid not in found]
print('UNMATCHED_COUNT', len(unmatched))
print('UNMATCHED_SAMPLE', unmatched[:20])
