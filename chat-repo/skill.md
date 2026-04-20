---
name: chat-repo
version: 2.0.0
description: |
  Chat with any codebase in Claude Code TUI. Runs the same uncertainty-reduction
  analysis as repo-alive (wide search → hypotheses → verification → manifests),
  then enters a persistent conversation where every answer is grounded in real
  source files. No HTML, no server, no browser — pure terminal chat.
  Use when asked to "chat with this codebase", "ask about the code",
  "explain this repo", "understand this project", "talk to the codebase".
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Agent
---

## Preamble

```bash
echo "CHAT-REPO v2.0.0"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
echo "REPO_ROOT: $REPO_ROOT"
GIT_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "NO_GIT")
echo "GIT_HEAD: $GIT_HEAD"
DATA_DIR="$REPO_ROOT/.repo-alive"
FINGERPRINT="$DATA_DIR/fingerprint.json"
FRESH="no"
FORCE_ANALYZE="${1:-}"  # pass "analyze" to force re-analysis
if [ "$FORCE_ANALYZE" = "analyze" ]; then
  echo "FORCE_ANALYZE: yes — will re-run analysis"
elif [ -f "$FINGERPRINT" ]; then
  STORED=$(python3 -c "import json; d=json.load(open('$FINGERPRINT')); print(d.get('git_head',''))" 2>/dev/null || echo "")
  [ "$STORED" = "$GIT_HEAD" ] && FRESH="yes"
fi
echo "MANIFESTS_FRESH: $FRESH"
```

Usage:
- `/chat-repo` — use cached manifests if fresh, else re-analyze
- `/chat-repo analyze` — force re-analysis even if manifests are fresh

---

## Phase 1 — Analysis (same as repo-alive, run if MANIFESTS_FRESH=no)

Run the full uncertainty-reduction analysis loop from `repo-alive/skill.md`:
- Phase 0: Wide search (file inventory, taint marking, entrypoints)
- Phase 1: Hypothesis generation (L0 partition candidates)
- Phase 2: Hypothesis verification loop (confidence math)
- Phase 3: L1 discovery (scoped per L0)
- Phase 4: Interface + connection extraction
- Phase 5: Three-view scenario extraction
- Phase 6: Verification pass
- Phase 7: Write manifests to `.repo-alive/`

**Read `~/.claude/skills/repo-alive/skill.md` for the full analysis algorithm.**

If `MANIFESTS_FRESH=yes`, skip to Phase 2 (Chat).

---

## Phase 2 — Chat (TUI conversation)

After analysis completes (or manifests are fresh), enter conversation mode.

### Orientation message

Print a brief intro based on the manifests:

```
Read .repo-alive/graph.json and summarize:
- Project name (from repo root dirname)
- What kind of project (CLI / web app / library / service)
- How many L0 nodes found, what they are
- One representative scenario available

Format: 4-6 lines max. End with "What would you like to know?"
```

### Answering questions

For every question:

1. **Identify which node(s) are relevant** — check `.repo-alive/graph.json` node list
2. **Load that node's manifest** — read `.repo-alive/nodes/<nodeId>.json`
3. **Read only the relevant owned files** (key_files first, then owned_files by priority)
   - Stop at 40,000 chars total
   - Skip files >32KB
4. **Answer from the source** — cite `file:line` for every claim
5. **If the answer spans multiple nodes** — load each node's manifest in turn

### Question types and how to handle them

**"How does X work?"**
- Grep for X to find which node owns it
- Load that node's manifest
- Read the key files
- Trace the call chain step by step, citing file:line

**"What's the difference between X and Y?"**
- Load both nodes' manifests
- Read their key files
- Compare side by side with evidence

**"Show me the code for X"**
- Grep to locate it
- Read the exact section
- Show the relevant lines with context

**"What happens when X fails / what if X?"**
- Find the relevant node
- Grep for error handling, retries, fallbacks in its owned files
- Trace the actual failure path with evidence

**"Walk me through a scenario"**
- Read `.repo-alive/scenarios/<scenarioId>.json`
- Walk through behavior_view.steps one by one
- For each step, read the evidence file and explain what's happening
- Show the data_view payloads where relevant

**Architecture / "how is this structured?"**
- Read `.repo-alive/graph.json` for the full node map
- Show L0 nodes with their summaries
- Offer to drill into any specific subsystem

### Rules

- **Only answer from real files.** If you haven't read a file yet, read it before answering.
- **Cite file:line for every factual claim.**
- **Never invent code or behavior.** If uncertain, say "I need to read X first" and read it.
- **Build on context within the session** — don't re-read files you've already read unless the question requires it.
- **Stay focused** — quote relevant sections, don't dump entire files.
- **If a question is outside the codebase** (e.g. general programming), answer briefly then offer to find the relevant code.

### Conversation memory

Within this session, track:
- Which nodes you've already loaded (don't reload unless needed)
- Which files you've already read
- Key facts established in previous answers (e.g. "we established that team mode uses plan→prd→exec→verify→fix")

Use this to give richer follow-up answers without re-reading everything.

### Staying in chat mode

After each answer, wait for the next question. Do not exit or summarize unless the user says to stop.

If the user asks about something outside any manifest (e.g. a file not in any node's owned_files), do a fresh Grep to find it, then answer from source.
