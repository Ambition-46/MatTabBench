import json
import re
import os
from collections import Counter, defaultdict
import statistics


def load_questions(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_where(sql):
    m = re.search(r"WHERE(.*?)(ORDER BY|GROUP BY|LIMIT|;|$)", sql, re.IGNORECASE | re.S)
    return m.group(1) if m else ''


def count_where_conditions(sql):
    where = extract_where(sql)
    if not where.strip():
        return 0
    # remove quoted strings to avoid counting AND/OR inside strings
    where_clean = re.sub(r"'[^']*'", '', where)
    # count AND/OR as separators
    and_count = len(re.findall(r"\bAND\b", where_clean, re.IGNORECASE))
    or_count = len(re.findall(r"\bOR\b", where_clean, re.IGNORECASE))
    # at least one condition if WHERE exists and non-empty
    conditions = 1 + and_count + or_count
    return conditions


def count_joins(sql):
    return len(re.findall(r"\bJOIN\b", sql, re.IGNORECASE))


def extract_property_ids(sql):
    ids = set()
    # property_id = 123
    for m in re.finditer(r"property_id\s*=\s*(\d+)", sql, re.IGNORECASE):
        ids.add(int(m.group(1)))
    # property_id IN (1,2,3)
    for m in re.finditer(r"property_id\s+IN\s*\(([^)]+)\)", sql, re.IGNORECASE):
        nums = re.findall(r"\d+", m.group(1))
        for n in nums:
            ids.add(int(n))
    return ids


def agg_functions_in_sql(sql):
    funcs = Counter()
    for f in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']:
        if re.search(r"\b%s\s*\(" % f, sql, re.IGNORECASE):
            funcs[f] += 1
    return funcs


def analyze_file(path):
    data = load_questions(path)
    stats = {
        'total_samples': len(data),
        'avg_joins': 0.0,
        'avg_where_conditions': 0.0,
        'distinct_property_count': 0,
        'agg_function_counts': {},
        'result_size_stats': {},
    }

    joins = []
    where_counts = []
    prop_ids = set()
    agg_counts = Counter()
    result_sizes = []

    for sample in data:
        sql = sample.get('sql', '')
        joins.append(count_joins(sql))
        where_counts.append(count_where_conditions(sql))
        prop_ids.update(extract_property_ids(sql))
        agg_counts.update(agg_functions_in_sql(sql))
        res = sample.get('result')
        if isinstance(res, list):
            result_sizes.append(len(res))
        else:
            try:
                result_sizes.append(int(res))
            except Exception:
                result_sizes.append(0)

    stats['avg_joins'] = statistics.mean(joins) if joins else 0
    stats['avg_where_conditions'] = statistics.mean(where_counts) if where_counts else 0
    stats['distinct_property_count'] = len(prop_ids)
    stats['agg_function_counts'] = dict(agg_counts)

    # result set distribution: basic stats + bins
    if result_sizes:
        stats['result_size_stats'] = {
            'mean': statistics.mean(result_sizes),
            'median': statistics.median(result_sizes),
            'min': min(result_sizes),
            'max': max(result_sizes),
            'count': len(result_sizes)
        }
        # bins
        bins = {'0': 0, '1': 0, '2-5': 0, '6-10': 0, '11-50': 0, '51-200': 0, '201+': 0}
        for s in result_sizes:
            if s == 0:
                bins['0'] += 1
            elif s == 1:
                bins['1'] += 1
            elif 2 <= s <= 5:
                bins['2-5'] += 1
            elif 6 <= s <= 10:
                bins['6-10'] += 1
            elif 11 <= s <= 50:
                bins['11-50'] += 1
            elif 51 <= s <= 200:
                bins['51-200'] += 1
            else:
                bins['201+'] += 1
        stats['result_size_bins'] = bins
    else:
        stats['result_size_stats'] = {}
        stats['result_size_bins'] = {}

    return stats


def main():
    base = os.path.dirname(__file__)
    files = {
        'simple': os.path.join(base, 'simple_questions.json'),
        'complex': os.path.join(base, 'complex_questions.json'),
        'aggregated': os.path.join(base, 'aggregated_questions.json')
    }

    report = {}
    for cat, path in files.items():
        if os.path.exists(path):
            report[cat] = analyze_file(path)

    out_json = os.path.join(base, 'questions_analysis.json')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # also write CSV summary per category
    csv_lines = ['category,total_samples,avg_joins,avg_where_conditions,distinct_property_count,mean_result_size,median_result_size']
    for cat, st in report.items():
        mean_rs = st['result_size_stats'].get('mean', '')
        median_rs = st['result_size_stats'].get('median', '')
        csv_lines.append(f"{cat},{st['total_samples']},{st['avg_joins']:.3f},{st['avg_where_conditions']:.3f},{st['distinct_property_count']},{mean_rs},{median_rs}")

    out_csv = os.path.join(base, 'questions_analysis.csv')
    with open(out_csv, 'w', encoding='utf-8', newline='') as f:
        f.write('\n'.join(csv_lines))

    print('Analysis written to', out_json, 'and', out_csv)


if __name__ == '__main__':
    main()
