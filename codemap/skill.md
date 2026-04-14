---
name: codemap
version: 3.1.0
description: |
  Deep codebase analysis → single-page interactive architecture explorer.
  Evidence-driven: uncertainty-reduction loop (wide search → hypotheses →
  targeted verification → converge). Never invents file:line references.
  Outputs single HTML with drill-down graph, execution timeline, bilingual toggle.
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
echo "CODEMAP v3.1.0"
_TARGET_DIR="${PWD}"
echo "TARGET: $_TARGET_DIR"
```

---

## The Core Loop (道)

This skill is an **uncertainty-reduction agent**.

```
while min_confidence(all_nodes) < 0.8 AND budget_remaining > 0:
    question = highest_uncertainty_question(fact_store)
    tool     = cheapest_tool_that_answers(question)
    result   = execute(tool)
    update(fact_store, confidence_scores, hypotheses)

output verified model as HTML
```

**Two absolute rules:**
1. Never output a fact that did not come from a tool result
2. Never invent file:line — if unverified, mark `confidence: "candidate"` or drop

---

## Phases Overview

Read the detailed phase rules only when entering that phase:

| Phase | When to read | File |
|-------|-------------|------|
| 0 — Wide Search | Start | `./phases.md` → `## Phase 0` |
| 1 — Hypotheses | After Phase 0 | `./phases.md` → `## Phase 1` |
| 2 — Dependency Skeleton | After Phase 1 | `./phases.md` → `## Phase 2` |
| 3 — Candidate Hierarchy | After Phase 2 | `./phases.md` → `## Phase 3` |
| 4 — Trace Derivation | After Phase 3 | `./phases.md` → `## Phase 4` |
| 5 — Verify + Merge | After Phase 4 | `./phases.md` → `## Phase 5` |
| 6 — Generate HTML | After Phase 5 | `./phases.md` → `## Phase 6` |

**Before Phase 1** (hypothesis generation), read `./few-shot.md` — it shows
exactly how to generate hypotheses and update confidence from grep results.

**Before Phase 6** (HTML generation), read `./output-demo.md` — it shows
the exact data structure shape, naming, and code snippet style to match.

---

## State Block (carry between phases)

Maintain this JSON in your context. Update after every tool call.

```json
{
  "phase": 0,
  "mode": "micro|standard|large",
  "budget_remaining": 40,
  "calls_used": 0,
  "tools": { "astgrep": "ts_ok|no", "ctags": "ok|no" },
  "tainted": [],
  "hypotheses": [],
  "fact_store": {
    "entry_points": [],
    "subsystem_dirs": [],
    "import_matrix": {},
    "hub_files": {},
    "l2_candidates": []
  },
  "confidence": {},
  "coverage": {
    "l2_verified": 0, "l2_candidate": 0, "l2_dropped": 0,
    "edges_verified": 0, "edges_inferred": 0
  }
}
```

Scale → budget:
- files < 50 → `micro`, budget=20
- files 50–300 → `standard`, budget=40
- files > 300 → `large`, budget=55, L1_depth_cap=3, L0_cap=6

---

## Taint List (apply before any scoring)

These patterns inflate fan-in without architectural meaning.
**Score = raw_fan_in × 0.1** (deprioritize, do not exclude):

```
**/index.ts  **/index.js  **/__init__.py   ← barrels
**/types.ts  **/types.py  **/schema.*      ← pure types
**/generated/**  **/vendor/**              ← generated/vendored
**/utils/**  **/shared/**  **/common/**    ← glue
**/*.config.*  **/constants.*             ← config
```

---

## Quality Gates (run before opening browser)

```bash
# JS syntax check
node -e "
const h = require('fs').readFileSync('index.html','utf8');
[...h.matchAll(/<script>([\s\S]*?)<\/script>/g)]
  .forEach((m,i) => { try { new Function(m[1]); console.log('Script',i+1,'OK'); }
    catch(e) { console.error('Script',i+1,'FAIL:',e.message); process.exit(1); } });
"

# No stale tab bar
grep -c 'id="tabbar"' index.html && echo "FAIL: tabbar present" || echo "OK"

# Coverage
wc -l index.html && open index.html
```

After opening: **"哪个节点需要再深入？" / "Which node needs more depth?"**
