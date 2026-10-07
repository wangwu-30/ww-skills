---
name: hpo-candidate-search
description: 根据锁定的 Task 需求和对照组快照，为一次常规 HPO Candidate 生成不含动作的实验组配置。
---

# HPO 候选搜索

遵循本 Job 提供的不可变输入、输入说明和输出 schema。输入输出的版本、字段和结构限制由 Job 决定；本 Skill 提供候选选择方法，不指定另一份合同。依据本 Job 的锁定需求和搜索约束生成 treatment，并按其输出 schema 交付。

Task 持有的需求根、用户约束、目标重点和成功策略状态用于选择 treatment，本 Skill 不得重新解释。保留所有精确身份与范围；保留已接受的自然语言和有意未指定的重点；不得补入主要目标、指标 ID、数值阈值、查询方法或成功结论。用户没有要求成功条件时，不替其补设。

依据本 Job 锁定的组数范围选择本轮 treatment 数量。每组交付可直接使用的完整配置，不返回参数补丁，或省略未变字段并期待平台补齐。不得从历史 treatment 推导配置形状。控制组属于 Task：本 Skill 不修改控制组，后续规范化由平台完成。

只提出候选及理由，不输出模板或参数绑定权威、用户参数范围或平台身份。不得创建或控制实验、修改 Task 状态、选择路由、查询 Provider 或报告观测结果。

存在 `output_validation_feedback` 时，它是同一有效 claim 中紧邻上一尝试的有界回执。修正其中报告的错误，继续遵循本 Job 的输入和输出 schema，不借修正改写任务事实或权限。

本 Job 冻结的 Provider 查询参数属于任务数据，按其原始表示保留。保留数字/原始字符串类型、数组顺序、空容器，以及选项缺省与显式 `false` 的区别。新增参数名不允许更改已确认的 report、metric、site、人群、窗口或比较。不得改用相近指标，也不得为取得值而静默删除筛选。

存在 `recent_reflection` 时，使用已采纳上一轮的完整反思和改进建议来选择下一组 treatments。其 `outer_loop` 与 Job/结果引用标识来源。反思仅供建议：保留已确认的 Task 需求、控制组字节与搜索约束；不得把 Reflector 建议转成路由或成功结论。

先读取 `context.intent_revision` 与 `intent_changes`。变更记录按原审计顺序给出前后值，A→B→A 的中间变化仍有意义。`completed_trials[].candidate_source_revision` 仅说明候选生成时的需求版本，不说明实验结果的归属；为 null 时表示来源无法证明，不要猜成初始版本。`recent_reflection.source_revision` 标明复盘使用的需求。结合共用变更说明判断旧建议是否仍适用，不把旧结论直接当成当前需求。

`completed_trials` 中 `status=not_created` 且 `outcome_reason=task_intent_source_changed` 表示“需求修改后不再适用，实验未创建”。这是旧需求下提出、曾获批准但未执行的候选，不是创建失败、参数被平台拒绝或参数效果的证据。保留原审批事实；这组参数如果仍符合当前需求，可以重新提出。已失败或已完成 Trial 的原结果原因保持不变。

`intent_changes.omitted` 标明因输入预算省略的变更覆盖范围和关联材料数量；Trial 事实仍保留，依赖已省略变化的复盘建议会一起省略。不得推断省略内容，或把没有解释的旧材料当作当前结论。当前需求仍以本 Job 冻结的需求字段为准。
