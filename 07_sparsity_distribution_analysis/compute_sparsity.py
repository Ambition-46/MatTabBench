#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compute database sparsity and distribution metrics for material DB.
Outputs: sparsity_report.json, sparsity_report.csv, sparsity_summary.txt
"""
import json
import os
import pymysql
from collections import Counter
from statistics import mean, median
from datetime import datetime
import csv

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': os.getenv('MYSQL_PASSWORD', '12345678'),
    'database': 'smart_small',
    'charset': 'utf8mb4'
}

SAMPLES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'sql_nl_test_samples_500_result_data.json')


def get_conn():
    return pymysql.connect(**MYSQL_CONFIG)


def to_jsonable(x):
    try:
        import decimal
        if isinstance(x, decimal.Decimal):
            return float(x)
    except Exception:
        pass
    return x


def main():
    print('Loading samples...')
    with open(SAMPLES_PATH, 'r', encoding='utf-8') as f:
        samples = json.load(f)

    # extract property IDs used in queries and result sizes
    sample_prop_ids = set()
    result_sizes = []
    for s in samples:
        sql = s.get('sql','')
        # find property_id = N occurrences
        import re
        for m in re.findall(r'property_id\s*=\s*(\d+)', sql):
            sample_prop_ids.add(int(m))
        result_sizes.append(len(s.get('result') or []))

    print('Connecting to DB...')
    conn = get_conn()
    try:
        cur = conn.cursor()
        # total entities
        cur.execute('SELECT COUNT(DISTINCT data_id) FROM smart_small.entity_table')
        num_entities = cur.fetchone()[0]

        # total properties (from property_table)
        cur.execute('SELECT COUNT(DISTINCT property_id) FROM smart_small.property_table')
        num_properties = cur.fetchone()[0]

        # existing entity-property pairs (sparsity numerator)
        cur.execute('SELECT COUNT(DISTINCT data_id, property_id) FROM smart_small.value_table')
        num_pairs = cur.fetchone()[0]

        density = num_pairs / (num_entities * num_properties) if num_entities and num_properties else 0.0

        # properties per entity distribution
        cur.execute('SELECT data_id, COUNT(DISTINCT property_id) as pcount FROM smart_small.value_table GROUP BY data_id')
        pcounts = [row[1] for row in cur.fetchall()]

        # entities per property distribution —— 覆盖全部 property_table 属性（无值属性计 0）
        cur.execute('''
            SELECT p.property_id, COUNT(DISTINCT v.data_id) AS ecount
            FROM smart_small.property_table p
            LEFT JOIN smart_small.value_table v ON v.property_id = p.property_id
            GROUP BY p.property_id
        ''')
        prop_rows = cur.fetchall()
        prop_ecounts = [r[1] for r in prop_rows]        # 全部属性（含 0 覆盖）
        prop_map = {int(r[0]): int(r[1]) for r in prop_rows}
        covered_ecounts = [c for c in prop_ecounts if c > 0]  # 仅统计有值的属性

        # low coverage properties (<= threshold)
        low_thresholds = [1,5,10]
        low_counts = {}
        for t in low_thresholds:
            low_counts[t] = [pid for pid,c in prop_map.items() if c <= t]

        # query-involved property coverage
        query_props = sorted(list(sample_prop_ids))
        query_prop_coverage = {pid: prop_map.get(pid,0) for pid in query_props}

    finally:
        conn.close()

    # result set size stats
    rs_mean = mean(result_sizes) if result_sizes else 0
    rs_median = median(result_sizes) if result_sizes else 0
    rs_min = min(result_sizes) if result_sizes else 0
    rs_max = max(result_sizes) if result_sizes else 0

    # properties per entity stats
    p_mean = mean(pcounts) if pcounts else 0
    p_median = median(pcounts) if pcounts else 0
    p_min = min(pcounts) if pcounts else 0
    p_max = max(pcounts) if pcounts else 0

    # entities per property stats（全部属性，0 覆盖计入）
    e_mean = mean(prop_ecounts) if prop_ecounts else 0
    e_median = median(prop_ecounts) if prop_ecounts else 0
    e_min = min(prop_ecounts) if prop_ecounts else 0
    e_max = max(prop_ecounts) if prop_ecounts else 0
    # 仅统计有值属性（covered）的口径
    c_mean = mean(covered_ecounts) if covered_ecounts else 0
    c_median = median(covered_ecounts) if covered_ecounts else 0
    c_min = min(covered_ecounts) if covered_ecounts else 0
    c_max = max(covered_ecounts) if covered_ecounts else 0

    # histograms (buckets)
    def hist_counts(values, bins):
        cnt = Counter()
        for v in values:
            for name,cond in bins:
                if cond(v):
                    cnt[name]+=1
                    break
        return cnt

    entity_prop_bins = [
        ('0', lambda x: x==0),
        ('1-2', lambda x: 1<=x<=2),
        ('3-5', lambda x: 3<=x<=5),
        ('6-10', lambda x: 6<=x<=10),
        ('>10', lambda x: x>10)
    ]
    ep_hist = hist_counts(pcounts, entity_prop_bins)

    prop_entity_bins = [
        ('0', lambda x: x==0),
        ('1', lambda x: x==1),
        ('2-5', lambda x: 2<=x<=5),
        ('6-20', lambda x: 6<=x<=20),
        ('21-100', lambda x: 21<=x<=100),
        ('>100', lambda x: x>100)
    ]
    pe_hist = hist_counts(prop_ecounts, prop_entity_bins)

    # prepare report
    report = {
        'timestamp': datetime.now().isoformat(),
        'num_entities': int(num_entities),
        'num_properties': int(num_properties),
        'num_entity_property_pairs': int(num_pairs),
        'density': density,
        'properties_per_entity_stats': {
            'mean': p_mean, 'median': p_median, 'min': p_min, 'max': p_max,
            'histogram': dict(ep_hist)
        },
        'entities_per_property_stats': {
            'mean': e_mean, 'median': e_median, 'min': e_min, 'max': e_max,
            'histogram': dict(pe_hist)
        },
        'covered_entities_per_property_stats': {
            'mean': c_mean, 'median': c_median, 'min': c_min, 'max': c_max,
            'num_covered_properties': len(covered_ecounts)
        },
        'low_coverage_properties': {str(t): low_counts[t] for t in low_thresholds},
        'query_properties': {
            'count': len(query_props),
            'properties': query_props,
            'coverage_counts': query_prop_coverage
        },
        'result_set_size_stats': {
            'mean': rs_mean, 'median': rs_median, 'min': rs_min, 'max': rs_max,
            'histogram_samples': {
                '0': sum(1 for r in result_sizes if r==0),
                '1': sum(1 for r in result_sizes if r==1),
                '2-5': sum(1 for r in result_sizes if 2<=r<=5),
                '6-20': sum(1 for r in result_sizes if 6<=r<=20),
                '21-100': sum(1 for r in result_sizes if 21<=r<=100),
                '>100': sum(1 for r in result_sizes if r>100)
            }
        }
    }

    # write JSON
    with open('sparsity_report.json','w',encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # write CSV for entities per property (top/bottom)
    with open('entities_per_property.csv','w',encoding='utf-8-sig',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['property_id','entity_count'])
        for pid,count in sorted(prop_map.items(), key=lambda x:-x[1]):
            writer.writerow([pid,count])

    # write CSV for properties per entity (top)
    with open('properties_per_entity.csv','w',encoding='utf-8-sig',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['data_id','property_count'])
        # need to fetch again ordered
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute('SELECT data_id, COUNT(DISTINCT property_id) as pcount FROM smart_small.value_table GROUP BY data_id')
            rows = cur.fetchall()
            for data_id,pc in rows:
                writer.writerow([int(data_id), int(pc)])
        finally:
            conn.close()

    # write human summary
    with open('sparsity_summary.txt','w',encoding='utf-8') as f:
        f.write('Sparsity analysis generated at: %s\n' % report['timestamp'])
        f.write('Num entities: %d\n' % report['num_entities'])
        f.write('Num properties: %d\n' % report['num_properties'])
        f.write('Num entity-property pairs: %d\n' % report['num_entity_property_pairs'])
        f.write('Density (pairs / (entities*properties)): %.6e\n\n' % report['density'])

        f.write('Properties per entity: mean=%.3f median=%.3f min=%d max=%d\n' % (
            report['properties_per_entity_stats']['mean'], report['properties_per_entity_stats']['median'],
            report['properties_per_entity_stats']['min'], report['properties_per_entity_stats']['max']))
        f.write('Histogram (entities by num properties): %s\n\n' % report['properties_per_entity_stats']['histogram'])

        f.write('Entities per property (all %d properties, zero-coverage included): mean=%.3f median=%.3f min=%d max=%d\n' % (
            report['num_properties'],
            report['entities_per_property_stats']['mean'], report['entities_per_property_stats']['median'],
            report['entities_per_property_stats']['min'], report['entities_per_property_stats']['max']))
        f.write('Entities per property (only %d covered properties): mean=%.3f median=%.3f min=%d max=%d\n' % (
            report['covered_entities_per_property_stats']['num_covered_properties'],
            report['covered_entities_per_property_stats']['mean'], report['covered_entities_per_property_stats']['median'],
            report['covered_entities_per_property_stats']['min'], report['covered_entities_per_property_stats']['max']))
        f.write('Histogram (properties by entity coverage): %s\n\n' % report['entities_per_property_stats']['histogram'])

        f.write('Low coverage properties (<= thresholds):\n')
        for t in low_thresholds:
            f.write('  <=%d: %d properties\n' % (t, len(low_counts[t])))
        f.write('\n')

        f.write('Query-involved properties: %d unique properties referenced in 500 samples\n' % report['query_properties']['count'])
        f.write('Sample of query properties coverage (property_id: entity_count)\n')
        for pid in query_props[:50]:
            f.write('  %d: %d\n' % (pid, report['query_properties']['coverage_counts'].get(pid,0)))
        f.write('\n')

        f.write('Result set sizes (samples): mean=%.3f median=%.3f min=%d max=%d\n' % (
            report['result_set_size_stats']['mean'], report['result_set_size_stats']['median'],
            report['result_set_size_stats']['min'], report['result_set_size_stats']['max']))
        f.write('Result size histogram samples: %s\n' % report['result_set_size_stats']['histogram_samples'])

    print('Wrote sparsity_report.json, sparsity_summary.txt, entities_per_property.csv, properties_per_entity.csv')


if __name__ == '__main__':
    main()
