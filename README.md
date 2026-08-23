# ww-skills

Eleven reusable Codex and Claude Code skills for agent-assisted software engineering: one stateless suite router, three focused leaf skills, and a seven-skill requirement workflow pilot.

## Skills

### [software-engineering-router](./skills/software-engineering-router/SKILL.md)

The stateless front door for ordinary software-engineering work. It frames the request, inspects the repository just enough to choose a route, then composes focused leaf skills or delegates an explicitly admitted lifecycle request to `requirement-workflow-router`. It does not persist a route, session, queue, approval, or requirement state.

This is the suite's **only implicitly invocable Skill**. Every leaf Skill and every requirement-workflow Skill is explicit-only, so installing the full repository does not inject eleven competing behaviors into an agent turn. You can still invoke any leaf directly with `$skill-name`.

### [repo-alive](./skills/repo-alive/SKILL.md)

Builds a compact, evidence-grounded navigation map and verifies its source snapshot and artifact manifest. The map accelerates future work; it never replaces the repository as the source of truth. A `fresh` result proves only snapshot consistency—not semantic correctness, passing tests, or runtime health.

**Modes:**
```
/repo-alive              — analyze (if needed), then chat
/repo-alive analyze      — force re-analysis, then chat
```

**What it does:**
- Select query mode (read-only, verify current facts) or map mode (write only `.repo-alive/**`) from the user's intent
- Compress from the repository's purpose into main flows and capability domains, while separating infrastructure and runtime variants
- Discover structure and entry points deterministically; use model reasoning for semantics, not file discovery
- Persist `overview.md`, an auditable `routes.md` coverage ledger, and optional domain nodes while leaving code-level leaves on demand
- Ground claims with stable symbols, routes, config keys, targets, tests, and repository-relative paths; distinguish `verified`, `inferred`, and `unknown`
- Detect committed, staged, unstaged, unignored-untracked, and non-Git source changes with a dependency-free state tool

**Core design:**
- Stable, greppable anchors are persistent keys; line numbers may be temporary navigation aids, not durable evidence
- Layered summaries + progressive disclosure: read the top, then load only the relevant domain and current source
- Wiki-style uniqueness: define a fact once and link to it from other nodes
- `routes.md` separates entry-point enumeration from end-to-end tracing, so shallow coverage cannot masquerade as complete understanding
- `scripts/repo_state.py` stamps a content-sensitive source snapshot and artifact hashes; legacy HEAD-only fingerprints fail closed and must be restamped

**Use when:** "理解这个仓库" / "chat with this codebase" / "讲讲这个项目" / "explain this repo", "understand this project"

---

### [force-thinker](./skills/force-thinker/SKILL.md)

Rigorous design reasoning kernel. Forces typed inputs (FACT/GOAL/HARD_CONSTRAINT/ASSUMPTION), derives obligations and forbidden states, generates candidate plans as witnesses, then commits or refuses selection cleanly. Works on any design problem.

**State machine:** `UNDER-CONSTRAINED` → `NEED-EVIDENCE` → `MULTIPLE-VALID-PLANS` → `READY-TO-COMMIT`

**Usage:**
```
/force-thinker              — interactive elicitation mode
/force-thinker <problem>    — start with a seed description
```

**Use when:** "help me think through this", "is this design sound", "what are the tradeoffs", "I need to make a decision about X"

---

### [decision-partner-communication](./skills/decision-partner-communication/SKILL.md)

结论先行的中文沟通能力。要求模型以决策伙伴而不是服务角色参与讨论：主动给出专业判断，只向用户询问无法从项目或公开资料中获得的私有事实，并用扎实证据解释反常识结论。

**适用场景：** 非平凡说明、方案讨论、状态汇报、架构决策、路线图对齐、评审结论和交接。

---

### Requirement workflow suite

一套显式调用的试点路由 Skill 加六个阶段 Skill，用于把获准进入该流程的非平凡需求从理解推进到验收，同时把机械状态留在 SQLite，把人类可读材料保存在独立 Git 历史中。`software-engineering-router` 只做无状态分流；它不会复制、写入或绕过这套流程的状态、授权和材料。未进入该流程的普通研发请求仍按无状态路径处理。

| Skill | 责任 |
|---|---|
| [requirement-workflow-router](./skills/requirement-workflow-router/SKILL.md) | 单一入口、短路径判断、最多三个并行需求、阶段与授权门禁 |
| [requirement-frame](./skills/requirement-frame/SKILL.md) | 明确目标、成功标准、范围、约束、事实来源和调研方式 |
| [requirement-research](./skills/requirement-research/SKILL.md) | 按决策风险选择项目核验、公开研究、有限实验或深度研究 |
| [requirement-align](./skills/requirement-align/SKILL.md) | 形成结论先行的提案，进行对抗性审查并完成方案对齐 |
| [requirement-plan](./skills/requirement-plan/SKILL.md) | 把已确认方案转成可授权、可回退、可验收的路线图 |
| [requirement-execute](./skills/requirement-execute/SKILL.md) | 按已批准路线图自主执行，并正确处理现实偏差 |
| [requirement-close](./skills/requirement-close/SKILL.md) | 按用户可观察结果和独立证据验收并关闭需求 |

路由 Skill 自带 `workflow_state.py` 和单元测试。首次试点默认只允许一个活跃需求；稳定后可配置为最多三个。

---

## Prerequisites

- Codex or [Claude Code](https://claude.ai/code) CLI installed
- macOS or Linux
- Python 3.11+ for `repo-alive` state verification and the requirement workflow router's SQLite state helper

## Install

This repo follows the [`vercel-labs/skills`](https://github.com/vercel-labs/skills) convention (`skills/<name>/SKILL.md`), so you can install it with the `skills` CLI — it auto-discovers the available skills and installs them into the right folder for your agent.

### Via skills CLI (recommended)

Install all skills globally for Claude Code (one command, no prompts):

```bash
npx skills add wangwu-30/ww-skills -g -a claude-code -y
```

The command installs all eleven Skills. After installation, only `software-engineering-router` may be invoked implicitly; all ten other Skills are explicit-only. Invoke a leaf directly with `$skill-name` when you already know the capability you want. The requirement workflow router remains intentionally explicit-only during its pilot period and is entered only after explicit workflow admission.

**Common variants:**

```bash
# List available skills without installing
npx skills add wangwu-30/ww-skills --list

# Install only one skill
npx skills add wangwu-30/ww-skills --skill repo-alive -g -a claude-code -y

# Install at project level (committed with your repo, shared with the team)
npx skills add wangwu-30/ww-skills -a claude-code -y

# Install for Codex as well
npx skills add wangwu-30/ww-skills -g -a claude-code -a codex -y
```

To update later, re-run the install command (the CLI updates in place), or:

```bash
npx skills update
```

### Via git clone (manual)

```bash
git clone https://github.com/wangwu-30/ww-skills /tmp/ww-skills \
  && cp -r /tmp/ww-skills/skills/repo-alive ~/.codex/skills/repo-alive
```

For Claude Code, replace `~/.codex/skills` with `~/.claude/skills`. Copy the whole `skills/` directory if you want the routed suite, or copy one leaf directory for explicit-only use. To update, run `git -C /tmp/ww-skills pull` and copy the selected directories again.

## License

[MIT](./LICENSE)
