# repo-alive

Makes any codebase self-explanatory. Analyzes the repo once, persists understanding
as JSON manifests, then serves an interactive canvas where every node is a queryable
Agent backed by real code.

## How it works

```
Analyze once  →  .repo-alive/ manifests  →  serve + interact
   (expensive)         (reusable)              (cheap)
```

1. **Analyze**: ~60–700 tool calls depending on repo size. Writes node manifests,
   scenario state machines, ownership index, and a fingerprint for freshness detection.

2. **Serve**: `node server.js` starts a local HTTP+WebSocket server on port 4311.
   Reads manifests from `.repo-alive/`. Zero cloud, zero database.

3. **Interact**: Click a node → loads only that node's manifest + owned files.
   Run a scenario → WebSocket streams steps with evidence refs.
   Ask a question → Agent reads only the relevant files, cites file:line.

## Files

```
server.js     Local runtime server (~300 lines, only dep: ws)
client.js     Drop-in HTML integration script (~340 lines, no deps)
skill.md      Claude Code skill definition (the analysis algorithm)
package.json  { "dependencies": { "ws": "^8.0.0" } }
```

## Usage

### Via Claude Code skill

```
/repo-alive
```

Claude will:
1. Check if `.repo-alive/` manifests are fresh (fingerprint matches git HEAD)
2. If stale/missing: analyze the repo and write manifests
3. Start the local server
4. Open `http://localhost:4311`

### Manual

```bash
# Install runtime dep
npm install ws

# Start server (reads .repo-alive/ in current dir)
node /path/to/ww-skills/repo-alive/server.js

# Open canvas
open http://localhost:4311
```

### Add to any HTML canvas

```html
<script src="/path/to/client.js"></script>
```

The client auto-connects to `http://localhost:4311`, fetches the graph,
and populates `ROOT_NODES`, `ROOT_EDGES`, `DETAILS`, `STEPS`, `SWIM_ACTORS`, `SWIM_MAP`.

## Output structure

```
.repo-alive/
  fingerprint.json      git HEAD + timestamp
  graph.json            node graph (nodes + edges)
  ownership.json        file → node ID map
  reverse-index.json    node ID → files + scenarios
  nodes/
    <node-id>.json      full manifest per node
  scenarios/
    <scenario-id>.json  scenario state machine
```

## Incremental updates

When files change, only affected manifests are regenerated.
Full re-analysis only when >20% of nodes are affected.

## Zero customization policy

No oh-my-codex-specific logic. No framework assumptions.
The analysis algorithm uses only generic signals:
- file structure + entrypoints
- generic grep patterns (import/export/fetch/publish...)
- root manifests (package.json, go.mod, Cargo.toml, etc.)
- README/docs for naming cues

Works on Django, Rust CLI, Go monorepo, React frontend, anything.
