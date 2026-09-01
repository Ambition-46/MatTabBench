#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
处理 sql_nl_test_samples_500_0807_result_data.json:
1. 删除所有 natural_language_en 字段（英文问题部分）
2. 对非聚合问题，将 result 中的 data_id 匹配到 data 目录下的完整数据记录，
   放入 result_data 字段
3. 聚合问题(MAX/MIN/AVG/SUM/COUNT)不进行匹配
"""

import json
import os
import re
import sys
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# 路径
RESULT_FILE = r'f:\Study\科研任务\论文\评测集\Code\评测集修改\500\0807\sql_nl_test_samples_500_0807_result_data.json'
DATA_DIR = r'f:\Study\科研任务\论文\评测集\Code\data'


def is_aggregation(sql):
    """判断SQL是否为聚合查询（MAX/MIN/AVG/SUM/COUNT）"""
    return bool(re.search(r'\b(MAX|MIN|AVG|SUM|COUNT)\s*\(', sql, re.IGNORECASE))


def build_id_index(data_dir):
    """
    遍历 data 目录下所有 JSON 文件，建立 data_id -> 完整记录 的索引。
    支持两种格式:
    1. dict: {"data": [{"meta": {"数据ID": id}, "content": {...}}, ...]}
    2. list: [{"_meta_id": id, ...}, ...]
    """
    index = {}
    stats = {'files': 0, 'records': 0, 'dict_format': 0, 'list_format': 0}
    print("读取data目录下的JSON文件...")

    for fname in sorted(os.listdir(data_dir)):
        if fname.endswith('.bak'):
            continue
        fpath = os.path.join(data_dir, fname)
        if not fname.endswith('.json'):
            continue

        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except Exception as e:
            print(f"  [WARN] 跳过 {fname}: {e}")
            continue

        records = []
        if isinstance(d, dict) and 'data' in d:
            # 格式1: dict wrapper
            records = d['data']
            stats['dict_format'] += 1
            id_path = 'meta.数据ID'
        elif isinstance(d, list):
            # 格式2: list
            records = d
            stats['list_format'] += 1
            id_path = '_meta_id'
        else:
            print(f"  [WARN] 未知格式: {fname}")
            continue

        file_matched = 0
        for rec in records:
            # 尝试多种方式获取ID
            rid = None
            if isinstance(rec, dict):
                # 格式1: meta.数据ID
                meta = rec.get('meta', {})
                if isinstance(meta, dict):
                    rid = meta.get('数据ID')
                # 格式2: _meta_id
                if rid is None:
                    rid = rec.get('_meta_id')

            if rid is not None:
                # 统一转为 int 类型作为 key
                try:
                    rid = int(rid)
                except (ValueError, TypeError):
                    pass
                index[rid] = rec
                file_matched += 1

        stats['records'] += file_matched
        stats['files'] += 1

    print(f"  共处理 {stats['files']} 个文件, {stats['records']} 条记录")
    print(f"  dict格式: {stats['dict_format']}, list格式: {stats['list_format']}")
    return index


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    # 1. 读取结果文件
    print(f"读取结果文件: {RESULT_FILE}")
    with open(RESULT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  共 {len(data)} 条数据")

    # 2. 删除 natural_language_en 字段
    en_deleted = 0
    for item in data:
        if 'natural_language_en' in item:
            del item['natural_language_en']
            en_deleted += 1
    print(f"  删除 natural_language_en: {en_deleted} 条")

    # 3. 识别聚合查询和非聚合查询
    agg_items = []
    non_agg_items = []
    for item in data:
        if is_aggregation(item.get('sql', '')):
            agg_items.append(item)
        else:
            non_agg_items.append(item)
    print(f"  聚合查询(跳过匹配): {len(agg_items)} 条")
    print(f"  非聚合查询(需要匹配): {len(non_agg_items)} 条")

    # 4. 建立 ID 索引
    id_index = build_id_index(DATA_DIR)

    # 5. 对非聚合查询进行匹配
    print("\n匹配 data_id -> 完整记录...")
    matched_total = 0
    unmatched_total = 0
    unmatched_ids = []

    for item in non_agg_items:
        sample_id = item.get('sample_id', '?')
        result_ids = item.get('result', [])
        result_data = []

        for rid in result_ids:
            try:
                key = int(rid)
            except (ValueError, TypeError):
                key = rid

            rec = id_index.get(key)
            if rec is not None:
                result_data.append(rec)
                matched_total += 1
            else:
                unmatched_total += 1
                unmatched_ids.append((sample_id, rid))

        item['result_data'] = result_data

    # 聚合查询也加空 result_data
    for item in agg_items:
        item['result_data'] = []

    print(f"  匹配成功: {matched_total} 条")
    print(f"  未匹配: {unmatched_total} 条")

    if unmatched_ids:
        print(f"\n  未匹配的ID (前20个):")
        for sid, rid in unmatched_ids[:20]:
            print(f"    sample_id={sid}, data_id={rid}")

    # 6. 写回文件
    print(f"\n写回文件: {RESULT_FILE}")
    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)

    print("完成!")

    # 7. 汇总
    print("\n" + "=" * 60)
    print("处理汇总:")
    print(f"  总问题数: {len(data)}")
    print(f"  删除EN字段: {en_deleted} 条")
    print(f"  聚合查询(无result_data): {len(agg_items)} 条")
    print(f"  非聚合查询(有result_data): {len(non_agg_items)} 条")
    print(f"  数据匹配成功率: {matched_total}/{matched_total + unmatched_total}"
          f" ({100*matched_total/(matched_total+unmatched_total):.1f}%)"
          if (matched_total + unmatched_total) > 0 else "N/A")
    print("=" * 60)


if __name__ == '__main__':
    main()
