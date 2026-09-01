#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检测运算符方向真正不一致的条目（修复误报）"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

file = r'f:\Study\科研任务\论文\评测集\Code\评测集修改\500\0807\sql_nl_test_samples_500_0807_result.json'
with open(file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 注意顺序：否定形式在前，避免 "不超过" 被 "超过" 误匹配
greater_patterns = [
    ('不小于', '>='), ('不低于', '>='), ('不少于', '>='), ('大于等于', '>='),
    ('大于', '>'), ('高于', '>'), ('超过', '>'), ('超出', '>'), ('高出', '>'), ('突破', '>'),
]
less_patterns = [
    ('不大于', '<='), ('不超过', '<='), ('不高于', '<='), ('小于等于', '<='),
    ('小于', '<'), ('低于', '<'), ('不到', '<'), ('不足', '<'), ('少于', '<'),
    ('控制在', '<='),   # "控制在X以内/以下"
]

real_mismatches = []

for item in data:
    sid = item['sample_id']
    nl = item['natural_language']
    sql = item['sql']

    # 提取SQL数值比较：property_id -> CAST -> op value
    sql_parts = sql.split('WHERE')[1] if 'WHERE' in sql else sql
    # 按 AND/OR 分割
    sql_conds = re.split(r'\s+(?:AND|OR)\s+', sql_parts, flags=re.IGNORECASE)

    # 解析每个条件：property_id=N ... CAST(v.value...) OP value
    sql_ops = []
    for cond in sql_conds:
        pid_m = re.search(r'property_id\s*=\s*(\d+)', cond)
        cast_m = re.search(r'CAST\(v\d*\.value.*?\)\s*(>=|<=|!=|>|<|=)\s*([\d.eE+-]+)', cond)
        str_m = re.search(r"v\d*\.value\s*(=|!=)\s*'([^']+)'", cond)
        if pid_m and cast_m:
            sql_ops.append({'pid': pid_m.group(1), 'op': cast_m.group(1), 'val': cast_m.group(2)})
        elif pid_m and str_m:
            sql_ops.append({'pid': pid_m.group(1), 'op': str_m.group(1), 'val': str_m.group(2)})

    def value_match(v1, v2):
        """比较两个数值是否相近"""
        try:
            return abs(float(v1) - float(v2)) < 0.001
        except ValueError:
            return v1 == v2

    # 检查每个NL条件与SQL条件
    for kw, expected_op in greater_patterns:
        # 用词边界确保不会误匹配子串
        pat = re.compile(r'([\u4e00-\u9fa5a-zA-Z]+?)\s*' + re.escape(kw) + r'\s*([\d.]+)')
        for m in pat.finditer(nl):
            prop = m.group(1).strip()
            nl_val = m.group(2)
            for sc in sql_ops:
                if value_match(sc['val'], nl_val):
                    # 大于类关键词 -> SQL 用了 < 或 <= 就是反了
                    if sc['op'] in ('<', '<='):
                        real_mismatches.append({
                            'sid': sid, 'nl': nl,
                            'issue': f'"{prop}" NL用"{kw}{nl_val}"(应>{sc["op"]}), SQL用了{sc["op"]}',
                        })
                    break

    for kw, expected_op in less_patterns:
        # "控制在" 特殊处理：控制在X以内/以下
        if kw == '控制在':
            pat = re.compile(r'([\u4e00-\u9fa5a-zA-Z]+?)\s*' + re.escape(kw) + r'\s*([\d.]+)')
        else:
            pat = re.compile(r'([\u4e00-\u9fa5a-zA-Z]+?)\s*' + re.escape(kw) + r'\s*([\d.]+)')
        for m in pat.finditer(nl):
            prop = m.group(1).strip()
            nl_val = m.group(2)
            for sc in sql_ops:
                if value_match(sc['val'], nl_val):
                    # 小于类关键词 -> SQL 用了 > 或 >= 就是反了
                    if sc['op'] in ('>', '>='):
                        real_mismatches.append({
                            'sid': sid, 'nl': nl,
                            'issue': f'"{prop}" NL用"{kw}{nl_val}"(应<={sc["op"]}), SQL用了{sc["op"]}',
                        })
                    break

print(f'真正运算符方向错误: {len(real_mismatches)} 条')
print()
for m in real_mismatches:
    print(f"[{m['sid']}] {m['nl']}")
    print(f"  -> {m['issue']}")
    print()
