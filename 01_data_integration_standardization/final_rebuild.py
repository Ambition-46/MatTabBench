import json, os, pymysql, re

BASE = r"f:\Study\科研任务\论文\评测集\Code\数据插入\sample"
MATCH_CACHE = r"f:\Study\科研任务\论文\评测集\Code\数据插入\field_match_cache.json"
CLASSIFICATION = r"f:\Study\科研任务\论文\评测集\Code\数据插入\dataset_classification.json"

with open(MATCH_CACHE, 'r', encoding='utf-8') as f: cache = json.load(f)
with open(CLASSIFICATION, 'r', encoding='utf-8') as f: dsc = json.load(f)

cache['硬度(Hv)'] = 189
cache['硬度（Hv）'] = 189

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='123456', database='smart_small', charset='utf8mb4')
cur = conn.cursor()
cur.execute("SELECT property_id, property_name FROM property_table")
prop_id_to_name = {r[0]: r[1] for r in cur.fetchall()}
valid_pids = set(prop_id_to_name.keys())
field_to_pid = {k: int(v) for k, v in cache.items() if v is not None and int(v) in valid_pids}

title_to_class = {}
for title, entry in dsc.items():
    cm = {}
    for cat in ['object', 'operate', 'result']:
        for pid in entry.get(cat, []): cm[pid] = cat
    title_to_class[title] = cm

CONTEXT_OVERRIDES = {
    '纳米压痕硬度(GPa)': {'硬度': '纳米压痕硬度(GPa)'},
    '纳米压痕模量(GPa)': {'模量': '纳米压痕模量(GPa)'},
    '纳米压痕硬度（GPa）': {'硬度': '纳米压痕硬度（GPa）'},
    '纳米压痕模量（GPa）': {'模量': '纳米压痕模量（GPa）'},
}

def is_scalar(v):
    return isinstance(v, (str, int, float, bool)) and v is not None

def clean_value(v):
    """Store value exactly as in JSON, no modification."""
    return str(v)

SKIP = {'化学结构式','MGE18_标题','MGE18_摘要','MGE18_DOI','MGE18_关键词',
        'MGE18_来源','MGE18_引用','MGE18_数据生产者','MGE18_数据生产机构','MGE18_方法'}

def extract_leaves(data):
    leaves = {}
    for k, v in data.items():
        if k in SKIP or k.startswith('MGE18_'): continue
        if is_scalar(v):
            leaves[k] = clean_value(v)
        elif isinstance(v, dict):
            if 'lb' in v or 'ub' in v:
                if 'lb' in v: leaves[f"{k}_lb"] = clean_value(v['lb'])
                if 'ub' in v: leaves[f"{k}_ub"] = clean_value(v['ub'])
            else:
                for sk, sv in v.items():
                    if is_scalar(sv): leaves[sk] = clean_value(sv)
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            override = CONTEXT_OVERRIDES.get(k, {})
            for item_dict in v:
                # Pattern: {"元素": "Co", "含量": 48.37} or {"成分": "H", "含量(wt%)": "0.015"}
                elem_key = next((k for k in item_dict if k in ('元素','成分','元素名称')), None)
                content_key = next((k for k in item_dict if '含量' in k or '质量分数' in k or 'wt%' in k), None)
                if elem_key and content_key:
                    elem = str(item_dict[elem_key]).strip()
                    content = item_dict[content_key]
                    if elem and content is not None:
                        leaves[elem] = clean_value(content)
                    continue
                # Pattern: {"相名称": "γ'相", "含量值": 75.1} -> phase name as key
                if '相名称' in item_dict and '含量值' in item_dict:
                    pname = str(item_dict['相名称']).strip()
                    pval = item_dict['含量值']
                    if pname and pval is not None:
                        leaves[pname] = clean_value(pval)
                    continue
                # General: flatten all scalar sub-keys
                for sk, sv in item_dict.items():
                    if is_scalar(sv):
                        mapped_key = override.get(sk, sk)
                        leaves[mapped_key] = clean_value(sv)
                    elif isinstance(sv, dict):
                        for ssk, ssv in sv.items():
                            if is_scalar(ssv): leaves[ssk] = clean_value(ssv)
    return leaves

# Clear
cur.execute("DELETE FROM value_table")
cur.execute("DELETE FROM entity_table")
cur.execute("ALTER TABLE value_table AUTO_INCREMENT = 1")
conn.commit()

ec = vc = 0
TYPE_B_OFFSET = 50_000_000
used_ids = set()

for fname in sorted(os.listdir(BASE)):
    if not fname.endswith('.json'): continue
    with open(os.path.join(BASE, fname), 'r', encoding='utf-8') as f:
        d = json.load(f)

    records = []
    if isinstance(d, list):
        for item in d:
            if 'data' not in item: continue
            data = item['data']
            meta = {k: v for k, v in data.items() if k.startswith('MGE18_')}
            leaves = extract_leaves(data)
            records.append((item.get('_meta_id'), item.get('title', fname),
                          str(meta.get('MGE18_数据生产者', ''))[:100],
                          str(meta.get('MGE18_数据生产机构', ''))[:100], leaves))
    elif isinstance(d, dict) and 'template' in d:
        tpl_key = [k for k in d['template'] if not k.startswith('_')][0]
        for item in d['data']:
            meta = item.get('meta', {})
            content = item['content'].get(tpl_key, {})
            items = content if isinstance(content, list) else [content]
            for sub in items:
                if not isinstance(sub, dict): continue
                leaves = extract_leaves(sub)
                records.append((meta.get('数据ID'), tpl_key, meta.get('上传人', ''), '', leaves))

    for raw_did, title, producers, orgs, leaves in records:
        if raw_did is None: continue
        if raw_did >= TYPE_B_OFFSET: data_id = int(raw_did)
        elif raw_did < 1_000_000: data_id = int(raw_did) + TYPE_B_OFFSET
        else: data_id = int(raw_did)
        if data_id in used_ids: data_id = max(used_ids) + 1
        used_ids.add(data_id)

        cat_map = title_to_class.get(title, {})
        obj_pids, ope_pids, res_pids = set(), set(), set()
        values = []

        for field, val in leaves.items():
            pid = field_to_pid.get(field)
            if pid is None: continue
            values.append((pid, prop_id_to_name.get(pid, str(pid)), str(val)[:2000]))
            cat = cat_map.get(pid, 'result')
            if cat == 'object': obj_pids.add(pid)
            elif cat == 'operate': ope_pids.add(pid)
            else: res_pids.add(pid)

        if not values: continue

        def bm(pids):
            chars = ['0'] * 1024
            for p in pids:
                if 0 <= p < 1024:
                    chars[p] = '1'
            return ''.join(chars)

        cur.execute(
            "INSERT INTO entity_table (data_id, object, operate, result, title, data_producers, data_organizations) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (data_id, bm(obj_pids), bm(ope_pids), bm(res_pids), str(title)[:200], producers, orgs))
        ec += 1
        # Merge duplicates: same pid -> join values with "|"
        merged = {}
        for pid, pname, val in values:
            if pid in merged:
                old_pname, old_val = merged[pid]
                merged[pid] = (old_pname, f"{old_val}|{val}")
            else:
                merged[pid] = (pname, val)
        for pid, (pname, val) in merged.items():
            try:
                cur.execute("INSERT INTO value_table (data_id, property_id, property_name, value) VALUES (%s,%s,%s,%s)",
                           (data_id, pid, pname, val))
                vc += 1
            except: pass

    if ec % 500 == 0: conn.commit(); print(f"  {ec}e/{vc}v...")

conn.commit()

cur.execute("SELECT COUNT(*), MIN(value_id), MAX(value_id) FROM value_table")
vr = cur.fetchone()
print(f"\nDone: {ec}e, {vc}v (id:{vr[1]}~{vr[2]})")

# Verify clean
for pid in [22, 76, 10, 60]:
    cur.execute(f"SELECT value FROM value_table WHERE property_id={pid} LIMIT 3")
    print(f"  pid{pid}: {[r[0] for r in cur.fetchall()]}")

cur.close()
conn.close()
