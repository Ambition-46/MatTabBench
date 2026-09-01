#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一致性验证：将 sql_nl_test_samples_500_result_data.json 中的 500 条 SQL
在 MySQL smart_small 库中逐条重跑，与记录的 gold result 比对。

  - 非聚合查询：比较返回的 data_id 有序列表与无序集合（论文要求 ID 列表 100% 匹配）
  - 聚合查询  ：比较数值（相对误差 <= 1e-9）
"""
import json
import os
import pymysql
import re
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE, '..', 'data', 'sql_nl_test_samples_500_result_data.json')

AGG_PATTERN = re.compile(r'\b(AVG|MAX|MIN|SUM|COUNT)\s*\(', re.IGNORECASE)


def main():
    with open(DATA_FILE, encoding='utf-8') as f:
        samples = json.load(f)
    print(f'样本数: {len(samples)}')

    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           password='12345678', charset='utf8mb4',
                           read_timeout=120, write_timeout=120)
    cur = conn.cursor()
    cur.execute('USE smart_small')

    ok_list = ok_set = agg_ok = 0
    mismatches = []
    errors = []
    t0 = time.time()
    for i, s in enumerate(samples):
        sql = s['sql'].rstrip(';').strip()
        gold = s['result']
        is_agg = bool(AGG_PATTERN.search(sql))
        try:
            cur.execute(sql)
            rows = [r[0] for r in cur.fetchall()]
        except Exception as e:
            errors.append((s['sample_id'], str(e)[:100]))
            continue

        if is_agg:
            # 聚合查询：单值比较
            if len(rows) == 1 and len(gold) == 1:
                try:
                    if abs(float(rows[0]) - float(gold[0])) <= 1e-9 * max(1.0, abs(float(gold[0]))):
                        agg_ok += 1
                    else:
                        mismatches.append((s['sample_id'], 'agg', rows, gold))
                except (TypeError, ValueError):
                    mismatches.append((s['sample_id'], 'agg非数值', rows, gold))
            else:
                mismatches.append((s['sample_id'], 'agg结果形态', rows, gold))
        else:
            # 非聚合查询：有序列表 + 无序集合 双重比较
            if rows == gold:
                ok_list += 1
            if set(rows) == set(gold) and len(rows) == len(gold):
                ok_set += 1
            else:
                mismatches.append((s['sample_id'], 'id列表', len(rows), len(gold),
                                   sorted(set(rows) - set(gold))[:5],
                                   sorted(set(gold) - set(rows))[:5]))

    elapsed = time.time() - t0
    n = len(samples)
    n_agg = sum(1 for s in samples if AGG_PATTERN.search(s['sql']))
    n_ret = n - n_agg

    print(f'总样本: {n} (聚合 {n_agg} / 非聚合 {n_ret})')
    print(f'执行错误(语法/运行失败): {len(errors)}')
    for sid, e in errors[:10]:
        print(f'  样本{sid}: {e}')
    print(f'聚合查询数值一致: {agg_ok}/{n_agg}')
    print(f'非聚合 有序列表一致: {ok_list}/{n_ret} ({ok_list/n_ret*100:.2f}%)')
    print(f'非聚合 无序集合一致: {ok_set}/{n_ret} ({ok_set/n_ret*100:.2f}%)')
    print(f'不一致样本数: {len(mismatches)}')
    for m in mismatches[:15]:
        print('  样本%s %s: 期望%s 实际%s' % m if len(m) == 4 else '  %s' % (m,))
    print(f'总耗时: {elapsed:.1f}s')


if __name__ == '__main__':
    main()
