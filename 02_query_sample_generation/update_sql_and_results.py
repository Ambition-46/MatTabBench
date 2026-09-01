#!/usr/bin/env python3
"""
1. 从 bad_samples_sql_nl_mismatch.txt 解析修正后的SQL
2. 按 sample_id 替换到 sql_nl_test_samples_500(7)_replaced.json 对应条目
3. 在MySQL中执行修正后的SQL，将结果写入 result 字段
"""

import json
import re
import sys

try:
    import pymysql
except ImportError:
    import MySQLdb as pymysql

# ---------- MySQL 配置 ----------
MYSQL_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': '123456',
    'database': 'smart_small', 'charset': 'utf8mb4',
    'connect_timeout': 30,
    'read_timeout': 60,
}

# ---------- 文件路径 ----------
BASE_DIR = r'f:\Study\科研任务\论文\评测集\Code\评测集修改\500'
TXT_FILE = f'{BASE_DIR}\\bad_samples_sql_nl_mismatch.txt'
JSON_FILE = f'{BASE_DIR}\\sql_nl_test_samples_500(7)_replaced.json'
OUTPUT_FILE = f'{BASE_DIR}\\sql_nl_test_samples_500(8)_replaced.json'  # 直接覆盖


def parse_corrected_sqls(txt_path):
    """从txt文件中解析 sample_id -> corrected SQL 的映射"""
    mapping = {}
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 匹配每个错误样本块: [数字] ... 修正后的SQL: ...
    pattern = r'\[(\d+)\].*?修正后的SQL:\s*(.*?)(?:\n\n|\n(?:---|$))'
    matches = re.findall(pattern, content, re.DOTALL)

    for sample_id_str, sql in matches:
        sample_id = int(sample_id_str)
        # 清理SQL: 去除首尾空白和换行
        sql_clean = sql.strip()
        mapping[sample_id] = sql_clean

    print(f'[INFO] 从txt文件解析到 {len(mapping)} 条修正后的SQL')
    return mapping


def execute_sql(connection, sql):
    """执行SQL并返回结果列表"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            # 返回第一列的列表
            return [row[0] for row in rows]
    except Exception as e:
        print(f'  [ERROR] SQL执行失败: {e}')
        print(f'  SQL: {sql[:200]}...')
        return None


def main():
    # 1. 解析修正后的SQL
    corrected_map = parse_corrected_sqls(TXT_FILE)

    # 2. 加载JSON
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        samples = json.load(f)
    print(f'[INFO] JSON中共有 {len(samples)} 条样本')

    # 3. 建立 sample_id -> index 索引
    id_to_idx = {}
    for i, sample in enumerate(samples):
        sid = sample.get('sample_id')
        if sid is not None:
            id_to_idx[sid] = i

    # 4. 替换SQL
    replaced_count = 0
    not_found = []
    for sid, corrected_sql in corrected_map.items():
        if sid in id_to_idx:
            old_sql = samples[id_to_idx[sid]]['sql']
            samples[id_to_idx[sid]]['sql'] = corrected_sql
            replaced_count += 1
            print(f'[REPLACED] sample_id={sid}: {old_sql[:80]}... -> {corrected_sql[:80]}...')
        else:
            not_found.append(sid)
            print(f'[WARN] sample_id={sid} 在JSON中未找到')

    print(f'\n[INFO] 成功替换 {replaced_count} 条SQL')
    if not_found:
        print(f'[WARN] {len(not_found)} 条在JSON中未找到: {not_found}')

    # 5. 连接数据库并执行修正后的SQL
    print('\n[INFO] 连接数据库...')
    try:
        conn = pymysql.connect(**MYSQL_CONFIG)
        print('[INFO] 数据库连接成功')
    except Exception as e:
        print(f'[ERROR] 数据库连接失败: {e}')
        sys.exit(1)

    try:
        success_count = 0
        fail_count = 0
        for sid in corrected_map:
            if sid not in id_to_idx:
                continue
            idx = id_to_idx[sid]
            sql = samples[idx]['sql']
            print(f'\n[EXEC] sample_id={sid}...')
            result = execute_sql(conn, sql)
            if result is not None:
                samples[idx]['result'] = result
                success_count += 1
                print(f'  返回 {len(result)} 条结果')
            else:
                fail_count += 1
                print(f'  执行失败，保留原有result')

        print(f'\n[INFO] 执行完成: 成功 {success_count}, 失败 {fail_count}')
    finally:
        conn.close()
        print('[INFO] 数据库连接已关闭')

    # 6. 保存JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    print(f'[INFO] 已保存到 {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
