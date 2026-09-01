import json
import re

def classify_questions(input_file):
    # 读取原始数据
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    aggregated_questions = []
    complex_questions = []
    simple_questions = []
    
    # 聚合函数的关键字
    agg_keywords = ['MAX(', 'MIN(', 'AVG(', 'SUM(', 'COUNT(']
    
    for item in data:
        # 提取 sql 并转换为大写，方便统一匹配
        sql = item.get('sql', '').upper()

        # 1. 优先检测聚合问题
        is_agg = any(keyword in sql for keyword in agg_keywords)
        if is_agg:
            aggregated_questions.append(item)
            continue

        # 2. 在剩下的问题中，检测属性数量和数据集来源来区分简单和复杂问题
        # 使用正则计算 sql 中 'PROPERTY_ID =' 的出现次数
        property_count = len(re.findall(r'PROPERTY_ID\s*=', sql))

        # 统计 result_data 中不同数据集的个数（通过 _tid 字段区分）
        result_data = item.get('result_data', [])
        unique_tids = set()
        for rd in result_data:
            tid = rd.get('_tid')
            if tid is not None:
                unique_tids.add(tid)
        dataset_count = len(unique_tids)

        # 简单问题：只包含一个属性 且 数据不跨数据集（所有结果来自同一个 _tid）
        # 复杂问题：包含多个属性 或 数据来自不同数据集
        if property_count == 1 and dataset_count <= 1:
            simple_questions.append(item)
        else:
            complex_questions.append(item)
            
    # 3. 将分类后的数据分别写入三个不同的 JSON 文件
    with open('aggregated_questions.json', 'w', encoding='utf-8') as f:
        json.dump(aggregated_questions, f, ensure_ascii=False, indent=4)
        
    with open('complex_questions.json', 'w', encoding='utf-8') as f:
        json.dump(complex_questions, f, ensure_ascii=False, indent=4)
        
    with open('simple_questions.json', 'w', encoding='utf-8') as f:
        json.dump(simple_questions, f, ensure_ascii=False, indent=4)
        
    # 打印分类统计结果
    print(f"总计处理问题: {len(data)} 个")
    print(f"[聚合问题] (已导出至 aggregated_questions.json): {len(aggregated_questions)} 个")
    print(f"[复杂问题] (已导出至 complex_questions.json): {len(complex_questions)} 个")
    print(f"[简单问题] (已导出至 simple_questions.json): {len(simple_questions)} 个")

if __name__ == '__main__':
    # 运行分类（确保脚本与 json 文件在同一目录下）
    classify_questions('sql_nl_test_samples_500.json')