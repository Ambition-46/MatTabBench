"""
Rebuild smart_small: clear, re-parse with leaf extraction, re-insert.
"""
import json, os, pymysql

BASE = r"f:\Study\科研任务\论文\评测集\Code\数据插入\sample"
MATCH_CACHE = r"f:\Study\科研任务\论文\评测集\Code\数据插入\field_match_cache.json"
CLASSIFICATION = r"f:\Study\科研任务\论文\评测集\Code\数据插入\dataset_classification.json"
DB_CONFIG = {'host':'127.0.0.1','port':3306,'user':'root','password':'123456','database':'smart_small','charset':'utf8mb4'}

# Load mappings and classifications
with open(MATCH_CACHE, 'r', encoding='utf-8') as f:
    cache = json.load(f)
with open(CLASSIFICATION, 'r', encoding='utf-8') as f:
    dsc = json.load(f)

conn = pymysql.connect(**DB_CONFIG)
cur = conn.cursor()
cur.execute("SELECT property_id, property_name FROM property_table")
prop_id_to_name = {r[0]: r[1] for r in cur.fetchall()}
valid_pids = set(prop_id_to_name.keys())

field_to_pid = {}
for k, v in cache.items():
    if v is not None and int(v) in valid_pids:
        field_to_pid[k] = int(v)

# Build dataset title -> classification lookup
title_to_class = {}
for title, entry in dsc.items():
    cat_map = {}
    for cat in ['object', 'operate', 'result']:
        for pid in entry.get(cat, []):
            cat_map[pid] = cat
    title_to_class[title] = cat_map

# ============================================================
# Clear and reset
# ============================================================
cur.execute("DELETE FROM value_table")
cur.execute("DELETE FROM entity_table")
cur.execute("ALTER TABLE value_table AUTO_INCREMENT = 1")
conn.commit()
print("Cleared. Ready to import.")

# ============================================================
# Parse and insert
# ============================================================
def is_scalar(v):
    return isinstance(v, (str, int, float, bool)) and v is not None

SKIP = {'化学结构式', 'MGE18_标题', 'MGE18_摘要', 'MGE18_DOI', 'MGE18_关键词',
        'MGE18_来源', 'MGE18_引用', 'MGE18_数据生产者', 'MGE18_数据生产机构', 'MGE18_方法'}

entity_count = value_count = skip_count = 0
TYPE_B_OFFSET = 50_000_000
used_ids = set()

def _insert_record(cur, data_id, title, producers, orgs, leaves):
    global entity_count, value_count
    title = str(title)[:200]
    cat_map = title_to_class.get(title, {})

    obj_pids, ope_pids, res_pids = set(), set(), set()
    values_to_insert = []

    for field, val in leaves.items():
        pid = field_to_pid.get(field)
        if pid is None: continue
        val_str = str(val)[:2000]
        values_to_insert.append((data_id, pid, prop_id_to_name.get(pid, str(pid)), val_str))
        cat = cat_map.get(pid, 'result')
        if cat == 'object': obj_pids.add(pid)
        elif cat == 'operate': ope_pids.add(pid)
        else: res_pids.add(pid)

    if not values_to_insert: return

    def bm(pids):
        if not pids: return '0'
        m = max(pids)
        chars = ['0'] * (m + 1)
        for p in pids: chars[p] = '1'
        return ''.join(reversed(chars))

    cur.execute(
        "INSERT INTO entity_table (data_id, object, operate, result, title, data_producers, data_organizations) VALUES (%s,%s,%s,%s,%s,%s,%s)",
        (data_id, bm(obj_pids), bm(ope_pids), bm(res_pids), title, producers, orgs)
    )
    entity_count += 1

    for did, pid, pname, val in values_to_insert:
        try:
            cur.execute("INSERT INTO value_table (data_id, property_id, property_name, value) VALUES (%s,%s,%s,%s)",
                       (did, pid, pname, val))
            value_count += 1
        except: pass

for fname in sorted(os.listdir(BASE)):
    if not fname.endswith('.json'): continue
    with open(os.path.join(BASE, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)

    if isinstance(d, list):  # TYPE A
        for item in d:
            if 'data' not in item: continue
            data = item['data']
            meta = {k: v for k, v in data.items() if k.startswith('MGE18_')}
            raw_did = item.get('_meta_id')
            title = item.get('title', fname)
            producers = str(meta.get('MGE18_数据生产者', ''))[:100]
            orgs = str(meta.get('MGE18_数据生产机构', ''))[:100]

            # Flatten leaves
            leaves = {}
            for k, v in data.items():
                if k in SKIP or k.startswith('MGE18_'): continue
                if is_scalar(v):
                    leaves[k] = v
                elif isinstance(v, dict):
                    if 'lb' in v or 'ub' in v:
                        if 'lb' in v: leaves[f"{k}_lb"] = v['lb']
                        if 'ub' in v: leaves[f"{k}_ub"] = v['ub']
                    else:
                        for sk, sv in v.items():
                            if is_scalar(sv):
                                leaves[sk] = sv
                elif isinstance(v, list) and v and isinstance(v[0], dict):
                    for item_dict in v:
                        for sk, sv in item_dict.items():
                            if is_scalar(sv):
                                leaves[sk] = sv
                            elif isinstance(sv, dict):
                                for ssk, ssv in sv.items():
                                    if is_scalar(ssv):
                                        leaves[f"{sk}_{ssk}"] = ssv

            if raw_did is None: skip_count += 1; continue
            data_id = int(raw_did)
            if data_id in used_ids: data_id = max(used_ids) + 1
            used_ids.add(data_id)
            _insert_record(cur, data_id, title, producers, orgs, leaves)

    elif isinstance(d, dict) and 'template' in d:  # TYPE B
        tpl_key = [k for k in d['template'] if not k.startswith('_')][0]
        for item in d['data']:
            meta = item.get('meta', {})
            raw_did = meta.get('数据ID')
            content = item['content'].get(tpl_key, {})
            items = content if isinstance(content, list) else [content]

            for sub in items:
                if not isinstance(sub, dict): continue
                leaves = {}
                for k, v in sub.items():
                    if k in SKIP: continue
                    if is_scalar(v):
                        leaves[k] = v
                    elif isinstance(v, dict):
                        if 'lb' in v or 'ub' in v:
                            if 'lb' in v: leaves[f"{k}_lb"] = v['lb']
                            if 'ub' in v: leaves[f"{k}_ub"] = v['ub']
                        else:
                            for sk, sv in v.items():
                                if is_scalar(sv):
                                    leaves[sk] = sv
                    elif isinstance(v, list) and v:
                        if isinstance(v[0], dict):
                            for item_dict in v:
                                for sk, sv in item_dict.items():
                                    if is_scalar(sv):
                                        leaves[sk] = sv

                if raw_did is None: skip_count += 1; continue
                data_id = int(raw_did) + TYPE_B_OFFSET
                if data_id in used_ids: data_id = max(used_ids) + 1
                used_ids.add(data_id)
                _insert_record(cur, data_id, tpl_key, meta.get('上传人', ''), '', leaves)

    entity_count += 1
    value_count += 1
    if entity_count % 500 == 0:
        print(f"  {entity_count} entities...")
        conn.commit()

conn.commit()
entity_count = ec_saved

# ============================================================
# Stats
# ============================================================
cur.execute("SELECT COUNT(*), MIN(value_id), MAX(value_id) FROM value_table")
vc, vmin, vmax = cur.fetchone()
cur.execute("SELECT COUNT(*) FROM entity_table")
ec = cur.fetchone()[0]

print(f"\n=== Rebuild Complete ===")
print(f"Entities: {ec}")
print(f"Values: {vc} (value_id: {vmin}~{vmax})")
print(f"Skipped: {skip_count}")

# Verify key property_ids
for pid in [1,7,10,11,13,21,22,25,26,29,30,31,32,134,141,143,146,148,149,157,158,164,189,208,219,220]:
    cur.execute("SELECT COUNT(*) FROM value_table WHERE property_id=%s", (pid,))
    print(f"  pid={pid}: {cur.fetchone()[0]} rows")

cur.close()
conn.close()
print("Done!")
