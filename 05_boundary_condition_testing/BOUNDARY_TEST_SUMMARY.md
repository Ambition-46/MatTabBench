# 边界条件测试报告（Boundary Condition Testing Report）

- 生成时间: 2026-08-30T11:54:27.794121
- 数据库: smart_small（最终评测库，43 数据集 / 2,138 实体 / 30,462 数值记录）
- 样本: /Users/ambition/Desktop/科研任务/论文/评测集/Code/GitHub/05_boundary_condition_testing/../data/sql_nl_test_samples_500_result_data.json（最终 500 样本）

## 关键指标

- 边界条件查询总数: **588** 条 (117.6% of all samples)
- 涉及属性总数: **103** 个
- 全数据库扫描验证通过率（扫描命中数 == 金标准结果集长度）: **100.0%** (588/588)

| Boundary Query Subset | Samples | Properties | Passed | Failed | Pass Rate | Result Range (min-avg-max) |
|---|---|---|---|---|---|---|
| Greater | 253 | 91 | 253 | 0 | 100.0% | 1-38-885 |
| Greater Equal | 43 | 49 | 43 | 0 | 100.0% | 1-15-92 |
| Less | 149 | 74 | 149 | 0 | 100.0% | 1-34-1162 |
| Less Equal | 51 | 55 | 51 | 0 | 100.0% | 1-14-77 |
| Range | 92 | 54 | 92 | 0 | 100.0% | 1-113-1361 |
