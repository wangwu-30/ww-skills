// repo-alive/server.js — local runtime + IPC bridge for Claude Code
// Usage: node server.js [port]
// Deps: ws (npm install ws)

import http   from "http";
import fs     from "fs";
import path   from "path";
import crypto from "crypto";
import { createRequire } from "module";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname  = path.dirname(__filename);

let WebSocketServer;
try {
  const ws = await import("ws");
  WebSocketServer = ws.WebSocketServer || ws.default?.WebSocketServer;
} catch (_) { console.error("Run: npm install ws"); process.exit(1); }

const PORT      = parseInt(process.argv[2] || process.env.PORT || "4311", 10);
const ROOT      = process.cwd();
const DATA_DIR  = path.join(ROOT, ".repo-alive");
const NODE_DIR  = path.join(DATA_DIR, "nodes");
const SCEN_DIR  = path.join(DATA_DIR, "scenarios");
const UI_FILE   = path.join(ROOT, "index.html");
const PENDING   = path.join(DATA_DIR, "pending.json");
const ANSWER    = path.join(DATA_DIR, "answer.json");

// ── helpers ───────────────────────────────────────────────────────────────────
function readJson(f) { return JSON.parse(fs.readFileSync(f, "utf8")); }

function j(res, code, body, extra = {}) {
  const p = JSON.stringify(body, null, 2);
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*", "Content-Length": Buffer.byteLength(p), ...extra });
  res.end(p);
}

function readBody(req) {
  return new Promise((ok, fail) => {
    let b = "";
    req.on("data", c => { b += c; });
    req.on("end", () => { try { ok(JSON.parse(b || "{}")); } catch (e) { fail(e); } });
    req.on("error", fail);
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
  const fp = path.join(NODE_DIR, `${path.basename(id)}.json`);
  if (!fs.existsSync(fp)) throw new Error(`Node not found: ${id}`);
  return readJson(fp);
}

function loadScenario(id) {
  const fp = path.join(SCEN_DIR, `${path.basename(id)}.json`);
  if (!fs.existsSync(fp)) throw new Error(`Scenario not found: ${id}`);
  return readJson(fp);
}

function listScenarioIds() {
  if (!fs.existsSync(SCEN_DIR)) return [];
  return fs.readdirSync(SCEN_DIR).filter(f => f.endsWith(".json")).map(f => f.replace(/\.json$/, ""));
}

function listNodeIds() {
  if (!fs.existsSync(NODE_DIR)) return [];
  return fs.readdirSync(NODE_DIR).filter(f => f.endsWith(".json")).map(f => f.replace(/\.json$/, ""));
}

function collectNodeContext(nodeId) {
  const node = loadNode(nodeId);
  const files = {};
  const MAX = 64 * 1024;
  for (const rel of (node.owned_files || [])) {
    const abs = path.join(ROOT, rel);
    if (!fs.existsSync(abs)) continue;
    const stat = fs.statSync(abs);
    if (!stat.isFile() || stat.size > MAX) continue;
    files[rel] = fs.readFileSync(abs, "utf8");
  }
  return { node, files };
}

// ── broadcast helpers ─────────────────────────────────────────────────────────
const sseClients = new Set();

function broadcastSSE(data) {
  const msg = `data: ${JSON.stringify(data)}\n\n`;
  for (const res of sseClients) {
    try { res.write(msg); } catch (_) { sseClients.delete(res); }
  }
}

function broadcastWS(data) {
  const msg = JSON.stringify(data);
  if (!wss) return;
  wss.clients.forEach(ws => { if (ws.readyState === 1) try { ws.send(msg); } catch (_) {} });
}

function broadcast(data) { broadcastSSE(data); broadcastWS(data); }

// ── scenario playback ─────────────────────────────────────────────────────────
const pendingSessions = new Map();

function playback(ws, scenario, branchId) {
  let steps = scenario.steps || (scenario.behavior_view || {}).steps || [];
  let mode  = "main";
  if (branchId) {
    const branch = ((scenario.behavior_view || {}).branches || []).find(b => b.id === branchId);
    if (!branch) { ws.send(JSON.stringify({ type: "error", error: `Unknown branch: ${branchId}` })); return; }
    steps = branch.steps || [];
    mode  = "branch";
  }
  ws.send(JSON.stringify({ type: "scenario:start", scenarioId: scenario.id, mode,
    name: scenario.name, summary: scenario.summary }));
  for (const cp of ((scenario.behavior_view || {}).checkpoints || []))
    ws.send(JSON.stringify({ type: "scenario:checkpoint", scenarioId: scenario.id, checkpoint: cp }));

  let i = 0;
  const STEP_MS = parseInt(process.env.STEP_MS || "600", 10);
  const timer = setInterval(() => {
    if (ws.readyState !== 1) { clearInterval(timer); return; }
    if (i >= steps.length) {
      clearInterval(timer);
      ws.send(JSON.stringify({ type: "scenario:end", scenarioId: scenario.id, mode }));
      return;
    }
    ws.send(JSON.stringify({ type: "scenario:step", scenarioId: scenario.id, mode, step: steps[i++] }));
  }, STEP_MS);
  ws.on("close", () => clearInterval(timer));
}

// ── watch answer.json → push to clients ──────────────────────────────────────
if (fs.existsSync(DATA_DIR)) {
  fs.watch(DATA_DIR, (event, filename) => {
    if (filename !== "answer.json" || !fs.existsSync(ANSWER)) return;
    try {
      const answer = readJson(ANSWER);
      broadcast(answer);
    } catch (_) {}
  });
}

// ── HTTP server ───────────────────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  const url  = new URL(req.url, `http://localhost:${PORT}`);
  const meth = req.method;
  const pth  = url.pathname;

  if (meth === "OPTIONS") {
    res.writeHead(204, { "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type" });
    return res.end();
  }

  // Canvas UI
  if (meth === "GET" && pth === "/") {
    if (!fs.existsSync(UI_FILE)) return res.writeHead(200, {"Content-Type":"text/html"}) && res.end(fallbackUI());
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    return res.end(fs.readFileSync(UI_FILE, "utf8"));
  }

  // Graph
  if (meth === "GET" && pth === "/graph") {
    try { return j(res, 200, loadGraph()); }
    catch (e) { return j(res, 503, { error: e.message }); }
  }

  // Node list
  if (meth === "GET" && pth === "/nodes") return j(res, 200, { nodes: listNodeIds() });

  // Single node
  if (meth === "GET" && pth.startsWith("/node/")) {
    const id = decodeURIComponent(pth.slice("/node/".length));
    try { return j(res, 200, loadNode(id)); }
    catch (e) { return j(res, 404, { error: e.message }); }
  }

  // Scenario list
  if (meth === "GET" && pth === "/scenarios") return j(res, 200, { scenarios: listScenarioIds() });

  // Single scenario
  if (meth === "GET" && pth.startsWith("/scenario/")) {
    const id = decodeURIComponent(pth.slice("/scenario/".length));
    try { return j(res, 200, loadScenario(id)); }
    catch (e) { return j(res, 404, { error: e.message }); }
  }

  // Node context for Q&A
  if (meth === "POST" && pth === "/query") {
    try {
      const body = await readBody(req);
      if (!body.nodeId) return j(res, 400, { error: "nodeId required" });
      return j(res, 200, collectNodeContext(body.nodeId));
    } catch (e) { return j(res, 400, { error: e.message }); }
  }

  // Branch session setup
  if (meth === "POST" && pth === "/branch") {
    try {
      const body = await readBody(req);
      if (!body.scenarioId || !body.branchId) return j(res, 400, { error: "scenarioId and branchId required" });
      const sessionId = crypto.randomUUID();
      pendingSessions.set(sessionId, { scenarioId: body.scenarioId, branchId: body.branchId });
      setTimeout(() => pendingSessions.delete(sessionId), 60_000);
      return j(res, 200, { sessionId });
    } catch (e) { return j(res, 400, { error: e.message }); }
  }

  // ── IPC: webpage → Claude Code ──────────────────────────────────────────────

  // SSE stream for real-time updates from Claude Code
  if (meth === "GET" && pth === "/events") {
    res.writeHead(200, { "Content-Type": "text/event-stream", "Cache-Control": "no-cache",
      "Connection": "keep-alive", "Access-Control-Allow-Origin": "*" });
    res.write(": connected\n\n");
    sseClients.add(res);
    req.on("close", () => sseClients.delete(res));
    return;
  }

  // POST /ask — webpage sends question, written to pending.json for CC to pick up
  if (meth === "POST" && pth === "/ask") {
    try {
      const body = await readBody(req);
      if (!body.question && !body.condition) return j(res, 400, { error: "question or condition required" });
      const pending = {
        id: crypto.randomUUID(),
        type: body.type || "query",
        question: body.question || null,
        nodeId: body.nodeId || null,
        scenarioId: body.scenarioId || null,
        checkpointId: body.checkpointId || null,
        condition: body.condition || null,
        asked_at: new Date().toISOString(),
        status: "pending",
      };
      fs.mkdirSync(DATA_DIR, { recursive: true });
      fs.writeFileSync(PENDING, JSON.stringify(pending, null, 2));
      broadcast({ type: "thinking", questionId: pending.id, nodeId: pending.nodeId });
      return j(res, 200, { questionId: pending.id, status: "pending" });
    } catch (e) { return j(res, 400, { error: e.message }); }
  }

  // GET /pending — CC polls for questions (fallback if fs.watch unavailable)
  if (meth === "GET" && pth === "/pending") {
    if (!fs.existsSync(PENDING)) return j(res, 200, { status: "empty" });
    try { return j(res, 200, readJson(PENDING)); }
    catch (_) { return j(res, 200, { status: "empty" }); }
  }

  // POST /answer — CC posts answer back (alternative to file write)
  if (meth === "POST" && pth === "/answer") {
    try {
      const body = await readBody(req);
      fs.writeFileSync(ANSWER, JSON.stringify(body, null, 2));
      broadcast(body);
      try { fs.unlinkSync(PENDING); } catch (_) {}
      return j(res, 200, { ok: true });
    } catch (e) { return j(res, 400, { error: e.message }); }
  }

  // Fingerprint
  if (meth === "GET" && pth === "/fingerprint") {
    const fp = path.join(DATA_DIR, "fingerprint.json");
    if (!fs.existsSync(fp)) return j(res, 404, { fresh: false, reason: "no manifests" });
    return j(res, 200, { fresh: true, ...readJson(fp) });
  }

  j(res, 404, { error: "Not found" });
});

// ── WebSocket ─────────────────────────────────────────────────────────────────
const wss = new WebSocketServer({ server, path: "/ws" });
wss.on("connection", (ws, req) => {
  const url        = new URL(req.url, `http://localhost:${PORT}`);
  const scenarioId = url.searchParams.get("scenario");
  const branchId   = url.searchParams.get("branch") || null;
  const sessionId  = url.searchParams.get("session") || null;
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
  } catch (e) { ws.send(JSON.stringify({ type: "error", error: e.message })); ws.close(); }
});

// ── Fallback UI ───────────────────────────────────────────────────────────────
function fallbackUI() {
  return `<!DOCTYPE html><html><head><meta charset="utf-8"><title>repo-alive</title>
<style>body{font-family:monospace;background:#0d1117;color:#e6edf3;padding:40px;}
a{color:#58a6ff;}pre{background:#161b22;padding:16px;border-radius:8px;}</style>
</head><body><h2>repo-alive running</h2><p>No index.html found.</p>
<pre>GET  /graph   GET  /node/:id   GET  /events (SSE)
POST /ask     GET  /pending    POST /answer</pre>
<p><a href="/graph">View graph.json</a></p></body></html>`;
}

// ── Start ─────────────────────────────────────────────────────────────────────
server.listen(PORT, "127.0.0.1", () => {
  console.log(`\nrepo-alive server at http://localhost:${PORT}`);
  console.log(`  Canvas:   http://localhost:${PORT}/`);
  console.log(`  Graph:    http://localhost:${PORT}/graph`);
  console.log(`  Events:   http://localhost:${PORT}/events  (SSE)`);
  console.log(`  Ask:      POST http://localhost:${PORT}/ask`);
  console.log(`  Pending:  GET  http://localhost:${PORT}/pending`);
  console.log(`  Answer:   POST http://localhost:${PORT}/answer`);
  console.log(`  WS:       ws://localhost:${PORT}/ws?scenario=<id>`);
  console.log(`  Data:     ${DATA_DIR}\n`);
});
