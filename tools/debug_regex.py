import json
import re

with open('sql_nl_test_samples_500.json', 'r', encoding='utf-8') as f:
    samples = json.load(f)

# 测试正则表达式
sql = samples[0]['sql']
print(f"Sample SQL:\n{sql}\n")
print("=" * 80)

# 归一化
sql_clean = ' '.join(sql.split())
print(f"Normalized SQL:\n{sql_clean}\n")
print("=" * 80)

# 测试各种模式
patterns = {
    'between1': r'CAST\([v]\d*\.value\s+AS\s+DECIMAL[^)]*\)\s+BETWEEN\s+([0-9.\-+]+)(?:AND|\s+AND)\s+([0-9.\-+]+)',
    'between2': r'BETWEEN\s+([0-9.\-+]+)(?:AND|\s+AND)\s+([0-9.\-+]+)',
    'less': r'CAST\([v]\d*\.value\s+AS\s+DECIMAL[^)]*\)\s*<\s*(?!=)([0-9.\-+]+)',
    'less_simple': r'DECIMAL.*?\)\s*<\s*([0-9.\-+]+)',
    'less_simple2': r'<\s*([0-9.\-+]+)',
}

for name, pattern in patterns.items():
    matches = re.findall(pattern, sql_clean, re.IGNORECASE)
    print(f"{name}: {matches}")

print("\n" + "=" * 80)
print("\n测试几个样本：\n")
for sample_id in [1, 2, 3, 5, 8, 9, 11]:
    sample = samples[sample_id - 1]
    sql_clean = ' '.join(sample['sql'].split())
    
    # 简化的检测
    if 'BETWEEN' in sql_clean.upper():
        print(f"[{sample_id}] BETWEEN: {sample.get('natural_language', '')[:50]}")
    elif '<' in sql_clean and 'DECIMAL' in sql_clean:
        print(f"[{sample_id}] LESS: {sample.get('natural_language', '')[:50]}")
    elif '>' in sql_clean and 'DECIMAL' in sql_clean:
        print(f"[{sample_id}] GREATER: {sample.get('natural_language', '')[:50]}")
    elif '<=' in sql_clean and 'DECIMAL' in sql_clean:
        print(f"[{sample_id}] LESS_EQUAL: {sample.get('natural_language', '')[:50]}")
    elif '>=' in sql_clean and 'DECIMAL' in sql_clean:
        print(f"[{sample_id}] GREATER_EQUAL: {sample.get('natural_language', '')[:50]}")
