# -*- coding: utf-8 -*-
"""Regenerate result/result_data for fixed samples by querying smart_small MySQL."""
import pymysql
import json

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'smart_small',
    'charset': 'utf8mb4'
}

JSON_PATH = r'f:\Study\科研任务\论文\评测集\Code\sample\sample_queries_with_sql_100_new_with_data.json'

def get_entity_data(cur, data_id):
    """Get all property-value pairs and entity info for a data_id."""
    # Get entity info
    cur.execute(
        'SELECT title, data_producers, data_organizations, mat_id '
        'FROM entity_table WHERE data_id = %s', (data_id,))
    entity = cur.fetchone()
    if not entity:
        return None

    # Get all properties
    cur.execute(
        'SELECT property_id, property_name, value '
        'FROM value_table WHERE data_id = %s', (data_id,))
    props = cur.fetchall()

    return {
        'title': entity[0],
        'data_producers': entity[1] or '',
        'data_organizations': entity[2] or '',
        'mat_id': entity[3] or '',
        'properties': props
    }

def build_result_data(cur, data_ids):
    """Build result_data array for a list of data_ids."""
    result = []
    for did in data_ids:
        edata = get_entity_data(cur, did)
        if edata:
            entry = {
                '_meta_id': did,
                'title': edata['title'],
                'data_producers': edata['data_producers'],
                'data_organizations': edata['data_organizations'],
                'data': {}
            }
            for pid, pname, pval in edata['properties']:
                entry['data'][pname] = pval
            result.append(entry)
    return result


def main():
    conn = pymysql.connect(**MYSQL_CONFIG)
    cur = conn.cursor()

    # Load JSON
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Samples to regenerate (14, 17, 31, 37)
    targets = [14, 17, 31, 37]
    stats = {}

    for item in data:
        sid = item['sample_id']
        if sid not in targets:
            continue
        if not item['result'] and not item['result_data']:
            pass  # needs regeneration
        else:
            # Skip if already has data
            print(f'#{sid}: already has {len(item["result"])} results, skipping')
            continue

        sql = item['sql']
        print(f'#{sid}: executing...')
        try:
            cur.execute(sql)
            results = [r[0] for r in cur.fetchall()]
            item['result'] = results
            print(f'  -> {len(results)} data_ids')

            # Build result_data (limit to first 50 to keep file manageable)
            max_data = min(len(results), 50)
            item['result_data'] = build_result_data(cur, results[:max_data])
            print(f'  -> {len(item["result_data"])} result_data entries')

            stats[sid] = len(results)
        except Exception as e:
            print(f'  ERROR: {e}')
            stats[sid] = -1

    conn.close()

    # Save
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print('\n=== SUMMARY ===')
    for sid, count in stats.items():
        status = f'{count} results' if count >= 0 else 'ERROR'
        print(f'  #{sid}: {status}')
    print('Saved!')

if __name__ == '__main__':
    main()
