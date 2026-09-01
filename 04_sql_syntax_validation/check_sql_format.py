import json

with open('sql_nl_test_samples_500.json', 'r', encoding='utf-8') as f:
    samples = json.load(f)

# 检查前20条中包含比较操作的SQL
print('前20条SQL中的比较操作：')
for i, sample in enumerate(samples[:20]):
    sql = sample['sql']
    if '<' in sql or '>' in sql or 'BETWEEN' in sql:
        print(f"\n[{sample['sample_id']}] {sample.get('natural_language', '')}")
        # 显示WHERE子句
        if 'WHERE' in sql:
            where_idx = sql.index('WHERE')
            where_part = sql[where_idx:where_idx+250]
            print(f'  SQL: {where_part}...')
