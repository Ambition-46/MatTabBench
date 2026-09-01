#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
读取 sql_nl_test_samples_500_0807_result.json 中的每个 SQL，
在 MySQL 数据库中执行，并将结果覆盖写入 result 字段。
"""

import json
import re
import sys
from decimal import Decimal
import pymysql


class DecimalEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 Decimal 类型"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


def convert_decimal(obj):
    """递归地将对象中的 Decimal 转换为 float"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_decimal(v) for v in obj]
    return obj


def fix_sql(sql):
    """修复 SQL 中的常见问题: 未转义单引号、运算符空格等"""
    # 1. 修复未转义的单引号
    quote_fixes = [
        # gamma-prime 化学符号中的引号未转义
        ("'γ+γ''", "'γ+γ'''"),
        ("'γ+γ'+TCP'", "'γ+γ''+TCP'"),
    ]
    for old, new in quote_fixes:
        sql = sql.replace(old, new)

    # 2. 修复运算符中的多余空格: '< =' -> '<='
    sql = sql.replace('< =', '<=')
    sql = sql.replace('> =', '>=')
    sql = sql.replace('! =', '!=')

    return sql


# MySQL 配置
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'database': 'smart_small',
    'charset': 'utf8mb4',
}

# JSON 文件路径
JSON_FILE = r'f:\Study\科研任务\论文\评测集\Code\评测集修改\500\0807\sql_nl_test_samples_500_0807_result.json'


def main():
    # 1. 读取 JSON 文件
    print(f"读取文件: {JSON_FILE}")
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"共 {len(data)} 条数据")

    # 2. 连接 MySQL
    print("连接 MySQL...")
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    try:
        success_count = 0
        fail_count = 0

        for i, item in enumerate(data):
            sample_id = item.get('sample_id', i + 1)
            sql = item.get('sql', '')

            if not sql:
                print(f"  [{sample_id}] 跳过: SQL 为空")
                item['result'] = []
                fail_count += 1
                continue

            try:
                # 自动修复 SQL 常见问题
                sql = fix_sql(sql)

                # 3. 执行 SQL
                cursor.execute(sql)
                rows = cursor.fetchall()

                # 4. 将结果转为列表格式并转换 Decimal 类型
                if rows:
                    # 如果每行只有一列，直接返回值；否则返回整行
                    if len(rows[0]) == 1:
                        result = [convert_decimal(row[0]) for row in rows]
                    else:
                        result = [convert_decimal(list(row)) for row in rows]
                else:
                    result = []

                item['result'] = result
                success_count += 1

                if (i + 1) % 50 == 0 or i == 0:
                    print(f"  进度: {i + 1}/{len(data)}, 成功: {success_count}, 失败: {fail_count}")

            except Exception as e:
                print(f"  [{sample_id}] SQL 执行失败: {e}")
                print(f"    SQL: {sql[:150]}...")
                item['result'] = []
                fail_count += 1

        print(f"\n执行完成！成功: {success_count}, 失败: {fail_count}")

    finally:
        cursor.close()
        conn.close()
        print("MySQL 连接已关闭")

    # 5. 写回 JSON 文件
    print(f"写回文件: {JSON_FILE}")
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, cls=DecimalEncoder)

    print("完成！")


if __name__ == '__main__':
    main()
