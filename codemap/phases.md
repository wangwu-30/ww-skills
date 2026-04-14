# Codemap — Phase Rules

## Phase 0 — Wide Search

Goal: enough signal to form first hypotheses. Do NOT form conclusions yet.

Run in parallel (one turn):
```
Glob("**", maxDepth=2)
Glob manifests: package.json, Cargo.toml, go.mod, pyproject.toml, pom.xml
Bash: find . -name "*.ts" -o -name "*.py" -o -name "*.go" -o -name "*.rs" \
      | grep -v node_modules | grep -v vendor | wc -l
Glob entry points: **/main.ts, **/index.ts, **/app.ts, **/main.go,
                   **/main.rs, **/main.py, **/cli.ts, **/server.ts
Glob tests: **/*.test.ts, **/*.spec.ts, **/test_*.py, **/*_test.go
```

Tool detection (same turn):
```bash
echo "const x: string = 'probe';" > /tmp/_probe.ts
ast-grep --pattern 'const $X: $T = $_' /tmp/_probe.ts 2>/dev/null \
  && echo "ASTGREP=ts_ok" || echo "ASTGREP=no"
which ctags 2>/dev/null && ctags --version 2>/dev/null | head -1 \
  && echo "CTAGS=ok" || echo "CTAGS=no"
rm -f /tmp/_probe.ts
```

Output: update state block with scale, tools, entry_points, subsystem_dirs.
→ **Now read `./few-shot.md` before Phase 1.**

---

## Phase 1 — Form Hypotheses

Only after Phase 0. Generate 2–3 candidate L0 partitions.

Hypothesis format:
```json
{
  "id": "H1",
  "type": "layered|event-driven|plugin|flat|microservices|mixed",
  "l0_partition": ["src/cli", "src/team", "src/mcp", "src/state"],
  "predicted_signals": [
    "src/cli imports from src/team but not vice versa",
    "src/team imports from src/state"
  ],
  "confidence": 0.4
}
```

Falsifying signals by type:
```
layered:      circular cross-layer imports → falsify
event-driven: no event bus / pub-sub pattern → falsify
plugin:       no registry/register() pattern → falsify
flat:         clear sub-directory ownership exists → falsify
microservices: shared code between entry points → falsify
```

Do NOT lock in a hypothesis. All remain active until evidence pushes one < 0.1.

---

## Phase 2 — Dependency Skeleton

Goal: verify/falsify hypotheses via import evidence.

**If ASTGREP=ts_ok:**
```bash
ast-grep --pattern 'import { $$ } from "$PATH"' src/ --json 2>/dev/null \
  | jq '[.[] | {from: .range.start.path, to: .metaVariables.PATH}]' | head -200
```

**Fallback (Grep):**
```bash
grep -r "^import\|^from\|require(" src/ \
  --include="*.ts" --include="*.py" -h \
  | grep -v node_modules | sort | uniq -c | sort -rn | head -100
```

For each hypothesis, run ONE targeted grep to test its key predicted signal.

Fan-in scoring:
```
raw_fan_in   = files outside this dir that import from it
taint_factor = 0.1 if dir matches taint list else 1.0
score        = raw_fan_in × taint_factor
```

Confidence update rules:
```
signal found that hypothesis predicted    → confidence += 0.2
signal found that hypothesis did NOT predict → confidence -= 0.3
predicted signal absent                   → confidence -= 0.15
```

---

## Phase 3 — Candidate Hierarchy

L0 assignment (deterministic):
```
candidates = subsystem dirs with score > 0 AND not fully tainted
sort by score descending
assign dag layers by topological sort of import direction:
  no incoming cross-L0 imports → layer 0 (entry)
  imports layer-0 only         → layer 1
  imported by many             → layer N (infrastructure)
cap: standard=8, large=6
```

L1 assignment (per L0, max 4 files):
```
Priority 1: highest export count (grep "^export" | wc -l)
Priority 2: highest external fan-in
Priority 3: largest non-tainted file by line count
Priority 4: file referenced in test describes
Exclude: index/barrel, generated, pure type files
```

L2 candidates (per L1, max 4 — CANDIDATES ONLY until Phase 5):
```bash
grep -n "^export (async function|function|class|interface|type|const)" {file}
```
Keep only symbols imported by 2+ other files (from Phase 2).
Mark all as `confidence: "candidate"` until verified.

Read hub files (targeted):
```
Read lines 1–60 (imports)
Grep "^export" -n → get line numbers
Read ±10 lines around top 2 exported functions → real signatures
```

---

## Phase 4 — Trace Derivation

Waterfall — try in order, stop at first success:

**Level 1 — E2E/Integration tests (confidence: verified)**
```
Glob "**/e2e/**", "**/*.e2e.*", "**/integration/**"
Read largest test → find describe() blocks
Follow deepest call chain
```

**Level 2 — Entry point trace (confidence: medium)**
```
Read entry point file
Find route/command registration
Pick ONE concrete operation
Follow imports 4–6 levels with targeted Reads
```

**Level 3 — Largest non-test file (confidence: low)**
```
Find largest non-tainted, non-test file
Read first 80 lines → find main exported function
Trace callees with 3 Reads
```

**Level 4 — Fallback (confidence: inferred)**
```
Use L0→L1 import edges as proxy for execution order
Show only 5–7 steps, not 13
Mark all steps: confidence="inferred"
```

Trace step format:
```json
{
  "step": 3,
  "title": { "zh": "...", "en": "..." },
  "actor": "codex",
  "nodes": ["codex", "state"],
  "edges": ["codex->state"],
  "file": "src/team/worker-bootstrap.ts",
  "line": 639,
  "confidence": "verified|inferred",
  "payload": "actual command or JSON — only if verified"
}
```

---

## Phase 5 — Verify + Merge

Verify each L2 candidate (batch up to 10 per grep call):
```bash
grep -n "export.*{symbolName}" {claimed_file}
```

Classification:
```
exact match at claimed line ±3  → verified, confidence=1.0
found but different line        → verified, update line
not found                       → candidate, confidence=0.3
```

Edge verification:
```bash
grep -r "from '.*{target_subsystem}" {source_dir}/ -l
```
No witness → mark `inferred`, render as dashed.

Merge rules (no exceptions):
```
M1: Only emit L0 nodes whose directory confirmed in Phase 0
M2: Only emit L1 nodes whose file confirmed by Read or Grep
M3: Only emit L2 leaves with confidence ≥ 0.3
    1.0 → green file:line badge
    0.3 → "~" prefix, grey badge, "unverified" tooltip
M4: Only emit edges with ≥1 witness import statement
M5: Trace steps with confidence=inferred → description only, no code
M6: Report coverage in state block
```

Never silently drop. Always report confidence level.

---

## Phase 6 — Generate HTML

**Read `./output-demo.md` now** for exact data structure shape and style.

Write in 5 chunks via `cat >` / `cat >>`. Each chunk must be syntactically complete.

```
Chunk 1: DOCTYPE + <head> + all CSS + HTML skeleton (~250 lines)
Chunk 2: ROOT_NODES + ROOT_EDGES (~80 lines)
Chunk 3: DETAILS + FLOW_STEPS + SWIM_ACTORS + SWIM_MAP (~300 lines)
Chunk 4: All JS rendering + interaction functions (~350 lines)
Chunk 5: Animation + lang toggle + init + closing tags (~100 lines)
```

### Layout (state-machine, no tabs)

```
#app (flex column, 100vh)
  #topbar: logo | breadcrumb | #coverage-badge | lang-btn
  #stage
    #arch-view (full width by default)
      #view-toggle (in-panel buttons: Architecture | Timeline)
      #graph-panel: #graph-svg + #tl-strip
      #detail-panel (width:0 → 480px with .open)
    #swim-view (hidden, full width when active)
```

Three states (no tabs):
```
Overview:       graph full width, no detail
Node selected:  graph + detail panel (480px)
Timeline:       swimlane full width
```

### Node data model
```js
{
  id, label:{zh,en}, color, layer, col, confidence,
  tip:{zh,en},
  children: Node[] | null,    // structural → drill-down
  childEdges: Edge[] | null,
  content: { desc:{zh,en}, subs:[{id,title,file,line,confidence,desc,code}] } | null
}
```

### Layout algorithm (responsive)
```js
function computePositions(nodes, edges, svgW, svgH) {
  // topoSort(nodes, edges) → assign layers
  // group by layer, sort by col
  // x = svgW / (count+1) * (idx+1)
  // y = svgH / (maxLayer+2) * (layer+1)
}
```

### Zoom (viewBox RAF, 3-phase)
```js
function drillInto(nodeId) {
  // Phase 1: animVB → zoom into node bbox (250ms)
  // Phase 2: swap content (1 frame)
  // Phase 3: animVB → zoom out to full sub-graph (300ms)
  // Uses requestAnimationFrame lerp, NOT CSS transition on viewBox
}
```

### State machine
```js
const STATE = {
  navStack: [],           // shallow copy on push
  currentNodes, currentEdges,
  selectedNodeId: null,
  flowStep: -1,           // flowGoTo() is the ONLY writer
  flowPlaying: false, flowTimer: null,
  activeTab: 'arch',
  flowActiveNodes: new Set(), flowActiveEdges: new Set(),
  swimBuilt: false,
};
```

### Design tokens
```css
--bg:#0d1117; --bg2:#161b22; --bg3:#21262d; --border:#30363d;
--text:#e6edf3; --text2:#8b949e; --text3:#6e7681;
--accent:#58a6ff; --green:#3fb950; --yellow:#d29922; --red:#f85149;
--purple:#bc8cff; --orange:#e3b341; --pink:#f778ba; --teal:#39d3b7;
```

### Bilingual
```css
[data-lang="zh"] .en { display:none!important; }
[data-lang="en"] .zh { display:none!important; }
```
Default: infer from user's message language.
Code blocks, file paths, variable names: English only.

### Confidence CSS
```css
.node-candidate rect { stroke-dasharray:4 2; opacity:0.75; }
.edge-inferred { stroke-dasharray:4 3; opacity:0.45; }
#coverage-badge { font-size:10px; color:var(--text3);
  padding:2px 8px; background:var(--bg3);
  border-radius:10px; border:1px solid var(--border); }
```
