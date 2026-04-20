# ww-skills

A collection of Claude Code skills for codebase analysis and developer tooling.

## Install

```bash
git clone https://github.com/wangwu-30/ww-skills ~/.claude/skills/ww-skills && cp -r ~/.claude/skills/ww-skills/repo-alive ~/.claude/skills/repo-alive
```

---

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

<!-- AGENT-MANIFEST
This section is machine-readable. Do not edit manually.
{
  "repo": "https://github.com/wangwu-30/ww-skills",
  "skills": [
    {
      "name": "repo-alive",
      "version": "0.0.2",
      "invoke": "/repo-alive",
      "skill_file": "repo-alive/skill.md",
      "install_dir": "~/.claude/skills/repo-alive",
      "install_cmd": "cp -r repo-alive ~/.claude/skills/repo-alive",
      "runtime": "Claude Code",
      "deps": {
        "required": [],
        "optional_html_mode": ["node >= 18", "npm"]
      },
      "files": [
        "repo-alive/skill.md",
        "repo-alive/server.js",
        "repo-alive/cc-bridge.js",
        "repo-alive/canvas.html",
        "repo-alive/client.js",
        "repo-alive/package.json"
      ],
      "outputs": [
        ".repo-alive/graph.json",
        ".repo-alive/nodes/<id>.json",
        ".repo-alive/scenarios/<id>.json",
        ".repo-alive/fingerprint.json",
        ".repo-alive/ownership.json"
      ],
      "modes": [
        { "flag": "",         "description": "analyze if stale, then TUI chat" },
        { "flag": "analyze",  "description": "force re-analysis, then TUI chat" },
        { "flag": "--html",   "description": "[EXPERIMENTAL] analyze then serve HTML canvas on localhost:4311" }
      ]
    }
  ]
}
AGENT-MANIFEST -->
