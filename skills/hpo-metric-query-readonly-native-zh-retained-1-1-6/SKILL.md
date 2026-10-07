---
name: hpo-metric-query-readonly
description: 使用只读查询解释并获取指标，保留已确认的原生查询身份、范围、筛选和结果归属。
---

# HPO 指标只读查询

将本候选入口作为 `queryMetric` 依赖，用于 primary contract 支持已确认 Libra 原生查询的 Job。读取已锁定的输入/输出版本；不得用本说明升级旧 Job 的语义。

读取不可变 Task 需求、来源线索、既往查询证据和当前 Trial 观测 context。既有结构化结果与交互合同归 primary Analyzer Skill 负责。

先读[共用查询指南](references/metric-query/GUIDE.md)，再读适用的 Provider 说明。根据本 Job 实际 site、实验、baseline/treatments 和允许的窗口运用其中知识。参考实验用于发现身份和含义；它的观测不是本 Trial 测量值。保留精确冻结身份及用户显式约束。

通过 primary Skill 既有字段和正常 Runtime trace，报告每次尝试解析出的身份、方法、范围、观测或实际阻断原因。不得添加顶层输出、提问协议或证据存储。缺失、歧义或失败的观测都不授予生命周期写权限。

[Analyzer 查询合同](references/query-contract.md)说明既有原生身份与结果边界。共用知识用于选择合适的官方只读方法；它不改变结果边界，也不冻结调用顺序。
