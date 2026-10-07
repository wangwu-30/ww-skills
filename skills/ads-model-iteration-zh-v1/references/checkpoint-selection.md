# Checkpoint 查询与切换

用于 planner 在**用户未显式指定 `spec.checkpoint_id`**（即 `checkpoint_hint_json = null`）时，自主决定是否基于某个 baseline 的 checkpoint 做 warm-start，以及如何把选中的 ckpt 落到本轮 trial。

---

## 何时应该考虑基于 baseline ckpt

- 直接替换主干、批量改名或改 shape 已有变量时，通常需要重新评估 checkpoint 兼容性
- 只增加独立模块/旁路且保留已有变量名和 shape 时，若当前框架支持部分恢复，可以加载匹配变量并初始化新增变量
- 训练的数据流里发现历史的数据不够多，期望在最新的 ckpt 上进行 warm-start 来加速收敛，则需要考虑基于最新 ckpt
- 此前使用了很久之前的 ckpt，样本分布已改变，可能需要查询并基于基线的新的 ckpt的参数。

---

## 第一步：查询 baseline Job 的 ckpt

**唯一命令**（`baseline_job_id` 和 `site` 都是 planner 的输入变量）：

```bash
forge job checkpoint list --job-id <baseline_job_id> --site <site>
```

返回 JSON 里 `checkpoints[]`，每条字段含义：

| 字段 | 含义 | 选 ckpt 时看什么 |
|---|---|---|
| `checkpoint_id` | 唯一 id | 用于后续 `checkpoint save` / plan 引用 |
| `checkpoint_time` | ckpt 落盘时间 | 越新越贴近当前基线 |
| `training_instance_time` | 对应训练数据水位 | streaming 任务优先看这个（决定“追到哪一天”） |
| `hdfs_path` | 权重实际落地路径 | plan_text 里要显式带上 |
| `size_mb` | ckpt 大小 | 空 / 异常小 → 该 ckpt 未完整落盘，跳过 |
| `status` | `normal` / `keep` / `deleting` … | 只允许 `normal` 或 `keep`；其它状态一律不用 |
| `remark` | 备注（人为标记 / 自动保留标签） | 有 “kept by retention” 类标签的更可靠 |

分页参数：默认 `--page 1 --page-size 100`；如果 100 条内没找到合适的，再翻页。

**选 ckpt 的默认策略**（planner 无特殊理由时按此顺序）：

1. 过滤 `status in {"normal", "keep"}` 且 `size_mb` 明显非零的正常 ckpt
2. 选一个时间较近的 ckpt，同时注意要修改 norbert 的实验调度配置，因为加载了 ckpt后，ckpt之前的数据已经训练了一次，norbert 的起始数据范围需要更改到 ckpt 后。

---

## 第二步：将 checkpoint“切换”到本轮 trial

⚠️ **限制**：`spec.checkpoint_id` 仅在 bootstrap 阶段读取一次，用于生成 `checkpoint_hint_json`；planner 中途**无法**改 spec 让下游自动 warm-start。所以“切换”意味着 planner 必须把选中的 ckpt 写进 `plan_text`，由 forge_agent 落成 workspace 里的代码 / 配置改动。

产出格式（写到 `plan_text` 里，让 forge_agent 消费）：

```
warm_start:
  source_job_id: <baseline_job_id>
  checkpoint_id: <choose from Step 1>
  checkpoint_time: <ISO time>
  hdfs_path: <hdfs://...>
  rationale: <一句话：为什么选这个 ckpt / 为什么本轮改动允许 warm-start>
```

forge_agent 应做的事（planner 在 plan_text 里明确指出）：

1. **在 workspace 里定位 warm-start 配置**：常见位置
   - `models/*.py` 里的 `warm_start_from` / `ckpt_path` / `restore_hdfs` / `pretrained_ckpt` 等常量或 config 字段；
   - `norbert/*.py` 或 `norbert/*.yaml` 里的 `restore_path` / `warm_start_ckpt`；
   - baseline 若走 dandelion / jaguar，看框架的 warmup config 段。
   若一次 `grep -rn "warm_start\|ckpt_path\|restore\|hdfs://" models/ norbert/` 找不到锚点，就在 plan_text 里说明**当前 baseline 未暴露 warm-start 接口**，本轮改回从 0 训，避免瞎猜。
2. **只替换 hdfs_path / checkpoint_id 字段**，保留原有开关（例如 `enable_warm_start`）为 True。
3. **保护 ckpt 不被回收**（可选）：如果本轮迭代要长期依赖这个 ckpt，先跑
   ```bash
   forge job checkpoint save --job-id <baseline_job_id> --checkpoint-id <checkpoint_id> --site <site>
   ```
   把该 ckpt 标记为保留，避免中途被 retention 清理。
   如果 checkpoint 当前为 `normal`，但 `save` 因执行人不是 job/version owner
   或不在管理员列表而被拒绝，记录 retention 风险并继续；不得把这个权限错误升级为
   trial fatal。只有 checkpoint 不存在、进入删除状态或 `hdfs_path` 已失效才停止。

---

## 第三步：兜底与风险

你需要预估风险，并进行测试，保证你的plan是可行的。

- **shape mismatch**：新增模块是否允许“checkpoint 中没有新变量”并初始化，取决于当前框架恢复语义；任何已有变量的 shape mismatch / rename 都说明兼容性被破坏。后续训练方式按任务输入与框架规则决定，不能静默 clear/drop 后继续。
- **staleness**：warm-start 后的前几个 step loss / AUC 可能剧烈波动，warmup 窗口应 >= 30min 再看指标；结合 `job_sma.md` 里的 `--warmup-min 60` 通用护栏。
- **可比性**：warm-start 的 trial 与从 0 训的 baseline 直接比 AUC 会显失公平；planner 在 `rationale` 里要标明**对比对象**（是 baseline 同 ckpt 起点，还是 baseline 完整训练）。
- **status 变化**：ckpt 可能在 trial 运行期间被 baseline 侧 retention 删除。开跑前若担心，先 `checkpoint save`；开跑后若日志出现 `hdfs path not found`，重新查一次 list 并选新 ckpt。

---

## 快速回顾（Planner 可直接照着做）

1. `checkpoint_hint_json != null` → 用户已指定，直接用，无需再查。
2. `checkpoint_hint_json == null` 且本轮改动**兼容** warm-start → 跑一次 `forge job checkpoint list`，按 Step 1 策略选一条，按 Step 2 写进 `plan_text`。
3. 修改后仍兼容 checkpoint → 按任务指定方式 warm-start，并明确新增变量初始化策略。
4. checkpoint 不兼容 → `warm_start: null`，训练数据窗口和 batch/streaming 方式由任务输入决定。
