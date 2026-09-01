import os
import json
import time
import pymysql


def get_conn():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "123456"),
        database=os.getenv("MYSQL_DATABASE", "smart_small"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.Cursor,
        autocommit=True,
    )


def normalize_sql(sql: str) -> str:
    # remove trailing semicolons and surrounding whitespace
    return sql.strip().rstrip(';')


def run_and_update(json_path: str):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    backup_path = json_path + '.bak.' + time.strftime('%Y%m%d%H%M%S')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('Backup written to', backup_path)

    conn = get_conn()
    cursor = conn.cursor()

    failed = []
    total = len(data)
    print(f'Starting execution of {total} queries...')

    for idx, sample in enumerate(data, 1):
        sid = sample.get('sample_id')
        sql = sample.get('sql', '')
        if not sql:
            failed.append((sid, 'empty sql'))
            continue
        try:
            q = normalize_sql(sql)
            cursor.execute(q)
            rows = cursor.fetchall()
            # take first column of each row and normalize types for JSON
            res = []
            for r in rows:
                val = r[0] if isinstance(r, (list, tuple)) else r
                # normalize common non-serializable types
                try:
                    from decimal import Decimal
                    if isinstance(val, Decimal):
                        val = float(val)
                except Exception:
                    pass
                if isinstance(val, bytes):
                    try:
                        val = val.decode('utf-8')
                    except Exception:
                        val = val.decode('latin-1', errors='ignore')
                # fallback: convert unknown objects to str
                try:
                    json.dumps(val)
                except Exception:
                    val = str(val)
                res.append(val)
            sample['result'] = res
        except Exception as e:
            failed.append((sid, str(e)))
        if idx % 50 == 0 or idx == total:
            print(f'  processed {idx}/{total}')

    # write back
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    cursor.close()
    conn.close()

    print('Update complete. Failed:', len(failed))
    if failed:
        for sid, err in failed[:20]:
            print(' ', sid, err)
        print('See first 20 failures above.')


if __name__ == '__main__':
    JSON_PATH = os.path.join(os.path.dirname(__file__), 'sql_nl_test_samples_500.json')
    if not os.path.exists(JSON_PATH):
        # allow running from repo root
        JSON_PATH = os.path.join(os.getcwd(), 'sql_nl_test_samples_500.json')
    if not os.path.exists(JSON_PATH):
        print('Cannot find sql_nl_test_samples_500.json')
    else:
        run_and_update(JSON_PATH)
