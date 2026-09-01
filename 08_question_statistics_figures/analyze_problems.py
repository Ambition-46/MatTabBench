import json
import re

path = r'f:\Study\科研任务\论文\评测集\Code\sql_nl_test_samples_500.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

aggregation_funcs = ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'GROUP BY', 'HAVING']
only_equal = 0
aggregation = 0
other_examples = []

for sample in data:
    sql = sample.get('sql', '')
    nl = sample.get('natural_language', '')
    sample_id = sample.get('sample_id', 0)
    
    is_agg = any(func in sql.upper() for func in aggregation_funcs)
    
    if is_agg:
        aggregation += 1
    else:
        sql_clean = re.sub(r"'[^']*'", '', sql)
        has_comparison = any(op in sql_clean for op in ['<', '>', '<=', '>=', '<>', 'BETWEEN'])
        
        if not has_comparison:
            only_equal += 1
        else:
            if len(other_examples) < 10:
                other_examples.append((sample_id, nl))

total_other = len(data) - aggregation - only_equal

print('问题分类统计:')
print(f'总样本数: {len(data)}')
print()
print(f'聚合问题: {aggregation}')
print(f'仅有=操作的问题: {only_equal}')
print(f'除了聚合和纯=操作的其他问题: {total_other}')
print()
print(f'验证: {aggregation} + {only_equal} + {total_other} = {aggregation + only_equal + total_other}')
print()
print('其他问题示例 (前10个):')
for sid, nl in other_examples[:10]:
    print(f'Sample {sid}: {nl}')
