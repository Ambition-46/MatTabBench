#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
边界条件测试（Boundary Condition Testing）
- 统计 >、<、<=、>=、BETWEEN 条件的查询数量
- 提取涉及的属性
- 在 smart_small（最终评测库）上执行全数据库扫描验证：
  依据样本 SQL 的全部过滤条件（每个 value_table 别名一组）构造独立扫描查询，
  将扫描命中数与样本金标准 result 长度比对（相等即通过，验证结果完整覆盖）
- 生成测试报告（JSON / CSV / Markdown）

输入：../data/sql_nl_test_samples_500_result_data.json（最终 500 样本）
数据库：MySQL smart_small（密码可用 MYSQL_PASSWORD 环境变量覆盖）
"""

import json
import re
import os
import csv
import pymysql
from collections import defaultdict
from datetime import datetime

MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': os.getenv('MYSQL_PASSWORD', '12345678'),
    'database': 'smart_small',
    'charset': 'utf8mb4'
}

SAMPLE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'data', 'sql_nl_test_samples_500_result_data.json')

AGG_PATTERN = re.compile(r'\b(AVG|MAX|MIN|SUM|COUNT)\s*\(', re.IGNORECASE)

# 条件解析模式（按 value_table 别名分组）
ALIAS_PROP_PATTERN = re.compile(r'(\w+)\.property_id\s*=\s*(\d+)')
ALIAS_VALUE_STR_PATTERN = re.compile(r"(\w+)\.value\s*(=|!=|<>)\s*'((?:[^']|'')*)'")
ALIAS_VALUE_LIKE_PATTERN = re.compile(r"(\w+)\.value\s+(?:NOT\s+)?LIKE\s+'((?:[^']|'')*)'", re.IGNORECASE)
# 数据清洗谓词（仅当样本中出现时才镜像到扫描中）
ALIAS_CLEAN_NE_PATTERN = re.compile(r"(\w+)\.value\s*!=\s*''")
ALIAS_CLEAN_NN_PATTERN = re.compile(r"(\w+)\.value\s+IS\s+NOT\s+NULL")
# CAST 数值条件（BETWEEN 容忍 "1.05AND 1.1" 这类少空格写法）
ALIAS_VALUE_NUM_PATTERN = re.compile(
    r'CAST\(\s*(\w+)\.value\s+AS\s+DECIMAL\(30\s*,\s*15\)\)\s*(>=|<=|>|<|=|!=|<>)\s*([0-9.eE+\-]+)')
ALIAS_VALUE_BETWEEN_PATTERN = re.compile(
    r'CAST\(\s*(\w+)\.value\s+AS\s+DECIMAL\(30\s*,\s*15\)\)\s*BETWEEN\s*([0-9.eE+\-]+)(?:AND|\s+AND)\s*([0-9.eE+\-]+)')
# 无 CAST 的裸数值条件（镜像样本的隐式转换语义）
ALIAS_VALUE_NUM_BARE_PATTERN = re.compile(
    r'(\w+)\.value\s*(>=|<=|>|<|=|!=|<>)\s*([0-9.eE+\-]+)')
ALIAS_VALUE_BETWEEN_BARE_PATTERN = re.compile(
    r'(\w+)\.value\s*BETWEEN\s*([0-9.eE+\-]+)(?:AND|\s+AND)\s*([0-9.eE+\-]+)')

BOUNDARY_TYPES = ['greater', 'greater_equal', 'less', 'less_equal', 'range']


def classify_question(sql):
    """按论文三类模板分类：聚合 / 复杂关联 / 简单。"""
    if AGG_PATTERN.search(sql):
        return 'aggregated'
    joins = len(re.findall(r'JOIN\s+[\w.]+\.value_table', sql, re.IGNORECASE))
    props = len(set(re.findall(r'property_id\s*=\s*(\d+)', sql)))
    if joins >= 2 or props >= 2:
        return 'complex'
    return 'simple'


def classify_boundary_query(sql):
    """识别样本中的数值边界条件类型（>、>=、<、<=、BETWEEN），返回类型列表。"""
    sql_clean = ' '.join(sql.split()).upper()
    types = []
    if re.search(r'BETWEEN\s+[0-9.\-+]+(?:AND|\s+AND)\s+[0-9.\-+]+', sql_clean) and 'DECIMAL' in sql_clean:
        types.append('range')
    ops = re.findall(r'(>=|<=|>|<)\s*([0-9.eE\-+]+)', sql_clean)
    if ops and 'DECIMAL' in sql_clean:
        for op, _ in ops:
            name = {'>': 'greater', '>=': 'greater_equal', '<': 'less', '<=': 'less_equal'}[op]
            if name not in types:
                types.append(name)
    return types or ['none']


def extract_conditions(sql):
    """从样本 SQL 解析全部过滤条件：
    {alias: {'property_id': int, 'ne_empty': bool, 'not_null': bool,
             'conds': [('num'/'bare_num', op, v) | ('str', op, v) | ('between'/'bare_between', a, b)]}}"""
    conds = defaultdict(lambda: {'property_id': None, 'ne_empty': False, 'not_null': False, 'conds': []})
    for m in ALIAS_PROP_PATTERN.finditer(sql):
        conds[m.group(1)]['property_id'] = int(m.group(2))
    for m in ALIAS_CLEAN_NE_PATTERN.finditer(sql):
        conds[m.group(1)]['ne_empty'] = True
    for m in ALIAS_CLEAN_NN_PATTERN.finditer(sql):
        conds[m.group(1)]['not_null'] = True
    for m in ALIAS_VALUE_STR_PATTERN.finditer(sql):
        conds[m.group(1)]['conds'].append(('str', m.group(2), m.group(3)))
    for m in ALIAS_VALUE_LIKE_PATTERN.finditer(sql):
        conds[m.group(1)]['conds'].append(('like', m.group(2)))
    for m in ALIAS_VALUE_BETWEEN_PATTERN.finditer(sql):
        conds[m.group(1)]['conds'].append(('between', m.group(2), m.group(3)))
    for m in ALIAS_VALUE_NUM_PATTERN.finditer(sql):
        conds[m.group(1)]['conds'].append(('num', m.group(2), m.group(3)))
    for m in ALIAS_VALUE_BETWEEN_BARE_PATTERN.finditer(sql):
        conds[m.group(1)]['conds'].append(('bare_between', m.group(2), m.group(3)))
    for m in ALIAS_VALUE_NUM_BARE_PATTERN.finditer(sql):
        conds[m.group(1)]['conds'].append(('bare_num', m.group(2), m.group(3)))
    return {a: c for a, c in conds.items() if c['property_id'] is not None}


def build_scan_sql(conditions):
    """按全部条件构造独立全库扫描查询（DISTINCT data_id 计数），
    与样本 SQL 的过滤语义一一镜像（含清洗谓词与裸数值比较）。"""
    aliases = sorted(conditions.keys())
    joins = '\n'.join(
        f"JOIN smart_small.value_table {a} ON {a}.data_id = e.data_id"
        for a in aliases[1:])
    where_parts = []
    for a in aliases:
        c = conditions[a]
        where_parts.append(f"{a}.property_id = {c['property_id']}")
        if c['ne_empty']:
            where_parts.append(f"{a}.value != ''")
        if c['not_null']:
            where_parts.append(f"{a}.value IS NOT NULL")
        for cond in c['conds']:
            kind = cond[0]
            if kind == 'num':
                _, op, v = cond
                where_parts.append(f"CAST({a}.value AS DECIMAL(30, 15)) {op} {v}")
            elif kind == 'bare_num':
                _, op, v = cond
                where_parts.append(f"{a}.value {op} {v}")
            elif kind == 'str':
                _, op, v = cond
                where_parts.append(f"{a}.value {op} '{v}'")
            elif kind == 'like':
                _, v = cond
                where_parts.append(f"{a}.value LIKE '{v}'")
            elif kind == 'between':
                _, lo, hi = cond
                where_parts.append(f"CAST({a}.value AS DECIMAL(30, 15)) BETWEEN {lo} AND {hi}")
            elif kind == 'bare_between':
                _, lo, hi = cond
                where_parts.append(f"{a}.value BETWEEN {lo} AND {hi}")
    join_first = (f"JOIN smart_small.value_table {aliases[0]} ON {aliases[0]}.data_id = e.data_id"
                  if aliases else "")
    sql = (f"SELECT COUNT(DISTINCT e.data_id) FROM smart_small.entity_table e {join_first}\n"
           f"{joins}\nWHERE " + ' AND '.join(where_parts))
    return sql


def get_property_names(conn, property_ids):
    """查询属性名称。"""
    names = {}
    if not property_ids:
        return names
    ids = ', '.join(map(str, property_ids))
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT property_id, property_name FROM smart_small.property_table "
                    f"WHERE property_id IN ({ids})")
        for pid, name in cur.fetchall():
            names[pid] = name
    except Exception:
        pass
    return names


def main():
    print("=" * 80)
    print("边界条件测试（Boundary Condition Testing）—— smart_small / 最终 500 样本")
    print("=" * 80)

    with open(SAMPLE_FILE, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    print(f"\n[1] 加载样本: {len(samples)} 条 (from {SAMPLE_FILE})")

    # 分类 + 边界查询统计
    classification = {s['sample_id']: classify_question(s['sql']) for s in samples}
    boundary_queries = defaultdict(list)
    properties_by_type = defaultdict(set)

    for s in samples:
        types = classify_boundary_query(s['sql'])
        conds = extract_conditions(s['sql'])
        for btype in types:
            if btype == 'none':
                continue
            boundary_queries[btype].append({
                'sample_id': s['sample_id'],
                'sql': s['sql'],
                'natural_language': s.get('natural_language', ''),
                'result': s.get('result', []),
                'conditions': conds,
            })
            for pid in {c['property_id'] for c in conds.values()}:
                properties_by_type[btype].add(pid)

    print("\n[2] 边界条件查询统计:")
    for btype in BOUNDARY_TYPES:
        print(f"   {btype:15s}: {len(boundary_queries[btype]):3d} 条, "
              f"{len(properties_by_type[btype]):2d} 个属性")

    boundary_by_category = defaultdict(lambda: defaultdict(int))
    for btype, queries in boundary_queries.items():
        for q in queries:
            boundary_by_category[btype][classification[q['sample_id']]] += 1

    conn = pymysql.connect(**MYSQL_CONFIG)
    try:
        print("\n[3] 执行 smart_small 全库扫描验证（扫描命中数 == 金标准 result 长度）...")
        report_data = []
        validation_by_category = defaultdict(lambda: {'passed': 0, 'failed': 0, 'total': 0, 'result_counts': []})
        failed_details = []

        for btype in BOUNDARY_TYPES:
            queries = boundary_queries[btype]
            if not queries:
                continue
            passed_count = failed_count = 0
            result_counts = []
            cur = conn.cursor()
            for q in queries:
                scan_sql = build_scan_sql(q['conditions'])
                try:
                    cur.execute(scan_sql)
                    cnt = cur.fetchone()[0] or 0
                except Exception as e:
                    cnt = -1
                    failed_details.append((q['sample_id'], btype, f'扫描失败: {e}'))
                gold = len(q['result'])
                passed = (cnt == gold)
                result_counts.append(cnt)
                cat = classification[q['sample_id']]
                if passed:
                    passed_count += 1
                    validation_by_category[cat]['passed'] += 1
                else:
                    failed_count += 1
                    validation_by_category[cat]['failed'] += 1
                    failed_details.append((q['sample_id'], btype, f'扫描 {cnt} vs 金标准 {gold}'))
                validation_by_category[cat]['total'] += 1
                validation_by_category[cat]['result_counts'].append(cnt)

            props = sorted(properties_by_type[btype])
            names = get_property_names(conn, props)
            prop_names = [f"{p}({names.get(p, '')})" for p in props]
            avg = sum(result_counts) / len(result_counts) if result_counts else 0
            report_data.append({
                'Boundary_Query_Subset': btype.replace('_', ' ').title(),
                'Samples': len(queries),
                'Properties_Covered': len(props),
                'Property_IDs': ', '.join(map(str, props[:8])) + ('...' if len(props) > 8 else ''),
                'Validation_Method': 'Full Database Scan (smart_small) == Gold',
                'Passed': passed_count,
                'Failed': failed_count,
                'Pass_Rate': f"{100.0 * passed_count / len(queries):.1f}%" if queries else "N/A",
                'Avg_Result_Count': f"{avg:.0f}",
                'Max_Result_Count': max(result_counts) if result_counts else 0,
                'Min_Result_Count': min(result_counts) if result_counts else 0,
            })
            print(f"   验证 {btype:15s}: 通过 {passed_count}/{len(queries)} "
                  f"({100.0 * passed_count / len(queries):.1f}%), 结果数 min={min(result_counts) if result_counts else 0}, "
                  f"avg={avg:.0f}, max={max(result_counts) if result_counts else 0}")

        # 按问题分类验证
        cat_labels = {'simple': '简单检索', 'complex': '复杂关联', 'aggregated': '聚合计算'}
        print("\n   按问题分类的验证通过率:")
        for cat in ['simple', 'complex', 'aggregated']:
            info = validation_by_category.get(cat, {'total': 0, 'passed': 0, 'failed': 0})
            if info['total']:
                print(f"     {cat_labels[cat]}: {info['passed']}/{info['total']} "
                      f"({100.0 * info['passed'] / info['total']:.1f}%)")
            else:
                print(f"     {cat_labels[cat]}: 无边界查询")

        # 报告文件
        report = {
            'timestamp': datetime.now().isoformat(),
            'database': 'smart_small',
            'sample_file': SAMPLE_FILE,
            'total_samples': len(samples),
            'boundary_summary': {
                'total_boundary_queries': sum(len(qs) for qs in boundary_queries.values()),
                'by_type': {b: {'count': len(boundary_queries[b]),
                                'properties': len(properties_by_type[b])}
                            for b in BOUNDARY_TYPES}
            },
            'validation_results': report_data,
            'validation_by_category': {
                cat: {'total': i['total'], 'passed': i['passed'], 'failed': i['failed'],
                      'pass_rate': f"{100.0 * i['passed'] / i['total']:.1f}%" if i['total'] else "N/A"}
                for cat, i in validation_by_category.items()
            },
            'failed_details': failed_details,
        }
        with open('boundary_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        with open('boundary_test_report.csv', 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Boundary_Query_Subset', 'Samples', 'Properties_Covered', 'Property_IDs',
                'Validation_Method', 'Passed', 'Failed', 'Pass_Rate',
                'Avg_Result_Count', 'Max_Result_Count', 'Min_Result_Count'])
            writer.writeheader()
            writer.writerows(report_data)

        # Markdown 摘要
        total_boundary = sum(len(qs) for qs in boundary_queries.values())
        total_props = len(set().union(*[properties_by_type[b] for b in BOUNDARY_TYPES]))
        total_passed = sum(r['Passed'] for r in report_data)
        total_tests = sum(r['Passed'] + r['Failed'] for r in report_data)
        md_lines = [
            '# 边界条件测试报告（Boundary Condition Testing Report）',
            '',
            f'- 生成时间: {datetime.now().isoformat()}',
            f'- 数据库: smart_small（最终评测库，43 数据集 / 2,138 实体 / 30,462 数值记录）',
            f'- 样本: {SAMPLE_FILE}（最终 500 样本）',
            '',
            '## 关键指标',
            '',
            f'- 边界条件查询总数: **{total_boundary}** 条 ({100.0 * total_boundary / len(samples):.1f}% of all samples)',
            f'- 涉及属性总数: **{total_props}** 个',
            f'- 全数据库扫描验证通过率（扫描命中数 == 金标准结果集长度）: '
            f'**{100.0 * total_passed / total_tests:.1f}%** ({total_passed}/{total_tests})',
            '',
            '| Boundary Query Subset | Samples | Properties | Passed | Failed | Pass Rate | Result Range (min-avg-max) |',
            '|---|---|---|---|---|---|---|',
        ]
        for row in report_data:
            md_lines.append(
                f"| {row['Boundary_Query_Subset']} | {row['Samples']} | {row['Properties_Covered']} | "
                f"{row['Passed']} | {row['Failed']} | {row['Pass_Rate']} | "
                f"{row['Min_Result_Count']}-{row['Avg_Result_Count']}-{row['Max_Result_Count']} |")
        if failed_details:
            md_lines.append('')
            md_lines.append('## 未通过样本明细')
            for sid, btype, msg in failed_details:
                md_lines.append(f'- 样本 {sid} ({btype}): {msg}')
        with open('BOUNDARY_TEST_SUMMARY.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines) + '\n')

        print("\n[4] 报告已保存: boundary_test_report.json / boundary_test_report.csv / BOUNDARY_TEST_SUMMARY.md")
        print(f"\n结论: 边界条件查询 {total_boundary} 条, 涉及属性 {total_props} 个, "
              f"全库扫描验证通过率 {100.0 * total_passed / total_tests:.1f}% ({total_passed}/{total_tests})")
    finally:
        conn.close()


if __name__ == '__main__':
    main()
