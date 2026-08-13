# ww-skills

Reusable Codex and Claude Code skills for codebase analysis, rigorous design reasoning, requirement delivery, and decision-partner communication.

## Skills

### [repo-alive](./skills/repo-alive/SKILL.md)

Guides an agent to **understand any codebase by compression** — compress the repo into layered, reusable, drill-downable knowledge, then answer questions from it. A crutch for models that don't yet compress on their own: it teaches *why* compress, *where* to compress from, *what* to compress into. The concrete means (the "术") can be swapped as models improve, even discarded entirely.

**Modes:**
```
/repo-alive              — analyze (if needed), then chat
/repo-alive analyze      — force re-analysis, then chat
```

**What it does:**
- Compress from the business goal outward: name what the service does → expand the main line → drill into details layer by layer (by business depth, not directory depth)
- Separate infra (frameworks/utils) from the business main line, or the trunk gets buried
- Determinism over guessing: structural facts (dirs, file ownership, imports) come from `ls`/`grep`/build system; the LLM only fills in semantics
- Persist a knowledge base to `.repo-alive/` — reused across sessions until git HEAD changes; leaves are always on-demand (never pre-flattened to avoid "summary of a summary")
- Chat grounded in real files: every fact cites a fully-qualified name, never a line number

**Core design:**
- Primary key = fully-qualified name (stable, greppable), **never line numbers** — eliminates the whole class of line-number hallucination rather than auditing it after the fact
- Layered summaries + progressive disclosure (read the top, drill down where needed)
- Wiki-style uniqueness: each entity defined in one place, referenced from many; it's a DAG, not a strict tree
- Every extracted cross-file relation carries a confidence; low-confidence flagged "待验证"
- Fixed contract is minimal: only `.repo-alive/fingerprint.json`'s `git_head` field is locked; all other manifest paths/schemas are demo, freely replaceable

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

一套路由 Skill 加六个阶段 Skill，用于把非平凡需求从理解推进到验收，同时把机械状态留在 SQLite，把人类可读材料保存在独立 Git 历史中。

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
- Python 3 is required only for the requirement workflow router's SQLite state helper and tests

## Install

This repo follows the [`vercel-labs/skills`](https://github.com/vercel-labs/skills) convention (`skills/<name>/SKILL.md`), so you can install it with the `skills` CLI — it auto-discovers the available skills and installs them into the right folder for your agent.

### Via skills CLI (recommended)

Install all skills globally for Claude Code (one command, no prompts):

```bash
npx skills add wangwu-30/ww-skills -g -a claude-code -y
```

Then invoke an installed skill by name. The requirement workflow router is intentionally explicit-only during its pilot period.

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
  && cp -r /tmp/ww-skills/skills/requirement-workflow-router ~/.codex/skills/requirement-workflow-router
```

For Claude Code, replace `~/.codex/skills` with `~/.claude/skills`. To update, run `git -C /tmp/ww-skills pull` and copy the selected skill again.

## License

MIT
