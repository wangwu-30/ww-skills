# Libra 发现、取值与诊断

使用已授权 site 和调用方现有身份/网络配置。精确语法查已安装的 bytedcli Libra Skill 与当前帮助。下列示例是可选的有用读取方式；按已给线索选择，并保留调用入口冻结的身份与范围。

## 原生查询身份

按调用入口提供的合同读取或表达 Libra 身份。执行 Job 时，以本 Job 冻结的身份和 `native_query` 为准：原生查询承载官方 bytedcli 子命令、字面参数向量，以及需要时的结果行选择规则。Provider 查询面和本指南帮助 Agent 理解如何使用它；本指南不规定身份的版本、字段表或类型。命令必须属于其实际 Libra namespace。

下面只示意原生查询如何保留参数与占位符，不是 HPO 输入输出 schema；实际冻结内容仍须符合调用入口合同和官方查询能力：

```json
{
  "subcommand": ["libra", "ad-report", "get"],
  "arguments": [
    "--flight-id", "{{trial.flight_id}}",
    "--report-id", "<confirmed report id>",
    "--group-id", "<confirmed config-group id>",
    "--metric-id", "<confirmed metric id>",
    "--filter", "abtest_bingo=1",
    "--start-date", "{{window.start_date}}",
    "--end-date", "{{window.end_date}}"
  ],
  "row_selection": {"...": "..."}
}
```

行选择器依查询而定：应足以从返回形状识别目标指标、当前 Trial 组和所需比较。不要臆造通用选择语法或取第一行。`{{trial.flight_id}}` 从当前 Trial 解析；`{{group.version_id}}`、`{{group.version_name}}`、`{{group.config.<candidate path>}}` 分别从每个当前组解析；`{{window.start_date}}`、`{{window.end_date}}`、`{{window.start}}`、`{{window.end}}` 来自需求观测窗口。固定业务筛选如 `abtest_bingo=1` 是原始字符串筛选，不得替换成某组版本 ID。参考 flight、日期和版本 ID 不能成为冻结查询中的字面量。

以下是三个不同原生查询面，不要求命令形状统一：

```text
libra experiment report --flight-id {{trial.flight_id}} --metric-group <id> --start {{window.start_date}} --end {{window.end_date}} --merge-type total
libra ad-report get --url <confirmed report URL with preserved filters> --start-date {{window.start_date}} --end-date {{window.end_date}}
libra ad-report get --table-name <confirmed table> --metric-name <confirmed metric> --start-date {{window.start_date}} --end-date {{window.end_date}}
libra experiment realtime --flight-id {{trial.flight_id}} --metric-group <realtime group> --start {{window.start}} --end {{window.end}} --period-type <confirmed granularity>
```

可用 flag 和语法以已安装的 bytedcli Skill 和最新 `--help` 为准。若当前能力与证据支持，可使用 report-link、table-name、metric-name 或 ID selector。命令包含观测窗口；旧 helper 遗漏日期不是省略日期的理由。执行时替换当前 Trial/组/窗口值，并将完整实际命令记入 `query_method`。核查响应完整性、查询状态、实际筛选及行归属。

## 普通 metric-group 与 template 发现

```bash
bytedcli --json --site <site> libra experiment get --flight-id <flight_id>
bytedcli --json --site <site> libra experiment report --flight-id <flight_id>
bytedcli --json --site <site> libra metric-group template get --url <template_url>
bytedcli --json --site <site> libra metric-group template get --id <template_id> --app-id <app_id> --type conclusion
bytedcli --json --site <site> libra metric-group get --id <ordinary_metric_group_id>
```

实验元数据提供实际版本、app、region 及 group/template 线索。template 可以采用 `normal` 或 `conclusion` 结构；应检查真实 category/group/metric 内容，不要把错误 JSON 路径误当空目录。另一元数据路径失败时，`experiment report` 可能仍提供 `metric_meta`；保留失败路径的实际错误。这里的 `metric-group get` 指普通报告组，不是 realtime 组。

```bash
bytedcli --json --site <site> libra experiment report --flight-id {{trial.flight_id}} --metric-group <metric_group_id> --start {{window.start_date}} --end {{window.end_date}} --merge-type total
bytedcli --json --site <site> libra experiment report --flight-id {{trial.flight_id}} --metric-group <metric_group_id> --list-dimensions
```

解释 `report.merge_data` 前检查 `metric_meta.metrics` 定义，以及组内维度/值元数据。维度选择格式 `<dimension_id>:<value_id[,value_id...]>`；同一语义维度在不同组中可能有不同 ID。cross dimensions、趋势和明确 baseline 会改变输出形状或比较语义，应检查其实际输出。当前帮助描述 `--baseline`、`--data-caliber`、`--period-type`、`--data-region`、`--force-show`；它们不覆盖用户约束，也不提供统计策略。错误 data-region 路由可能返回成功但值全为 null 的响应；断言确实无数据前应先排查路由。异步查询超时属于有 continuation 信息的查询失败，不是指标身份缺失。

## Ad-report 发现与精确查询

`/report/ad/<report_id>` URL 标识 ad-report，不是 app 或普通 metric-group。report、config-group、metric 要分开。元数据发现可能包含 UI 名称、描述、表达式、变量和可用筛选项。

广告目录可能包含 folder、tab 和 report。仅有数据新鲜度词不足以选择查询面；来源证据指向广告报告导航或 report 路径时，才支持进入该类型。即使尚不清楚精确 report，也保留来源路径。报告发现和已知报告的框架读取是不同能力。假设存在目录命令前先看当前 CLI 帮助。

在 bytedcli 0.163.0 中，官方 SDK preview 请求携带 `flightId`、`layerId`、`managerType`、`tagIdList`，没有显式 app-ID 参数。记录这些输入、从 flight 解析出的 app context 和返回范围。空 tags 不能证明拿到了完整目录；可读取的已知 report 也可能不在 preview 中。不同 folder/tab 下的名称不会因涉及相同业务就自动等价。若官方工具缺少旧/完整目录发现能力，记录该能力缺口，或使用带原身份的可用官方来源/UI。不得改 experiment tags、猜 endpoint，或从 preview 宣称全局不存在。官方 SDK POST 可用于只读元数据；是否读操作取决于其语义，不只取决于 HTTP 方法。

```bash
bytedcli --json --site <site> libra ad-report get --url '<ad_report_url>' --summary-only
```

Summary 模式提供元数据/组名，不是观测值，且不能与 group/metric selector 同用。解析业务名称时，要检查每个返回 config-group 中全部 metric，才能判断唯一性。保留能闭合 report、config-group、metric 和名称的一条完整元数据项。零匹配、多个真实匹配和枚举不完整是不同的未决事实；部分元数据不能证明身份唯一。detail value 响应不能修复失败的身份查找。创建阶段若明确支持用户确认的身份路径，由调用入口负责；它不构成分析观测。

直接读取使用 `--flight-id`、`--report-id`、`--group-id`、`--metric-id`。封闭的 HPO 身份必须使用其调用入口已有投影合同；官方 CLI 功能不能给该合同添加新字段/筛选。

当前 CLI 帮助将 URL 中非结构化 query key 视为原始字符串筛选，百分号解码值，并用 `@` 拆分选择。显式 `--filter` 可覆盖 URL 值；数值型 `--dimension` 必须明确提供，不从 URL 推断。查当前帮助，不要沿用旧 URL parser 规则。保留所有已出现的 boolean，包括 `false`；不得添加原本缺省的默认值。参考 flight/date 和数值型 query 字段是带有实际语义的线索，不自动替换为当前 flight/group。

## Ad-report 筛选、窗口与结果

分别保留 report/config-group 谓词、可选筛选目录、值枚举和显式 query filter。report URL 可携带字符串筛选；当前帮助支持时，直接 `--filter` 参数也能表达它们。看似数字的字符串仍是字符串筛选。尤其 `abtest_bingo=1` 是原始筛选选择，不是数值维度，也不是版本标识。已知筛选值不代表当前实验版本。只有确认查询确实需要版本 ID 时才用 `{{group.version_id}}`，不能把它替换筛选值。

筛选持续无数据时，还要检查筛选字段如何由实验配置产生。`abtest_bingo` 的查询参数和实验 bingo 命中规则是两个环节：官方[实验 bingo 标签说明](https://bytedance.larkoffice.com/wiki/wikcnRqe8CGQXBDIXAl7gOyDcAf)规定，未填写命中规则时流数据标记为 0。广告实验创建后，在详情页编辑命中规则并点击“保存当前实验”后生效，操作历史记录这次修改；仅编辑而未保存不改变生效规则。保存后，满足规则的新数据标记为 1，修改不回溯历史。实验元数据的 `ad_flight_hit_rules` 承载命中规则；不要把同名展示字段 `bingo` 或辅助报告标签当作规则已经配置的证明。依据当前实验的实际规则、保存时间和查询窗口判断原因，参考实验的规则不能代替当前配置。

错误正文若说明查询结果为空，便有必要检查这些数据生产条件，而不能只按错误码推断权限故障。规则缺失、规则尚未生效与已有规则但没有命中流量，需要不同的处理；结合当前配置、流量和窗口给出判断。若确认缺配，报告所需修订与生效后的可用窗口；旧窗口不会因后来补配置而回填，去掉筛选得到的总量也不能代表命中数据。

正常读取核对官方支持参数、本方调用、内外层状态和返回范围；有效匹配结果可以采用，缺少 scope/SQL 本身不拒绝。新方法接入、参数变化或具体矛盾时，可读执行回执、SQL或做针对性对照；已知筛选被忽略的结果仍不能采用。零值不证明筛选被忽略，差分也不证明枚举完整覆盖。旧[类型化范围 argv helper](scripts/build_ad_report_command.py)仅供原调用者使用，不是冻结身份或原生查询必须使用的执行器。

每项需要时间窗口的查询都应带上窗口。执行时根据当前观测窗口解析日期/时间占位符，并把完整替换后的命令记入 `query_method`。不得因旧 command builder 不接受日期就省略，也不能把参考实验日期冻结到新 Task。

检查实际响应模式：直接 metric 可能用 `group_data`，完整 report 可能用带组级错误的 `group_data_list`，summary 则可能用 `ad_report`。直接结果检查 `has_data`、`base_row`、`rows` 及其 version ID。`base_row` 在 treatment key 下的 diff 与 treatment 行上的反向比较不同。先按已确认指标和当前组 binding 选择行，再依返回 schema 选择相关比较 key。区分 Provider 的方向、单位、值来源与统计；不得臆造置信度或显著性阈值。Table/name、report-link、ID 和完整 report 读取能力各不相同；依据当前帮助和证据选择，不固定调用序列。

## Realtime 层级与筛选

该查询面用于用户的 realtime 看板，不是所有数据新鲜的指标。根据来源定义确定 dashboard/group 关系。在 bytedcli 0.163.0 中，隐式 flight 目录会使用 app -1，虽然 flight 实际 app 可读。显式 `--list-dashboards --app-id` 会选 app，但该版本的 `--dashboard-info` 不会转发传入 app。检查当前工具行为和返回范围；这些限制不能证明指标不存在，也不能解释未解决的广告报告身份。

```bash
bytedcli --json --site <site> libra experiment realtime --flight-id <flight_id>
bytedcli --json --site <site> libra experiment realtime --list-dashboards --app-id <app_id>
bytedcli --json --site <site> libra experiment realtime --dashboard-info <dashboard_id> --show-sql
bytedcli --json --site <site> libra experiment realtime --flight-id <flight_id> --metric-group <realtime_group_id> --start '<YYYY-MM-DD HH:mm:ss>' --end '<YYYY-MM-DD HH:mm:ss>' --period-type h
```

Dashboard list 是目录，不证明哪个 dashboard 符合业务。检查 `realtime_dashboard.metric_groups`、其 metric/定义、组 SQL view 和 `filters`；业务指标可能嵌套在标题不含其名称的 dashboard 下。依据原链接、业务路径、定义、app/site 和 region 确认匹配。ROW dashboard 存在不代表适用于其他 region。

使用 site 时区设定实际窗口：官方文档对 TikTok ROW/US 使用 UTC，对中国使用本地 CST。保留明确窗口并记录时区/粒度。原生 realtime 命令不提供 `--data-region`、dashboard filter 或单 metric selector。它查询整个 realtime group；未知的 `metric_id`/`metric_ids` 参数不能证明服务器做了缩窄。根据 `realtime_report.merge_data` 中 metric 的 baseline/treatment 行和 pairwise diff key 选择，不取第一行。

需求要求的 dashboard filter 若原生帮助无法表达，当前官方 `insearch get` 支持对 allowlisted 内部 URL 发只读 plain GET，并使用调用方受管认证。这是既有授权下的一种查询方法，不是更改身份或使用原始秘密的许可。实时数据 endpoint 为：

```text
GET https://<authorized-libra-host>/datatester/report/api/v3/app/<app_id>/experiment/<flight_id>/realtime/dashboard/data
```

常见 query key 包含 `flight_id`、`metric_group`、`period_type`、`view_type=merge`、`start_date` 和 `end_date`。Dashboard `filters[].key` 给出精确后端 filter key。参考实现把每个 key 作为 URL 参数，并使用运算符/值表达式（如 `=,0`）；按实际定义对 key/value 做 URL 编码，不能根据展示标签猜测，也不能附加通用 `filters=` JSON 参数。保留所选枚举值和精确排除条件；子串排除可能误删另一个真实值。

接入这种查询方法或参数语义改变时，核实官方支持的 key/value 与本方调用，针对已知忽略问题做回归。正常请求正确且返回有效匹配结果时可采用，不要求每轮响应含 SQL。出现具体范围矛盾时，若响应提供 SQL可检查 `WHERE`，或使用其他针对性证据；已证实筛选缺失的结果不能采用。全为零也不证明筛选被忽略。保留方法限制，不臆造 Task范围，不回退到未筛选值。

## 深度分析定义及受支持的计算

广告 config-group 也可能暴露官方 deep-analysis 数据源、metric 和 dimension 定义。用当前 `libra deep-analysis` 帮助选择元数据读取方式；datasource list 可能只有 metric 名/ID 摘要，detail 才提供定义和表达式。应检查完整返回定义，不只看首屏片段。Datasource ID、metric ID、dimension catalog ID 和 detail ordinal 要区分。GMV 公式相似不代表是所需指标，除非 attribution、单位与人群也匹配。币种/筛选证据缺失时仍保持未确认。

元数据读取不会计算数值，也不能证明统计可用。当前查询帮助要求受支持的结构化 `--body-file`；URL 输入只是 locator，不能提供或覆盖 body。检查受支持的 select/where/time 结构；不支持的 group/dimension 字段要拒绝，不能假设任意 SQL 或请求字段都被接受。保留真实请求，核对正确参数和响应范围；正常无 SQL/scope 的有效结果可采用，具体矛盾再针对性取证。遵循官方客户端当前认证有效性检查：即使 envelope success，session 也可能失效或结果不可用。不得导出凭据或绕过格式/auth 拒绝。

对 HPO 调用入口而言，定义证据可帮助把需求解析为既有受支持身份。如果唯一可用的值查询不能由已锁 schema 忠实表达，则在已有分析字段记录准确合同/能力缺口。不得臆造 datasource union member、向封闭 identity 附加 query 字段，或把 deep-analysis 结果改标成其他查询。

## 大型 realtime 响应

Realtime group 可能一次返回所有 metric、版本行、成对差异和执行 SQL。缩短窗口未必减少结构。原生 Libra 与 `insearch get` envelope 不同：原生 JSON 通常用 `data.realtime_report`；plain GET 把原始 body 包在 `data.body` 下（里面本身还可能有 Provider `data`）。选 JSON 路径前检查 status、`bodyKind`、`truncated` 和实际形状。jq 投影返回 null 本身不是数据缺失证据。

当前 `insearch get` plain-GET wrapper 有独立响应字节上限；把 stdout 重定向或增加 `--http-body-limit` 不会提高该上限。遇到 wrapper 截断时，官方 HTTP response-body trace 可作为恢复路径，使用 `--http-print b`、`--http-trace-file <local_file>` 和合适的 `--http-body-limit <bytes>`，请求仍只读。上限应根据实际响应大小确定，不照抄固定预算。这些参数选择 body trace，不选择认证 header。trace 和正文留在本地；不要开启默认 header trace，也不要在上下文打印完整正文。

Trace 是诊断输出，可能含多份响应、脱敏内容和自身的 `[truncated]` 标记。找出目标成功数据响应，确认 JSON 完整可解析、Provider status 成功，目标 metric、当前组与比较行完整匹配；SQL/scope不是正常结果的必需字段。不能盲取最后一行，也不能把部分 body 称为完整。若无法恢复或仍不完整，应报告 query error，而非 metric missing。只把目标 metric/行及相关范围证据摘录到既有分析，并按调用入口现有规则保留完整文件。
