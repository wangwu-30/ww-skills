---
name: repo-alive
description: Build, refresh, and use an evidence-grounded repository navigation map and verify that its source snapshot and declared artifacts remain consistent. Use only when explicitly invoked or selected by software-engineering-router for repository orientation, code navigation, entry-point coverage, impact discovery, or `.repo-alive` maintenance. Explicit `analyze` or “重新分析” requests rebuild the persistent map. Freshness proves only the map-to-source snapshot closure; it does not prove semantic correctness, test success, or runtime health.
metadata:
  version: "0.3.0"
---

# Repo Alive

把仓库压缩成可复用的导航层，同时始终把当前工作区当作事实源。知识库用于快速定位，不替代代码、配置、测试和仓库内权威文档。

## 选择工作模式

先根据用户意图选择一种模式：

- **查询模式**：用户问具体架构、实现、调用链、差异或维护问题。默认只读；可以使用已有 `.repo-alive/`，但必须按需核验当前文件。
- **建图模式**：用户明确要求理解/分析整个仓库、建立可复用知识、刷新缓存，或传入 `analyze`。只允许创建或更新 `.repo-alive/**`；除非用户另有授权，不改产品代码、测试、配置或 Git 历史。

若请求同时包含建图和具体问题，先建立足以回答问题的地图，再回答；不要为了“完整”展开所有叶子。

## 0. 先尊重仓库和工作区

1. 定位仓库根目录；读取适用于当前范围的 `AGENTS.md`、`CLAUDE.md`、贡献说明和架构导航。仓库规则优先于本 Skill 的默认方法。
2. 查看 Git 状态并保护用户改动。不要清理、覆盖、暂存或提交现有变更。
3. 将 `scripts/repo_state.py` 相对本 `SKILL.md` 所在目录解析为绝对路径，然后运行状态工具；不要把它误解析为目标仓库自己的 `scripts/`：

   ```bash
   python3 <repo-alive-skill-dir>/scripts/repo_state.py status --repo <repo-root>
   ```

   - `fresh`：知识产物及源快照一致，可作为导航。
   - `missing`：没有可用知识库。
   - `stale`：HEAD、暂存区、未暂存或未被 Git 忽略的未跟踪源文件已变化。只刷新受影响节点；查询模式可直接核验相关当前文件，不必先全量重建。
   - `invalid`：指纹或产物清单损坏；不得信任缓存。
   - `forced`：按用户要求重新分析；显式 `analyze` / “重新分析”时给 `status` 加 `--force`。

只比较 Git HEAD 不足以判断新鲜度。不要手写 `fingerprint.json`，不要把绝对仓库路径、时间戳或文件内容放入指纹。Git ignored 文件不参与快照；若问题依赖本地 ignored 配置，只核验其存在性、Schema 和读取路径，不展开或持久化秘密值。非 Git 目录使用文件快照：只排除知识目录自身和 VCS 元数据；即使普通目录名为 `vendor`、`build`、`dist`、`node_modules`、`.cache` 或虚拟环境目录，其中的文件仍参与 freshness 判断。状态快照的覆盖范围不同于后续语义分析范围；Agent 分析时仍可按第 1 节规则选择性跳过依赖、构建和生成产物。Git submodule 只由主仓 gitlink 表示；若问题涉及子模块，进入子模块根目录单独检查其状态。

## 1. 建立确定性仓库骨架

先收集结构，再解释语义：

1. 用 `rg --files`、构建/包清单和目录级说明识别语言、包、进程、部署单元、生成代码与测试边界。若 `rg` 不可用，再用等价工具。
2. 从真实入口反查能力：HTTP/RPC、CLI、事件/MQ、定时任务、Workflow、插件、库的公开 API、构建和运维入口。不要把目录名直接当业务域。
3. 找出配置、feature flag、依赖注入、路由注册和部署差异；区分“代码存在”“已注册”“默认启用”“实际部署”。
4. 根据仓库类型命名能力：服务仓可用业务流程/领域，库用消费者任务/公开 API，工具仓用命令/工作流，文档或 Skill 仓用能力/维护流程。DDD 只是可选视角。
5. 跳过 vendor、构建产物、大型生成文件和二进制；需要时只定位相关符号段。Agent 不展开 `.env`、私钥、credential store 或疑似秘密文件的值；从示例配置、Schema 和读取代码理解配置形状。状态工具可以为本地一致性计算不可逆摘要，但不得输出文件内容；知识产物绝不保存凭据值。

结构事实由工具取得，语义结论由代码与权威文档交叉解释。README 只能证明其声明，不能单独证明运行时接线。

## 2. 自顶向下压缩，自底向上校验

按以下层次展开：

1. 用一句话写清用户、输入、核心产出或副作用。
2. 写出主要业务/使用主线，以及与主线分离的基础设施。
3. 划分少量能力域，记录各域责任、状态权威、入口和依赖。
4. 对用户当前问题和高风险代表链路追到可观察终点，例如持久化、外部调用、事件投递、进程执行或返回值。
5. 从子域证据回到总览，修正矛盾；无法闭合的关系标为 `unknown`，不要硬推。

仓库较大且环境支持子代理时，只委派可独立验证的域或入口族。每个产物指定唯一 owner；父代理统一术语、去重并复核跨域关系。不要让多个代理同时写同一文件。

## 3. 使用可复查证据

每个影响结论的事实都附稳定锚点：

- 代码实体：优先 `package.module.Class.method`、`namespace::Class::method` 或带签名的真实全限定名，并附文件路径。
- 非代码实体：使用真实路由、命令、配置键、清单 target、表名、文档标题或测试名，并附文件路径。
- 持久知识中不把行号当主键。即时回答可把刚核验的行号作为辅助定位，但不得用陈旧行号替代符号或路径。

关系只使用三种证据状态：

- `verified`：注册、调用、配置、测试或构建证据直接闭合。
- `inferred`：由多个事实推得但缺少运行时闭环；同时写出推理和可证伪条件。
- `unknown`：证据不足或相互冲突。

不要编造看似精确的小数置信度。外部依赖中的实体明确标为外部，不伪造本仓定义。

对“无调用者、未使用、仅测试、已废弃、所有入口”这类负面或穷尽性断言，必须记录搜索范围、模式变体和排除项。未覆盖动态注册、生成代码、反射、插件或外部消费者时，只能写“在已搜索范围内未发现”。

## 4. 写入可下钻知识

建图模式必须先读 [知识契约](references/knowledge-contract.md)，再一次规划全部产物。必需文件：

- `.repo-alive/overview.md`：仓库目标、主线、能力地图、技术/进程边界、动态变体、导航和未知项。
- `.repo-alive/routes.md`：入口覆盖账本；区分“已枚举”和“已追到终点”，不得用入口列表冒充完整调用链。
- `.repo-alive/fingerprint.json`：最后由状态工具生成的源快照与产物清单。

按需增加 `domains/*.md`、`relations.md` 或其他一层深的主题文件。每个事实只在一处展开，其他位置链接引用；不要把代码叶子预先改写成“摘要的摘要”。

更新已有知识库时：

1. 以状态工具返回的 `changed_paths` 为刷新起点。
2. 搜索这些文件影响的入口、域和关系；更新所有受影响节点。
3. 删除或明确标记已失效知识，避免用 `working-tree.md` 之类无限叠加补丁掩盖主文档陈旧。
4. 保留与当前变化无关且仍有证据的人工整理内容。

## 5. 回答仓库问题

1. 先读 `overview.md` 和 `routes.md`，再只加载相关域。
2. 即使状态为 `fresh`，对用户问题的关键事实也按当前文件核验；对改代码任务，缓存永远只是导航。
3. 状态为 `stale` 时，说明相关缓存可能过期，并以当前变化和真实文件为准。不要为了一个局部问题强制全量刷新。
4. 先给结论或调用链，再给最少必要解释和锚点；明确区分当前实现、兼容路径、规划/休眠代码与未知项。
5. 用户追问时沿已有节点继续下钻，不重复加载整个仓库。

## 6. 完成 Gate

查询模式只在以下条件同时满足时结束：已回答用户问题；关键事实已从当前工作区核验；证据与未知项清楚；没有把缓存状态冒充业务正确性。

建图模式在写完后逐项检查 [知识契约](references/knowledge-contract.md)，然后运行：

```bash
python3 <repo-alive-skill-dir>/scripts/repo_state.py stamp --repo <repo-root>
python3 <repo-alive-skill-dir>/scripts/repo_state.py verify --repo <repo-root>
```

只有 `verify` 成功后才能称知识库“当前且完整可读”。这只证明源快照和产物闭环，不证明每个语义结论正确；语义仍由锚点和覆盖账本负责。

最终告知用户：结论、创建/更新的知识节点、覆盖到什么程度、仍未知什么、当前状态是否通过验证，以及 `.repo-alive/` 当前是 tracked、ignored 还是 untracked。不要自行修改 `.gitignore` 或提交产物。不要声称“完整理解整个仓库”，除非覆盖账本真的证明了用户所指范围。
