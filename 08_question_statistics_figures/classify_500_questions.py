#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 sql_nl_test_samples_500_result_data.json 中的 500 个样本按问题类型分为三类：

  1. Simple Retrieval（简单检索）：
     严格限定为单一属性、单一数据集内的查询——通过 value_table(T_V) 到
     entity_table 的单次连接提取数据，不涉及跨数据集、多属性联合过滤或嵌套子查询。

  2. Complex Correlation Retrieval（复杂关联检索）：
     目标数据跨数据集或涉及多个属性，通过 AND/OR 等多维逻辑算符进行联合属性过滤，
     利用 T_V 上的自连接（或子查询）解析多属性与跨数据集依赖。

  3. Aggregated Attribute Calculation Queries（聚合属性计算查询）：
     使用 AVG/MAX/MIN 聚合函数，对跨实体数据集执行统计汇总与边界识别。

分类依据：读取每个样本的 natural_language（自然语言问题），并结合其配对 SQL 的
结构特征相互印证：
  - SQL 含 AVG(/MAX(/MIN( 聚合函数        -> 聚合属性计算查询
  - SQL 对 value_table 自连接 >=2 次，或含 >=2 个不同 property_id，或含子查询
                                          -> 复杂关联检索
  - 其余（单属性 + 单次连接）              -> 简单检索
自然语言关键词（平均/最大/最小/统计 -> 聚合；且/同时/并且/以及 -> 多属性）作为
交叉验证统计输出，不单独作为分类依据（SQL 为问题语义的权威表示）。

输出：
  - simple_retrieval.json                       简单检索样本（整条样本）
  - complex_correlation_retrieval.json          复杂关联检索样本（整条样本）
  - aggregated_attribute_calculation.json       聚合属性计算查询样本（整条样本）
  - 控制台打印各类样本条数与占比
"""
import json
import os
import re
from collections import Counter

# 输入/输出路径（脚本与输入 json 在同一父目录下）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, '..', 'sql_nl_test_samples_500_result_data.json')

OUTPUT_FILES = {
    'simple': os.path.join(BASE_DIR, 'simple_retrieval.json'),
    'complex': os.path.join(BASE_DIR, 'complex_correlation_retrieval.json'),
    'aggregated': os.path.join(BASE_DIR, 'aggregated_attribute_calculation.json'),
}

CATEGORY_NAMES = {
    'simple': 'Simple Retrieval（简单检索）',
    'complex': 'Complex Correlation Retrieval（复杂关联检索）',
    'aggregated': 'Aggregated Attribute Calculation Queries（聚合属性计算查询）',
}

# 聚合函数（对应分类定义中的 AVG / MAX / MIN）
AGG_PATTERN = re.compile(r'\b(AVG|MAX|MIN)\s*\(', re.IGNORECASE)
# 子查询（分类定义中的 nested subqueries / subqueries over T_V）
SUBQUERY_PATTERN = re.compile(r'\(\s*SELECT\b', re.IGNORECASE)
# 自然语言交叉验证关键词
NL_AGG_WORDS = ('平均', '最大', '最小', '统计')
NL_MULTI_WORDS = ('且', '同时', '并且', '以及', '都', '分别')


def classify_sample(item):
    """根据样本的 SQL 结构（主依据）与 natural_language（交叉验证）判定类别。"""
    sql = item.get('sql', '')
    nl = item.get('natural_language', '')

    # 1. 聚合属性计算查询：AVG / MAX / MIN
    if AGG_PATTERN.search(sql):
        return 'aggregated'

    # 2. 复杂关联检索：T_V 自连接（>=2 次 value_table 连接）或多属性（>=2 个 property_id）或子查询
    value_table_joins = len(re.findall(r'JOIN\s+[\w.]+\.value_table', sql, re.IGNORECASE))
    property_ids = set(re.findall(r'property_id\s*=\s*(\d+)', sql))
    if value_table_joins >= 2 or len(property_ids) >= 2 or SUBQUERY_PATTERN.search(sql):
        return 'complex'

    # 3. 简单检索：单一属性 + 单次 entity_table 连接
    return 'simple'


def classify_questions(input_file):
    # 读取原始数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    buckets = {'simple': [], 'complex': [], 'aggregated': []}

    # 交叉验证统计：natural_language 关键词与 SQL 判定类别的一致性
    agreement = Counter()
    nl_agg_hits = Counter()
    nl_multi_hits = Counter()

    for item in data:
        nl = item.get('natural_language', '')
        category = classify_sample(item)
        buckets[category].append(item)

        # 统计 natural_language 关键词命中情况（仅用于一致性报告）
        agreement[category] += 1
        if any(w in nl for w in NL_AGG_WORDS):
            nl_agg_hits[category] += 1
        if any(w in nl for w in NL_MULTI_WORDS):
            nl_multi_hits[category] += 1

    # 写出三个分类结果文件（整条样本）
    for category, items in buckets.items():
        with open(OUTPUT_FILES[category], 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

    # 打印分类统计结果
    total = len(data)
    print('=' * 72)
    print(f'总计处理样本: {total} 个')
    print('=' * 72)
    for category, name in CATEGORY_NAMES.items():
        n = len(buckets[category])
        pct = n / total * 100
        print(f'[{name}]')
        print(f'  条数: {n}  占比: {pct:.2f}%  ->  {os.path.basename(OUTPUT_FILES[category])}')

    # 验证三类合计 = 500
    assert sum(len(v) for v in buckets.values()) == total, '分类总数与样本数不一致！'

    # natural_language 交叉验证报告
    print('-' * 72)
    print('natural_language 关键词交叉验证（与 SQL 判定类别的对照）:')
    for category in ('aggregated', 'complex', 'simple'):
        n = agreement[category]
        a = nl_agg_hits[category]
        m = nl_multi_hits[category]
        print(f'  {CATEGORY_NAMES[category]}: {n} 条, '
              f'NL 含聚合词({NL_AGG_WORDS}) {a} 条 ({a / n * 100:.1f}%), '
              f'NL 含多属性并列词({NL_MULTI_WORDS}) {m} 条 ({m / n * 100:.1f}%)')

    # 每类抽样展示 natural_language 示例
    print('-' * 72)
    for category in ('simple', 'complex', 'aggregated'):
        print(f'--- {CATEGORY_NAMES[category]} natural_language 示例 ---')
        for item in buckets[category][:3]:
            print(f'  [样本 {item.get("sample_id")}] {item.get("natural_language", "")}')


if __name__ == '__main__':
    # 运行分类（脚本与输入 json 文件为 ../sql_nl_test_samples_500_result_data.json）
    classify_questions(INPUT_FILE)
