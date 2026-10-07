---
name: qcpx-aeolus-auuc
description: "使用 Aeolus SQL 评估 QCPX 各券档的 uplift 并生成 AUUC 报告。适用于 100 桶 AUUC、20 桶校准/均匀度诊断，或与 15% 券档对照组进行比较。"
---

# QCPX Aeolus AUUC 评估

通过 `bytedcli aeolus query-editor` 查询 DeepInsight 明细，评估 QCPX 各券档相对 15% 券的 uplift 排序效果。

使用前按任务读取对应参考文件；执行完整报告时必须完整读取以下三个文件：

- [references/auuc-sql.sql](./references/auuc-sql.sql)：20 桶值准与组间样本均匀度诊断。
- [references/auuc-sql-100.sql](./references/auuc-sql-100.sql)：100 桶 AUUC 明细。
- [references/chart.py](./references/chart.py)：合并两份查询结果，计算核心指标、诊断指标并生成综合图。

相对路径以本 skill 所在目录为准，不依赖调用者的工作目录。参考文件带有具体模型、日期和输出目录，只作为模板；为任务生成副本后修改，不覆盖参考文件。

## 输入与前置校验

执行前确定以下信息；能从上下文或元数据获得的无需重复询问，无法确认时先向用户补齐，不沿用参考 SQL 的历史参数：

- 目标 Forge job ID、site，或已确认的 `model_name` 和 ClickHouse 数据源。
- 请求时间窗口、服务端落库时间窗口，以及是否需要固定数据快照截止时间。
- label、预测 head 和样本筛选条件；比较模型时分别确认映射，并保持业务含义一致。
- 输出 20 桶诊断、100 桶 AUUC，还是包含 CSV 与图片的完整报告；已有评估协议时优先遵守该协议，不擅自更换归一化方式。

需要查询 Forge 元数据时使用 `forge-cli` skill；执行 Aeolus 命令时使用 `bytedcli` skill。

### 数据源与 Head 映射

对每个目标 job 分别读取 verbose meta：

```bash
forge --site <site> job deepinsight get-meta --job-id <job_id> --verbose
```

读取 `model_name`、head 映射及 `clickhouse_cluster`、`clickhouse_database`、`clickhouse_table`：

- Aeolus 的 `--cluster-name` 使用该 job 的 `clickhouse_cluster`。
- SQL 的 `FROM` 使用 `<clickhouse_database>.<clickhouse_table>`。
- 不根据 job ID 猜测模型名，也不假设 baseline 与 trial 位于同一集群或同一张表。不同来源分别查询，再对齐口径比较。
- 核对 `head_8` 是否为 15% 券预测，`head_9` 至 `head_13` 是否为对应 treatment 预测，`head_68` 是否为目标 label。
- 确认 `predict{'head_5'}=1` 的业务含义，以及 `extra_int{'coupon_discount_rate'}` 的取值单位。元数据不足时继续检查模型定义，不根据 head 编号推断。

## 参考 SQL 口径

### 文件选择

| 用户目标 | 必需文件 | 产物 |
|---|---|---|
| 查看值准或样本均匀度 | `auuc-sql.sql` | 每个 treatment 的 20 桶观测/预测 uplift 与组内样本数 |
| 计算 AUUC | `auuc-sql-100.sql` | 每个 treatment 的 100 桶正样本数与 score 统计 |
| 完整诊断报告或综合图 | 两份 SQL + `chart.py` | 核心指标、值准/均匀度诊断、明细、SQL 快照和 PNG |

不能用 20 桶结果代替 `chart.py` 所需的 100 桶 AUUC 输入，也不能只运行 100 桶 SQL 后生成值准和均匀度诊断。

### Treatment 与排序分数

对照组固定为 `extra_int{'coupon_discount_rate'} = 15`，不是 no-coupon，也不是 `actual_coupon_index = 0`。

| treatment | 对照档位 | score |
|---|---|---|
| 20 | 15 | `predict{'head_9'} - predict{'head_8'}` |
| 25 | 15 | `predict{'head_10'} - predict{'head_8'}` |
| 30 | 15 | `predict{'head_11'} - predict{'head_8'}` |
| 35 | 15 | `predict{'head_12'} - predict{'head_8'}` |
| 40 | 15 | `predict{'head_13'} - predict{'head_8'}` |

`y = label{'head_68'}`。只有确认 label 为二元转化标签时，`avg(y)` 才解释为 CVR；否则应称为 label 均值。

两份 SQL 的共同处理顺序：

1. `expanded` 将样本展开到 `[20,25,30,35,40]`，为每个 treatment 计算 score。
2. `paired` 仅保留实际档位为 15 或当前 treatment 的样本。
3. `ranked` 在每个 treatment 内按 `score DESC, uid ASC` 排序，对 treatment 与 control 混合分桶，不分别排名。
4. 20 桶 SQL 使用 `least(20, intDiv((rn-1)*20, total_n)+1)`；100 桶 SQL 使用对应的 100 桶表达式。桶 1 的预测 uplift 最高。
5. 20 桶 SQL 输出组内 label 均值；100 桶 SQL 输出两组 label 总和，供后处理精确计算 AUUC。

`uid` 仅用于同分排序，SQL 不会按用户去重。同一 `uid` 有多行且 score 相同时，顺序仍可能不稳定；只有确认了稳定的样本唯一键后，才在比较双方同步补充排序键。

### 必须检查和替换的位置

两份 SQL 是带具体参数的完整模板，**没有 `{{...}}` 占位符**。生成独立的执行 SQL，并在两份副本中同步替换所有参数；保留参考文件不变。

| 两份 SQL 中的位置 | 执行前处理 |
|---|---|
| `FROM reckon.deep_insight2_sail` | 替换为目标 job 的真实明细表 |
| `model_name='shop_qcpx_t3_sipw_0813_streaming_r6641741_0'` | 替换为确认后的模型名 |
| `toDate(server_time)` 的 `2026-09-01` 至 `2026-09-10` | 替换为落库时间窗口 |
| `server_time <= 1789047442` | 替换为目标快照截止时间；确认不需要快照限制时才移除 |
| `toDate(req_time)` 的 `2026-09-01` 至 `2026-09-10` | 替换为请求时间窗口 |
| `label{'head_68'}` 和 `sample_rate{'head_68'}` | 同步对齐目标 label head，包含非空过滤处 |
| `predict{'head_5'}=1` | 确认并保留目标样本群体的筛选语义 |
| `head_8` 至 `head_13` | 同步对齐 control 和各 treatment 的预测 head |
| `[20,25,30,35,40]`、`IN (15,20,25,30,35,40)`、所有 `actual_discount=15` | 共同定义 treatment/control；改变档位时同步修改配对、计数和均值条件 |

注意：

- 两个 `BETWEEN` 均包含首尾日期。请求时间、落库时间和快照截止时间的过滤会同时生效；保留旧截止时间可能让新窗口完全无数据。
- 确认时间字段类型、Unix 秒值含义和 ClickHouse 查询时区，不直接按本机时区解释边界。
- `sample_rate{'head_68'} > 0` 仅筛选样本，不代表已做逆采样率加权或 IPW。不要将本结果称为去偏因果效应估计。
- 不自动套用其它 AUUC 模板中的 `head_20`、`head_37`、`actual_coupon_index` 或额外 `incentive_type` 条件。
- 改 treatment 列表时同步改 `multiIf`；当前最后一个分支默认使用 40% 券预测，不能直接追加新档位。
- 完整报告中两份 SQL 的数据源、模型、双时间窗口、快照、head、过滤条件、treatment/control 和排序规则必须完全一致。任一差异都会使 AUUC、值准和均匀度结论不可联合解释。

## 查询执行

### 1. 轻量校验

先对每个目标数据源确认模型有数据。以下占位符需替换后再提交：

```sql
SELECT model_name, count() AS cnt
FROM <source_table>
WHERE toDate(req_time) BETWEEN toDate('<req_start>') AND toDate('<req_end>')
  AND toDate(server_time) BETWEEN toDate('<server_start>') AND toDate('<server_end>')
  AND server_time <= <snapshot_end_unix_seconds>
  AND model_name = '<model_name>'
GROUP BY model_name
```

不使用快照限制时，同步移除此条件。随后按完整样本筛选条件检查各 `coupon_discount_rate` 的数量、label 非空率及均值，确认 control 和目标 treatment 都有有效样本。核对 score 是否含 NULL、NaN 或 Inf；存在异常时先查 head 映射或数据质量，明确过滤口径后才继续。

### 2. 提交完整 SQL

完整报告需要执行两份参数一致的 SQL。建议将副本分别保存为：

- `/tmp/qcpx_auuc_20bin.sql`
- `/tmp/qcpx_auuc_100bin.sql`

文件中只放 ClickHouse SQL，不夹带 Python 或 Markdown。对于 i18n/SG 数据源，每份 SQL 分别执行：

```bash
SQL=$(cat /tmp/qcpx_auuc_100bin.sql)
bytedcli --json aeolus query-editor query one \
  --sql "$SQL" \
  --region sg \
  --engine ch \
  --cluster-name <clickhouse_cluster> \
  --ch-region SG
```

| 参数 | 含义 |
|---|---|
| `--sql` | 完整 ClickHouse SQL |
| `--region sg` | Aeolus 服务 region，适用于此处 i18n/SG 场景 |
| `--engine ch` | ClickHouse 引擎 |
| `--cluster-name` | 来自当前 job 的 verbose meta，不能固定 |
| `--ch-region SG` | ClickHouse 物理 region |
| `--json` | 返回 JSON，供后续解析 |

其它 region 需先确认对应配置和权限，不盲目复用 `sg` / `SG`。检查返回中的查询状态与错误，再读取实际数据行；不要将命令已提交等同于查询成功。

完整报告须将查询数据行保存为带表头的 CSV，并保留执行 SQL：

```text
<output_dir>/uplift_20bin_sep_snapshot.csv
<output_dir>/uplift_100bin_sep_snapshot.csv
<output_dir>/uplift_20bin_sep_snapshot.sql
<output_dir>/uplift_100bin_sep_snapshot.sql
```

不要把 Aeolus 外层 JSON 元数据直接写入 CSV。解析实际结果集，严格保留 SQL 字段名。若按 treatment 拆分查询，先校验列结构一致，再按 treatment、bucket 排序合并成上述单个 CSV。

### 3. 检查分桶结果

- 20 桶结果正常为 `5 * 20 = 100` 行，每个 `treatment, bucket_20` 唯一。
- 100 桶结果正常为 `5 * 100 = 500` 行，每个 `treatment, bucket_100` 唯一。
- 每行应满足 `n = treatment_n + control_n`。每个 treatment 的 control 总量应一致，因为复用了同一批 15% 券样本；不可跨 treatment 累加为独立样本量。
- `treatment_cvr` / `control_cvr` 是当前桶的组内均值；`observed_uplift` 是两者之差，不是累计 uplift，也不是 AUUC。
- `predicted_uplift` 是当前桶 score 的均值；结合 `min_score` / `max_score` 检查排序与分数集中情况。
- 100 桶中的 `treatment_positive` / `control_positive` 是 label 总和，不一定是整数；只有二元 label 才可称为正样本数。
- 对每个 treatment，20 桶与 100 桶的 `treatment_n`、`control_n` 汇总必须分别相等。否则说明两次查询口径或快照不一致，停止生成联合报告。
- 两份结果的 bucket 必须从 1 连续到 20/100。缺桶通常意味着有效样本过少；`chart.py` 仍可能运行，但图形和指标不再是预期口径，应中止并报告。
- 单侧无样本时，`avgIf` 可能返回非有限值或空值，该桶的 observed uplift 不可解释；不要填零后当作真实观测。

## AUUC 与综合报告

### 指标定义

`chart.py` 对 100 桶结果按 treatment 独立计算 AUUC。令：

```text
nt, nc = treatment/control 的全量样本数
pt, pc = treatment/control 的全量 label 总和
ATE = pt / nt - pc / nc
x_b = 前 b 桶累计总样本数 / (nt + nc)
Q_b = 前 b 桶累计 treatment_positive / nt
      - 前 b 桶累计 control_positive / nc

raw_AUUC = trapezoid_integral(Q, x), 并包含原点 (0, 0)
random_AUUC = ATE / 2
normalized_AUUC = raw_AUUC / ATE
adjusted_AUUC = raw_AUUC - random_AUUC
```

这里的 `Q_b` 使用全量组样本数作分母，不是桶内 CVR 差，也不是旧版 20 桶累计 rate gain。`normalized_AUUC` 的随机基线为 0.5。报告时必须同时给出 `raw_AUUC`、`random_AUUC`、`adjusted_AUUC`、`ATE` 和两组样本量，避免只报归一化值。

约束：

- `nt`、`nc` 必须大于 0，`ATE` 必须非零且不能接近 0；否则 `normalized_AUUC` 不可解释或数值不稳定，报告原始曲线并标记不可归一化。
- `ATE < 0` 时，归一化后的方向会发生反转，不能仅按 `normalized_AUUC` 越大越好排名。
- 横轴使用实际累计样本占比 `x_b`，不是固定 `bucket/100`。不要替换成等距积分。
- 不能对 20 桶的 `observed_uplift` 直接平均来计算 AUUC，也不能默认对 5 个 treatment 的 AUUC再取平均。

### 运行 `chart.py`

不要直接运行参考脚本。先复制为任务工作脚本，并至少参数化以下硬编码：

| `chart.py` 项 | 必须修改 |
|---|---|
| `BASE` | 指向本次查询的 `<output_dir>` |
| `treatments`、`colors` | 与 SQL treatment 列表一致 |
| 图标题、副标题、页脚 | 模型名、control、日期、label、快照与筛选口径 |
| 输出 CSV/SQL/PNG 文件名 | 移除不适用于当前任务的 `SIPW`、`9月` 等固定名称 |

参考脚本的 balance 面板将 control 画在下方、treatment 堆在上方，却在 `overall * 100` 处绘制 treatment share 参考线。任务副本中必须二选一修正：

- 将 treatment 画在下方并保留 `overall * 100` 参考线；或
- 保持 control 在下方，将分界线改为 `(1 - overall) * 100`，并将图例说明为总体组间分界。

脚本输入字段契约：

- 100 桶 CSV：`treatment,bucket_100,n,treatment_n,control_n,treatment_positive,control_positive,avg_score,min_score,max_score`
- 20 桶 CSV：`treatment,bucket_20,n,treatment_n,control_n,treatment_cvr,control_cvr,observed_uplift,predicted_uplift,min_score,max_score`

脚本依赖 `numpy`、`matplotlib` 和 `Pillow`，运行前先做语法和依赖检查。然后在包含目标 `output_dir` 的工作目录运行：

```bash
python -m py_compile /tmp/qcpx_auuc_chart.py
python /tmp/qcpx_auuc_chart.py
```

参考脚本生成：

- 核心指标汇总 CSV。
- 均匀度与值准诊断 CSV。
- 100 桶 AUUC 明细、20 桶诊断明细和两份 SQL 快照。
- 综合诊断 PNG：第一行 AUUC 曲线，第二行 20 桶 observed/predicted uplift，第三行 treatment/control 样本占比。

执行后检查脚本退出码、所有文件是否存在且非空，并读取终端打印的 `CORE` / `DIAG`。使用图片查看工具检查 PNG 尺寸、文字、图例、曲线与柱图是否完整；仅生成文件不代表图表正确。

### 诊断指标解释

- `20桶占比CV`：20 个桶内 treatment share 的标准差除以均值；越低通常表示组间混合越均匀。
- `最大占比偏差_pp`：桶内 treatment share 相对全量 treatment share 的最大绝对百分点偏差。
- `值准_MAE` / `值准偏差_预测减实际`：按桶样本量加权的预测与观测 uplift 误差。
- `Pearson_r` / `Spearman_rho`：20 桶预测与观测 uplift 的线性/排序相关性；常量、缺失或非有限输入时可能为 NaN。
- `同号率`：20 桶预测与观测 uplift 符号一致比例。

参考脚本的 `ranks()` 不对并列值取平均秩。若 observed 或 predicted uplift 存在重复值，应改用支持并列秩的 Spearman 实现并在报告中注明，否则 `Spearman_rho` 可能依赖原始桶顺序。

这些指标是描述性诊断，不自动提供置信区间或显著性。样本分配不均、label 成熟度不足或选择偏差存在时，不应直接作因果结论。

## 超时与报错

- `Timeout exceeded ... maximum: 180`：优先将 20 桶和 100 桶 SQL 各自按 treatment 拆为 5 个等价查询。分别将 `arrayJoin([20,25,30,35,40])` 改成 `arrayJoin([20])`、`arrayJoin([25])` 等，其余配对、score、排序和分桶逻辑保持一致，可低并发执行。
- 不按日期拆分后平均各日 AUUC，这不等价于全窗口排序。缩短窗口会改变评估范围，必须同步所有模型并披露。
- 无数据或缺 treatment：依次检查每个 job 的数据源、模型名、双时间窗口、旧快照截止时间、样本过滤和 label/sample_rate head。
- `Cannot resolve column ...`：核对目标表结构、head 映射和 `extra_int` 字段，不直接换成另一个模板的 head。
- `access denied` / `permission`：检查身份、集群及 region 权限，按 CLI skill 的认证流程处理，不绕过权限控制。
- label 均值全为 0：先检查标签语义、成熟度及落库情况，不直接判定模型 uplift 为零。
- `KeyError` / CSV 字段错误：检查是否误把 Aeolus 外层 JSON 保存为 CSV，或混用了两份 SQL 的输出。
- `ZeroDivisionError` / `normalized_AUUC` 为 NaN/Inf：检查 treatment/control 样本量及 `ATE`，不得用任意 epsilon 或填零掩盖。
- 图标题或文件名仍显示参考模型、`SIPW`、`9月`：说明任务脚本未完成参数化，修正后重新生成全部产物。

## 结果交付

报告模型/job、集群与表、请求及落库窗口、快照截止时间、head 映射和样本过滤条件。按 treatment 分别给出两组样本量、总体 CVR uplift、`normalized/raw/random/adjusted AUUC`、值准和均匀度诊断，并附综合图与明细文件。

模型比较必须使用相同业务样本口径、时间边界、control/treatment 定义、分桶规则及 AUUC 归一化方式，并列出各模型样本量差异。只获得 20 桶结果时明确说明尚未计算 AUUC；只获得 100 桶结果时明确说明尚未完成值准/均匀度诊断。不要把预测分数、单桶 uplift 或图片中的某条曲线直接当作完整结论。
