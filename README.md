# ww-skills

A collection of Claude Code skills for codebase analysis and developer tooling.

## Skills

### [repo-alive](./repo-alive/skill.md)

Makes any codebase self-explanatory. Runs an uncertainty-reduction analysis loop, then enters a persistent TUI conversation grounded in real source files.

**What it does:**
- Evidence-driven analysis: wide search → hypotheses → targeted verification → converge
- Never invents `file:line` references or architecture narratives
- Persists manifests to `.repo-alive/` for fast reuse across sessions
- Default: TUI chat grounded in manifests and source files
- `--html` (experimental): interactive HTML canvas with drill-down graph and scenario playback

**Core design (道/法/术):**
- **道**: Uncertainty-reduction loop — stop when confidence ≥ threshold, not when "done collecting"
- **法**: Hypothesis → verification → revision cycle (same as DeepResearch)
- **术**: Glob/Grep/Read — cheapest tool that answers the current question

**Usage:**
```
/repo-alive              — analyze (if needed) then chat in TUI
/repo-alive analyze      — force re-analysis, then chat
/repo-alive --html       — [EXPERIMENTAL] analyze then serve interactive HTML canvas
```

**Use when:** "chat with this codebase", "explain this repo", "understand this project", "explore this codebase"

---

## Usage

These skills are designed for [Claude Code](https://claude.ai/code). Place the skill directory in your Claude skills folder:

```bash
cp -r repo-alive ~/.claude/skills/
```

Then invoke with `/repo-alive` in Claude Code.
