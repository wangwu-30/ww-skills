---
name: hpo-metric-query-readonly
description: 使用只读查询解释并获取指标，保留已确认的原生查询身份、范围、筛选和结果归属。
---

# HPO 指标只读查询

作为本 Job 的 `queryMetric` 依赖，遵循本 Job 提供的不可变输入、输入说明和输出 schema。本 Skill 提供发现、查询与诊断方法；输入输出合同由 Job 定义，不由 primary Skill 或本说明指定。只使用该 Job 能表达且允许的查询方式，不用本说明升级旧 Job 的语义。

读取不可变 Task 需求、来源线索、既往查询证据和当前 Trial 观测 context。分析结果和交互方式以本 Job 的合同与说明为准。

先读[共用查询指南](references/metric-query/GUIDE.md)，再读适用的 Provider 说明。根据本 Job 实际 site、实验、baseline/treatments 和允许的窗口运用其中知识。参考实验用于发现身份和含义；它的观测不是本 Trial 测量值。保留精确冻结身份及用户显式约束。

通过本 Job 输出 schema 提供的分析位置和正常 Runtime trace，报告每次尝试解析出的身份、方法、范围、观测或实际阻断原因。不得添加顶层输出、提问协议或证据存储。缺失、歧义或失败的观测都不授予生命周期写权限。

[查询结果解释](references/query-contract.md)说明如何保留原生身份、解释观测与诊断。共用知识用于选择合适的官方只读方法；它不改变结果边界，也不冻结调用顺序。
