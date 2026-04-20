# ww-skills

Claude Code skills for codebase analysis and developer tooling.

## Prerequisites

- [Claude Code](https://claude.ai/code) CLI installed
- macOS or Linux
- `node >= 18` + `npm` — only required for `/repo-alive --html` (experimental). The default TUI mode has no runtime deps.

## Install

One command — copies the skill into your Claude skills folder:

```bash
git clone https://github.com/wangwu-30/ww-skills /tmp/ww-skills && cp -r /tmp/ww-skills/repo-alive ~/.claude/skills/repo-alive
```

Then invoke with `/repo-alive` inside Claude Code.

To update later:

```bash
git -C /tmp/ww-skills pull && cp -r /tmp/ww-skills/repo-alive ~/.claude/skills/repo-alive
```

---

## Skills

### [repo-alive](./repo-alive/skill.md)

Makes any codebase self-explanatory. Runs an uncertainty-reduction analysis loop to build node manifests, then enters a persistent TUI conversation grounded in real source files.

**Modes:**
```
/repo-alive              — analyze (if stale), then chat in TUI
/repo-alive analyze      — force re-analysis, then chat
/repo-alive --html       — [EXPERIMENTAL] analyze, then serve interactive canvas at localhost:4311
```

**What it does:**
- Evidence-driven analysis: wide search → hypotheses → targeted verification → converge
- Never invents `file:line` references or architecture narratives
- Persists manifests to `.repo-alive/` — reused across sessions until git HEAD changes
- TUI chat: answer questions grounded in manifests + source files, cite `file:line`
- HTML mode (experimental): interactive graph, scenario playback, in-browser Q&A

**Core design:**
- Uncertainty-reduction loop — stop when confidence ≥ 0.8, not when "done collecting"
- Hypothesis → verification → revision cycle
- Cheapest tool first: `rg --files` → `rg -n` → `Read`

**Use when:** "chat with this codebase", "explain this repo", "understand this project", "explore this codebase"

---

<!-- AGENT-MANIFEST
{
  "repo": "https://github.com/wangwu-30/ww-skills",
  "skills": [
    {
      "name": "repo-alive",
      "version": "0.0.2",
      "invoke": "/repo-alive",
      "skill_file": "repo-alive/skill.md",
      "install_dir": "~/.claude/skills/repo-alive",
      "install_cmd": "git clone https://github.com/wangwu-30/ww-skills /tmp/ww-skills && cp -r /tmp/ww-skills/repo-alive ~/.claude/skills/repo-alive",
      "runtime": "Claude Code",
      "prerequisites": {
        "required": ["Claude Code CLI"],
        "optional_html_mode": ["node >= 18", "npm"]
      },
      "files": [
        "repo-alive/skill.md",
        "repo-alive/server.js",
        "repo-alive/canvas.html",
        "repo-alive/client.js",
        "repo-alive/package.json"
      ],
      "outputs": [
        ".repo-alive/fingerprint.json",
        ".repo-alive/graph.json",
        ".repo-alive/nodes/<id>.json",
        ".repo-alive/scenarios/<id>.json",
        ".repo-alive/ownership.json",
        ".repo-alive/reverse-index.json"
      ],
      "modes": [
        { "flag": "",         "description": "analyze if stale, then TUI chat" },
        { "flag": "analyze",  "description": "force re-analysis, then TUI chat" },
        { "flag": "--html",   "description": "[EXPERIMENTAL] analyze then serve HTML canvas on localhost:4311" }
      ],
      "notes": "node_modules/ is gitignored. npm install runs automatically in --html mode."
    }
  ]
}
-->
