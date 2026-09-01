"""
为 smart_small 数据库的 entity_table 新增 dataset_id 列。
title 内容相同的记录分配同一个 dataset_id，从 0001 开始递增。
"""
import pymysql

MYSQL_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': '123456',
    'database': 'smart_small', 'charset': 'utf8mb4',
}


def add_dataset_id():
    conn = pymysql.connect(**MYSQL_CONFIG)
    cur = conn.cursor()

    # ============================================================
    # Step 1: 新增 dataset_id 列（如果不存在）
    # ============================================================
    print("检查 dataset_id 列是否存在...")
    cur.execute("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = 'smart_small'
          AND TABLE_NAME = 'entity_table'
          AND COLUMN_NAME = 'dataset_id'
    """)
    exists = cur.fetchone()[0] > 0

    if not exists:
        print("新增 dataset_id 列 (VARCHAR(10))...")
        cur.execute("""
            ALTER TABLE entity_table
            ADD COLUMN dataset_id VARCHAR(10) DEFAULT NULL
            COMMENT '数据集ID，相同title共享同一ID，从0001开始'
        """)
        conn.commit()
        print("dataset_id 列已添加。")
    else:
        print("dataset_id 列已存在，跳过 ALTER TABLE。")

    # ============================================================
    # Step 2: 查询所有不重复的 title
    # ============================================================
    print("\n查询不重复的 title...")
    cur.execute("SELECT DISTINCT title FROM entity_table")
    titles = [row[0] for row in cur.fetchall()]
    print(f"共有 {len(titles)} 个不重复的 title。")

    # ============================================================
    # Step 3: 按顺序分配 dataset_id，从 0001 开始
    # ============================================================
    print("\n分配 dataset_id...")
    for idx, title in enumerate(titles, start=1):
        dataset_id = f"{idx:04d}"  # 格式化为 4 位数字，如 0001, 0002, ...
        cur.execute(
            "UPDATE entity_table SET dataset_id = %s WHERE title = %s",
            (dataset_id, title)
        )
        affected = cur.rowcount
        if idx % 100 == 0 or idx == 1:
            print(f"  [{dataset_id}] title='{title[:50]}' -> 更新 {affected} 行")

    conn.commit()
    print(f"\n已为 {len(titles)} 个不同 title 分配 dataset_id（0001 ~ {len(titles):04d}）。")

    # ============================================================
    # Step 4: 验证结果
    # ============================================================
    cur.execute("SELECT COUNT(*) FROM entity_table WHERE dataset_id IS NULL")
    null_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT dataset_id) FROM entity_table")
    distinct_ids = cur.fetchone()[0]

    cur.execute("SELECT COUNT(DISTINCT title) FROM entity_table")
    distinct_titles = cur.fetchone()[0]

    cur.execute("SELECT MIN(dataset_id), MAX(dataset_id) FROM entity_table")
    min_id, max_id = cur.fetchone()

    print("\n=== 验证结果 ===")
    print(f"总记录数:     (见下方)")
    print(f"dataset_id 为 NULL: {null_count}")
    print(f"不同 dataset_id 数: {distinct_ids}")
    print(f"不同 title 数:      {distinct_titles}")
    print(f"dataset_id 范围:    {min_id} ~ {max_id}")

    cur.execute("SELECT COUNT(*) FROM entity_table")
    print(f"entity_table 总行数: {cur.fetchone()[0]}")

    # 展示几个示例
    print("\n=== 示例数据（前10行）===")
    cur.execute("SELECT data_id, title, dataset_id FROM entity_table LIMIT 10")
    for row in cur.fetchall():
        title_short = str(row[1])[:60]
        print(f"  data_id={row[0]}, dataset_id={row[2]}, title='{title_short}'")

    cur.close()
    conn.close()
    print("\n完成！")


if __name__ == '__main__':
    add_dataset_id()
