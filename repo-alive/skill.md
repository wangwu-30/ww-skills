---
name: repo-alive
version: 1.0.0
description: |
  Makes any codebase self-explanatory. Analyzes the repo once, persists
  understanding as JSON manifests in .repo-alive/, then serves an interactive
  canvas where every node is a queryable Agent backed by real code.
  Zero framework assumptions. Works on any language or project layout.
  Use when asked to "explore this codebase", "make it alive", "understand this repo",
  "explain this codebase interactively".
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
echo "REPO-ALIVE v1.0.0"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
echo "REPO_ROOT: $REPO_ROOT"
GIT_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "NO_GIT")
echo "GIT_HEAD: $GIT_HEAD"
DATA_DIR="$REPO_ROOT/.repo-alive"
FINGERPRINT="$DATA_DIR/fingerprint.json"
echo "DATA_DIR: $DATA_DIR"
FRESH="no"
if [ -f "$FINGERPRINT" ]; then
  STORED=$(python3 -c "import json,sys; d=json.load(open('$FINGERPRINT')); print(d.get('git_head',''))" 2>/dev/null || echo "")
  [ "$STORED" = "$GIT_HEAD" ] && FRESH="yes"
fi
echo "MANIFESTS_FRESH: $FRESH"
```

---

## Rules (read before doing anything)

- Work against `$REPO_ROOT`. Never hardcode paths.
- Do not assume any framework, language, or project layout.
- Never write oh-my-codex-specific logic. Every pattern must be generic.
- Manifests are the only persistent state. Plain JSON under `.repo-alive/`.
- When answering a question about a node: read only that node's manifest + its `owned_files`. Nothing else.
- Every claim in a manifest must have `evidence` (file + line + snippet). No evidence = omit the claim.
- If budget runs out mid-analysis: write partial manifests with `"analysis_status": "partial"`. Never hallucinate.

---

## Phase 1 — Freshness Check

If `MANIFESTS_FRESH=yes`: skip to Phase 3 (Serve).
If `MANIFESTS_FRESH=no`: run Phase 2 (Analyze).

---

## Phase 2 — Analysis (run once, ~60-700 tool calls depending on repo size)

### Step 2.0 — Scope and budget

```bash
# File count for budget planning
find "$REPO_ROOT" -type f \
  ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/vendor/*" \
  ! -path "*/dist/*" ! -path "*/build/*" ! -path "*/target/*" \
  ! -path "*/.next/*" ! -path "*/coverage/*" ! -name "*.png" \
  ! -name "*.jpg" ! -name "*.gif" ! -name "*.pdf" ! -name "*.zip" \
  ! -name "*.exe" ! -name "*.dll" ! -name "*.so" ! -name "*.dylib" \
  | wc -l
```

Budget by file count:
- < 200 files  → 120 tool calls max
- 200–1500     → 300 tool calls max
- > 1500       → 700 tool calls max

Allocation: 5% fingerprint/scope · 20% L0 discovery · 35% L1 discovery · 20% interfaces+connections · 15% scenarios · 5% consistency

### Step 2.1 — Inventory

Run these in parallel:

**A. Full file list (filtered)**
```
Glob: ** (exclude: .git, node_modules, vendor, dist, build, target, .next, coverage, *.{png,jpg,gif,pdf,zip,exe,dll,so,dylib,class,jar})
```

**B. Root manifests**
```
Glob: {package.json,pyproject.toml,requirements.txt,setup.py,go.mod,Cargo.toml,pom.xml,build.gradle,Makefile,Dockerfile,compose.yaml,compose.yml,.env.example}
```

**C. Workspace/monorepo hints**
```
Glob: {packages/*/package.json,apps/*/package.json,services/*/go.mod,crates/*/Cargo.toml,*/pyproject.toml}
```

Read any root manifests found. Extract: package names, workspace members, bin/scripts entries, dependencies.

### Step 2.2 — L0 boundary detection

L0 = a top-level executable/deployable subsystem, or a major bounded module in a single-app repo.

**Signals (in priority order):**

1. Monorepo workspace members → one L0 per member
2. Multiple `go.mod` / `Cargo.toml` / `package.json` under subdirs → one L0 per package root
3. Directories containing entrypoints:
```
Grep: pattern="if __name__ == ['\"]__main__['\"]|func main\(|process\.argv|commander|click\.command|argparse|FastAPI\(|Flask\(|express\(|http\.ListenAndServe|tokio::main|cobra\.Command"
glob="**/*.{py,js,ts,go,rs}"
```
4. README/docs naming subsystems:
```
Grep: pattern="(service|worker|api|server|frontend|backend|cli|daemon|gateway|job|consumer|producer|package|crate|module)"
paths=["README*","docs/**","*.md"]
```
5. Fallback: top-level directories with >5% of source files each

**L0 count targets:** 3–8 for small repos · 5–15 for medium · 10–30 for large
If too many candidates: merge those sharing >40% imports or the same root manifest.

**For each L0, record:**
```json
{
  "id": "<slug>",
  "name": "<human name>",
  "level": "L0",
  "root_path": "<relative path>",
  "language_mix": ["<lang>"],
  "owned_files": ["<relative paths>"],
  "key_files": [{"path": "...", "reason": "..."}],
  "entrypoints": [{"kind": "server|cli|job|consumer", "path": "...", "evidence": [...]}]
}
```

### Step 2.3 — L1 boundary detection (per L0)

L1 = internal bounded component inside an L0.

For each L0:
```
Glob: <l0-root>/**
Grep: pattern="(import |from |require\(|use |mod )" paths=[<l0-root>/**]
```

Score directory clusters by:
- source file count
- presence of role-named files: `routes|handlers|controllers|views|api|service|usecase|domain|core|repo|store|db|queue|jobs|worker|client|sdk|ui|components|pages`
- import cohesion within cluster vs cross-cluster

Create L1 if cluster has coherent responsibility and ≥3 files.
Each L1 must own a non-overlapping file set.
Small L0s (<10 files) may skip L1.

### Step 2.4 — Interface extraction (per node)

For each L0 and L1, grep owned files with these generic patterns:

**Inbound (receives):**
```
Grep: pattern="(route|router|handler|controller|endpoint|command|subcommand|stdin|argv|flag|consumer|subscribe|listen|websocket|cron|schedule)"
```

**Outbound (sends):**
```
Grep: pattern="(fetch\(|axios\.|requests\.|http\.|grpc|rpc|publish|produce|emit|send|enqueue|writeFile|fs\.|sql|query|exec\(|insert|update|delete)"
```

**Data shapes:**
```
Grep: pattern="(schema|model|struct|class|interface|type |zod|pydantic|serde|dto|payload|request|response|event|message)"
```

Read only matched files. Classify each match into:
- `receives` / `sends` / `reads_from` / `writes_to` / `triggers` / `exposes`

**Do not infer transport from framework name alone.** Infer from behavior:
- route + request/response → HTTP interface
- file/DB ops → storage interface
- publish/emit/send → message interface
- argv/flag parsing → CLI interface
- schedule/cron → scheduled trigger

### Step 2.5 — Connection extraction

For each node pair, look for:

```
Grep: pattern="(import |from |require\(|use )" → cross-ownership imports
Grep: pattern="(fetch\(|axios\.|requests\.|http\.|grpc|rpc)" → HTTP calls
Grep: pattern="(publish|emit|produce|enqueue|subscribe|consume|topic|queue|event|message)" → messages
Grep: pattern="(sql|query|table|collection|bucket|redis|cache|s3|blob)" → shared storage
Grep: pattern="(exec\(|spawn\(|fork\(|subprocess|os\.exec)" → process spawning
```

For each match: map the target symbol/path/resource back to an owned node.
**No evidence = no edge.** Store: `{ to, type, direction, label, confidence, evidence: [{file, line, snippet}] }`

### Step 2.6 — Scenario extraction

Detect candidate entry actions:
```
Grep: pattern="(request|login|create|update|delete|sync|run|start|serve|build|upload|download|process)"
paths=["README*","docs/**","tests/**","examples/**","**/test_*.{py,go}","**/*.test.{ts,js}","**/*.spec.{ts,js}"]
```

Score by: centrality in graph · README/docs mention · completeness of downstream path · user-facing nature.

For top 3–10 candidates:
1. Read entry file + immediate downstream files
2. Walk one concrete path until: response produced / data persisted / job enqueued / terminal side effect
3. Record each hop as a step with actor, node, action, evidence
4. Place a checkpoint after the first irreversible transition
5. Find the first explicit error/guard/retry path → failure branch

### Step 2.7 — Write manifests

Create `.repo-alive/` and write:

**`fingerprint.json`**
```json
{
  "schema_version": "1.0",
  "git_head": "<GIT_HEAD>",
  "generated_at": "<ISO timestamp>",
  "tool": "repo-alive/1.0.0"
}
```

**`graph.json`**
```json
{
  "schema_version": "1.0",
  "generated_at": "...",
  "nodes": [
    {
      "id": "<id>",
      "name": "<name>",
      "level": "L0",
      "root_path": "...",
      "summary": "...",
      "child_node_ids": ["..."],
      "scenario_refs": ["..."]
    }
  ],
  "edges": [
    { "from": "<id>", "to": "<id>", "type": "call|http|message|storage|spawn|config|import",
      "label": "...", "confidence": 0.0–1.0 }
  ]
}
```

**`nodes/<node-id>.json`** — full manifest per node (see schema below)

**`scenarios/<scenario-id>.json`** — scenario state machine (see schema below)

**`ownership.json`** — `{ "<file-path>": "<node-id>", ... }`

**`reverse-index.json`** — `{ "<node-id>": { "owned_files": [...], "key_files": [...], "scenario_refs": [...] } }`

---

## Node Manifest Schema

```json
{
  "schema_version": "1.0",
  "kind": "l0_node|l1_node|l2_file",
  "id": "<slug>",
  "name": "<human name>",
  "level": "L0|L1|L2",
  "parent_id": null,
  "child_node_ids": [],
  "repo_root": ".",
  "root_path": "<relative path>",
  "language_mix": ["<lang>"],
  "analysis_status": "complete|partial",
  "generated_at": "<ISO>",
  "fingerprint": { "git_head": "...", "owned_files_count": 0 },

  "summary": "<one paragraph, evidence-grounded>",
  "responsibilities": ["<claim>"],

  "owned_files": ["<relative paths>"],
  "key_files": [{ "path": "...", "reason": "..." }],
  "entrypoints": [{
    "kind": "server|cli|job|consumer|library",
    "path": "...",
    "symbol": "...",
    "evidence": [{ "file": "...", "line": 0, "snippet": "..." }]
  }],

  "interfaces": {
    "receives": [{ "id": "...", "kind": "http|cli|message|file|schedule|socket",
      "name": "...", "shape": "...",
      "evidence": [{ "file": "...", "line": 0, "snippet": "..." }] }],
    "sends":      [...],
    "reads_from": [...],
    "writes_to":  [...],
    "triggers":   [...],
    "exposes":    [...]
  },

  "connections": [{
    "to": "<node-id>",
    "type": "call|http|message|storage|spawn|config|import",
    "direction": "outbound|inbound",
    "label": "...",
    "confidence": 0.0,
    "evidence": [{ "file": "...", "line": 0, "snippet": "..." }]
  }],

  "data_shapes": [{ "name": "...", "kind": "request|response|event|model", "defined_in": "..." }],
  "scenario_refs": ["<scenario-id>"],

  "open_questions": [],
  "unknown_interfaces": [],
  "unknown_connections": [],
  "coverage_ratio": 1.0
}
```

---

## Scenario Manifest Schema

```json
{
  "schema_version": "1.0",
  "kind": "scenario",
  "id": "<slug>",
  "name": "<human name>",
  "generated_at": "<ISO>",
  "summary": "...",
  "start_node": "<node-id>",
  "node_refs": ["<node-id>"],
  "tags": ["request|job|cli|sync|async"],

  "steps": [{
    "id": "step-N",
    "index": 0,
    "actor": "<node-id>",
    "node": "<node-id>",
    "action": "...",
    "inputs": {},
    "outputs": {},
    "evidence": [{ "file": "...", "line": 0, "snippet": "..." }]
  }],

  "checkpoints": [{
    "id": "checkpoint-<name>",
    "after_step": "step-N",
    "label": "...",
    "state": {}
  }],

  "branches": [{
    "id": "branch-<name>",
    "from_checkpoint": "checkpoint-<name>",
    "condition": "...",
    "steps": [...]
  }]
}
```

---

## Phase 3 — Serve

```bash
cd "$REPO_ROOT"
# Install ws if needed
if [ ! -d node_modules/ws ]; then
  echo "Installing ws..."
  npm install ws --no-save 2>/dev/null || npm install ws 2>/dev/null
fi
# Start server in background
node "$(dirname "$0")/server.js" 4311 &
SERVER_PID=$!
sleep 1
# Open canvas
open http://localhost:4311 2>/dev/null || \
  xdg-open http://localhost:4311 2>/dev/null || \
  echo "Open http://localhost:4311 in your browser"
echo "Server PID: $SERVER_PID"
echo "Stop with: kill $SERVER_PID"
```

---

## Phase 4 — Interact (per user question)

When the user asks about a specific node:

1. Identify the node ID from user's question (match against node names in graph.json)
2. Read `.repo-alive/nodes/<node-id>.json`
3. Read **only** files listed in `owned_files` (skip files >64KB)
4. Answer from: manifest summary + interfaces + connections + owned source files
5. Every answer must cite file:line evidence
6. If the answer requires files outside this node's ownership: say so explicitly, offer to activate the peer node

When the user asks to demonstrate a scenario:
1. Identify scenario ID from graph.json's scenario list
2. Read the scenario manifest
3. Walk through steps, reading evidence files as needed
4. For "what if X fails?" — identify the relevant checkpoint and branch, walk the branch steps

---

## Incremental Update

When files change (e.g., after a commit):

```bash
CHANGED=$(git diff --name-only HEAD~1 2>/dev/null || echo "")
```

1. Load `ownership.json`
2. Map changed files → affected node IDs
3. Regenerate only those node manifests
4. If any changed file is a root manifest, entrypoint, or router → rerun L0/L1 discovery for its enclosing root
5. Rerun scenarios that reference regenerated nodes
6. Rewrite `graph.json`, `ownership.json`, `reverse-index.json`, `fingerprint.json`
7. If >20% of nodes affected → full re-analysis

---

## Quality Gates

Do not report completion until:
- `.repo-alive/fingerprint.json` exists and matches current HEAD
- `.repo-alive/graph.json` has ≥1 node
- At least one `nodes/*.json` file exists
- At least one `scenarios/*.json` file exists
- Server responds to `GET /graph`
- At least one scenario plays over WebSocket without error
