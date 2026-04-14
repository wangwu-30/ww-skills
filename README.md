# ww-skills

A collection of Claude Code skills for codebase analysis, architecture visualization, and developer tooling.

## Skills

### [codemap](./codemap/skill.md)

Deep codebase analysis → single-page interactive architecture explorer.

**What it does:**
- Evidence-driven analysis: collects verifiable facts via an uncertainty-reduction loop (wide search → hypotheses → targeted verification → converge)
- Never invents `file:line` references or architecture narratives
- Outputs a single self-contained HTML file with:
  - Drill-down architecture graph (click nodes to zoom into subsystems)
  - Execution timeline with animated data flow (step-by-step playback)
  - Bilingual (中/EN) toggle
  - Confidence markers: `verified` vs `candidate` vs `inferred`

**Core design (道/法/术):**
- **道**: Uncertainty-reduction loop — stop when confidence ≥ threshold, not when "done collecting"
- **法**: Hypothesis → verification → revision cycle (same as DeepResearch)
- **术**: Glob/Grep/Read/ast-grep/LSP — cheapest tool that answers the current question

**Use when:** "visualize this codebase", "architecture doc", "codemap", "analyze this project"

---

## Usage

These skills are designed for [Claude Code](https://claude.ai/code). Place the skill directory in your Claude skills folder:

```bash
# Global install
cp -r codemap ~/.claude/skills/

# Or reference directly in your project's CLAUDE.md
```

Then invoke with `/codemap` in Claude Code.
