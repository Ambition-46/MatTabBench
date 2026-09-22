# MatEAV-Bench

**A unified entity-attribute-value benchmark for natural-language retrieval across sparse materials databases**

MatEAV-Bench is a domain-specific benchmark for evaluating natural language-to-SQL (NL2SQL) retrieval over sparse and heterogeneous materials databases.

The benchmark integrates 43 public materials datasets into a unified Entity-Attribute-Value (EAV) relational database and provides 500 human-validated natural-language retrieval queries with verified execution results. It is designed to evaluate retrieval accuracy and completeness under domain-specific terminology, sparse property distributions, multi-condition filtering, numerical boundary constraints, and aggregate operations.

This repository contains the code and supporting resources used for benchmark construction, data standardization, reference-result generation, technical validation, sparsity analysis, and query-level statistical analysis.

---

## Benchmark at a Glance

| Item | Value |
|---|---:|
| Source datasets | 43 |
| Material entities | 2,138 |
| Material properties | 245 |
| Non-empty entity-property records | 30,462 |
| Global matrix density | 5.82% |
| Global matrix sparsity | 94.18% |
| Natural-language queries | 500 |
| Simple Retrieval | 121 |
| Multi-Condition Retrieval | 323 |
| Aggregate Queries | 56 |
| Queries containing boundary conditions | 419 |
| Boundary-operator instances | 588 |

---

## Benchmark Components

MatEAV-Bench contains two major components.

### 1. Unified EAV Materials Database

Heterogeneous source datasets are standardized into a common relational schema consisting of three core tables:

```text
entity_table
property_table
value_table
```

The database contains:

- **2,138 material entities**
- **245 material properties**
- **30,462 non-empty entity-property records**

Source provenance is retained through `dataset_id`.

The EAV representation supports heterogeneous source schemas while preserving the sparse property distributions observed in the original materials datasets.

### 2. Natural-Language Retrieval Benchmark

The benchmark contains **500 natural-language retrieval queries** covering three levels of query complexity:

- **Simple Retrieval:** 121 queries
- **Multi-Condition Retrieval:** 323 queries
- **Aggregate Queries:** 56 queries

The queries cover single-property lookup, multi-property filtering, cross-dataset retrieval, numerical range constraints, and statistical aggregation.

Reference SQL statements were manually constructed and used internally during benchmark development to generate and verify the reference execution results. The released benchmark is evaluated using execution results rather than literal SQL-string matching.

---

## Benchmark Construction

The finalized benchmark was constructed using a human-in-the-loop workflow:

```text
Source materials datasets
        ↓
EAV data integration and standardization
        ↓
Expert-designed reference SQL
        ↓
Executable SQL validation
        ↓
LLM-assisted SQL-to-Text generation
        ↓
Manual expert filtering and rewriting
        ↓
Semantic consistency verification
        ↓
Reference SQL execution
        ↓
Human-verified reference results
        ↓
Final 500-query benchmark
```

GPT-5.6 Sol was used to generate initial natural-language candidates from reference SQL statements under a zero-shot prompting setting.

LLM-generated text was not directly included in the benchmark. All finalized queries were manually reviewed and, where necessary, rewritten to ensure semantic consistency, domain-appropriate expression, and agreement with the intended retrieval logic.

---

## Released Benchmark Data

The main benchmark file is:

```text
sql_nl_test_samples_500_result_data.json
```

Each benchmark sample contains five fields:

| Field | Description |
|---|---|
| `sample_id` | Unique sample identifier |
| `natural_language` | Finalized Chinese natural-language query |
| `natural_language_en` | Manually checked English translation |
| `result` | Human-verified reference execution result |
| `result_data` | Full records corresponding to retrieved entity identifiers |

For retrieval queries, `result` contains qualifying `data_id` values and `result_data` contains the corresponding records.

For aggregate queries, `result` contains the reference scalar value and `result_data` is empty.

A simplified example is shown below:

```json
{
  "sample_id": "...",
  "natural_language": "...",
  "natural_language_en": "...",
  "result": ["..."],
  "result_data": [
    {
      "data_id": "...",
      "...": "..."
    }
  ]
}
```

Reference SQL statements are used as internal construction and validation artifacts and are not included as fields in the released benchmark samples.

---

## Repository Structure

```text
.
├── 01_data_integration_standardization/
├── 02_query_sample_generation/
├── 03_gold_standard_execution/
├── 04_sql_syntax_validation/
├── 05_boundary_condition_testing/
├── 06_semantic_consistency_review/
├── 07_sparsity_distribution_analysis/
├── 08_question_statistics_figures/
├── sql_nl_test_samples_500_result_data.json
└── README.md
```

### 01 — Data Integration and Standardization

This module processes heterogeneous source records and converts them into the unified EAV representation.

It covers:

- source-data parsing;
- schema alignment;
- identifier normalization;
- entity/property/value mapping;
- missing-value processing;
- unit extraction;
- duplicate handling;
- provenance preservation through `dataset_id`;
- construction of the finalized benchmark database.

### 02 — Query Sample Generation

This module contains the utilities used during benchmark query construction and refinement.

It supports:

- reference-query preparation;
- SQL-related annotation processing;
- natural-language candidate generation;
- sample revision;
- intermediate benchmark refinement.

Some utilities in this module were used during historical development stages and are retained for transparency and reproducibility.

### 03 — Reference Result Generation

This module executes internally annotated reference SQL statements and generates the corresponding benchmark reference outputs.

It supports:

- SQL execution;
- reference-result generation;
- entity-record matching;
- construction of `result_data`;
- regeneration of corrected benchmark outputs.

### 04 — SQL Executability and Cross-Database Validation

This module validates SQL executability and supports cross-database consistency checking.

The 500 internally annotated reference queries were validated using:

- **MySQL 9.6**
- **PostgreSQL 18.4**

After normalization of output ordering and numerical precision, the reference queries produced equivalent results across both database systems.

### 05 — Boundary-Condition Validation

This module focuses on numerical range and inequality constraints.

Among the 500 benchmark queries:

- **419 distinct queries** contain at least one boundary operator;
- these queries contain **588 boundary-operator instances** in total.

The validation covers:

- comparison-operator consistency;
- open and closed interval semantics;
- numerical casting;
- missing-value handling;
- complete retrieval of qualifying records.

### 06 — Semantic Consistency Review

This module supports automated and manual consistency checking among:

```text
Natural-language query
        ↕
Reference SQL logic
        ↕
Execution result
```

Two materials-domain experts independently reviewed all finalized benchmark samples. Disagreements were resolved through additional expert adjudication.

The review focused on scientific terminology, retrieval semantics, predicate consistency, missing records, and false-positive results.

### 07 — Sparsity and Distribution Analysis

This module characterizes the sparse structure of the integrated EAV database.

The complete entity-property matrix contains:

```text
2,138 entities
245 properties
30,462 populated records
```

which corresponds to approximately:

```text
Density:  5.82%
Sparsity: 94.18%
```

The analysis also examines:

- properties per entity;
- entities per property;
- long-tailed property coverage;
- result-set size distributions.

The reported global sparsity is calculated using the complete 245-property database schema.

### 08 — Query Statistics and Figures

This module provides statistical characterization of the benchmark queries and generates analysis results used in the accompanying study.

It includes analyses of:

- query complexity categories;
- JOIN operations;
- filtering predicates;
- property coverage;
- execution-result sizes;
- execution runtime;
- benchmark figures and statistical summaries.

---

## Evaluation Protocol

MatEAV-Bench uses execution-result-based evaluation.

A model-generated executable query is run against the released database snapshot and compared with the human-verified reference output.

Three metrics are used:

### Execution Accuracy (EX)

Execution Accuracy requires complete equivalence between the predicted and reference outputs.

For entity-retrieval queries, comparison is performed using deduplicated and order-independent entity-ID sets.

For aggregate queries, scalar values are compared using an absolute numerical tolerance of:

```text
1e-6
```

Execution failures or invalid outputs receive a score of zero.

### Macro Recall

Macro Recall measures the average retrieval completeness across all benchmark queries.

For entity-retrieval queries, recall is calculated as the proportion of reference entities recovered by the predicted query.

For aggregate queries, the scalar result is treated as one atomic target.

### Micro Recall

Micro Recall pools all reference targets across the complete benchmark before calculating retrieval completeness.

Macro Recall therefore weights each query equally, whereas Micro Recall reflects the overall proportion of recovered reference targets.

Recall is reported together with Execution Accuracy because recall measures omission behavior but does not independently penalize false-positive entities.

---

## Reproducibility

For comparable evaluation results, users should:

- use the released database snapshot;
- evaluate all 500 benchmark queries unless a subset is explicitly reported;
- deduplicate returned entity identifiers;
- ignore entity-result ordering;
- use an absolute tolerance of `1e-6` for scalar aggregate outputs;
- assign zero to failed or malformed executions;
- report the database engine, model version, and inference configuration.

Because evaluation is based on execution results, different SQL statements that are semantically equivalent can receive identical scores.

---

## Quick Start

### Clone the repository

```bash
git clone https://github.com/Ambition-46/MatTabBench.git
cd MatTabBench
```

If the repository is renamed to `MatEAV-Bench`, use the updated URL accordingly.

### Python Environment

The analysis and validation utilities were developed using Python 3.8+.

Typical dependencies include:

```bash
pip install pymysql pandas matplotlib
```

Additional dependencies may be required for individual analysis modules.

### Database Environment

The primary evaluation environment uses MySQL, while PostgreSQL is additionally used for cross-database consistency validation.

The finalized benchmark database should be imported before running database-dependent validation modules.

---

## Code Availability

This repository provides the code used for:

- heterogeneous data integration;
- EAV database construction;
- benchmark-query construction and refinement;
- reference-result generation;
- SQL executability validation;
- boundary-condition validation;
- semantic consistency checking;
- database sparsity analysis;
- query-level statistical analysis;
- benchmark figure generation.

Intermediate and historical utilities are retained where they document relevant stages of benchmark development.

---
