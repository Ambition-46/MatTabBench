import json, re

with open(r"f:\Study\科研任务\论文\评测集\Code\sample\sample_queries.json", 'r', encoding='utf-8') as f:
    queries = json.load(f)

# NL term -> property_id (from property_table, all global/dedicated IDs)
# No more lazy mapping to 135 or 224 for everything
GLOBAL_MAPPING = {
    # Material identifiers
    "材料名称": 1,
    # Physical properties
    "密度": 7, "温度": 134, "湿度": 141,
    # Mechanical properties
    "抗拉强度": 22, "屈服强度": 21, "弹性模量": 25, "性模量": 25,
    "泊松比": 26, "硬度": 189,
    "应变": 164, "应力": 165,
    "断后伸长率": 31, "伸长率": 31, "延伸率": 31,
    "断面收缩率": 32,
    "冲击吸收能": 29, "冲击吸收功": 29,
    "冲击韧性": 30,
    "上抗拉强度": 190, "下抗拉强度": 191,
    # Transport / thermal
    "电导率": 127, "电阻率": 10,
    "比热": 11, "热扩散率": 193, "热扩散速率": 193,
    # Grain / structure
    "晶粒度": 13, "体积": 121, "半径": 122, "表面积": 123,
    "面数": 119, "平均宽度": 225, "位置": 120,
    # Nanoindentation
    "模量": 222, "压入深度": 220, "辐照剂量": 219,
    # Corrosion / environment
    "腐蚀速率": 148, "已腐蚀量": 149, "PH值": 143, "ph": 143,
    "开位电路": 146, "液膜电阻": 144,
    # Stress / fracture
    "剪切应力": 160, "剪切速率": 162, "粘度": 163,
    "应力强度因子K": 208, "裂纹扩展速率": 216,
    # Semiconductor transport
    "载流子浓度": 125, "p型载流子浓度": 125, "n型载流子浓度": 129,
    "p型电导率": 127, "n型电导率": 131,
    "n型电子热导率": 132,
    "p型泽贝克系数": 126, "n型泽贝克系数": 130,
    # Special properties
    "能量": 244, "化学式": 6, "晶粒": 118,
    # Element content (dedicated property_ids)
    "氢含量": 35, "氢": 35, "H含量": 35, "H": 35,
    "硼含量": 39, "硼": 39, "B含量": 39, "B": 39,
    "碳含量": 40, "碳": 40, "C含量": 40, "C": 40,
    "氮含量": 41, "氮": 41, "N含量": 41, "N": 41,
    "镁含量": 46, "镁": 46, "Mg含量": 46, "Mg": 46,
    "铝含量": 47, "铝": 47, "Al含量": 47, "Al": 47,
    "硅含量": 48, "硅": 48, "Si含量": 48, "Si": 48,
    "磷含量": 49, "磷": 49, "P含量": 49, "P": 49,
    "硫含量": 50, "硫": 50, "含硫量": 50, "S含量": 50, "S": 50,
    "钛含量": 56, "钛": 56, "Ti含量": 56, "Ti": 56,
    "钒含量": 57, "钒": 57, "V含量": 57, "V": 57,
    "铬含量": 58, "铬": 58, "Cr含量": 58, "Cr": 58,
    "锰含量": 59, "锰": 59, "Mn含量": 59, "Mn": 59,
    "铁含量": 60, "铁": 60, "Fe含量": 60, "Fe": 60,
    "钴含量": 61, "钴": 61, "Co含量": 61, "Co": 61,
    "镍含量": 62, "镍": 62, "Ni含量": 62, "Ni": 62,
    "铜含量": 63, "铜": 63, "Cu含量": 63, "Cu": 63,
    "锌含量": 64, "锌": 64, "Zn含量": 64, "Zn": 64,
    "铌含量": 75, "铌": 75, "Nb含量": 75, "Nb": 75,
    "钼含量": 76, "钼": 76, "Mo含量": 76, "Mo": 76,
    "钨含量": 108, "钨": 108, "W含量": 108, "W": 108,
}

# Per-dataset overrides: some terms mean different things in different datasets
DATASET_OVERRIDES = {
    "3d晶粒信息汇总": {
        "位置": 120,  # grain_position
        "晶粒": 118,  # grain_id
    },
    "RPV材料辐照纳米压痕数据-模量": {
        "模量": 222,  # nanoindentation_modulus
    },
    "RPV材料辐照纳米压痕数据": {
        "硬度": 221,  # nanoindentation_hardness
    },
    "RPV材料辐照样品纳米压痕数据": {
        "硬度": 221,  # nanoindentation_hardness
    },
    "SCC试验数据": {
        "实验温度": 134,  # temperature (part of test_condition in JSON, but 134 is dedicated)
        "应力强度因子K": 208,
    },
    "高通量电输运计算数据": {
        "电导率": 127,  # p-type default
        "载流子浓度": 125,
    },
    "流变-模量": {
        "模量": 25,  # elastic_modulus (rheological context)
    },
    "激光表面处理IF钢截面硬度": {
        "相对位置x": 157, "相对位置y": 158,
    },
    "高铁材料服役大数据采集与计算-金属大气腐蚀": {
        "温度": 134, "湿度": 141,
        "腐蚀速率": 148, "已腐蚀量": 149,
        "PH值": 143,
    },
}

def parse_nl(nl, dataset):
    """Parse natural language into conditions: [(prop_id, operator, value)]"""
    # Merge global + dataset overrides
    mapping = dict(GLOBAL_MAPPING)
    if dataset in DATASET_OVERRIDES:
        mapping.update(DATASET_OVERRIDES[dataset])

    conditions = []
    nl = nl.replace('，', '.').replace('、', '.')

    # Find all known terms sorted by position
    sorted_terms = sorted(mapping.keys(), key=len, reverse=True)
    found_terms = []
    for term in sorted_terms:
        for m in re.finditer(re.escape(term), nl):
            found_terms.append((m.start(), m.end(), term))
    found_terms.sort()

    # Remove overlapping (substring) terms
    filtered = []
    for i, (s1, e1, t1) in enumerate(found_terms):
        overlap = False
        for j, (s2, e2, t2) in enumerate(found_terms):
            if i != j and s1 >= s2 and e1 <= e2 and len(t1) < len(t2):
                overlap = True
                break
        if not overlap:
            filtered.append((s1, e1, t1))

    for start, end, term in filtered:
        after = nl[end:].strip()

        # Comparison + number (supports negative)
        comp_m = re.match(r'(大于等于|小于等于|不小于|不大于|大于|小于|不低于|不高于|超过|不足|高于|低于)\s*(-?[\d.]+(?:万)?)', after)
        if comp_m:
            op_text = comp_m.group(1)
            val_str = comp_m.group(2).replace('万', '0000')
            op_map = {'大于': '>', '小于': '<', '大于等于': '>=', '小于等于': '<=',
                      '不小于': '>=', '不大于': '<=', '不低于': '>=', '不高于': '<=',
                      '超过': '>', '不足': '<', '高于': '>', '低于': '<'}
            conditions.append((mapping[term], op_map[op_text], float(val_str)))
            continue

        # "在X以上" (= >X) and "在X以下" (= <X)
        above_m = re.match(r'在\s*(-?[\d.]+)\s*以上', after)
        if above_m:
            conditions.append((mapping[term], '>', float(above_m.group(1))))
            continue
        below_m = re.match(r'在\s*(-?[\d.]+)\s*以下', after)
        if below_m:
            conditions.append((mapping[term], '<', float(below_m.group(1))))
            continue

        # Equality + number
        eq_n = re.match(r'(为|等于|是)\s*(-?[\d.]+(?:万)?)', after)
        if eq_n:
            val_str = eq_n.group(2).replace('万', '0000')
            conditions.append((mapping[term], '=', float(val_str)))
            continue

        # Equality + string
        eq_s = re.match(r'(为|等于|是)\s+([^\s一-鿿]+)', after)
        if eq_s:
            val_str = eq_s.group(2).strip()
            conditions.append((mapping[term], '=', val_str))
            continue

        # BETWEEN
        between_m = re.match(r'在\s*(-?[\d.]+)\s*(?:到|和|至|~)\s*(-?[\d.]+)', after)
        if between_m:
            v1, v2 = float(between_m.group(1)), float(between_m.group(2))
            conditions.append((mapping[term], 'BETWEEN', (v1, v2)))
            continue

    return conditions


def build_sql(conditions):
    """Build SQL query. All properties now use dedicated property_ids — no JSON_EXTRACT."""
    lines = ["SELECT DISTINCT e.data_id"]
    joins = []
    wheres = []

    for i, (pid, op, val) in enumerate(conditions):
        alias = "v" if i == 0 else f"v{i+1}"

        if i == 0:
            joins.append(f"FROM smart_small.entity_table e\nJOIN smart_small.value_table {alias} \n    ON {alias}.data_id = e.data_id")
        else:
            joins.append(f"JOIN smart_small.value_table {alias} \n    ON {alias}.data_id = e.data_id")

        prefix = "WHERE" if i == 0 else "    AND"
        wheres.append(f"{prefix} {alias}.property_id = {pid}")

        if op == 'BETWEEN':
            v1, v2 = val
            wheres.append(f"    AND {alias}.value != ''\n    AND {alias}.value IS NOT NULL\n    AND CAST({alias}.value AS DECIMAL(30, 15)) BETWEEN {v1} AND {v2}")
        elif op == '=':
            if isinstance(val, str):
                wheres.append(f"    AND {alias}.value = '{val}'")
            else:
                wheres.append(f"    AND {alias}.value != ''\n    AND {alias}.value IS NOT NULL\n    AND CAST({alias}.value AS DECIMAL(30, 15)) = {val}")
        else:
            wheres.append(f"    AND {alias}.value != ''\n    AND {alias}.value IS NOT NULL\n    AND CAST({alias}.value AS DECIMAL(30, 15)) {op} {val}")

    return "\n".join(lines + joins + wheres) + "\nORDER BY e.data_id ASC\n"


results = []
warnings = []

for q in queries:
    sid = q['sample_id']
    nl = q['natural_language']
    dataset = q['title']

    conditions = parse_nl(nl, dataset)

    if not conditions:
        warnings.append(f"Sample {sid}: {nl[:80]}")
        results.append({"sample_id": int(sid), "sql": f"-- TODO: {nl}", "result": [], "natural_language": nl})
        continue

    sql = build_sql(conditions)
    results.append({"sample_id": int(sid), "sql": sql, "result": [], "natural_language": nl})

output_path = r"f:\Study\科研任务\论文\评测集\Code\sample\sample_queries_with_sql.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Generated: {len(results)} queries, Warnings: {len(warnings)}")
for w in warnings:
    print(f"  {w}")
for r in results[:5]:
    print(f"\nSample {r['sample_id']}: {r['natural_language']}")
    print(r['sql'][:350])
