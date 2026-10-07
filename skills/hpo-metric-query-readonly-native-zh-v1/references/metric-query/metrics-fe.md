# Metrics-FE / Bosun 只读查询

Metrics-FE 属于 Byteplot/Bosun，与 Libra 使用不同 namespace。从给定 service/page URL、canonical metric/expression、site、region 和显式查询约束开始。支持语法以已安装的 bytedcli APM Skill 及当前帮助为准。本知识不定义 Libra metric ID、create-body metric、参考 control-plane site 或目标实验创建站点/区域。

## 来源线索、URL 与查询范围

Plot URL 的 fragment 可能包含窗口、region 和分号分隔的表达式，例如：

```text
https://<metrics-fe-host>/web/plot/metrics#now-1h,now,,,,,,,<region>,false,,;<expression>;0
```

提取实际表达式；必要时对 URL 编码的字节进行百分号解码，并保留原始 URL 作为来源。不得改写 metric、aggregator、tag key 或 tag value。`now-1h,now` 的来源窗口可对应 `--duration 1h`；明确绝对窗口则须用适用的时间参数。复制示例不会为原本未指定的 Task 新增窗口。

以下来源示例仅供线索参考，不是完整 site 注册表，也不能证明身份：

| 来源 host | 查询 site | Byteplot region 示例 |
|---|---|---|
| `metrics-fe-ttp-us.tiktok-row.org` | `us-ttp` | `US-TTP` |
| `metrics-fe-i18n.tiktok-row.org` | `i18n-tt` | `Singapore-Central` |
| `metrics-fe.byted.org` | `cn` | 使用实际 plot region |

依据来源的实际选择方式和当前 bytedcli 能力进行核对。site 选择后端；`--region` 不会切换 site。fragment 中的 region 不能单独证明页面/后端切换。Byteplot region 与另一 Metrics OpenAPI 的 `_region` 不同。保留调用方已授权网络/profile；请求失败不能授权换 endpoint 或凭据。

先辨明链接是当前任务来源、参考对象、历史示例还是一般说明。示例中的 host、region、tag和窗口都不能静默成为当前固定条件。创建时核对本任务数据来源与站点/区域的适用依据，并在完整预览中披露重要推断；不能仅因链接能解析就确认身份。执行站点与查询站点不要求相等，但二者用途和依据都须明确。正式观测沿本 Job 已确认值使用显式参数。

空序列时，实验实际生效区域、指标路由和原链接用途能帮助检验查询区域是否适用；执行区域与查询区域不同本身还不是错误证明。有元数据支持另一条路由时，可保持指标、聚合、当前组标签、窗口和评估锚点相同，比较不同 site/region 组合的响应及返回标签。这样的对照比轮换区域直到有值更能说明原因。按共用指南区分诊断证据与正式观测，记录两套依据及需要的修订。

```bash
bytedcli --site <site> --json apm bosun query '<expression>' \
  --duration <lookback> --region <byteplot-region>
```

将表达式作为单个字面 argv 参数传入，绝不作为 shell 代码插值。当前支持时，原始 OpenTSDB/ByteTSD 表达式可含 `p90:`、`p99:`、`pct90:`、`store:` 和 `literal_or(...)`。当前帮助也支持完整 `q(...)` 和多行 Argos alert template（直接文本或 `@file`）；较旧 recipe 中“所有多行格式都不支持”的说法不能覆盖当前能力。不得臆造其他语句形式，也不得换成独立的 `apm argos bosun query` VMP/PromQL 接口。

根据帮助查 `--duration`、`--downsample`、`--region`、`--all-regions`、`--end-time`、`--start-time` 和 `--at`。Downsample 会改变采样细节；`--all-regions` 仍限制在选定 site 内，且必须符合目标范围。`--end-time` 是 Unix 秒级 UTC 评估锚点；`q(...)` 中的 duration 相对于它计算，应保留该锚点以便复现。范围查询/显式点查询与原始表达式 lookback 不同。CLI 默认属于应记录的查询行为，不是新的 Task 约束。扩大窗口会改变成本和细节，只能在用户允许范围内选择。

身份不完整时，来源文档与可用 instrumentation 代码可用于把用户含义连接到已发出的 metric、aggregator、tag key 和配置派生值。保留精确来源坐标及映射；仅有 service 名或配置键并非 metric 定义。适用于该来源时，官方只读元数据方法包括：

```bash
bytedcli --site <site> --json apm metric search --prefix '<metric-prefix>'
bytedcli --site <site> --json apm metric field-list --metric '<metric-name>'
bytedcli --site <site> --json apm metric tagk-list --metric '<metric-name>'
bytedcli --site <site> --json apm metric tagv-list --metric '<metric-name>' --tags '<tag-key>'
```

这些命令发现原生 metric 字段/tag；它们可用并不代表 Bosun `store:` 表达式可与原生 `apm metric query` 或 Libra 查询互换。如果来源不支持这些 metadata，就保留实际缺口和用户提供的精确表达式，不臆造 endpoint。

## 当前实验 tag 与组覆盖

metric 名称标识服务 instrumentation，不标识 Libra 实验。使用当前观测 context 与冻结版本配置中的精确组 tag 值，并使用能证明 tag key 的表达式或 instrumentation 映射。执行时，已确认的组专属值可写为 `{{group.config.lsa_ltv_opt_traffic_exptag}}`，并为每个组从该组冻结 candidate config 解析。原 Metrics-FE URL 保持原样作为来源，同时单独记录已解析表达式和查询窗口。配置键 `lsa_ltv_opt_traffic_exptag` 能提供一个值，但不能证明发出的 tag key 是 `abtest_tag`。

若实际 key 是 `abtest_tag`，多个精确值使用 `literal_or(<control-tag>|<treatment-tag>)`，分隔符为 `|` 而不是逗号。逐组查询时用该组自己的 tag，不能重用参考实验的值。保留大小写/下划线及所有必需组。control tag 缺失就仍然缺失；不得伪造或从参考实验借来当前身份。具体 service 如 `ad.reranker.tiktok.lsa_longterm_value.disturb_coef` 或历史 tag 值只是候选来源示例，不得在没有匹配证据时成为默认值或冻结 Task 值。

核对返回的 `Group` tags 与请求组相符。若用户规则适用于任意单组，须分别评估每条 series；跨组平均可能掩盖违规。分开记录 percentile 与 mean，不要把数值接近当作身份依据。

## 响应形状、完整性与本地统计

常见成功 series 响应包含 `data.Type = "series"` 和 `data.Results[]`；每项含 `Group` 对象以及按 Unix 秒索引的 `Values`：

```json
{"status":"success","data":{"Type":"series","Results":[{"Group":{"abtest_tag":"<exact-tag>"},"Values":{"1785842730":0.0961,"1785843030":0.5351}}]}}
```

这只是形状示例，不是查询回执或备用结果。检查实际 type、组、数值时间戳、值与范围。空 `Results`、空 series、null/缺失点、合法零值、不支持的响应形状和查询失败属于不同结果；都不能静默证明 guardrail 健康。大响应遵循共用指南中的本地文件/完整性处理；原始捕获字节、实际请求/窗口与派生统计分开保存，并遵循调用入口已有证据规则。

每条 series 的本地统计可包括 count、min、max、样本算术平均值、total 和最早/最晚样本时间。按数值排序时间戳，并记录 UTC 与相关本地时区。示例两点的 count 为 2、mean 为 0.3156、total 为 0.6312。算术平均是不加权平均：逐分钟 p90 的平均不等于总体 p90；样本求和也不是事件计数或积分。不要补齐缺失 bucket。

保留完整 series，包括最新可能不完整的 bucket。若允许的方法要求排除一个已确认不完整的 bucket，记录时间、原因及完整/纳入后的两份统计。不得为通过阈值而丢弃异常末点。包内纯本地[统计辅助脚本](scripts/metrics_fe_summarize.py)可读取已捕获的成功 series 响应文件或 stdin，只依赖 Python 标准库，不调用服务/CLI、不写文件：

```bash
python3 scripts/metrics_fe_summarize.py --help
python3 scripts/metrics_fe_summarize.py result.json
python3 scripts/metrics_fe_summarize.py < result.json
```

从该 guide 的安装目录运行，或相对该安装解析脚本路径。仅管道输入不会保留原始回执；调用入口需要来源时，应先保存回执。辅助脚本保留所有 bucket，逐 series 汇报，不提供统计策略。退出码 0 表示本地处理完成（包括无数据）；1 表示输入错误/无效；2 表示 CLI 用法错误。本地解析成功不是 Provider/query 成功或业务接受。按现有结果合同报告不确定状态；统计和本指南均不授予实验生命周期权限。
