#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检测 SQL 检索结果是否符合自然语言问题要求。
从以下维度检查:
1. 运算符方向: NL中的"大于/小于/不低于"等与SQL中的 > / < / >= 是否一致
2. 条件完整性: NL中提到的属性是否在SQL中都有对应
3. 结果合理性: 结果数量是否异常
"""

import json
import re
import sys

JSON_FILE = r'f:\Study\科研任务\论文\评测集\Code\评测集修改\500\0807\sql_nl_test_samples_500_0807_result.json'

# NL 运算符 -> SQL 运算符映射
NL_OP_MAP = {
    '大于': '>', '高于': '>', '超过': '>', '超出': '>', '高出': '>', '突破': '>',
    '大于等于': '>=', '不小于': '>=', '不低于': '>=', '不少于': '>=', '达到': '>=',
    '小于': '<', '低于': '<', '不到': '<', '不足': '<', '少于': '<',
    '小于等于': '<=', '不大于': '<=', '不超过': '<=', '不高于': '<=', '控制在': '<=',
    '等于': '=', '为': '=', '是': '=',
    '介于': 'BETWEEN', '处于': 'BETWEEN', '在.*之间': 'BETWEEN', '在.*到.*之间': 'BETWEEN',
}

# 可能的数据源属性关键词（用户问题中常出现的属性名）
PROPERTY_KEYWORDS = [
    '泊松比', '晶粒半径', '硬度', '碳含量', '硫含量', '弹性模量', '屈服强度',
    '抗拉强度', '断后伸长率', '断面收缩率', '延伸率', '冲击功', '冲击韧性',
    '剪切应力', '流变模量', '晶粒度', '电阻率', '比热', '比热容',
    '纳米压痕硬度', '纳米压痕模量', '辐照剂量', '压入深度', '开路电位',
    '极化电阻', '腐蚀速率', '腐蚀深度', '已腐蚀量', '氯离子沉积量',
    '暴露时间', '采集地点', '热处理工艺', '显微组织', '相结构',
    '试样类型', '测试机构', '牌号', '晶粒体积', '晶粒面数', '晶粒表面积',
    '电导率', '电子热导率', '温度', '锌', '硅', '碳', '硫', '铬', '锰',
    '镍', '铝', '铌', '钛', '钴', '钽', '磷', '氧', '氮',
    'Cr', 'Mn', 'Ni', 'Al', 'Nb', 'Ti', 'Co', 'Ta', 'P', 'O', 'N', 'C', 'Si', 'S', 'Zn',
    '质量分数', '含量',
]


def extract_nl_conditions(nl_text):
    """从自然语言中提取数值条件"""
    conditions = []
    # 匹配模式: 属性名 + 运算符词 + 数值
    patterns = [
        # "泊松比大于0.2"
        (r'([\u4e00-\u9fa5a-zA-Z]+)\s*(大于|高于|超过|超出|高出|突破)\s*([\d.]+)', '>'),
        # "硬度不低于350"
        (r'([\u4e00-\u9fa5a-zA-Z]+)\s*(不小于|不低于|不少于|大于等于|达到)\s*([\d.]+)', '>='),
        # "氯离子沉积量控制在11以下" / "腐蚀速率不到5"
        (r'([\u4e00-\u9fa5a-zA-Z]+)\s*(小于|低于|不到|不足|少于|控制在)\s*([\d.]+)(?:\s*(?:以下|以内|以下时))?', '<'),
        # "温度不超过1000" / "C质量分数不到0.5%"
        (r'([\u4e00-\u9fa5a-zA-Z]+)\s*(不大于|不超过|不高于|小于等于)\s*([\d.]+)', '<='),
        # "开路电位在0.13到0.15之间"
        (r'([\u4e00-\u9fa5a-zA-Z]+)\s*(?:在|介于|处于)?\s*([\d.]+)\s*(?:到|至|和|~|~)\s*([\d.]+)\s*(?:之间)?', 'BETWEEN'),
        # "等于"/"为"
        (r'([\u4e00-\u9fa5a-zA-Z]+)\s*(?:等于|为|是)\s*([\d.]+)', '='),
    ]

    for pattern, op in patterns:
        for match in re.finditer(pattern, nl_text):
            groups = match.groups()
            prop = groups[0].strip()
            if op == 'BETWEEN' and len(groups) >= 3:
                conditions.append({
                    'property': prop,
                    'op_nl': '介于/在...之间',
                    'op_sql': 'BETWEEN',
                    'value': f"{groups[1]} AND {groups[2]}",
                    'text': match.group(0)
                })
            elif op in ('>','<','>=','<=','=') and len(groups) >= 3:
                conditions.append({
                    'property': prop,
                    'op_nl': groups[1],
                    'op_sql': op,
                    'value': groups[2],
                    'text': match.group(0)
                })
    return conditions


def extract_sql_conditions(sql):
    """从SQL中提取数值比较条件"""
    conditions = []
    # CAST(v.value AS DECIMAL(30,15)) > 0.2
    cast_pattern = re.findall(
        r"CAST\(v\d*\.value AS DECIMAL\(\d+,\s*\d+\)\)\s*(>=|<=|!=|>|<|=)\s*([\d.]+)",
        sql
    )
    for op, val in cast_pattern:
        conditions.append({'op': op, 'value': val, 'type': 'numeric'})

    # v.value = 'xxx' (字符串比较)
    str_pattern = re.findall(
        r"v\d*\.value\s*(=|!=)\s*'([^']*)'",
        sql
    )
    for op, val in str_pattern:
        conditions.append({'op': op, 'value': val, 'type': 'string'})

    # v.property_id = N
    prop_ids = re.findall(r"v\d*\.property_id\s*=\s*(\d+)", sql)

    return conditions, prop_ids


def check_item(item):
    """检查单条数据的合理性，返回问题列表"""
    issues = []
    nl = item.get('natural_language', '')
    sql = item.get('sql', '')
    result = item.get('result', [])
    sid = item.get('sample_id', '?')

    # 1. 基础检查
    if not sql:
        issues.append({'type': 'error', 'msg': 'SQL为空'})
        return issues

    # 2. 提取NL条件和SQL条件
    nl_conds = extract_nl_conditions(nl)
    sql_conds, prop_ids = extract_sql_conditions(sql)

    # 3. 检查operator方向一致性
    for nc in nl_conds:
        # 在SQL中找对应的数值条件
        matched = False
        for sc in sql_conds:
            if sc['type'] == 'numeric' and sc['value'] == nc['value']:
                matched = True
                if sc['op'] != nc['op_sql']:
                    issues.append({
                        'type': 'op_mismatch',
                        'msg': f'运算符不一致: NL="{nc["text"]}" 期望{">/</>=/<=/="}, SQL用 {sc["op"]}',
                        'nl_text': nc['text'],
                        'nl_op': nc['op_sql'],
                        'sql_op': sc['op']
                    })
                break

    # 4. 检查空结果（对宽泛条件可能是异常）
    if len(result) == 0:
        # 如果条件看起来不苛刻，空结果可能是问题
        if len(nl_conds) <= 2:
            issues.append({
                'type': 'empty_suspicious',
                'msg': f'条件较少({len(nl_conds)}个)但结果为空，可能SQL有问题'
            })

    # 5. 检查SQL中的多个property_id是否都不同（重复JOIN同一属性）
    if len(prop_ids) != len(set(prop_ids)):
        issues.append({
            'type': 'duplicate_prop',
            'msg': f'SQL中有重复的property_id: {prop_ids}'
        })

    # 6. 检查是否有 SELECT * 或 JOIN 了不存在的表
    if 'FROM' not in sql.upper():
        issues.append({'type': 'error', 'msg': 'SQL缺少FROM子句'})

    # 7. 检查 CAST 的列是否正确（应该是 v.value 或 v1.value 等）
    bad_casts = re.findall(r"CAST\((\w+) AS DECIMAL", sql)
    for bc in bad_casts:
        if not re.match(r'v\d*\.value', bc):
            issues.append({'type': 'bad_cast', 'msg': f'CAST的目标列可能不对: {bc}'})

    return issues


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f'共 {len(data)} 条数据，开始检查...\n')

    all_issues = []
    stats = {'error': 0, 'op_mismatch': 0, 'empty_suspicious': 0,
             'duplicate_prop': 0, 'bad_cast': 0, 'clean': 0}

    for item in data:
        issues = check_item(item)
        if issues:
            all_issues.append({
                'sample_id': item['sample_id'],
                'nl': item['natural_language'],
                'issues': issues
            })
        else:
            stats['clean'] += 1
        for iss in issues:
            t = iss['type']
            if t in stats:
                stats[t] += 1

    # 输出统计
    print('=' * 60)
    print('检查统计:')
    print(f'  完全通过: {stats["clean"]} 条')
    print(f'  运算符不匹配: {stats["op_mismatch"]} 条')
    print(f'  可疑空结果: {stats["empty_suspicious"]} 条')
    print(f'  重复property_id: {stats["duplicate_prop"]} 条')
    print(f'  CAST列名异常: {stats["bad_cast"]} 条')
    print(f'  其他错误: {stats["error"]} 条')
    print()

    # 输出详情
    if all_issues:
        print('=' * 60)
        print(f'有问题的条目共 {len(all_issues)} 条:\n')
        for entry in all_issues:
            print(f'--- sample_id={entry["sample_id"]} ---')
            print(f'  NL: {entry["nl"]}')
            for iss in entry['issues']:
                print(f'  [{iss["type"]}] {iss["msg"]}')
            print()
    else:
        print('未发现问题！')

    # 输出结果集分布
    print('=' * 60)
    result_sizes = [len(item.get('result', [])) for item in data]
    print(f'结果数范围: {min(result_sizes)} ~ {max(result_sizes)}')
    print(f'空结果: {sum(1 for s in result_sizes if s == 0)} 条')


if __name__ == '__main__':
    main()
