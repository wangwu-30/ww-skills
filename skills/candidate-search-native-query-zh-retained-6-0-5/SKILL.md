---
name: hpo-candidate-search
description: 根据锁定的 Task 需求和对照组快照，为一次常规 HPO Candidate 生成不含动作的实验组配置。
---

# HPO 候选搜索

只使用 Agent Job 提供的不可变 `hpo.candidate-search-input/v7`。Task 持有的需求根、用户约束、目标重点和成功策略状态用于选择 treatment，本 Skill 不得重新解释。保留所有精确身份与范围；保留已接受的自然语言和有意未指定的重点；不得补入主要目标、指标 ID、数值阈值、查询方法或成功结论。`explicitly_none` 表示用户没有要求成功条件。

严格返回注入的 `hpo.candidate-search-result/v8` 合同。实际 treatment 数必须处于已锁定的 `min_treatment_count` 与 `max_treatment_count` 区间。顶层对象只能包含：

- `schema_version`；
- 非空的 `treatments` 数组；每项只能包含完整 JSON 对象 `config`；以及
- 必需且长度受限的 `summary` 字符串。

不得输出 `action`、`candidate`、`questions`、`control`、`REQUEST_HUMAN` 或 `NO_OP`。控制组不属于本 Skill：Agent Job 携带的不可变 Task 控制组快照，只会在成功完成后由 Job-to-Trial 规范化器准确合并一次。

每个 treatment 的 `config` 都必须是完整 JSON 对象。不得返回参数补丁，或省略未变字段并期待平台补齐。不得从历史 treatment 推导配置形状。不得输出模板或参数绑定权威、用户参数范围、控制组字节或平台身份。不得创建或控制实验、修改 Task 状态、选择路由、查询 Provider 或报告观测结果。

存在 `output_validation_feedback` 时，它是同一有效 claim 中紧邻上一尝试的有界回执。只修正其中报告的结构错误，仍严格返回 v8 形状。

广告查询范围会把 Provider 参数键作为数据放在已确认的 dimensions 与 filters map 中。保留数字/原始字符串类型、数组顺序、空容器，以及选项缺省与显式 `false` 的区别。新增参数名不允许更改已确认的 report、metric、site、人群、窗口或比较。不得改用相近指标，也不得为取得值而静默删除筛选。

存在 `recent_reflection` 时，使用已采纳上一轮的完整反思和改进建议来选择下一组 treatments。其 `outer_loop` 与 Job/结果引用标识来源。反思仅供建议：保留已确认的 Task 需求、控制组字节与搜索约束；不得把 Reflector 建议转成路由或成功结论。
