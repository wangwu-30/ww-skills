# Codemap — Few-Shot Examples

## Hypothesis Generation (Phase 1)

**Input** — directory skeleton after Phase 0:
```
src/ subdirs: cli/, team/, pipeline/, mcp/, state/, ralph/, hooks/, hud/
manifests: package.json (bin: omx), Cargo.toml (workspace)
entry points: src/cli/omx.ts, src/cli/index.ts
file count: 435 TS, 33 Rust
```

**Correct output:**
```json
[
  {
    "id": "H1", "type": "layered", "confidence": 0.5,
    "l0_partition": ["src/cli","src/team","src/mcp","src/state","crates/"],
    "predicted_signals": [
      "src/cli imports src/team — but src/team does NOT import src/cli",
      "src/mcp imports src/state",
      "crates/ has no TypeScript imports"
    ]
  },
  {
    "id": "H2", "type": "mixed", "confidence": 0.4,
    "l0_partition": ["src/cli","src/team","src/mcp","src/state","src/ralph","src/pipeline","crates/"],
    "predicted_signals": [
      "src/team and src/ralph are parallel modes, both import from src/state",
      "src/pipeline imports from both src/team and src/ralph"
    ]
  }
]
```

**Why not event-driven or plugin?**
- No event bus in package.json (no `eventemitter2`, `rxjs`, `kafka-node`)
- No `register()`/`plugin.add()` pattern in top-level dirs
- Two separate mode dirs (team/, ralph/) suggest parallel paths, not plugins

---

## Confidence Update (Phase 2)

**Input** — two grep results:
```bash
$ grep -r "from '../cli'" src/team/ --include="*.ts" -l
(no output)

$ grep -r "from '../team'" src/cli/ --include="*.ts" -l
src/cli/index.ts
src/cli/team-runner.ts
```

**Correct update:**
```
H1 "layered":
  predicted "team does NOT import cli" → CONFIRMED (+0.2)
  predicted "cli imports team" → signal present but not uniquely predicted → no change
  confidence: 0.5 + 0.2 = 0.70

H2 "mixed":
  no predicted signal tested yet → no change
  confidence: 0.4

Next question (highest uncertainty):
  "Does src/pipeline import from both src/team AND src/ralph?"
  → confirms H2's key differentiator
  → cheapest tool: grep -r "from '../team'\|from '../ralph'" src/pipeline/
  → run this NEXT (1 call resolves main ambiguity)
```

**Why not a bigger jump?**
One confirmed signal in a 3-signal hypothesis = partial evidence.
Do not lock in until confidence > 0.8.

---

## Taint Example (what NOT to do)

**Wrong** — ranking `src/utils/paths.ts` as L1 hub:
```
fan-in = 47 BUT matches "**/utils/**" taint pattern
actual score = 47 × 0.1 = 4.7  ← deprioritized
```

**Wrong** — treating `src/team/index.ts` as hub:
```
fan-in = 22 BUT matches "**/index.ts" taint pattern
actual score = 22 × 0.1 = 2.2

Real hub: src/team/orchestrator.ts
  fan-in = 8, NOT tainted → score = 8.0  ← wins
  exports: createTeamState, transitionPhase, TRANSITIONS
  verified by: grep -n "^export" src/team/orchestrator.ts
```

---

## Next Search Decision (budget allocation)

**Input** — state after Phase 2:
```
H1 confidence: 0.70, H2 confidence: 0.40
Budget remaining: 28 calls
Unverified L2 candidates: 12 symbols across 4 hub files
Trace: not started
```

**Correct decision:**
```
Run in parallel (same turn, 2 calls):

Call A — resolve hypothesis (1 call):
  grep -r "from '../team'\|from '../ralph'" src/pipeline/ --include="*.ts"
  Value: resolves H1 vs H2 ambiguity

Call B — batch verify L2 candidates (1 call):
  grep -n "export.*createTeamState\|export.*transitionPhase\|
           export.*startMode\|export.*runPipeline\|
           export.*normalizeRalphPhase\|export.*stateWrite\|
           export.*isPaneIdle\|export.*buildWorkerProcessLaunchSpec" src/
  Value: verifies 8 L2 candidates at once

Defer trace until hypothesis resolved.
Do not waste reads on wrong architectural framework.
```
