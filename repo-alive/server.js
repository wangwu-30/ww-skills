// repo-alive/server.js
// Local runtime server for the repo-alive skill.
// Zero framework dependencies except the built-in `ws` package.
// Usage: node server.js [port]
// Reads manifests from .repo-alive/ in the current working directory.

const http = require("http");
const fs   = require("fs");
const path = require("path");
const crypto = require("crypto");

// ws is a single-file dep — install with: npm install ws
let WebSocketServer;
try {
  WebSocketServer = require("ws").WebSocketServer;
} catch (_) {
  console.error("Missing dependency: run `npm install ws` in this directory");
  process.exit(1);
}

const PORT     = parseInt(process.argv[2] || process.env.PORT || "4311", 10);
const ROOT     = process.cwd();
const DATA_DIR = path.join(ROOT, ".repo-alive");
const NODE_DIR = path.join(DATA_DIR, "nodes");
const SCEN_DIR = path.join(DATA_DIR, "scenarios");
const UI_FILE  = path.join(ROOT, "index.html");

// ── helpers ──────────────────────────────────────────────────────────────────

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

function json(res, code, body) {
  const payload = JSON.stringify(body, null, 2);
  res.writeHead(code, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Content-Length": Buffer.byteLength(payload),
  });
  res.end(payload);
}

function html(res, code, body) {
  res.writeHead(code, { "Content-Type": "text/html; charset=utf-8" });
  res.end(body);
}

function notFound(res, msg) {
  json(res, 404, { error: msg || "Not found" });
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let buf = "";
    req.on("data", c => { buf += c; });
    req.on("end",  () => { try { resolve(JSON.parse(buf || "{}")); } catch (e) { reject(e); } });
    req.on("error", reject);
  });
}

// ── data access ───────────────────────────────────────────────────────────────

function loadGraph() {
  const gp = path.join(DATA_DIR, "graph.json");
  if (!fs.existsSync(gp)) throw new Error("graph.json not found — run analysis first");
  const g = readJson(gp);
  g.scenarios = listScenarioIds();
  return g;
}

function loadNode(id) {
  // sanitize id to prevent path traversal
  const safe = path.basename(id);
  const fp = path.join(NODE_DIR, `${safe}.json`);
  if (!fs.existsSync(fp)) throw new Error(`Node not found: ${id}`);
  return readJson(fp);
}

function loadScenario(id) {
  const safe = path.basename(id);
  const fp = path.join(SCEN_DIR, `${safe}.json`);
  if (!fs.existsSync(fp)) throw new Error(`Scenario not found: ${id}`);
  return readJson(fp);
}

function listScenarioIds() {
  if (!fs.existsSync(SCEN_DIR)) return [];
  return fs.readdirSync(SCEN_DIR)
    .filter(f => f.endsWith(".json"))
    .map(f => f.replace(/\.json$/, ""));
}

function listNodeIds() {
  if (!fs.existsSync(NODE_DIR)) return [];
  return fs.readdirSync(NODE_DIR)
    .filter(f => f.endsWith(".json"))
    .map(f => f.replace(/\.json$/, ""));
}

// ── query: load node + its owned files for targeted Q&A ──────────────────────

function collectNodeContext(nodeId) {
  const node  = loadNode(nodeId);
  const files = {};
  const MAX   = 64 * 1024; // 64 KB per file
  for (const rel of (node.owned_files || [])) {
    const abs = path.join(ROOT, rel);
    if (!fs.existsSync(abs)) continue;
    const stat = fs.statSync(abs);
    if (!stat.isFile() || stat.size > MAX) continue;
    files[rel] = fs.readFileSync(abs, "utf8");
  }
  return { node, files };
}

// ── scenario playback over WebSocket ─────────────────────────────────────────

const pendingSessions = new Map(); // sessionId → { scenarioId, branchId }

function playback(ws, scenario, branchId) {
  let steps = scenario.steps || [];
  let mode  = "main";

  if (branchId) {
    const branch = (scenario.branches || []).find(b => b.id === branchId);
    if (!branch) {
      ws.send(JSON.stringify({ type: "error", error: `Unknown branch: ${branchId}` }));
      return;
    }
    steps = branch.steps || [];
    mode  = "branch";
  }

  ws.send(JSON.stringify({ type: "scenario:start", scenarioId: scenario.id, mode,
    name: scenario.name, summary: scenario.summary }));

  for (const cp of (scenario.checkpoints || [])) {
    ws.send(JSON.stringify({ type: "scenario:checkpoint", scenarioId: scenario.id, checkpoint: cp }));
  }

  let i = 0;
  const STEP_MS = parseInt(process.env.STEP_MS || "600", 10);
  const timer = setInterval(() => {
    if (ws.readyState !== 1 /* OPEN */) { clearInterval(timer); return; }
    if (i >= steps.length) {
      clearInterval(timer);
      ws.send(JSON.stringify({ type: "scenario:end", scenarioId: scenario.id, mode }));
      return;
    }
    ws.send(JSON.stringify({ type: "scenario:step", scenarioId: scenario.id, mode, step: steps[i++] }));
  }, STEP_MS);

  ws.on("close", () => clearInterval(timer));
}

// ── HTTP server ───────────────────────────────────────────────────────────────

const server = http.createServer(async (req, res) => {
  const url  = new URL(req.url, `http://localhost:${PORT}`);
  const meth = req.method;
  const pth  = url.pathname;

  // CORS preflight
  if (meth === "OPTIONS") {
    res.writeHead(204, { "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type" });
    return res.end();
  }

  // ── Canvas UI ──
  if (meth === "GET" && pth === "/") {
    if (!fs.existsSync(UI_FILE)) return html(res, 200, fallbackUI());
    return html(res, 200, fs.readFileSync(UI_FILE, "utf8"));
  }

  // ── Graph ──
  if (meth === "GET" && pth === "/graph") {
    try { return json(res, 200, loadGraph()); }
    catch (e) { return json(res, 503, { error: e.message }); }
  }

  // ── Node list ──
  if (meth === "GET" && pth === "/nodes") {
    return json(res, 200, { nodes: listNodeIds() });
  }

  // ── Single node ──
  if (meth === "GET" && pth.startsWith("/node/")) {
    const id = decodeURIComponent(pth.slice("/node/".length));
    try { return json(res, 200, loadNode(id)); }
    catch (e) { return notFound(res, e.message); }
  }

  // ── Scenario list ──
  if (meth === "GET" && pth === "/scenarios") {
    return json(res, 200, { scenarios: listScenarioIds() });
  }

  // ── Single scenario ──
  if (meth === "GET" && pth.startsWith("/scenario/")) {
    const id = decodeURIComponent(pth.slice("/scenario/".length));
    try { return json(res, 200, loadScenario(id)); }
    catch (e) { return notFound(res, e.message); }
  }

  // ── Node Q&A context (returns manifest + file contents for Claude to use) ──
  if (meth === "POST" && pth === "/query") {
    try {
      const body = await readBody(req);
      if (!body.nodeId) return json(res, 400, { error: "nodeId required" });
      const ctx = collectNodeContext(body.nodeId);
      return json(res, 200, {
        node:     ctx.node,
        files:    ctx.files,
        question: body.question || null,
      });
    } catch (e) { return json(res, 400, { error: e.message }); }
  }

  // ── Branch session setup ──
  if (meth === "POST" && pth === "/branch") {
    try {
      const body = await readBody(req);
      if (!body.scenarioId || !body.branchId)
        return json(res, 400, { error: "scenarioId and branchId required" });
      const sessionId = crypto.randomUUID();
      pendingSessions.set(sessionId, { scenarioId: body.scenarioId, branchId: body.branchId });
      // auto-expire after 60s
      setTimeout(() => pendingSessions.delete(sessionId), 60_000);
      return json(res, 200, { sessionId });
    } catch (e) { return json(res, 400, { error: e.message }); }
  }

  // ── Fingerprint / freshness ──
  if (meth === "GET" && pth === "/fingerprint") {
    const fp = path.join(DATA_DIR, "fingerprint.json");
    if (!fs.existsSync(fp)) return json(res, 404, { fresh: false, reason: "no manifests" });
    return json(res, 200, { fresh: true, ...readJson(fp) });
  }

  notFound(res);
});

// ── WebSocket ─────────────────────────────────────────────────────────────────

const wss = new WebSocketServer({ server, path: "/ws" });

wss.on("connection", (ws, req) => {
  const url        = new URL(req.url, `http://localhost:${PORT}`);
  const scenarioId = url.searchParams.get("scenario");
  const branchId   = url.searchParams.get("branch")   || null;
  const sessionId  = url.searchParams.get("session")  || null;

  try {
    if (sessionId && pendingSessions.has(sessionId)) {
      const s = pendingSessions.get(sessionId);
      pendingSessions.delete(sessionId);
      return playback(ws, loadScenario(s.scenarioId), s.branchId);
    }
    if (!scenarioId) {
      ws.send(JSON.stringify({ type: "error", error: "Missing ?scenario= param" }));
      return ws.close();
    }
    playback(ws, loadScenario(scenarioId), branchId);
  } catch (e) {
    ws.send(JSON.stringify({ type: "error", error: e.message }));
    ws.close();
  }
});

// ── Fallback UI (when index.html is missing) ──────────────────────────────────

function fallbackUI() {
  return `<!DOCTYPE html><html><head><meta charset="utf-8">
<title>repo-alive</title>
<style>body{font-family:monospace;background:#0d1117;color:#e6edf3;padding:40px;}
a{color:#58a6ff;}pre{background:#161b22;padding:16px;border-radius:8px;overflow:auto;}</style>
</head><body>
<h2>repo-alive is running</h2>
<p>No <code>index.html</code> found in the repo root.</p>
<p>Endpoints:</p>
<pre>GET  /graph          — node graph
GET  /nodes          — list all node IDs
GET  /node/:id       — single node manifest
GET  /scenarios      — list scenario IDs
GET  /scenario/:id   — single scenario
POST /query          — { nodeId, question } → node context
POST /branch         — { scenarioId, branchId } → sessionId
WS   /ws?scenario=X  — scenario playback
GET  /fingerprint    — freshness check</pre>
<p><a href="/graph">View graph.json</a></p>
</body></html>`;
}

// ── Start ─────────────────────────────────────────────────────────────────────

server.listen(PORT, "127.0.0.1", () => {
  console.log(`\nrepo-alive server running at http://localhost:${PORT}`);
  console.log(`  Canvas:      http://localhost:${PORT}/`);
  console.log(`  Graph:       http://localhost:${PORT}/graph`);
  console.log(`  WebSocket:   ws://localhost:${PORT}/ws?scenario=<id>`);
  console.log(`  Data dir:    ${DATA_DIR}`);
  console.log(`\nPress Ctrl+C to stop.\n`);
});
