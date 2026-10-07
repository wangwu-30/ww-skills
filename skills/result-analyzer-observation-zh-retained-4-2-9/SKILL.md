---
name: hpo-result-analyzer
description: 分析当前 HPO Trial 的指标，保留逐需求记忆、查询证据和有界历史，并提出可审阅的建议。
---

# HPO 结果分析

读取已锁定的 `hpo.result-analysis-context/v9` 中的 Task、Trial、Binding、组快照、cadence 和指标查询锚点。使用已安装的 `queryMetric` 与 `bytedcli` Skills 执行只读查询。已确认目标与 guardrail 是完整的需求权威。精确身份可使用 Libra 或 Metrics-FE；自然语言需求可能需要解释。保留用户约束、区域、站点、人群和成功策略。查询 Provider 不会改变实验 Provider，也不授权生命周期写入。

严格按 Job 锁定的输出 schema 返回 `hpo.result-analysis-result/v7`。包含 `recommended_action`、`metric_query_status`、`metric_query_summary`、`analysis`，以及一个 `hpo.analyzer-metric-snapshot/v3` 格式的 `metric_snapshot`。设置 `source: agent_reported` 和 `purpose: display_only`；从输入复制 Task/Trial/Binding/组/cadence 身份，并报告带时区的 `collected_at`。

读取每项冻结需求原始的分析/成功/guardrail 条件、先前观测时间和读数，以判断当前哪些需求到期。快照的 `requirements` 必须恰有本轮检查的每项需求，并以 `requirement_ref` 承载。尚未到期的需求省略；省略不代表查询缺失。每轮可检查一项或多项需求。每个引用都必须属于冻结目标/guardrail。不得仅因查询相同指标而合并两项需求。每项要求：

- 保留已确认的精确身份，或报告自然语言需求实际解析出的身份。不得声称解释会改变冻结 Task 需求。
- 记录实际只读 `query_method`、可取得时的已知统计 `window`，否则明确写未知窗口；并精确列出冻结组快照中适用的实验组。`applicable_groups` 位于 objective/guardrail 需求上：缺省或 `all` 覆盖所有组，`treatment_only` 仅覆盖 treatments。该需求的状态和停止证据都要排除 control 行。不得替换为参考实验组或版本 ID。
- 对观测到的组，包含有限值、值来源和可得的有界统计。零是有效值。
- 查询缺失、歧义或失败时分别使用 `missing`、`ambiguous` 或 `error`，提供具体且非空的 `reason`，并省略值/统计。身份或查询方式尚未解析时可以为 null。不得编造值，也不得在无法完成查询时丢掉该项已检查需求。

整体 `metric_query_status` 概括本轮已检查需求；仅当它们所有适用组均已观测时才用 `observed`。即使其他要求支持停止建议，也要保留每项已检查需求的缺失、歧义或失败状态。

对 `STOP_RECOMMENDED`，可选提供非空且唯一的 `stop_evidence_refs`。每个引用必须是冻结需求、本轮检查项，并且每个适用组均已观测。解释这些观测为何支持停止，以及其他需求仍有何缺口或本轮未查哪些项。无引用时，必须在本轮检查并观测全部冻结需求和其全部适用组。旧读数单独不能作为当前停止引用。平台会开放既有人工决策；该建议本身不会停止实验。Agent 快照不是 Provider 签署证据，也不会自动授予控制权限。

可选返回正数 `next_check_after_seconds`，根据下一项到期需求、条件、历史和数据新鲜度设定。分析完成后，程序会将等待限制在平台最小值与 Task 已确认的 `analyzer_cadence_seconds` 最大值内。省略此值或本轮失败时使用该最大值。分析耗时会计入实际间隔；这不保证每项需求都能在最大等待时间内观测。时间阈值应来自冻结输入和公开 capability，不得臆造默认值。

缺口若依赖用户独知事实，可选返回 `question_for_user: {question, requirement_refs}`。提出具体业务问题，例如哪份报告/站点代表目标路径，或零流量是否符合预期。缺失日期参数、工具/传输错误及可从已安装 Skills 查明的事实属于你的诊断职责：修复或报告 `error`。完成当前报告后继续监控，等待用户答复。若有 `open_question`，不得再发新问题；在分析中描述仍在等待。后续 `question_answers` 只能作为解释材料，并保留用户原始答复。选择范围覆盖整个 Task，包括更早 Trial。读取 `question_answers_coverage`：`latest_request_ref_by_requirement` 把每项需求映射到最新已回答请求。多个需求共用的问题只携带一次原始引用；仅应用于当前映射仍指向该请求的需求。更新答复会替换该需求的旧答复。`included_request_refs` 和 `omitted_request_refs` 标明预算中携带或省略了哪些完整答复。省略的答复不是撤销事实，也不能据此采用过时答复。解析记忆也有独立 coverage；不得假定其中包含已省略原始答复的方法或身份。答复完整保存在决策历史中，输入携带上限为 8000 字符。答复不会改变冻结需求或精确身份。若答复要求不同的已确认身份/含义，仍是缺口；用户须走原有流程修改需求。

把经过清理的查询回执留在 Runtime trace。不得把原始工具输出、凭据、trace 文本或未声明字段放进有界结果。不得写入 Task、Provider、实验或证据。

解释提供的 Analyzer 报告前，先读取 `history_scope` 覆盖范围。输入按 cadence 顺序冻结了本 Trial 最近至多 `limit` 份有效已完成报告。每份投影保留完整 `analysis` 与 `metric_query_summary`，并通过 digest 引用完整持久 Job 结果。每份报告的 `requirement_resolutions` 可包含已采纳查询状态、原因、解析身份、执行方式、观测时间/窗口及分组读数/统计。`latest_requirement_resolutions` 独立提供每项需求最近一次已检查报告的解析，它可能早于这三份完整正文。优先复用此前成功的解析方式，同时替换为当前 Trial/组/窗口值；若证据变化或先前失败，则重新发现并解释新方法。旧解析是有用证据，但不是新的冻结身份。需要连续观测或累计条件时，使用实际历史读数；不得从摘要虚构连续性。

读取 `resolutions_coverage`：可选记忆按“先删方法、再删组读数、再删整项”的顺序缩减。计数器报告省略量；完整持久结果不变。缺少读数不等于零。整项省略计数无法指出此前检查了哪些冻结需求，不得据此推断缺失记忆等于从未检查。不得截断或概述输入中的报告正文。更早报告以完整正文形式省略，其最近需求事实仍可能出现在独立记忆中。没有额外历史读取入口。

问题/答复记录仍保存在既有持久人工决策历史中。累计问题历史过长时，输入 coverage 是独立的有界交接决策；不得声称当前输入包含所有先前答复。

使用 `history_scope` 区分近期证据和 Trial 全部执行历史。不得推断被省略报告的内容，也不得把近期模式说成覆盖全部历史周期的结论。

对已确认 Libra 身份，使用冻结的 `hpo.libra-native-metric-query/v1` 字节作为查询权威：`provider`、`query_type`、`site`、`display_name` 和不透明的 `native_query`。不要把旧 dimensions/filters map 重建为身份，也不要调用其 argv helper 作为身份合同。命令参数查已安装 bytedcli Skill 的最新帮助；对该指标使用冻结的原生子命令和参数。执行时才把 `{{trial.flight_id}}` 替换成当前 Trial；并分别解析每个当前组的 `{{group.version_id}}`、`{{group.version_name}}` 和任意 `{{group.config.<candidate path>}}`。`{{window.start_date}}`、`{{window.end_date}}`、`{{window.start}}`、`{{window.end}}` 从观测窗口解析。不得复制参考 flight、日期或版本值到新 Trial 查询。例如固定筛选 `abtest_bingo=1` 应保持原始字符串筛选值 `"1"`，既不是数值维度，也不是版本 ID 替换。

使用冻结查询的行选择规则和完整响应元数据，选出目标指标、当前组行及所需比较键。不得把第一行当捷径。通过 SQL/scope 等执行证据核实 Provider 确实应用了请求筛选；请求回显和 HTTP 成功都不充分。`query_method` 记录完整实际命令，包括替换后的 Trial/组/窗口值。原生 report-link、表名、指标名与 ID 选择器可能因 Provider capability 而异；保留冻结选择，不强行统一语法。旧 helper 缺少窗口参数不授权省略实际观测日期。

相关细节由本 Job 已安装的 `hpo-metric-query-readonly` Skill 提供。按该包目录读取：
- `references/metric-query/libra.md`：Libra 发现、取值与诊断。
- `references/metric-query/metrics-fe.md`：Metrics-FE / Bosun。
