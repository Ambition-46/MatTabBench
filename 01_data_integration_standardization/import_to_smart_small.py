"""
Import sample JSON data into smart_small database.
Uses field_match_cache.json for field-to-property mapping.
"""
import json, os, pymysql

SAMPLE_DIR = r"f:\Study\科研任务\论文\评测集\Code\数据插入\sample"
MATCH_CACHE = r"f:\Study\科研任务\论文\评测集\Code\数据插入\field_match_cache.json"
PROP_TABLE = r"f:\Study\科研任务\论文\评测集\Code\数据插入\property_table_smart_small.json"

MYSQL_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': '123456',
    'database': 'smart_small', 'charset': 'utf8mb4',
}

# Load property table and field match
with open(PROP_TABLE, 'r', encoding='utf-8') as f:
    props = json.load(f)
prop_by_id = {p['id']: p for p in props}

with open(MATCH_CACHE, 'r', encoding='utf-8') as f:
    field_match = json.load(f)

# Build field -> (property_id, property_name)
field_to_prop = {}
for field, pid in field_match.items():
    if pid is not None and pid in prop_by_id:
        field_to_prop[field] = (pid, prop_by_id[pid]['name'])

print(f"Field-to-property mappings: {len(field_to_prop)}")

# ============================================================
# Parse all records
# ============================================================
all_records = []

for fname in sorted(os.listdir(SAMPLE_DIR)):
    if not fname.endswith('.json'):
        continue
    fpath = os.path.join(SAMPLE_DIR, fname)
    with open(fpath, 'r', encoding='utf-8') as f:
        d = json.load(f)

    if isinstance(d, list):
        # === TYPE A ===
        for item in d:
            if 'data' not in item:
                continue
            data_fields = item['data']
            core = {k: v for k, v in data_fields.items() if not k.startswith('MGE18_')}
            meta = {k: v for k, v in data_fields.items() if k.startswith('MGE18_')}

            rec = {
                'data_id': item.get('_meta_id'),
                'title': item.get('title', fname),
                'producers': meta.get('MGE18_数据生产者', ''),
                'organizations': meta.get('MGE18_数据生产机构', ''),
                'fields': core,
            }
            all_records.append(rec)

    elif isinstance(d, dict) and 'template' in d:
        # === TYPE B ===
        tpl_key = [k for k in d['template'] if not k.startswith('_')][0]
        for item in d['data']:
            meta = item.get('meta', {})
            content = item.get('content', {})
            cd = content.get(tpl_key, {})

            if isinstance(cd, list):
                for sub in cd:
                    rec = {
                        'data_id': meta.get('数据ID'),
                        'title': tpl_key,
                        'producers': meta.get('上传人', ''),
                        'organizations': '',
                        'fields': dict(sub),
                    }
                    all_records.append(rec)
            elif isinstance(cd, dict):
                rec = {
                    'data_id': meta.get('数据ID'),
                    'title': tpl_key,
                    'producers': meta.get('上传人', ''),
                    'organizations': '',
                    'fields': cd,
                }
                all_records.append(rec)

print(f"Total records to import: {len(all_records)}")

# ============================================================
# Insert into database
# ============================================================
conn = pymysql.connect(**MYSQL_CONFIG)
cur = conn.cursor()

# Clear existing data
print("Clearing existing data...")
cur.execute("DELETE FROM value_table")
cur.execute("DELETE FROM entity_table")
conn.commit()

entity_count = 0
value_count = 0
skip_count = 0
error_count = 0

# Track data_ids to avoid conflicts
used_ids = set()
TYPE_B_OFFSET = 50_000_000  # offset Type B to avoid collision with Type A _meta_id

for idx, rec in enumerate(all_records):
    if idx % 500 == 0:
        print(f"  Processing {idx}/{len(all_records)}... (entities: {entity_count}, values: {value_count})")
        conn.commit()

    # Determine data_id
    raw_id = rec['data_id']
    if raw_id is None:
        skip_count += 1
        continue

    if raw_id >= TYPE_B_OFFSET:
        # Already offset or very large Type A ID
        data_id = int(raw_id)
    elif raw_id < 1_000_000:
        # Type B: small IDs
        data_id = int(raw_id) + TYPE_B_OFFSET
    else:
        # Type A: large IDs
        data_id = int(raw_id)

    if data_id in used_ids:
        data_id = max(used_ids) + 1
    used_ids.add(data_id)

    title = str(rec['title'])[:200]
    producers = str(rec.get('producers', ''))[:100]
    organizations = str(rec.get('organizations', ''))[:100]

    # Build object bitmask
    matched_pids = set()
    for field in rec['fields']:
        if field in field_to_prop:
            matched_pids.add(field_to_prop[field][0])

    if matched_pids:
        max_pid = max(matched_pids)
        obj_chars = ['0'] * (max_pid + 1)
        for pid in matched_pids:
            obj_chars[pid] = '1'
        object_str = ''.join(reversed(obj_chars))
    else:
        object_str = ''

    try:
        # Insert entity
        cur.execute(
            """INSERT INTO entity_table (data_id, object, operate, result, title, data_producers, data_organizations)
               VALUES (%s, %s, '', '', %s, %s, %s)
               ON DUPLICATE KEY UPDATE title=VALUES(title)""",
            (data_id, object_str, title, producers, organizations)
        )
        if cur.rowcount in (1, 2):
            entity_count += 1

        # Insert values
        for field, val in rec['fields'].items():
            if field not in field_to_prop:
                continue
            pid, pname = field_to_prop[field]

            # Convert value to string
            if isinstance(val, dict):
                # Range type: store as JSON or single values
                if 'lb' in val or 'ub' in val:
                    # Store both bounds as separate value records
                    for bound_key in ['lb', 'ub']:
                        if bound_key in val:
                            val_str = str(val[bound_key])[:2000]
                            bound_name = f"{pname}_{bound_key}"
                            try:
                                cur.execute(
                                    """INSERT INTO value_table (data_id, property_id, property_name, value)
                                       VALUES (%s, %s, %s, %s)
                                       ON DUPLICATE KEY UPDATE value=VALUES(value)""",
                                    (data_id, pid, bound_name, val_str)
                                )
                                if cur.rowcount in (1, 2):
                                    value_count += 1
                            except:
                                pass
                    continue
                else:
                    val_str = json.dumps(val, ensure_ascii=False)[:2000]
            elif isinstance(val, list):
                val_str = json.dumps(val, ensure_ascii=False)[:2000]
            elif val is None:
                continue
            else:
                val_str = str(val)[:2000]

            try:
                cur.execute(
                    """INSERT INTO value_table (data_id, property_id, property_name, value)
                       VALUES (%s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE value=VALUES(value)""",
                    (data_id, pid, pname, val_str)
                )
                if cur.rowcount in (1, 2):
                    value_count += 1
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"  Value error (data_id={data_id}, field={field}): {e}")

    except Exception as e:
        error_count += 1
        if error_count <= 5:
            print(f"  Entity error (data_id={data_id}): {e}")

conn.commit()

# Final stats
cur.execute("SELECT COUNT(*) FROM entity_table")
et = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM value_table")
vt = cur.fetchone()[0]

print(f"\n=== Import Complete ===")
print(f"Records parsed: {len(all_records)}")
print(f"Entity rows: {et}")
print(f"Value rows: {vt}")
print(f"Skipped (no ID): {skip_count}")
print(f"Errors: {error_count}")

cur.close()
conn.close()
print("Done!")
