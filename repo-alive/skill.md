---
name: repo-alive
version: 1.1.0
description: |
  Makes any codebase self-explanatory. Runs an uncertainty-reduction analysis loop
  to build node manifests, then serves an interactive canvas where every node is a
  queryable Agent backed by real code. Zero framework assumptions.
  Use when asked to "explore this codebase", "make it alive", "understand this repo".
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
echo "REPO-ALIVE v1.1.0"
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
echo "REPO_ROOT: $REPO_ROOT"
GIT_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "NO_GIT")
echo "GIT_HEAD: $GIT_HEAD"
DATA_DIR="$REPO_ROOT/.repo-alive"
FINGERPRINT="$DATA_DIR/fingerprint.json"
FRESH="no"
if [ -f "$FINGERPRINT" ]; then
  STORED=$(python3 -c "import json; d=json.load(open('$FINGERPRINT')); print(d.get('git_head',''))" 2>/dev/null || echo "")
  [ "$STORED" = "$GIT_HEAD" ] && FRESH="yes"
fi
echo "MANIFESTS_FRESH: $FRESH"
```

If `MANIFESTS_FRESH=yes` → skip to **Phase: Serve**.
If `MANIFESTS_FRESH=no` → run **Analysis Engine**.

---

## Rules

- Work against `$REPO_ROOT`. Never hardcode paths.
- Every claim must carry `evidence: [{path, line, snippet}]`. No evidence = omit or mark `candidate: true, confidence: 0.3`.
- Apply taint **before** any fan-in or cluster scoring.
- Three views (structure / behavior / data) must stay separate in scenario manifests.
- Budget is a soft optimization. If a run stops early, persist state as `partial: true` and resume next run.

---

## Analysis Engine

This is **not** a fixed pipeline. It is an uncertainty-reduction loop.

### Core loop (道)

```pseudo
threshold = 0.8

while min_confidence(all_candidate_nodes) < threshold:
    question = highest_uncertainty_question(state.questions)
    tool     = cheapest_tool_that_answers(question)
    result   = execute(tool)
    update_fact_store(state, result)
    apply_taint_before_scoring(state)
    update_hypotheses(state.hypotheses, result)
    update_confidence(state.confidence, result)
    refresh_questions(state)

output verified_model(state)
```

Tool cost order (always pick cheapest first):
1. `rg --files` — path existence / inventory
2. `rg -n` — pattern scan / signal existence
3. `sed -n` — targeted file window read
4. scoped cross-reference scan

### State Block

Maintain this JSON between phases. Update after every tool call.

```json
{
  "phase": 0,
  "scope": ".",
  "threshold": 0.8,
  "fact_store": {
    "repo_root": ".",
    "files": [],
    "directories": [],
    "manifests": [],
    "candidate_roots": [],
    "import_edges": [],
    "interface_signals": [],
    "open_questions": [],
    "locked_partitions": { "L0": [], "L1": {} }
  },
  "hypotheses": [],
  "confidence": {},
  "questions": [],
  "tainted": [],
  "budget_used": { "tool_calls": 0 },
  "partial": false
}
```

---

## Phase 0 — Wide Search (parallel, one turn)

Goal: broad repo facts + taint marking + seed for first hypotheses.

Run these in parallel:

**A. File inventory**
```bash
rg --files . \
  -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/dist/**' \
  -g '!**/build/**' -g '!**/target/**' -g '!**/coverage/**' \
  -g '!**/.venv/**' -g '!**/vendor/**'
```

**B. Root/manifest/boundary scan**
```bash
rg --files . | rg '(^|/)(package\.json|pyproject\.toml|setup\.py|Cargo\.toml|go\.mod|go\.work|pom\.xml|build\.gradle|Makefile|Dockerfile|README\.md)$'
```

**C. Import/reference seed**
```bash
rg -n --no-heading \
  -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/dist/**' \
  -g '!**/build/**' -g '!**/target/**' -g '!**/coverage/**' \
  '\b(import|export\s+.+\s+from|require\(|from\s+["\x27]|include\s+|use\s+|mod\s+)'
```

**D. Entrypoint/interface seed**
```bash
rg -n --no-heading \
  -g '!**/.git/**' -g '!**/node_modules/**' -g '!**/dist/**' \
  '\b(main\s*\(|if __name__ == .__main__.|listen|serve|handle|receive|consume|dispatch|fetch|connect|query|insert|update|delete|publish|subscribe|emit|render)\b'
```

**E. Taint scan (run first, before any scoring)**
```bash
rg --files . | rg '(^|/)(index\.(ts|js)|__init__\.py|types\.(ts|py)|schema\.[^/]+|generated/|vendor/|utils/|shared/|common/|[^/]+\.config\.[^/]+|constants\.[^/]+)'
```

After Phase 0, populate `state.fact_store` and `state.tainted`.
Apply taint multiplier `0.1` to any edge involving a tainted path before scoring.

---

## Phase 1 — Hypothesis Generation (法: 假设)

Generate **2–3 falsifiable L0 partition hypotheses** from Phase 0 facts.

Hypotheses are about **L0 partitions** (which directories are top-level nodes), not architecture types.

**Hypothesis format:**
```json
{
  "id": "H1",
  "level": "L0",
  "scope": ".",
  "partition": [
    { "id": "l0:api", "path": "services/api" },
    { "id": "l0:web", "path": "apps/web" }
  ],
  "predicted_signals": [
    { "id": "S1", "type": "path_exists",        "value": "services/api/package.json" },
    { "id": "S2", "type": "path_exists",        "value": "apps/web/package.json" },
    { "id": "S3", "type": "boundary_reference", "value": "root workspace references services/* apps/*" },
    { "id": "S4", "type": "edge_pattern",       "value": "apps/web imports services/api or shared" }
  ],
  "confidence": 0.45,
  "status": "active"
}
```

Seed confidence: 0.4–0.5 based on how many Phase 0 signals support the partition.

---

## Phase 2 — Hypothesis Verification Loop (法: 检验→修正)

For each active hypothesis, test its predicted signals with the cheapest probe first.

**Probe by signal type:**

`path_exists`:
```bash
rg --files . | rg '^services/api/package\.json$'
```

`boundary_reference`:
```bash
rg -n 'apps/|services/|packages/' package.json pnpm-workspace.yaml yarn.lock go.work Cargo.toml 2>/dev/null
```

`edge_pattern`:
```bash
rg -n --no-heading 'services/api|packages/shared' apps/web 2>/dev/null
```

**Confidence update math:**
```
signal found AND predicted by H     → confidence += 0.20
signal found AND NOT predicted by H → confidence -= 0.30
signal absent AND predicted by H    → confidence -= 0.15
```
Clamp to [0.0, 1.0].

**Stop criteria:**
- Lock hypothesis when `confidence > 0.8`
- Falsify hypothesis when `confidence < 0.1`
- Stop L0 loop when one hypothesis is locked AND all others are falsified

**Worked example:**

Initial: `{ H1: 0.45, H2: 0.30, H3: 0.25 }`

Probe: `services/api/package.json` exists?
- H1 predicted it → `0.45 + 0.20 = 0.65`
- H2 did not predict it → `0.30 - 0.30 = 0.00` (falsified)
- H3 did not predict it → `0.25 - 0.30 = 0.00` (falsified)

Probe: `apps/web/package.json` exists?
- H1 predicted it → `0.65 + 0.20 = 0.85` → **locked**

---

## Phase 3 — L1 Discovery (same loop, scoped per L0)

For each locked L0 node, run the same Phase 0→1→2 loop scoped to that subtree.

```bash
# Scoped to one L0
rg --files services/api
rg -n --no-heading '\b(import|export\s+.+\s+from|require\()' services/api
rg --files services/api | rg '(^|/)(index\.(ts|js)|types\.(ts|py)|generated/|utils/|shared/)'
```

Apply taint before scoring. Generate L1 partition hypotheses. Verify. Lock.

Small L0s (<10 files) may skip L1.

---

## Phase 4 — Interface + Connection Extraction

After L0 and L1 are locked. Generic patterns only — no framework names.

**Inbound:**
```bash
rg -n --no-heading '\b(handle|listen|serve|receive|consume|accept|dispatch)\b'
```

**Outbound:**
```bash
rg -n --no-heading '\b(send|publish|emit|request|fetch|call|connect|open)\b'
```

**Storage:**
```bash
rg -n --no-heading '\b(query|select|insert|update|delete|save|load|persist|commit)\b'
```

**Data contracts:**
```bash
rg -n --no-heading '\b(type|interface|schema|struct|record|dto|payload|message|event)\b'
```

**Interface classification (by local evidence, not framework name):**
```
inbound_score  += 2 if path/name contains handler|route|controller|listener|consumer|entry|main
inbound_score  += 1 per context verb: handle listen serve receive consume accept dispatch

outbound_score += 2 if path/name contains client|gateway|adapter|publisher|producer
outbound_score += 1 per context verb: send publish emit request fetch call connect open

storage_score  += 2 if path/name contains repo|store|dao|model|migration|schema
storage_score  += 1 per context verb: query select insert update delete save load persist
```

Pick highest score ≥ 2. Otherwise: `{ "type": "unknown", "candidate": true, "confidence": 0.3 }`.

**Connection requires evidence on BOTH sides:**
```json
{
  "from": "l1:api.handler",
  "to": "l1:data.repo",
  "type": "internal_call",
  "confidence": 0.9,
  "evidence": [
    { "path": "services/api/src/handler.ts", "line": 27, "snippet": "await repo.insert(payload)" },
    { "path": "services/data/src/repo.ts",   "line": 4,  "snippet": "export async function insert(data) {" }
  ]
}
```

One-sided evidence → `candidate: true, confidence: 0.3`. No evidence → drop.

---

## Phase 5 — Three-View Scenario Extraction

Three views, always separate. Never mix them.

### Structure view
Which nodes/interfaces/connections participate. Derived from locked manifests.

### Behavior view (sequence diagram)
Ordered execution steps. Derived from static code reading.

Algorithm:
1. Choose a confirmed inbound interface or entrypoint as seed
2. Read the seed definition
3. Walk calls in **lexical order** inside the function body
4. Resolve each call using Phase 4 connection evidence
5. Emit a step only when order is **explicit in code**
6. When encountering `if/switch/catch/retry/async fan-out` → record branch/checkpoint, do not flatten
7. Stop when: leaving repo scope / entering unresolved dynamic dispatch / confidence < 0.8

**Behavior step:**
```json
{
  "id": "b2",
  "actor": "l1:api.create_user_handler",
  "action": "calls repository insert",
  "target": "l1:data.user_repo",
  "confidence": 0.9,
  "evidence": [{ "path": "services/api/src/handlers/create-user.ts", "line": 27, "snippet": "await repo.insert(payload)" }]
}
```

### Data view (payloads)
What values flow at each step. Derived from visible code artifacts only.

Sources: parameter shapes, object literals, type/schema definitions, test fixtures, docs.
Never invent examples.

**Data step:**
```json
{
  "step_ref": "b2",
  "payload_shape": { "id": "string", "email": "string", "name": "string" },
  "example": { "email": "user@example.com" },
  "confidence": 0.8,
  "evidence": [{ "path": "services/api/src/types/user.ts", "line": 5, "snippet": "type UserPayload = { id: string; email: string; name: string }" }]
}
```

### Scenario schema

```json
{
  "id": "scenario.create-user",
  "name": "Create user flow",
  "confidence": 0.86,
  "candidate": false,
  "structure_view": {
    "nodes": ["l1:api.handler", "l1:data.repo"],
    "connections": [{ "from": "l1:api.handler", "to": "l1:data.repo", "type": "internal_call" }]
  },
  "behavior_view": {
    "steps": [
      { "id": "b1", "actor": "l1:api.handler", "action": "validates input", "confidence": 0.9,
        "evidence": [{ "path": "...", "line": 14, "snippet": "validate(payload)" }] },
      { "id": "b2", "actor": "l1:api.handler", "action": "calls repo insert", "target": "l1:data.repo",
        "confidence": 0.9, "evidence": [{ "path": "...", "line": 27, "snippet": "await repo.insert(payload)" }] }
    ],
    "checkpoints": [{ "label": "user persisted", "after_step": "b2", "confidence": 0.9,
      "evidence": [{ "path": "...", "line": 27, "snippet": "await repo.insert(payload)" }] }],
    "branches": [{ "label": "validation fails", "confidence": 0.8,
      "evidence": [{ "path": "...", "line": 16, "snippet": "if (!valid) return error" }] }]
  },
  "data_view": {
    "steps": [
      { "step_ref": "b1", "payload_shape": { "email": "string", "name": "string" },
        "example": null, "confidence": 0.8, "evidence": [{ "path": "...", "line": 12, "snippet": "const { email, name } = payload" }] },
      { "step_ref": "b2", "payload_shape": { "id": "string", "email": "string", "name": "string" },
        "example": { "email": "user@example.com" }, "confidence": 0.8,
        "evidence": [{ "path": "...", "line": 5, "snippet": "type UserPayload = { id: string; email: string; name: string }" }] }
    ]
  }
}
```

---

## Phase 6 — Verification Pass

Batch-verify all retained claims before writing manifests.

Build a grep pattern from all retained symbols/paths:
```bash
rg -n --no-heading \
  -e 'createUser' -e 'repo.insert' -e 'UserPayload' \
  services/api/src packages/shared/src
```

**Drop** when: no evidence, verification grep misses entirely, supporting hypothesis was falsified.
**Keep as candidate** (`confidence: 0.3`) when: one-sided connection, partial payload, plausible but unproven order.
**Keep as verified** when: evidence exists + grep confirms + confidence ≥ 0.8.

---

## Phase 7 — Write Manifests

Write to `.repo-alive/`:

- `fingerprint.json` — `{ schema_version, git_head, generated_at, tool }`
- `graph.json` — `{ nodes: [...], edges: [...] }` (summary level only)
- `nodes/<id>.json` — full node manifest per node
- `scenarios/<id>.json` — three-view scenario manifest
- `ownership.json` — `{ "<file>": "<node-id>" }`
- `reverse-index.json` — `{ "<node-id>": { owned_files, key_files, scenario_refs } }`
- `state.json` — final state block (for incremental updates)

---

## Node Manifest Schema

```json
{
  "schema_version": "1.0",
  "id": "<slug>",
  "name": "<human name>",
  "level": "L0|L1|L2",
  "parent_id": null,
  "child_node_ids": [],
  "root_path": "<relative>",
  "language_mix": ["<lang>"],
  "analysis_status": "complete|partial",
  "generated_at": "<ISO>",
  "confidence": 0.0,
  "candidate": false,

  "summary": "<one paragraph, evidence-grounded>",
  "responsibilities": ["<claim>"],

  "owned_files": ["<relative paths>"],
  "key_files": [{ "path": "...", "reason": "..." }],
  "entrypoints": [{
    "kind": "server|cli|job|consumer|library",
    "path": "...", "symbol": "...",
    "evidence": [{ "path": "...", "line": 0, "snippet": "..." }]
  }],

  "interfaces": {
    "receives":   [{ "id": "...", "kind": "http|cli|message|file|schedule|socket", "name": "...", "shape": "...", "evidence": [...] }],
    "sends":      [...],
    "reads_from": [...],
    "writes_to":  [...],
    "exposes":    [...]
  },

  "connections": [{
    "to": "<node-id>",
    "type": "call|http|message|storage|spawn|config|import",
    "direction": "outbound|inbound",
    "label": "...",
    "confidence": 0.0,
    "candidate": false,
    "evidence": [{ "path": "...", "line": 0, "snippet": "..." }]
  }],

  "scenario_refs": ["<scenario-id>"],
  "tainted_paths": [],
  "open_questions": [],
  "coverage_ratio": 1.0
}
```

---

## Phase: Serve

```bash
# Resolve skill directory (where server.js lives) — robust across all shells
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"

# Install ws in the skill directory if missing (server.js resolves modules from there)
if [ ! -d "$SKILL_DIR/node_modules/ws" ]; then
  echo "Installing ws in skill directory..."
  (cd "$SKILL_DIR" && npm install ws --no-save 2>/dev/null || npm install ws)
fi

# Start server — pass REPO_ROOT via env so server.js uses the correct project
REPO_ALIVE_ROOT="$REPO_ROOT" node "$SKILL_DIR/server.js" 4311 &
SERVER_PID=$!
sleep 1

open "http://localhost:4311" 2>/dev/null ||   xdg-open "http://localhost:4311" 2>/dev/null ||   echo "Open http://localhost:4311"
echo "Server PID: $SERVER_PID  |  Stop: kill $SERVER_PID"
```

---

## Phase: Interact

After the server starts, enter a **watch loop** for questions from the webpage.

### Watch loop

```bash
echo "Watching for questions from webpage..."
while true; do
  # Poll for pending question (fs.watch handles this server-side,
  # but also check directly for reliability)
  if [ -f "$DATA_DIR/pending.json" ]; then
    PENDING=$(cat "$DATA_DIR/pending.json")
    TYPE=$(python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d.get('type','query'))" <<< "$PENDING")
    if [ "$TYPE" = "query" ]; then
      # Node Q&A
      handle_query
    elif [ "$TYPE" = "trace" ]; then
      # What-if path tracing
      handle_trace
    fi
  fi
  sleep 0.5
done
```

### handle_query — node question answering

When `.repo-alive/pending.json` has `type: "query"`:

1. Read the pending question:
   - `nodeId`: which node is being asked about
   - `question`: the user's question

2. Load the node manifest: `.repo-alive/nodes/<nodeId>.json`

3. Load **only** the node's owned files (priority order):
   - Files in `key_files` first (always include)
   - Remaining `owned_files` sorted by size ascending
   - Stop at 40,000 chars total
   - Skip files >32KB individually

4. Answer the question:
   - Stay within the node's files only
   - Cite every claim with `file:line`
   - If the answer requires peer node files, say so explicitly

5. Write the answer to `.repo-alive/answer.json`:
   ```json
   {
     "questionId": "<from pending>",
     "nodeId": "<nodeId>",
     "text": "<answer markdown>",
     "evidence": [{ "path": "...", "line": 0, "snippet": "..." }]
   }
   ```

6. The server detects the file change and pushes to the webpage.

7. Delete `.repo-alive/pending.json` to mark as handled.

### handle_trace — what-if path tracing

When `.repo-alive/pending.json` has `type: "trace"`:

1. Read the pending trace request:
   - `scenarioId`: which scenario
   - `checkpointId`: where to fork from
   - `condition`: the what-if condition (e.g. "worker crashes here")

2. Load the scenario manifest: `.repo-alive/scenarios/<scenarioId>.json`

3. Find the checkpoint in `behavior_view.checkpoints`

4. Load files for ALL nodes in `scenario.structure_view.nodes`
   (same size strategy as handle_query, 40,000 char total limit)

5. Derive the new execution path:
   - Starting from the checkpoint state
   - Given the condition
   - Walk the code to find what actually happens
   - Each step must cite file:line evidence
   - Mark steps as `"what_if": true`

6. Write steps one by one to `.repo-alive/answer.json` as they are derived:
   ```json
   {
     "type": "trace:start",
     "scenarioId": "<id>",
     "condition": "<condition>"
   }
   ```
   Then for each step:
   ```json
   {
     "type": "trace:step",
     "step": {
       "id": "wi-1",
       "actor": "<node-id>",
       "action": "<what happens>",
       "what_if": true,
       "confidence": 0.85,
       "evidence": [{ "path": "...", "line": 0, "snippet": "..." }]
     }
   }
   ```
   Finally:
   ```json
   { "type": "trace:end" }
   ```

   Write each JSON object to the file and pause 300ms between steps
   so the server can pick up each one and animate them onto the canvas.

7. Delete `.repo-alive/pending.json`.

### Alternative: server polling

If the watch loop is not running, the server also exposes:
- `GET /pending` — returns current pending question
- `POST /answer` — Claude Code can POST the answer directly

Use `POST /answer` for streaming: post each step immediately as it is derived.

---

## Incremental Update

```bash
CHANGED=$(git diff --name-only HEAD~1 2>/dev/null || echo "")
```

1. Load `ownership.json` → map changed files to node IDs
2. Regenerate only affected node manifests
3. If changed file is a root manifest/entrypoint/router → rerun L0/L1 discovery for its enclosing root
4. Regenerate scenarios referencing touched nodes
5. Rewrite `graph.json`, `ownership.json`, `reverse-index.json`, `fingerprint.json`
6. If >20% of nodes affected → full re-analysis

---

## Quality Gates

Do not report completion until:
- `fingerprint.json` exists and matches current HEAD
- `graph.json` has ≥1 node
- ≥1 `nodes/*.json` exists
- ≥1 `scenarios/*.json` exists with all three views
- Server responds to `GET /graph`
- At least one scenario plays over WebSocket without error
