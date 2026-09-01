import csv
import json
import os
import statistics
import time
from collections import Counter, defaultdict

import pymysql


BASE_DIR = os.path.dirname(__file__)
INPUT_FILES = {
    'simple': os.path.join(BASE_DIR, 'simple_questions.json'),
    'complex': os.path.join(BASE_DIR, 'complex_questions.json'),
    'aggregated': os.path.join(BASE_DIR, 'aggregated_questions.json'),
}
OUTPUT_JSON = os.path.join(BASE_DIR, 'runtime_report.json')
OUTPUT_CSV = os.path.join(BASE_DIR, 'runtime_report.csv')


def get_conn():
    return pymysql.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', '123456'),
        database=os.getenv('MYSQL_DATABASE', 'smart_small'),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.Cursor,
        autocommit=True,
    )


def normalize_sql(sql: str) -> str:
    return sql.strip().rstrip(';')


def norm_value(v):
    try:
        from decimal import Decimal
        if isinstance(v, Decimal):
            return float(v)
    except Exception:
        pass
    if isinstance(v, bytes):
        try:
            return v.decode('utf-8')
        except Exception:
            return v.decode('latin-1', errors='ignore')
    try:
        json.dumps(v)
        return v
    except Exception:
        return str(v)


def load_samples(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_category(conn, samples):
    cursor = conn.cursor()
    timings_ms = []
    failures = []
    result_sizes = []

    for sample in samples:
        sql = normalize_sql(sample.get('sql', ''))
        sid = sample.get('sample_id')
        if not sql:
            failures.append({'sample_id': sid, 'error': 'empty sql'})
            continue

        t0 = time.perf_counter()
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            _ = [norm_value(r[0] if isinstance(r, (tuple, list)) else r) for r in rows]
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            timings_ms.append(elapsed_ms)
            result_sizes.append(len(rows))
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            failures.append({'sample_id': sid, 'error': str(e), 'elapsed_ms': elapsed_ms})

    cursor.close()
    return timings_ms, result_sizes, failures


def summarize(values):
    if not values:
        return {'count': 0}
    return {
        'count': len(values),
        'mean_ms': statistics.mean(values),
        'median_ms': statistics.median(values),
        'min_ms': min(values),
        'max_ms': max(values),
        'p95_ms': statistics.quantiles(values, n=20)[18] if len(values) >= 20 else max(values),
    }


def main():
    conn = get_conn()
    report = {}
    rows_for_csv = []

    for category, path in INPUT_FILES.items():
        samples = load_samples(path)
        timings_ms, result_sizes, failures = run_category(conn, samples)
        report[category] = {
            'total_samples': len(samples),
            'executed_samples': len(timings_ms),
            'failed_samples': len(failures),
            'timing_summary_ms': summarize(timings_ms),
            'result_size_summary': {
                'mean': statistics.mean(result_sizes) if result_sizes else 0,
                'median': statistics.median(result_sizes) if result_sizes else 0,
                'min': min(result_sizes) if result_sizes else 0,
                'max': max(result_sizes) if result_sizes else 0,
            },
            'failures': failures[:20],
        }
        rows_for_csv.append({
            'category': category,
            'total_samples': len(samples),
            'executed_samples': len(timings_ms),
            'failed_samples': len(failures),
            'mean_ms': report[category]['timing_summary_ms'].get('mean_ms', ''),
            'median_ms': report[category]['timing_summary_ms'].get('median_ms', ''),
            'min_ms': report[category]['timing_summary_ms'].get('min_ms', ''),
            'max_ms': report[category]['timing_summary_ms'].get('max_ms', ''),
            'p95_ms': report[category]['timing_summary_ms'].get('p95_ms', ''),
        })

    conn.close()

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_CSV, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_for_csv[0].keys()))
        writer.writeheader()
        writer.writerows(rows_for_csv)

    print('Runtime report written to:')
    print(' ', OUTPUT_JSON)
    print(' ', OUTPUT_CSV)
    for category, info in report.items():
        ts = info['timing_summary_ms']
        print(f"{category}: mean={ts.get('mean_ms', 0):.3f} ms, median={ts.get('median_ms', 0):.3f} ms, executed={info['executed_samples']}, failed={info['failed_samples']}")
        if info['failures']:
            print('  first failure:', info['failures'][0])


if __name__ == '__main__':
    main()
