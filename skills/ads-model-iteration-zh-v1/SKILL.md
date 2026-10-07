---
name: ads-model-iteration
description: 解释并组织广告模型迭代知识。适用于广告模型阶段（召回、粗排、精排、混排）、特征与数据流、延迟反馈、冷启动、校准、模型稳定性、在线服务架构、实验参数，以及常见优化方法与取舍相关任务。
---

# 广告模型迭代

## 概览

当用户询问广告模型的工作方式、如何迭代，或如何分析召回、粗排、精排、混排中的训练、服务与优化取舍时，使用本技能。

本技能独立成包，可复制到其他 Agent 工作区使用，不依赖仓库内的知识库页面。

本技能包含完整知识集，但应按需逐步读取。默认不要一次读取全部参考文件。

## 路由规则

先将用户问题归入以下一个或多个类别，再只读取对应的参考文件。

### 1. 阶段理解

用户询问以下内容时使用：

- `recall`、`rough rank`、`final rank` 或 `mix rank` 的作用；
- 某个阶段负责什么；
- 各阶段有什么区别。

读取：

- [references/stages.md](./references/stages.md)

### 2. 训练流水线与在线架构

用户询问以下内容时使用：

- 训练数据如何构建；
- `slot / FID / instance` 的含义；
- 特征如何组织；
- `Marine / Viking / Pilot / online PS` 的作用；
- `fast emit` 解决什么问题。

读取：

- [references/pipeline-and-serving.md](./references/pipeline-and-serving.md)

### 3. 目标与方法选择

用户询问以下内容时使用：

- 应优化什么目标；
- 是否应使用 `CTR / CVR / PVR / ecpm / LTV`；
- 是否应使用 `LTR`、`RECPM`、`multi-task`、`Feature Mask`、`Meta Learning`、聚类、不确定性建模。

读取：

- [references/objectives-and-methods.md](./references/objectives-and-methods.md)

### 4. 特殊建模问题

用户询问延迟反馈、冷启动、预测偏差、校准、稳定性或效率时使用。

读取：

- [references/special-topics.md](./references/special-topics.md)

### 5. 调参、参数含义与验证

用户询问以下内容时使用：

- “怎么调参”；
- “为什么效果差”；
- “下一步该试什么”；
- JSON 或配置片段的含义；
- 如何解读实验。

读取：

- [references/tuning-and-validation.md](./references/tuning-and-validation.md)

### 6. Warm-start / checkpoint 选择

符合以下情况时使用：

- 用户未在 spec 中指定 `checkpoint_id`（即 Planner 收到 `checkpoint_hint_json = null`），需要自主判断是否使用 baseline 的 ckpt；
- 需要了解如何查询 baseline Job 的 checkpoint 列表、字段含义和默认选择策略；
- 需要了解如何将选中的 ckpt 切换到本轮 trial（修改工作区中的哪些配置，是否要运行 `checkpoint save` 以防回收）；
- 需要判断本轮改动是否兼容 warm-start（例如结构改动、embedding 维度或 fid 分片发生变化时不兼容）。

读取：

- [references/checkpoint-selection.md](./references/checkpoint-selection.md)

### 7. 范围广或混合问题

如果问题横跨多个类别，先读取：

- [references/overview.md](./references/overview.md)

然后只加载准确回答问题所需的最少附加文件。

## 核心回答规则

### 先明确阶段

始终说明问题涉及哪个阶段：

- `recall`
- `rough rank`
- `final rank`
- `mix rank`

涉及多个阶段时，明确分开说明。

### 再明确目标

讨论架构或参数前，先识别真正的目标：

- `CTR`
- `CVR`
- `PVR`
- 深度转化
- `ecpm / sorted ecpm`
- `LTV`
- 与 `GMV` 相关的价值
- 序列级混排价值

如果用户只说“效果差”，根据阶段推断最可能的目标，并明确说明这是一个假设。

### 按稳定顺序诊断

优先按以下顺序分析：

1. 目标定义；
2. 样本构造；
3. 特征假设及训练、服务一致性；
4. 模型结构；
5. 服务、稳定性和实验风险。

### 用业务语言解释参数

用户提供配置片段时：

1. 将每个参数对应到它影响的阶段；
2. 区分 `switch`、`weight/beta`、`threshold` 和 `tag/routing` 参数；
3. 解释可能的影响方向；
4. 说明主要风险；
5. 建议最小验证计划。

仅凭一个配置片段，不要声称已知精确线上影响；除非有代码或实验依据。

## 建议的输出模板

回答调参或参数问题时，优先按以下结构组织：

1. 阶段
2. 目标
3. 参数或瓶颈
4. 建议的调参方向
5. 预期效果
6. 主要风险
7. 验证方法

除非用户明确要求详细说明，否则保持简洁。

## 不应采取的做法

- 未检查样本和特征假设前，不建议先改架构；
- 不把离线 AUC 提升当作充分证据；
- 除非用户明确要求跨阶段诊断，否则不把多个阶段混在一段解释中；
- 不假设所有排序问题都是校准问题，反之亦然。
