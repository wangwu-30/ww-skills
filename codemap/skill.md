---
name: codemap
version: 3.0.0
description: |
  Deep codebase analysis → single-page interactive architecture explorer.
  Evidence-driven: collects verifiable facts via an uncertainty-reduction loop
  (wide search → hypotheses → targeted verification → converge), never invents
  file:line references or architecture narratives. Outputs a single HTML file
  with drill-down graph, execution timeline, and bilingual (中/EN) toggle.
  Use when asked to "visualize this codebase", "architecture doc", "codemap",
  "analyze this project", or "document this repo".
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - AskUserQuestion
---

## Preamble

```bash
echo "CODEMAP SKILL LOADED"
_TARGET_DIR="${PWD}"
echo "TARGET: $_TARGET_DIR"
```

---

## The Core Loop (道)

This skill is an **uncertainty-reduction agent**, not a sequential pipeline.

```
while confidence < threshold:
    identify highest-uncertainty question
    choose cheapest tool that answers it
    execute → update fact store + confidence scores
    if budget exhausted → output with honest confidence markers
output verified model as HTML
```

Stop condition: all L0 nodes confidence ≥ 0.8 AND all L2 leaves verified OR budget exhausted.

**Never output a fact that did not come from a tool result.**
**Never invent file:line. Never invent edges. Never invent execution steps.**

---

## Phase 0 — Wide Search (道: 先广后深)

Goal: get enough signal to form the first hypotheses. Do NOT form conclusions yet.

Run these in parallel (one turn, multiple tool calls):

```
1. Glob("**", maxDepth=2)                    → directory skeleton
2. Glob manifests: package.json, Cargo.toml, go.mod, pyproject.toml, pom.xml
3. Bash: find . -name "*.ts" -o -name "*.py" -o -name "*.go" -o -name "*.rs" \
         | grep -v node_modules | grep -v vendor | wc -l   → file count
4. Bash: find . -type d | grep -v node_modules | grep -v .git \
         | grep -v vendor | head -40            → all directories
5. Glob entry points: **/main.ts, **/index.ts, **/app.ts, **/main.go,
                      **/main.rs, **/main.py, **/cli.ts, **/server.ts
6. Glob tests: **/*.test.ts, **/*.spec.ts, **/test_*.py,
               **/*_test.go, **/tests/**
```

**Tool detection** (run in same turn):
```bash
echo "const x: string = 'probe';" > /tmp/_codemap_probe.ts
ast-grep --pattern 'const $X: $T = $_' /tmp/_codemap_probe.ts 2>/dev/null \
  && echo "ASTGREP=ts_ok" || echo "ASTGREP=no"
which ctags 2>/dev/null && ctags --version 2>/dev/null | head -1 \
  && echo "CTAGS=ok" || echo "CTAGS=no"
rm -f /tmp/_codemap_probe.ts
```

**Scale detection**:
```
files < 50    → mode=micro,   budget=20 calls
files 50-300  → mode=standard, budget=40 calls
files > 300   → mode=large,   budget=55 calls, L1_depth_cap=3, L0_cap=6
```

**Taint list** — mark these patterns before any scoring:
```
tainted = [
  "**/index.ts", "**/index.js", "**/__init__.py",   # barrels
  "**/types.ts", "**/types.py", "**/schema.*",       # pure types
  "**/generated/**", "**/vendor/**", "**/.gen/**",   # generated
  "**/utils/**", "**/shared/**", "**/common/**",     # glue
  "**/*.config.*", "**/constants.*",                 # config
]
# Tainted files: fan-in score × 0.1 (not excluded, just deprioritized)
```

**After Phase 0, write the initial state block:**

```json
{
  "phase": 0,
  "mode": "standard",
  "budget_remaining": 40,
  "calls_used": 6,
  "scale": { "files": N, "dirs": N },
  "tools": { "astgrep": "ts_ok|no", "ctags": "ok|no" },
  "candidates": {
    "entry_points": [],
    "subsystem_dirs": [],
    "tainted": []
  },
  "hypotheses": [],
  "fact_store": {
    "nodes": {},
    "edges": [],
    "trace_steps": []
  },
  "confidence": {}
}
```

---

## Phase 1 — Form Hypotheses (法: 假设)

**Only after Phase 0.** Generate 2-3 candidate L0 partitions based on directory
structure + manifest content. These are falsifiable predictions, not conclusions.

Hypothesis format:
```json
{
  "id": "H1",
  "type": "layered|event-driven|plugin|flat|microservices|mixed",
  "l0_partition": ["src/cli", "src/team", "src/mcp", "src/state"],
  "predicted_signals": [
    "src/cli imports from src/team but not vice versa",
    "src/team imports from src/state",
    "no circular imports between top-level dirs"
  ],
  "confidence": 0.4
}
```

**Hypothesis types and their falsifying signals:**
```
layered:      circular cross-layer imports → falsify
event-driven: no event bus / no pub-sub pattern → falsify
plugin:       no registry/register() pattern → falsify
flat:         clear sub-directory ownership → falsify (it's actually layered)
microservices: shared code between entry points → falsify
```

Do NOT lock in a hypothesis yet. All hypotheses remain active until evidence
pushes one below 0.1 confidence.

---

## Phase 2 — Dependency Skeleton (法: 检验)

Goal: verify or falsify hypotheses using import evidence.
Choose tool based on availability:

**If ASTGREP=ts_ok** (TypeScript):
```bash
ast-grep --pattern 'import { $$ } from "$PATH"' src/ --json 2>/dev/null | \
  jq '[.[] | {file: .metaVariables.PATH, from: .range.start.path}]' | head -200
```

**If ASTGREP=no** (fallback Grep):
```bash
grep -r "^import\|^from\|require(" src/ \
  --include="*.ts" --include="*.js" --include="*.py" \
  -h | grep -v node_modules | sort | uniq -c | sort -rn | head -100
```

For each hypothesis, run ONE targeted grep to test its key predicted signal:
```
H1 "layered" → grep "from '../cli'" in src/team/ → should find nothing
H2 "event-driven" → grep "EventEmitter\|\.emit\|\.on(" → should find bus
```

**Fan-in scoring** (after import grep):
```
for each subsystem dir:
  raw_fan_in = count of files outside this dir that import from it
  taint_penalty = 0.1 if dir matches tainted patterns else 1.0
  score = raw_fan_in × taint_penalty
```

Sort subsystems by score. High score + NOT tainted = real hub.
High score + tainted = glue (deprioritize but do not delete).

**Update hypotheses** based on grep results:
```
signal found that hypothesis predicted → confidence += 0.2
signal found that hypothesis did NOT predict → confidence -= 0.3
predicted signal absent → confidence -= 0.15
```

**Update state block** with import matrix and hypothesis scores.

---

## Phase 3 — Candidate Hierarchy (法: 修正)

Goal: build L0/L1/L2 candidates. Only from verified facts.

**L0 assignment** (deterministic, no invention):
```
L0 candidates = subsystem dirs with score > 0 AND not fully tainted
Sort by score descending
Assign dag layers by topological sort of import direction:
  no incoming cross-L0 imports → layer 0 (entry)
  imports from layer 0 only → layer 1
  imported by many → layer N (infrastructure)
Cap at mode-dependent limit (standard=8, large=6)
```

**L1 assignment** (per L0, max 4 files):
```
Priority 1: file with highest export count (grep "^export" | wc -l)
Priority 2: file with highest external fan-in (from Phase 2)
Priority 3: largest file by line count (not tainted)
Priority 4: file referenced in test describes (if tests found)
Exclude: index/barrel files, generated files, pure type files
```

**L2 candidates** (per L1, max 4 symbols — CANDIDATES ONLY, not verified yet):
```
grep "^export (async function|function|class|interface|type|const)" {file}
  → list of exported symbols with line numbers
Filter: keep only symbols imported by 2+ other files (from Phase 2 grep)
These are CANDIDATES. Mark confidence=0 until Phase 5 verifies them.
```

**Read hub files** (targeted, not whole files):
```
For each L1 hub file:
  Read lines 1-60 (imports reveal dependencies)
  Grep "^export" with -n flag → get line numbers
  Read ±10 lines around top 2 exported functions → get real signatures
```

---

## Phase 4 — Trace Derivation (检验: 执行链)

Goal: one verified 10-13 step execution trace. Derive, do not invent.

**Waterfall strategy** (try in order, stop at first success):

```
Level 1 — E2E/Integration tests:
  Glob "**/e2e/**", "**/*.e2e.*", "**/integration/**"
  Read largest test file → find describe() blocks
  Follow the deepest call chain in the test
  Confidence: high (test is executable documentation)

Level 2 — Entry point trace:
  Read entry point file (from Phase 0)
  Find route/command registration
  Pick ONE concrete operation (most lines = most interesting)
  Follow imports 4-6 levels deep with targeted Reads
  Confidence: medium

Level 3 — Largest non-test file:
  Find largest file by wc -l that is not tainted and not test
  Read first 80 lines → find main exported function
  Trace its callees with 3 targeted Reads
  Confidence: low

Level 4 — Fallback:
  Use L0→L1 import edges as proxy for execution order
  Steps = subsystems in topological order
  Mark all steps: trace_confidence="inferred"
  Show only 5-7 steps, not 13
```

**Trace step format:**
```json
{
  "step": 3,
  "title": { "zh": "Worker 读 inbox，发送 ACK", "en": "Worker reads inbox, sends ACK" },
  "actor": "codex",
  "nodes": ["codex", "state"],
  "edges": ["codex->state"],
  "file": "src/team/worker-bootstrap.ts",
  "line": 639,
  "confidence": "verified|inferred",
  "payload": "actual command or JSON from Read result"
}
```

Only steps with `confidence=verified` get real code payloads.
Steps with `confidence=inferred` get description-only payloads.

---

## Phase 5 — Verify + Merge (收敛)

Goal: confirm every L2 leaf. Drop or downgrade unconfirmed ones.
**Never silently drop. Always report confidence level.**

**Verification per L2 leaf** (one Grep per leaf, batch up to 10 per call):
```bash
grep -n "export.*{symbolName}" {claimed_file}
```

Result classification:
```
grep finds exact match at claimed line ±3  → verified, confidence=1.0
grep finds symbol but different line       → verified, update line number
grep finds nothing                         → downgrade to candidate, confidence=0.3
```

**Edge verification** (one Grep per edge):
```bash
grep -r "from '.*{target_subsystem}" {source_subsystem}/ --include="*.ts" -l
```
Edge without at least one witness file → mark as `inferred`, show as dashed.

**Merge rules** (apply in order, no exceptions):
```
M1: Only emit L0 nodes whose directory was confirmed to exist in Phase 0
M2: Only emit L1 nodes whose file path was confirmed by Read or Grep
M3: Only emit L2 leaves with confidence ≥ 0.3
    confidence=1.0 → show with green file:line badge
    confidence=0.3 → show with "~" prefix, grey badge, "unverified" tooltip
M4: Only emit edges with at least one witness import statement
M5: Trace steps with confidence=inferred → description only, no code snippet
M6: Report coverage: "Verified N/M candidate leaves"
```

**Final state block** before generating HTML:
```json
{
  "model": {
    "nodes": { ... },        // only verified
    "edges": [ ... ],        // only witnessed
    "details": { ... },      // L1/L2 with confidence tags
    "trace": [ ... ],        // steps with confidence field
    "coverage": {
      "l2_verified": N,
      "l2_candidate": N,
      "l2_dropped": N,
      "edges_verified": N,
      "edges_inferred": N
    }
  }
}
```

---

## Phase 6 — Generate HTML

Write the single HTML file in 5-6 chunks via `cat >` / `cat >>`.
**Every chunk must complete syntactically** — never split mid-string or mid-function.

### Layout (two-panel, state-machine driven)

```
#app (flex column, 100vh)
  #topbar (44px): logo | breadcrumb | lang-btn
  #stage (flex:1, overflow:hidden)
    #arch-view (full width by default)
      #view-toggle (in-panel: Architecture | Timeline buttons)
      #graph-panel (flex:1)
        #graph-svg (viewBox="0 0 860 440", responsive)
        #tl-strip (timeline scrubber + play/step controls)
      #detail-panel (width:0 → 480px with .open, slides in)
    #swim-view (hidden by default, full width when active)
```

**Three UI states** (no tabs):
```
State 1: Overview     — graph full width, no detail panel
State 2: Node selected — graph + detail panel (480px)
State 3: Timeline view — swimlane full width
```

State transitions:
```
click structural node (has children) → drillInto() → zoom animation → State 1 at new level
click leaf node (no children)        → openDetail() → State 2
click view-toggle "Timeline"         → setView('swim') → State 3
click breadcrumb                     → pop navStack → State 1 at parent level
close detail panel                   → State 1
```

### Node data model

```js
{
  id: string,
  label: { zh, en },
  color: string,
  layer: number,          // 0=top, computed from topological sort
  col: number,            // column within layer
  tip: { zh, en },
  confidence: number,     // 0.3–1.0 from Phase 5

  // Structural node (has sub-graph):
  children: Node[] | null,
  childEdges: Edge[] | null,

  // Leaf or hybrid node (has code content):
  content: {
    desc: { zh, en },
    subs: [{
      id, title, file, line,
      confidence: "verified" | "candidate",
      desc: { zh, en },
      code: string         // only if confidence=verified
    }]
  } | null
}
```

### Layout algorithm (responsive, no hardcoded positions)

```js
function computePositions(nodes, svgW, svgH) {
  const NW = 130, NH = 44;
  const layers = topoSort(nodes, edges);
  const maxLayer = Math.max(...Object.values(layers));
  const layerH = svgH / (maxLayer + 2);

  // Group nodes by layer, sort by col within layer
  // x = slot * (idx+1), y = layerH * (layer+1)
  // Tainted/low-confidence nodes rendered with reduced opacity
}
```

### Zoom animation (viewBox interpolation, RAF)

```js
function drillInto(nodeId) {
  // Phase 1: zoom into clicked node bbox (250ms, ease-in-out)
  // Phase 2: swap content (1 frame, invisible)
  // Phase 3: zoom out to full sub-graph (300ms)
  // Uses requestAnimationFrame lerp, NOT CSS transition on viewBox
}
```

### Confidence visualization

```css
/* Verified nodes: normal */
.node-verified rect { stroke-width: 1.5; }

/* Candidate nodes: dashed border, reduced opacity */
.node-candidate rect { stroke-dasharray: 4 2; opacity: 0.7; }

/* Inferred edges: dashed line */
.edge-inferred { stroke-dasharray: 4 3; opacity: 0.5; }

/* Coverage badge in topbar */
#coverage-badge { font-size: 10px; color: var(--text3); }
```

### Design tokens

```css
--bg:#0d1117; --bg2:#161b22; --bg3:#21262d; --border:#30363d;
--text:#e6edf3; --text2:#8b949e; --text3:#6e7681;
--accent:#58a6ff; --green:#3fb950; --yellow:#d29922; --red:#f85149;
--purple:#bc8cff; --orange:#e3b341; --pink:#f778ba; --teal:#39d3b7;
```

### Bilingual support

```css
[data-lang="zh"] .en { display: none !important; }
[data-lang="en"] .zh { display: none !important; }
```

Default: infer from user's message language.
All user-visible text needs `<span class="zh">` + `<span class="en">`.
Code blocks, file paths, variable names: English only.

### Swimlane (lazy-built, class-toggle only on update)

Built once on first view switch. `refreshSwimHighlights()` only toggles
CSS classes — never rebuilds the table DOM.

### State machine (single STATE object)

```js
const STATE = {
  navStack: [],              // [{nodes, edges, label}] — shallow copy on push
  currentNodes: ROOT_NODES,
  currentEdges: ROOT_EDGES,
  selectedNodeId: null,
  flowStep: -1,
  flowPlaying: false,
  flowTimer: null,
  activeTab: 'arch',
  flowActiveNodes: new Set(),
  flowActiveEdges: new Set(),
  swimBuilt: false,
};
// flowGoTo() is the ONLY function that writes STATE.flowStep
```

---

## Chunk Strategy

Write in exactly 5 chunks to avoid content limits:

```
Chunk 1: DOCTYPE + <head> + all CSS + HTML body skeleton (no closing tags)
Chunk 2: ROOT_NODES + ROOT_EDGES (with children arrays for structural nodes)
Chunk 3: DETAILS object + FLOW_STEPS + SWIM_ACTORS + SWIM_MAP
Chunk 4: All JS functions (renderGraph, drillInto, animVB, selectNode,
          openDetail, closeDetail, buildSwimLane, refreshSwimHighlights,
          setView, updateBreadcrumb, goHome, bcClick)
Chunk 5: flowGoTo, flowTogglePlay, flowStep, tlClick, toggleLang,
          DOMContentLoaded init + closing </script></body></html>
```

Each chunk: `cat > index.html << 'EOF'` for chunk 1,
`cat >> index.html << 'EOF'` for chunks 2-5.

---

## Quality Gates (run before opening browser)

```bash
# 1. JS syntax check
node -e "
const html = require('fs').readFileSync('index.html','utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
scripts.forEach((s,i) => { try { new Function(s); console.log('Script',i+1,'OK'); }
  catch(e) { console.error('Script',i+1,'FAIL:',e.message); process.exit(1); } });
"

# 2. Verify no orphaned HTML (no stray divs outside expected structure)
grep -c 'id="tabbar"' index.html && echo "FAIL: old tabbar present" || echo "OK: no tabbar"

# 3. Coverage report
node -e "
const html = require('fs').readFileSync('index.html','utf8');
const verified = (html.match(/confidence.*verified/g)||[]).length;
const candidate = (html.match(/confidence.*candidate/g)||[]).length;
console.log('Coverage: verified=' + verified + ' candidate=' + candidate);
"

# 4. Open
wc -l index.html && open index.html
```

---

## After Opening

Ask: **"哪个节点需要再深入？"** / **"Which node needs more depth?"**

To deepen a node: add more entries to `DETAILS[nodeId].subs` or add
`children` + `childEdges` to make it structural (drill-down instead of panel).

To add a new graph level: set `node.children = [...]` and `node.childEdges = [...]`.
The renderer handles arbitrary depth — no code changes needed.

---

## Few-Shot Example (oh-my-codex)

This example shows the three judgment-heavy decision points. Use it as a template.

### Decision Point 1: Hypothesis Generation

**Input** (after Phase 0 — directory skeleton only):
```
top-level dirs: src/, crates/, prompts/, skills/, agents/
src/ subdirs: cli/, team/, pipeline/, hooks/, notifications/,
              hud/, mcp/, config/, autoresearch/, state/,
              openclaw/, utils/, modes/, agents/, ralph/
manifests: package.json (bin: omx), Cargo.toml (workspace)
entry points found: src/cli/omx.ts, src/cli/index.ts
file count: 435 TS files, 33 Rust files
```

**Output** (correct hypothesis generation):
```json
[
  {
    "id": "H1",
    "type": "layered",
    "l0_partition": ["src/cli", "src/team", "src/mcp", "src/state", "crates/"],
    "predicted_signals": [
      "src/cli imports from src/team but src/team does NOT import from src/cli",
      "src/mcp imports from src/state",
      "crates/ has no TypeScript imports"
    ],
    "confidence": 0.5
  },
  {
    "id": "H2",
    "type": "mixed",
    "l0_partition": ["src/cli", "src/team", "src/mcp", "src/state",
                     "src/ralph", "src/pipeline", "crates/"],
    "predicted_signals": [
      "src/team and src/ralph are parallel modes, both import from src/state",
      "src/pipeline orchestrates both src/team and src/ralph"
    ],
    "confidence": 0.4
  }
]
```

**Why H1 and H2, not event-driven or plugin?**
- No event bus manifest (no `eventemitter2`, `rxjs`, `kafka-node` in package.json)
- No `register()`/`plugin.add()` pattern visible in top-level dirs
- Two separate mode dirs (team/, ralph/) suggest parallel execution paths, not plugins
- Rust workspace suggests performance-critical subsystem, not plugin extensions

---

### Decision Point 2: Confidence Update

**Input** (Phase 2 grep result):
```bash
$ grep -r "from '../cli'" src/team/ --include="*.ts" -l
(no output)

$ grep -r "from '../team'" src/cli/ --include="*.ts" -l
src/cli/index.ts
src/cli/team-runner.ts
```

**Output** (correct confidence update):
```
H1 "layered": predicted "cli does NOT import team" → WRONG (cli imports team)
  → BUT also predicted "team does NOT import cli" → CORRECT
  → Net: confidence 0.5 + 0.2 (one signal confirmed) - 0.15 (one absent) = 0.55

H2 "mixed": predicted "team and ralph are parallel modes" → still unverified
  → No change yet: confidence stays 0.4

Next highest-uncertainty question:
  "Does src/pipeline import from both src/team AND src/ralph?"
  → This would confirm H2's key differentiator from H1
  → Cheapest tool: grep -r "from '../team'\|from '../ralph'" src/pipeline/
```

**Why this update, not a bigger jump?**
- One confirmed signal in a 3-signal hypothesis = partial evidence, not proof
- The absent signal (cli→team direction) is the more important one for "layered"
- Do not lock in until confidence > 0.8

---

### Decision Point 3: Next Search Decision

**Input** (current state after Phase 2):
```
H1 confidence: 0.55
H2 confidence: 0.4
Budget remaining: 28 calls
Highest uncertainty: are src/team and src/ralph truly parallel modes?
Unverified L2 candidates: 12 symbols across 4 hub files
Trace: not started
```

**Output** (correct next search decision):
```
Priority 1 (hypothesis resolution, 1 call):
  grep -r "from '../team'\|from '../ralph'" src/pipeline/ --include="*.ts"
  → If both found: H2 confidence +0.3 → likely winner
  → If only team: H1 confidence +0.2, H2 confidence -0.2
  Cost: 1 call. Value: resolves main hypothesis ambiguity.

Priority 2 (L2 verification, 1 call for 8 symbols):
  grep -n "export.*createTeamState\|export.*transitionPhase\|
           export.*startMode\|export.*runPipeline\|
           export.*normalizeRalphPhase\|export.*stateWrite\|
           export.*isPaneIdle\|export.*buildWorkerProcessLaunchSpec" src/
  → Verifies 8 L2 candidates in one grep
  Cost: 1 call. Value: confirms 8 file:line references.

Priority 3 (trace, 2 calls):
  Glob src/**/*.test.ts → find e2e tests
  Read largest test → extract call chain
  Cost: 2 calls. Value: enables execution timeline.

Decision: run Priority 1 and Priority 2 in parallel (same turn).
Skip Priority 3 until hypothesis is resolved (don't waste reads on wrong framework).
```

---

### Taint Example (what NOT to do)

**Wrong**: ranking `src/utils/paths.ts` as L1 because it has fan-in=47
```
src/utils/paths.ts is in tainted pattern "**/utils/**"
fan-in score = 47 × 0.1 = 4.7
→ deprioritized, not a hub candidate
```

**Wrong**: treating `src/team/index.ts` as hub because it has fan-in=22
```
src/team/index.ts matches "**/index.ts" taint pattern
fan-in score = 22 × 0.1 = 2.2
Real hub: src/team/orchestrator.ts (fan-in=8, not tainted, score=8.0)
```

**Correct**: the real L1 hub for src/team/ is:
```
src/team/orchestrator.ts  → exports createTeamState, transitionPhase, TRANSITIONS
src/team/state.ts         → largest file (1400 LOC), exports TeamState operations
src/team/worker-bootstrap.ts → exports writeTeamWorkerInstructionsFile
```
All three verified by: `grep -n "^export" src/team/orchestrator.ts`

---

### Coverage Report Example

```
Codemap coverage for oh-my-codex:
  L0 nodes:  6 verified (confidence=1.0)
  L1 nodes:  18 verified, 2 candidate (confidence=0.3)
  L2 leaves: 34 verified, 8 candidate, 4 dropped
  Edges:     14 verified (with witness), 2 inferred (dashed)
  Trace:     13 steps — 11 verified, 2 inferred
```

This is what the `#coverage-badge` in the topbar should show.

---

## Output Demo (oh-my-codex — key data structures)

The generated HTML must match this style exactly. These are real excerpts from
a working output. Use them as the canonical reference for data structure shape,
naming conventions, and code snippet style.

### ROOT_NODES example (structural node with children)

```js
const ROOT_NODES = {
  leader: {
    id: 'leader',
    label: { zh: 'OMX Leader', en: 'OMX Leader' },
    color: '#58a6ff',
    layer: 0, col: 1,
    confidence: 1.0,
    tip: {
      zh: 'CLI 入口 + 编排核心，驱动所有模式和流水线',
      en: 'CLI entry + orchestration core, drives all modes and pipelines'
    },
    // Structural: click → zoom drill-down
    children: LEADER_CHILDREN,
    childEdges: LEADER_EDGES,
    // Also has content for detail panel (hybrid node)
    content: null   // set to detail object if hybrid
  },
  state: {
    id: 'state',
    label: { zh: 'State Files', en: 'State Files' },
    color: '#3fb950',
    layer: 2, col: 0,
    confidence: 1.0,
    tip: { zh: '.omx/state/*.json，原子写入', en: '.omx/state/*.json, atomic write' },
    // Leaf: click → detail panel only
    children: null,
    childEdges: null,
    content: null   // populated in DETAILS object
  },
};
```

### ROOT_EDGES example (with witness)

```js
const ROOT_EDGES = [
  {
    from: 'leader', to: 'codex',
    label: { zh: 'spawn+注入', en: 'spawn+inject' },
    style: 'solid',    // solid = synchronous/primary
    confidence: 1.0,   // has witness
    witness: 'src/team/runtime.ts imports spawn from child_process'
  },
  {
    from: 'mcp', to: 'state',
    label: { zh: '读写', en: 'read/write' },
    style: 'dash',     // dash = async/secondary
    confidence: 1.0,
    witness: 'src/mcp/state-server.ts imports stateWrite from state/operations'
  },
];
```

### DETAILS example (leaf node content with confidence)

```js
const DETAILS = {
  state: {
    desc: {
      zh: '所有协调状态的真相来源。JSON 文件，原子写入（temp+rename），按路径 Promise 队列防并发损坏。',
      en: 'Single source of truth. JSON files, atomic write (temp+rename), per-path Promise queue.'
    },
    subs: [
      {
        id: 'atomic',
        title: '原子写入',
        file: 'src/state/operations.ts',
        line: 45,
        confidence: 'verified',   // ← grep confirmed this symbol at this line
        desc: { zh: 'Promise 链 + temp rename', en: 'Promise chain + temp rename' },
        // Code only included when confidence=verified
        code: `<span class="ck">const</span> writeQueues =
  <span class="ck">new</span> Map&lt;<span class="co">string</span>, Promise&lt;<span class="co">void</span>&gt;&gt;();
<span class="ck">async function</span> <span class="cp">withStateWriteLock</span>(path, fn) {
  <span class="ck">const</span> prev = writeQueues.<span class="cp">get</span>(path) ?? Promise.<span class="cp">resolve</span>();
  <span class="ck">const</span> next = prev.<span class="cp">then</span>(() => <span class="cp">fn</span>());
  writeQueues.<span class="cp">set</span>(path, next); <span class="ck">await</span> next;
}
<span class="cc">// write: JSON → tmpFile → rename(tmp, final)</span>`
      },
      {
        id: 'layout',
        title: '文件布局',
        file: '.omx/state/',
        line: null,
        confidence: 'candidate',  // ← directory exists but no specific line verified
        desc: { zh: '磁盘目录结构', en: 'Disk directory structure' },
        // No code field when confidence=candidate — show description only
      },
    ]
  },
};
```

### FLOW_STEPS example (with confidence field)

```js
const STEPS = [
  {
    title: { zh: '用户运行 omx team 3:executor', en: 'User runs omx team 3:executor' },
    actor: 'leader',
    nodes: ['leader'],
    edges: [],
    confidence: 'verified',   // traced from src/cli/index.ts directly
    file: 'src/cli/index.ts',
    line: 1,
    payload: `<span class="pk">$</span> omx team <span class="pn">3</span>:executor
<span class="cc">// CLI 解析 (src/cli/index.ts):</span>
workerCount = <span class="pn">3</span>
agentType   = <span class="pss">"executor"</span>`
  },
  {
    title: { zh: 'Worker 执行任务（并行）', en: 'Workers execute tasks (parallel)' },
    actor: 'codex',
    nodes: ['codex'],
    edges: [],
    confidence: 'inferred',   // inferred from test, not directly read
    file: null,
    line: null,
    // No code payload when inferred — description only
    payload: `<span class="cc">// 3 个 worker 在独立 git worktree 并行工作</span>
<span class="cc">// 来源: 从集成测试推断，未直接验证</span>`
  },
];
```

### Confidence CSS (must be in the generated HTML)

```css
/* Verified nodes: normal appearance */
.node-verified rect { opacity: 1; }

/* Candidate nodes: dashed border, slightly dimmed */
.node-candidate rect {
  stroke-dasharray: 4 2;
  opacity: 0.75;
}

/* Inferred edges: dashed, dimmed */
.edge-inferred {
  stroke-dasharray: 4 3;
  opacity: 0.45;
}

/* Coverage badge */
#coverage-badge {
  font-size: 10px;
  color: var(--text3);
  padding: 2px 8px;
  background: var(--bg3);
  border-radius: 10px;
  border: 1px solid var(--border);
}
```

### Coverage badge HTML (in topbar)

```html
<div id="topbar">
  <div class="logo">project-<em>name</em></div>
  <div id="breadcrumb"></div>
  <!-- Coverage badge: shows verified/candidate/dropped counts -->
  <div id="coverage-badge" title="L2 leaves: 34 verified, 8 candidate, 4 dropped">
    ✓ 34 · ~ 8
  </div>
  <button id="lang-btn" onclick="toggleLang()">EN →</button>
</div>
```

### Syntax highlighting spans (use exactly these class names)

```
.ck  → keyword      (#ff7b72)   export, const, function, async, return
.cp  → function     (#d2a8ff)   function names being called/defined
.cs  → string       (#a5d6ff)   "string literals"
.cc  → comment      (text3, italic)  // comments
.cn  → number       (#79c0ff)   42, 3.14
.co  → type/class   (#ffa657)   TypeScript types, class names
.cg  → green        (#3fb950)   true, success values

Payload panel spans (different prefix to avoid CSS collision):
.ph  → purple       (#d2a8ff)
.pk  → keyword red  (#ff7b72)
.pss → string blue  (#a5d6ff)
.pn  → number       (#79c0ff)
.pg  → green        (#3fb950)
```

### What the final output looks like (structure summary)

```
index.html (~60-80KB, 1200-1500 lines)
├── <head>: CSS (~250 lines)
├── <body>: HTML skeleton (~100 lines)
│   ├── #topbar: logo + breadcrumb + coverage-badge + lang-btn
│   ├── #stage
│   │   ├── #arch-view: #graph-panel + #detail-panel
│   │   └── #swim-view: #swim-scroll + #swim-payload
├── <script> chunk 2: ROOT_NODES + ROOT_EDGES (~80 lines)
├── <script> chunk 3: DETAILS + FLOW_STEPS + SWIM_ACTORS + SWIM_MAP (~300 lines)
├── <script> chunk 4: rendering + interaction functions (~350 lines)
└── <script> chunk 5: animation + lang + init (~100 lines)
```

The data section (chunks 2-3) is the largest and most important.
Every node, edge, detail sub, and trace step must trace back to a tool result.
