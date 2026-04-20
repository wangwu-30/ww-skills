---
name: repo-alive
version: 0.0.2
description: |
  Makes any codebase self-explanatory. Runs an uncertainty-reduction analysis loop
  (wide search → hypotheses → verification → manifests), then enters a persistent
  TUI conversation grounded in real source files. Zero framework assumptions.

  Usage:
    /repo-alive              — analyze (if needed) then chat in TUI
    /repo-alive analyze      — force re-analysis, then chat
    /repo-alive --html       — [EXPERIMENTAL] analyze then serve interactive HTML canvas

  Use when asked to "chat with this codebase", "explain this repo",
  "understand this project", "make it alive", "explore this codebase".
allowed-tools:
  - Bash
  - Glob
  - Grep
  - Read
  - Write
  - Agent
---

## Preamble

```bash
echo "REPO-ALIVE v0.0.2"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
echo "REPO_ROOT: $REPO_ROOT"
GIT_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "NO_GIT")
echo "GIT_HEAD: $GIT_HEAD"
DATA_DIR="$REPO_ROOT/.repo-alive"
FINGERPRINT="$DATA_DIR/fingerprint.json"

# Parse arguments
MODE="chat"           # default: TUI chat
FORCE_ANALYZE="no"
for arg in "$@"; do
  case "$arg" in
    --html)     MODE="html" ;;
    analyze)    FORCE_ANALYZE="yes" ;;
  esac
done
echo "MODE: $MODE"
echo "FORCE_ANALYZE: $FORCE_ANALYZE"

# Check freshness
FRESH="no"
if [ "$FORCE_ANALYZE" = "yes" ]; then
  echo "MANIFESTS_FRESH: no (forced)"
elif [ -f "$FINGERPRINT" ]; then
  STORED=$(python3 -c "import json; d=json.load(open('$FINGERPRINT')); print(d.get('git_head',''))" 2>/dev/null || echo "")
  [ "$STORED" = "$GIT_HEAD" ] && FRESH="yes"
fi
echo "MANIFESTS_FRESH: $FRESH"
```

---

## Analysis Engine (run when MANIFESTS_FRESH=no)

This is **not** a fixed pipeline. It is an uncertainty-reduction loop.

```
threshold = 0.8

while min_confidence(all_candidate_nodes) < threshold:
    question = highest_uncertainty_question(state.questions)
    tool     = cheapest_tool_that_answers(question)
    result   = execute(tool)
    update(fact_store, hypotheses, confidence)

output verified_model → write .repo-alive/
```

Tool cost order: `rg --files` → `rg -n` → `sed -n` → scoped cross-reference scan

### State Block

```json
{
  "phase": 0, "scope": ".", "threshold": 0.8,
  "fact_store": { "files": [], "manifests": [], "candidate_roots": [],
                  "import_edges": [], "interface_signals": [],
                  "locked_partitions": { "L0": [], "L1": {} } },
  "hypotheses": [], "confidence": {}, "questions": [],
  "tainted": [], "budget_used": { "tool_calls": 0 }, "partial": false
}
```

### Phase 0 — Wide Search (parallel, one turn)

```bash
# A. File inventory
rg --files . -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/dist/**' \
  -g '!**/build/**' -g '!**/target/**' -g '!**/coverage/**' \
  -g '!**/.venv/**' -g '!**/vendor/**'

# B. Root/manifest scan
rg --files . | rg '(^|/)(package\.json|pyproject\.toml|setup\.py|Cargo\.toml|go\.mod|go\.work|pom\.xml|build\.gradle|Makefile|Dockerfile|README\.md)$'

# C. Import/reference seed
rg -n --no-heading -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/dist/**' \
  '\b(import|export\s+.+\s+from|require\(|from\s+["\x27]|include\s+|use\s+|mod\s+)'

# D. Entrypoint seed
rg -n --no-heading -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/dist/**' \
  '\b(main\s*\(|if __name__ == .__main__.|listen|serve|handle|receive|consume|dispatch|fetch|connect|query|insert|update|delete|publish|subscribe|emit|render)\b'

# E. Taint scan (before any scoring)
rg --files . | rg '(^|/)(index\.(ts|js)|__init__\.py|types\.(ts|py)|schema\.[^/]+|generated/|vendor/|utils/|shared/|common/|[^/]+\.config\.[^/]+|constants\.[^/]+)'
```

Apply taint multiplier `0.1` to any edge involving a tainted path before scoring.

### Phase 1 — Hypothesis Generation

Generate **2–3 falsifiable L0 partition hypotheses** from Phase 0 facts.
Hypotheses are about **L0 partitions** (which directories are top-level nodes).

```json
{
  "id": "H1", "level": "L0", "scope": ".",
  "partition": [{ "id": "l0:api", "path": "services/api" }],
  "predicted_signals": [
    { "id": "S1", "type": "path_exists", "value": "services/api/package.json" }
  ],
  "confidence": 0.45, "status": "active"
}
```

### Phase 2 — Hypothesis Verification Loop

Test predicted signals cheapest-first. Update confidence:
```
signal found AND predicted     → confidence += 0.20
signal found AND NOT predicted → confidence -= 0.30
signal absent AND predicted    → confidence -= 0.15
```
Lock at `> 0.8`. Falsify at `< 0.1`. Stop when one locked, all others falsified.

### Phase 3 — L1 Discovery (same loop, scoped per L0)

For each locked L0, run Phase 0→1→2 scoped to that subtree. Apply taint before scoring.

### Phase 4 — Interface + Connection Extraction

Generic patterns only — no framework names:

```bash
rg -n --no-heading '\b(handle|listen|serve|receive|consume|accept|dispatch)\b'  # inbound
rg -n --no-heading '\b(send|publish|emit|request|fetch|call|connect|open)\b'    # outbound
rg -n --no-heading '\b(query|select|insert|update|delete|save|load|persist)\b'  # storage
```

Connection requires evidence on BOTH sides. One-sided → `candidate: true, confidence: 0.3`.

### Phase 5 — Three-View Scenario Extraction

Three views, always separate:
- **structure_view**: participating nodes/connections
- **behavior_view**: ordered steps (lexical order only, branch on if/switch/catch)
- **data_view**: payload shapes from visible artifacts only

### Phase 6 — Verification Pass

Batch-grep all retained symbols. Drop if not found. Keep as candidate if one-sided.

### Phase 7 — Write Manifests

Write to `.repo-alive/`:
- `fingerprint.json` — `{ git_head, generated_at, tool: "repo-alive/0.0.2" }`
- `graph.json` — `{ nodes, edges }`
- `nodes/<id>.json` — full node manifest
- `scenarios/<id>.json` — three-view scenario
- `ownership.json` — `{ "<file>": "<node-id>" }`
- `reverse-index.json` — `{ "<node-id>": { owned_files, scenario_refs } }`

### Node Manifest Schema

```json
{
  "schema_version": "1.0", "id": "<slug>", "name": "<human name>",
  "level": "L0|L1|L2", "root_path": "<relative>", "language_mix": ["<lang>"],
  "analysis_status": "complete|partial", "confidence": 0.0,
  "summary": "<evidence-grounded>", "responsibilities": ["<claim>"],
  "owned_files": ["<relative paths>"],
  "key_files": [{ "path": "...", "reason": "..." }],
  "interfaces": { "receives": [...], "sends": [...], "reads_from": [...], "writes_to": [...] },
  "connections": [{ "to": "<id>", "type": "call|http|message|storage|spawn|config|import",
    "direction": "outbound|inbound", "label": "...", "confidence": 0.0,
    "evidence": [{ "path": "...", "line": 0, "snippet": "..." }] }],
  "scenario_refs": [], "open_questions": [], "coverage_ratio": 1.0
}
```

---

## Mode: Chat (default)

After analysis, enter **persistent TUI conversation**.

### Orientation

Read `.repo-alive/graph.json` and print 4-6 lines:
- Project name, type (CLI/web app/library/service)
- L0 nodes found
- One scenario available (if any)

End with: **"What would you like to know?"**

### Answering questions

For every question:
1. Identify relevant node(s) from `graph.json`
2. Load `nodes/<nodeId>.json`
3. Read owned files (key_files first, stop at 40k chars, skip >32KB)
4. Answer with `file:line` citations
5. If multi-node, load each in turn

**"How does X work?"** → Grep → load node → read files → trace call chain

**"What's the difference between X and Y?"** → load both → compare with evidence

**"Show me code for X"** → Grep → read section → show with context

**"What if X fails?"** → find node → grep error handling → trace failure path

**"Walk me through a scenario"** → read scenario JSON → walk behavior_view.steps → show data_view payloads

**Architecture** → read graph.json → show L0 map → offer to drill in

### Rules
- Only answer from real files. Read before answering.
- Cite `file:line` for every factual claim.
- Never invent. If uncertain, say so and read more.
- Build on session context — don't re-read already-read files.
- Stay focused — quote sections, don't dump files.

### Session memory
Track: nodes loaded, files read, key facts established. Use for richer follow-ups.

After each answer, wait for the next question.

---

## Mode: HTML [EXPERIMENTAL]

> ⚠️ This mode is experimental. It starts a local web server and opens a browser.
> Requires Node.js. The canvas UI is a work in progress.

After analysis, start the local server and open the canvas:

```bash
SKILL_DIR="$HOME/.claude/skills/repo-alive"

# Install ws if needed
if [ ! -d "$SKILL_DIR/node_modules/ws" ]; then
  echo "Installing ws..."
  (cd "$SKILL_DIR" && npm install ws --no-save 2>/dev/null || npm install ws)
fi

# Kill any existing server on 4311
lsof -ti:4311 | xargs kill -9 2>/dev/null || true
sleep 0.3

# Start server and bridge
REPO_ALIVE_ROOT="$REPO_ROOT" node "$SKILL_DIR/server.js" 4311 &
SERVER_PID=$!
sleep 1.5

REPO_ALIVE_ROOT="$REPO_ROOT" REPO_ALIVE_DATA="$REPO_ROOT/.repo-alive" PORT=4311 \
  node "$SKILL_DIR/cc-bridge.js" "$REPO_ROOT/.repo-alive" 4311 &
BRIDGE_PID=$!
sleep 0.5

echo "Server PID: $SERVER_PID | Bridge PID: $BRIDGE_PID"
echo "Stop: kill $SERVER_PID $BRIDGE_PID"

open "http://localhost:4311" 2>/dev/null || \
  xdg-open "http://localhost:4311" 2>/dev/null || \
  echo "Open http://localhost:4311"
```

Then enter the same TUI chat mode alongside the canvas — questions can be asked
in either the terminal or the web UI.

---

## Incremental Update

When files change:
```bash
CHANGED=$(git diff --name-only HEAD~1 2>/dev/null || echo "")
```
1. Load `ownership.json` → map changed files to node IDs
2. Regenerate only affected manifests
3. If root manifest/entrypoint changed → rerun L0/L1 for enclosing root
4. If >20% nodes affected → full re-analysis
5. Rewrite `graph.json`, `ownership.json`, `fingerprint.json`

---

## Quality Gates

Do not report completion until:
- `fingerprint.json` exists and matches current HEAD (or NO_GIT)
- `graph.json` has ≥1 node
- ≥1 `nodes/*.json` exists
- Chat mode: ready to answer questions
- HTML mode: server responds to `GET /graph`
