# 面向海量稀疏材料数据库 Text-to-SQL 查全能力评测数据集 —— 实验代码仓库

本仓库汇总《面向海量稀疏材料数据库文本转结构化查询语言任务的查全能力评测数据集》
所涉及的全部实验代码。

所有实验均基于最终评测库 **MySQL `smart_small`**（43 个数据集 / 2,138 条实体记录 /
30,462 条数值记录 / 245 个属性）执行。

## 目录结构总览

```
.
├── data/                                  # 论文"数据记录"部分的数据文件
├── 01_data_integration_standardization/   # 数据来源整合与标准化（43 数据集、模式对齐、三表构建）
├── 02_query_sample_generation/            # 自然语言查询与 SQL 标注流程（三类模板、500 问题）
├── 03_gold_standard_execution/            # 质量评估：执行准确率（EX）/ 金标准结果集生成
├── 04_sql_syntax_validation/              # 技术验证：SQL 结构化验证（EXPLAIN 语法校验）
├── 05_boundary_condition_testing/         # 技术验证：查全率边界测试（smart_small 全库扫描 == 金标准）
├── 06_semantic_consistency_review/        # 语义一致性检查与人工评审辅助
├── 07_sparsity_distribution_analysis/     # 技术验证：数据库稀疏性与分布质量评估（smart_small）
└── 08_question_statistics_figures/        # 问题分类统计、运行时间测量与论文图表生成
```

## 论文实验 ↔ 目录 ↔ 代码对照

### data/ —— 论文"数据记录"部分

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `sql_nl_test_samples_500_result_data.json` | 最终 500 样本评测集（`sample_id` / `natural_language` / `result` / `result_data`），对应论文中评测集文件的完整版 | `实验修改/` |
| `entity_table.sql` / `property_table.sql` / `value_table.sql` | 底层数据库三表导出（43 个数据集，`data_id` / `property_id` / `value` 统一映射） | `评测集/中间/` |

### 01_data_integration_standardization/ —— 方法·数据来源与数据集成标准化

43 个真实材料数据集整合、模式对齐（`data_id` / `property_id` / `value` 统一映射）、
Entity / Attribute / Value 三表构建、三阶段数据清洗（字符过滤、完整性筛查）、`dataset_id` 分配。

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `import_to_smart_small.py` | 将样本 JSON 数据导入 smart_small 数据库（字段-属性映射缓存） | `数据插入/` |
| `rebuild_smart_small.py` | 清空重建：叶子字段抽取解析后重新插入 | `数据插入/` |
| `final_rebuild.py` | 最终重建流程（含数据集分类、字段匹配） | `数据插入/` |
| `add_dataset_id.py` | 为 entity_table 新增 dataset_id 列（按 title 聚类，0001 起递增） | `数据插入/数据集id新增/` |
| `transform_data_id.py` | data 文件中 `meta.数据ID` 统一补零为 8 位 | 根目录 |
| `transform_all_ids.py` | 批量执行上述 ID 变换 | 根目录 |
| `fix_ids.py` | 修复多补前导"5"的 8 位 ID | 根目录 |
| `field_match_cache.json` 等 | 字段→属性匹配缓存、数据集/属性分类表、叶子字段清单（运行支撑文件） | `数据插入/` |

### 02_query_sample_generation/ —— 方法·自然语言查询与 SQL 标注流程

三类查询意图模板（简单检索 / 多条件关联检索 / 聚合属性计算查询）、SQL 编写规范
（JOIN 关联、DISTINCT 去重、`CAST(value AS DECIMAL(30,15))` 类型匹配）、500 个问题的生成与修订。

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `gen_sql.py` | 由自然语言问题生成 SQL（NL 术语 → property_id 全局映射） | `sample/` |
| `regenerate_results.py` | 对修订样本重新执行 SQL 生成 result/result_data | `sample/` |
| `update_sql_and_results.py` | 按 `bad_samples_sql_nl_mismatch.txt` 替换修正 SQL 并重新执行写回 result | `评测集修改/500/` |
| `fix_500_samples.py` / `fix_500_v2.py` | 500 样本批量修复（含 smart_mged → smart_small 模式迁移） | 根目录 |
| `bad_samples_*.txt` | 问题样本清单（修复输入） | `评测集修改/500/` |

### 03_gold_standard_execution/ —— 方法·质量评估（执行准确率 EX / 金标准）

每条 SQL 在 smart_small 中实际运行，记录执行结果作为金标准；
仅语法合法且结果与标注一致者纳入评测集。

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `run_sql_and_match_data.py` | 全部 SQL 在 MySQL 执行更新 result，并将 data_id 匹配到完整数据记录写回 result_data | 根目录 |
| `run_sql_update.py` | 对替换版样本执行 SQL 更新 result 字段 | 根目录 |
| `run_sql_and_update.py` | 对 0807 版样本执行 SQL 并覆盖 result | `评测集修改/500/0807/` |
| `update_results.py` / `rerun_3.py` | 执行 SQL 更新结果 / 重跑 3 条空结果样本 | 根目录 |
| `match_500_data.py` / `match_result_data.py` | result 中 data_id → data 目录 JSON 记录（`_meta_id` / `meta.数据ID`）匹配出 result_data | 根目录 |
| `fix_empty_results.py` | 修复 39 条空结果条目并重跑 | 根目录 |
| `fix_result_data*.py`（v1~v4） | result_data 缺失/错配的多轮修复 | 根目录 |
| `add_result_data.py` | 0807 版：删除 natural_language_en、为非聚合问题匹配完整数据记录 | `评测集修改/500/0807/` |
| `export_empty_results.py` | 导出空结果样本清单 | 根目录 |

### 04_sql_syntax_validation/ —— 技术验证·查询逻辑的结构化验证

以 SQL 语法校验器对全部 500 条 SQL 进行语法分析，保证 ANSI 合规、无误编译执行；
含 MySQL → PostgreSQL DDL 转换管线（历史遗留工具）。

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `check_sql_format.py` | 检查含比较操作的 SQL 格式（WHERE 子句） | 根目录 |
| `convert_mysql_to_pg.py` | MySQL DDL 转 PostgreSQL（历史工具） | `possql/` |
| `fix_ddl.py` / `fix_triggers.py` | DDL / 触发器修正（历史工具） | `possql/` |
| `final_convert.py` | 最终转换产出 `*_final.sql`（历史工具） | `possql/` |

### 05_boundary_condition_testing/ —— 技术验证·查全率边界测试

对极值条件查询（如"泊松比 > 0.99"、"应变 < 0.01"）进行专项检查：按样本 SQL 的
全部过滤条件在 smart_small 上构造独立全库扫描，将扫描命中数与金标准 result 长度比对
（相等即验证完整覆盖）。**结果：588 条边界条件、103 个属性、通过率 100%（588/588）。**

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `boundary_condition_test.py` | 边界条件测试主程序（smart_small + 最终 500 样本） | 根目录 |
| `generate_paper_tables.py` | 由边界测试报告生成论文表格 | 根目录 |
| `BOUNDARY_TEST_SUMMARY.md` / `boundary_test_report.csv` / `boundary_test_report.json` | 边界测试结果报告（2026-08-30 重跑） | 根目录 |

### 06_semantic_consistency_review/ —— 语义一致性检查与人工评审

NL-SQL-结果三元组一致性自动检查（运算符方向、条件匹配、结果满足性），
以及人工评测表（Excel）生成，支撑论文"语义解析的人工评审 / 双盲复审"实验。

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `verify_consistency.py` | NL-SQL-result_data 一致性核验 | 根目录 |
| `analyze_sql.py` | 100 条样本 NL-SQL 一致性分析 | `sample/` |
| `check_results.py` | 检测 SQL 检索结果是否符合 NL 要求（运算符方向等） | `评测集修改/500/0807/` |
| `check_op_direction.py` | 运算符方向不一致条目检测（修复误报） | `评测集修改/500/0807/` |
| `comprehensive_check.py` | 检索结果符合性的综合评估 | `评测集修改/500/0807/` |
| `update_excel.py` | 将样本内容写入人工评测表 xlsx（对比新旧值） | `评测集修改/500/0807/excel/` |

### 07_sparsity_distribution_analysis/ —— 技术验证·数据库稀疏性与分布质量评估

统计 smart_small 底层数据的属性稀疏性分布（2026-08-30 重跑）：
**2,138 实体 / 245 属性 / 30,462 实体-属性对，密度 5.82%；
每实体属性数 mean 14.25 / median 15（4~30）；
每属性覆盖实体数（全部 245 个属性，0 覆盖计入）mean 124.3 / median 50（0~1,487），
其中 72 个属性（29.4%）无任何数值记录；仅统计 173 个有值属性时 mean 176.1；
500 样本涉及 108 个属性；结果集大小 mean 46.5 / median 9（1~1,361），无空结果样本。**

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `compute_sparsity.py` | 稀疏性统计（每实体属性数 / 每属性实体数分布，smart_small） | `稀疏性验证/` |
| `plot_sparsity.py` | 稀疏性分布图（rank-frequency / CDF / 结果集大小直方图） | `稀疏性验证/` |
| `generate_paper_figure.py` | 成对属性关系总览论文图 | `sample/` |
| `sparsity_report.json` / `*.csv` / `sparsity_summary.txt` / `*.png` | 稀疏性统计结果与图表（smart_small 重跑） | `稀疏性验证/` |

### 08_question_statistics_figures/ —— 分类统计与论文图表

三类问题的分类、各分类 SQL 结构统计（JOIN/条件数/独立属性/结果集中位数）、
查询执行时间测量与论文图表生成。

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `classify_questions.py` | 500 问题按聚合/复杂/简单三分（早期版本） | 根目录 |
| `classify_500_questions.py` | 最终版三分类：Simple / Complex Correlation / Aggregated Attribute Calculation | `实验修改/问题分类/` |
| `classify_stats.py` | 各分类 SQL 平均 JOIN/WHERE 条件数、独立属性总数、结果集中位数 | `实验修改/统计不同分类信息/` |
| `analyze_questions.py` / `analyze_problems.py` | 问题特征分析（聚合函数、比较算符等） | `questions/`、根目录 |
| `measure_runtime.py` | 各分类查询执行时间测量 | `questions/` |
| `count_props_in_nl.py` | 统计 NL 问题涉及属性及名称 | 根目录 |
| `generate_png.py` | 按问题类别的样本质量总览图 | `sample/` |
| `analysis.txt` / `final_analysis.txt` | 问题分析结果（示例输出） | 根目录 |

### tools/ —— 验证与调试工具

| 文件 | 说明 | 原始位置 |
|---|---|---|
| `verify_gold_results.py` | 500 条 SQL 在 smart_small 重跑并与金标准 result 比对（一致性验证） | 本次整理新增 |
| `debug_plot.py` | matplotlib/pandas 绘图环境自检 | 根目录 |
| `debug_regex.py` | 正则表达式测试 | 根目录 |

## 复现说明

- 数据库环境：MySQL（`smart_small` 库，本机实测密码为 `12345678`，与部分脚本默认
  `123456` 不同，运行时请以 `MYSQL_PASSWORD` 环境变量覆盖）。
- 部分脚本内嵌 Windows 绝对路径（`f:\Study\...`），运行时请按本仓库相对路径调整。
- 底层 43 个源数据集 JSON 与各类中间产物体积较大，未纳入本仓库；可用 `data/` 中
  三表 SQL 重建数据库后复现全部执行实验（已验证：导入后重跑 500 条 SQL 与金标准
  100% 一致，见 [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md)）。
- 被后续版本取代的旧脚本（根目录 `compute_sparsity.py` / `plot_sparsity.py`、
  `稀疏性验证/debug_plot.py`）未收录，对应新版本见 `07_sparsity_distribution_analysis/`。
- 实验结果与论文声明的一致性核验结论见 [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md)。

## 代码可用性（Code Availability）

本仓库代码用于生成、验证与统计评测数据集，Python 3.8+，依赖 PyMySQL、matplotlib、
pandas 等（各脚本头部有说明）。
