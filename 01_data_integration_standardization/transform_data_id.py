#!/usr/bin/env python3
"""
Modify meta.数据ID in three dict-type data files:
Prepend '5' and pad with zeros to make exactly 8 digits.
Example: 2305 -> 50002305, 230924 -> 50230924
"""
import json
import os

DATA_DIR = r"f:\Study\科研任务\论文\评测集\Code\data"

TARGET_FILES = [
    "共聚PA6T系_玻璃化转变温度与密度的数据集.json",
    "共聚PA6T系_玻璃化转变温度与能量数据集.json",
    "接箍部件材料常用金属材料力学性能.json",
]

def transform_id(old_id):
    """Prepend '5' and pad with zeros to 8 digits."""
    s = str(old_id)
    padding = 7 - len(s)  # 7 because first digit is always 5
    new_id_str = "5" + "0" * padding + s
    return int(new_id_str)

def main():
    for fname in TARGET_FILES:
        fpath = os.path.join(DATA_DIR, fname)
        print(f"Processing: {fname}")

        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict) or 'data' not in data:
            print(f"  SKIP: unexpected format")
            continue

        records = data['data']
        changes = []
        for item in records:
            old_id = item['meta']['数据ID']
            new_id = transform_id(old_id)
            item['meta']['数据ID'] = new_id
            changes.append((old_id, new_id))

        print(f"  Records modified: {len(changes)}")
        print(f"  First: {changes[0][0]} -> {changes[0][1]}")
        print(f"  Last:  {changes[-1][0]} -> {changes[-1][1]}")

        # Write back
        with open(fpath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  Written.")

if __name__ == '__main__':
    main()
