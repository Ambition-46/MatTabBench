#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统计三个分类（simple / complex / aggregated）下样本 SQL 与结果集的结构特征：

  - 平均 JOIN 数量          ：每条 SQL 中 JOIN 关键字的平均出现次数（min~max）
  - 平均 WHERE 数量         ：每条 SQL 中 WHERE 关键字的平均出现次数
                             （注：部分样本把过滤谓词写在 ON 子句中，故另统计条件数）
  - 平均过滤条件数          ：ON/WHERE 子句按顶层 AND/OR 拆分后的平均条件（谓词）
                             个数，剔除纯连接键相等条件（*.data_id = *.data_id）
                             （SELECT 列表、ORDER BY 等不计入；BETWEEN ... AND ...
                             视为单条件）
  - 独立属性总数            ：该类所有 SQL 中出现过的不同 property_id 的总数
                             （另给出每样本平均独立属性数）
  - 结果集数量的中位数      ：每条样本 result 列表长度的中位数（聚合类恒为 1，
                             表示单个统计值；简单/复杂类为命中实体 id 个数）

输入：../问题分类/ 下的三个分类结果 JSON 文件（整条样本）。
输出：控制台分类统计表。
"""
import json
import os
import re
import statistics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLASS_DIR = os.path.join(BASE_DIR, '..', '问题分类')

INPUT_FILES = {
    'simple': os.path.join(CLASS_DIR, 'simple_retrieval.json'),
    'complex': os.path.join(CLASS_DIR, 'complex_correlation_retrieval.json'),
    'aggregated': os.path.join(CLASS_DIR, 'aggregated_attribute_calculation.json'),
}

CATEGORY_NAMES = {
    'simple': 'Simple Retrieval（简单检索）',
    'complex': 'Complex Correlation Retrieval（复杂关联检索）',
    'aggregated': 'Aggregated Attribute Calculation Queries（聚合属性计算查询）',
}

JOIN_PATTERN = re.compile(r'\bJOIN\b', re.IGNORECASE)
WHERE_PATTERN = re.compile(r'\bWHERE\b', re.IGNORECASE)
PROPERTY_PATTERN = re.compile(r'property_id\s*=\s*(\d+)')
# 顶层 AND/OR 分隔符（配合括号深度判断，避免拆分 CAST(...) 等括号内的 AND）
AND_OR_PATTERN = re.compile(r'\s+(?:AND|OR)\s+', re.IGNORECASE)
# 纯连接键相等条件：v.data_id = e.data_id（不计为过滤条件）
JOIN_KEY_PATTERN = re.compile(r'^[\w.]+\.data_id\s*=\s*[\w.]+\.data_id$', re.IGNORECASE)


def split_top_level_and_or(sql):
    """按括号深度感知的顶层 AND/OR 拆分 SQL，返回片段列表。"""
    parts, depth, last = [], 0, 0
    for m in AND_OR_PATTERN.finditer(sql):
        depth += sql[last:m.start()].count('(') - sql[last:m.start()].count(')')
        if depth == 0:
            parts.append(sql[last:m.start()])
            last = m.end()
    parts.append(sql[last:])
    return parts


def filter_condition_count(sql):
    """统计 ON/WHERE 子句中的过滤条件（谓词）个数。

    方法：截取第一个顶层 ON/WHERE 之后的子句部分（本数据集 SQL 无子查询、
    无 CASE WHEN，SELECT 列表中的 v.value 引用不会被误计），去掉 ORDER BY，
    按顶层 AND/OR 拆分，合并 BETWEEN ... AND ...，剔除纯连接键条件后计数。
    """
    clause_start = re.search(r'\b(?:ON|WHERE)\b', sql, re.IGNORECASE)
    if not clause_start:
        return 0
    clause = sql[clause_start.end():]
    # 去掉 ORDER BY 及之后部分
    clause = re.split(r'\bORDER\s+BY\b', clause, maxsplit=1, flags=re.IGNORECASE)[0]

    parts = split_top_level_and_or(clause)
    # 合并被误拆的 BETWEEN ... AND ...
    merged = []
    for p in parts:
        if merged and merged[-1].rstrip().upper().endswith('BETWEEN'):
            merged[-1] += ' ' + p
        else:
            merged.append(p)

    conds = []
    for p in merged:
        p = p.strip().rstrip(';').strip()
        if not p or JOIN_KEY_PATTERN.match(p):
            continue  # 空片段或纯连接键（如 v.data_id = e.data_id）
        # 过滤谓词须引用 property_id 或 value 列（本数据集谓词仅涉及这两列；
        # 无连接的聚合查询使用裸列名 value，故也匹配 \bvalue\b）
        if re.search(r'\bproperty_id\b|\bvalue\b', p, re.IGNORECASE):
            conds.append(p)
    return len(conds)


def collect_stats(items):
    join_counts = []
    where_counts = []
    where_cond_counts = []
    result_sizes = []
    all_property_ids = set()
    per_sample_prop_counts = []

    for item in items:
        sql = item.get('sql', '')
        join_counts.append(len(JOIN_PATTERN.findall(sql)))
        where_counts.append(len(WHERE_PATTERN.findall(sql)))
        where_cond_counts.append(filter_condition_count(sql))

        prop_ids = set(PROPERTY_PATTERN.findall(sql))
        all_property_ids.update(prop_ids)
        per_sample_prop_counts.append(len(prop_ids))

        result = item.get('result', [])
        result_sizes.append(len(result) if isinstance(result, list) else 1)

    return {
        'samples': len(items),
        'avg_joins': statistics.mean(join_counts) if join_counts else 0,
        'min_joins': min(join_counts) if join_counts else 0,
        'max_joins': max(join_counts) if join_counts else 0,
        'avg_where': statistics.mean(where_counts) if where_counts else 0,
        'avg_where_conds': statistics.mean(where_cond_counts) if where_cond_counts else 0,
        'min_where_conds': min(where_cond_counts) if where_cond_counts else 0,
        'max_where_conds': max(where_cond_counts) if where_cond_counts else 0,
        'distinct_props': len(all_property_ids),
        'avg_props_per_sample': statistics.mean(per_sample_prop_counts) if per_sample_prop_counts else 0,
        'median_result_size': statistics.median(result_sizes) if result_sizes else 0,
    }


def main():
    print('=' * 96)
    print('各分类样本 SQL / 结果集结构统计')
    print('=' * 96)

    rows = {}
    for category, path in INPUT_FILES.items():
        with open(path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        rows[category] = collect_stats(items)

        s = rows[category]
        print(f"\n[{CATEGORY_NAMES[category]}]  (样本数: {s['samples']})")
        print(f"  平均 JOIN 数量        : {s['avg_joins']:.2f}  (范围 {s['min_joins']} ~ {s['max_joins']})")
        print(f"  平均 WHERE 数量       : {s['avg_where']:.2f}  (WHERE 关键字出现次数)")
        print(f"  平均过滤条件数        : {s['avg_where_conds']:.2f}  (ON/WHERE 中按 AND/OR 拆分的谓词, 范围 {s['min_where_conds']} ~ {s['max_where_conds']})")
        print(f"  独立属性总数          : {s['distinct_props']}  (每样本平均 {s['avg_props_per_sample']:.2f} 个)")
        print(f"  结果集数量中位数      : {s['median_result_size']:.0f}")

    # 汇总行
    total_samples = sum(r['samples'] for r in rows.values())
    print('\n' + '-' * 96)
    print(f'总计: {total_samples} 个样本')


if __name__ == '__main__':
    main()
