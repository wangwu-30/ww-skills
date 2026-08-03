# ww-skills

Claude Code skills for codebase analysis, developer tooling, and rigorous design reasoning.

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

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- macOS or Linux
- No runtime dependencies — `repo-alive` is a pure-text skill (uses only `ls`/`grep`/`git` and Claude's own tools)

## Install

This repo follows the [`vercel-labs/skills`](https://github.com/vercel-labs/skills) convention (`skills/<name>/SKILL.md`), so you can install it with the `skills` CLI — it auto-discovers both skills and installs them into the right folder for your agent.

### Via skills CLI (recommended)

Install both skills globally for Claude Code (one command, no prompts):

```bash
npx skills add wangwu-30/ww-skills -g -a claude-code -y
```

Then invoke inside Claude Code with `/repo-alive` or `/force-thinker`.

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
  && cp -r /tmp/ww-skills/skills/repo-alive ~/.claude/skills/repo-alive \
  && cp -r /tmp/ww-skills/skills/force-thinker ~/.claude/skills/force-thinker
```

To update: `git -C /tmp/ww-skills pull` then re-run the `cp -r` lines.

## License

MIT
