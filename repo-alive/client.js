/**
 * repo-alive client integration
 * Drop this script into any HTML canvas to make it data-driven.
 * Replaces hardcoded ROOT_NODES / ROOT_EDGES / DETAILS / STEPS / SWIM_ACTORS / SWIM_MAP
 * with live data from the repo-alive server.
 *
 * No framework. No build step. Works as a plain <script src="client.js">.
 *
 * The HTML canvas only needs to expose these optional hook functions:
 *   renderGraph()          — called after ROOT_NODES/ROOT_EDGES are populated
 *   openDetail(nodeId)     — called when a node is activated
 *   flowGoTo(stepIndex)    — called for each scenario step during playback
 *   resetPlayback()        — called at scenario:start
 *   buildSwimLane()        — called after SWIM_ACTORS/SWIM_MAP are ready
 *
 * The client also exposes window.repoAlive for manual control.
 */

(function () {
  "use strict";

  const SERVER = (typeof REPO_ALIVE_SERVER !== "undefined")
    ? REPO_ALIVE_SERVER
    : "http://localhost:4311";

  const WS_SERVER = SERVER.replace(/^http/, "ws");

  // ── state ──────────────────────────────────────────────────────────────────
  const state = {
    graph:            null,
    activeNodeId:     null,
    activeScenarioId: null,
    socket:           null,
    stepBuffer:       [],   // scenario steps received so far
    playing:          false,
  };

  // ── helpers ────────────────────────────────────────────────────────────────

  function call(hook, ...args) {
    if (typeof window[hook] === "function") {
      try { window[hook](...args); } catch (e) { console.warn("[repo-alive]", hook, e); }
    }
  }

  async function get(path) {
    const r = await fetch(SERVER + path);
    if (!r.ok) throw new Error(`GET ${path} → ${r.status}`);
    return r.json();
  }

  async function post(path, body) {
    const r = await fetch(SERVER + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`POST ${path} → ${r.status}`);
    return r.json();
  }

  // ── graph → canvas data structures ────────────────────────────────────────

  function graphToCanvasData(graph) {
    // Populate the globals the existing HTML rendering code expects.
    // We produce a minimal shape; the canvas code reads what it needs.

    window.ROOT_NODES = {};
    window.ROOT_EDGES = [];

    for (const n of (graph.nodes || [])) {
      window.ROOT_NODES[n.id] = {
        id:       n.id,
        label:    { zh: n.name, en: n.name },
        color:    levelColor(n.level),
        layer:    levelToLayer(n.level, n.id, graph.nodes),
        col:      0,   // recomputed by layout algorithm
        tip:      { zh: n.summary || "", en: n.summary || "" },
        children: n.child_node_ids?.length ? [] : null,   // populated on drill-down
        childEdges: null,
        content:  null,
      };
    }

    // assign col within each layer
    const byLayer = {};
    for (const n of Object.values(window.ROOT_NODES)) {
      (byLayer[n.layer] = byLayer[n.layer] || []).push(n);
    }
    for (const nodes of Object.values(byLayer)) {
      nodes.forEach((n, i) => { n.col = i; });
    }

    for (const e of (graph.edges || [])) {
      window.ROOT_EDGES.push({
        from:  e.from,
        to:    e.to,
        label: { zh: e.label || e.type, en: e.label || e.type },
        style: e.type === "spawn" || e.type === "call" ? "solid" : "dash",
      });
    }
  }

  function levelColor(level) {
    return { L0: "#58a6ff", L1: "#bc8cff", L2: "#3fb950" }[level] || "#8b949e";
  }

  function levelToLayer(level, id, nodes) {
    // Use topological position based on connections in graph if available,
    // otherwise fall back to level number.
    return { L0: 0, L1: 1, L2: 2 }[level] ?? 0;
  }

  // ── node manifest → DETAILS entry ─────────────────────────────────────────

  function nodeToDetails(node) {
    const subs = [];

    // key files as sub-cards
    for (const kf of (node.key_files || []).slice(0, 6)) {
      subs.push({
        id:    kf.path.replace(/[^a-z0-9]/gi, "-"),
        title: kf.path.split("/").pop(),
        file:  kf.path,
        line:  null,
        confidence: "verified",
        desc:  { zh: kf.reason, en: kf.reason },
        code:  null,
      });
    }

    // interfaces as sub-cards
    const allIfaces = [
      ...(node.interfaces?.receives  || []),
      ...(node.interfaces?.sends     || []),
      ...(node.interfaces?.exposes   || []),
    ].slice(0, 8);

    for (const iface of allIfaces) {
      const ev = (iface.evidence || [])[0];
      subs.push({
        id:    iface.id,
        title: iface.name,
        file:  ev?.file || "",
        line:  ev?.line || null,
        confidence: ev ? "verified" : "candidate",
        desc:  { zh: `${iface.kind}: ${iface.shape || ""}`, en: `${iface.kind}: ${iface.shape || ""}` },
        code:  ev ? `<span class="cc">// ${ev.file}:${ev.line}</span>\n${escHtml(ev.snippet || "")}` : null,
      });
    }

    return {
      desc: { zh: node.summary || "", en: node.summary || "" },
      subs,
    };
  }

  function escHtml(s) {
    return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  // ── scenario → STEPS / SWIM_ACTORS / SWIM_MAP ─────────────────────────────

  function scenarioToSteps(scenario) {
    window.STEPS = (scenario.steps || []).map(s => ({
      title:  { zh: s.action, en: s.action },
      actor:  s.actor,
      nodes:  [s.node].filter(Boolean),
      edges:  [],
      confidence: "verified",
      payload: formatPayload(s),
    }));

    const actorIds = [...new Set((scenario.steps || []).map(s => s.actor).filter(Boolean))];
    window.SWIM_ACTORS = actorIds.map(id => ({
      id,
      label: { zh: id, en: id },
      color: levelColor("L0"),
    }));

    window.SWIM_MAP = (scenario.steps || []).map(s => ({
      actor: s.actor,
      target: s.node !== s.actor ? s.node : undefined,
    }));
  }

  function formatPayload(step) {
    const ev = (step.evidence || [])[0];
    const lines = [];
    if (step.inputs  && Object.keys(step.inputs).length)
      lines.push(`<span class="cc">// inputs</span>\n${escHtml(JSON.stringify(step.inputs, null, 2))}`);
    if (step.outputs && Object.keys(step.outputs).length)
      lines.push(`<span class="cc">// outputs</span>\n${escHtml(JSON.stringify(step.outputs, null, 2))}`);
    if (ev)
      lines.push(`<span class="cc">// ${ev.file}:${ev.line}</span>\n<span class="cs">${escHtml(ev.snippet || "")}</span>`);
    return lines.join("\n") || `<span class="cc">// ${step.action}</span>`;
  }

  // ── public API ─────────────────────────────────────────────────────────────

  async function loadGraph() {
    try {
      const graph = await get("/graph");
      state.graph = graph;
      graphToCanvasData(graph);
      call("renderGraph");

      // pre-populate DETAILS for nodes already in graph summary
      for (const n of (graph.nodes || [])) {
        if (n.summary) {
          window.DETAILS = window.DETAILS || {};
          window.DETAILS[n.id] = { desc: { zh: n.summary, en: n.summary }, subs: [] };
        }
      }

      // load first scenario if available
      if (graph.scenarios?.[0]) {
        state.activeScenarioId = graph.scenarios[0];
      }

      console.log("[repo-alive] graph loaded:", (graph.nodes || []).length, "nodes");
    } catch (e) {
      console.error("[repo-alive] loadGraph failed:", e.message);
    }
  }

  async function activateNode(nodeId) {
    state.activeNodeId = nodeId;
    try {
      const node = await get(`/node/${encodeURIComponent(nodeId)}`);
      window.DETAILS = window.DETAILS || {};
      window.DETAILS[nodeId] = nodeToDetails(node);

      // update scenario if node has one
      if (node.scenario_refs?.[0]) state.activeScenarioId = node.scenario_refs[0];

      call("openDetail", nodeId);
    } catch (e) {
      console.error("[repo-alive] activateNode failed:", e.message);
    }
  }

  async function playScenario(scenarioId, branchId) {
    const sid = scenarioId || state.activeScenarioId;
    if (!sid) { console.warn("[repo-alive] no active scenario"); return; }

    // fetch full scenario to populate STEPS/SWIM
    try {
      const scenario = await get(`/scenario/${encodeURIComponent(sid)}`);
      scenarioToSteps(scenario);
      call("buildSwimLane");
    } catch (_) {}

    if (state.socket) { state.socket.close(); state.socket = null; }

    let wsUrl = `${WS_SERVER}/ws?scenario=${encodeURIComponent(sid)}`;
    if (branchId) wsUrl += `&branch=${encodeURIComponent(branchId)}`;

    const ws = new WebSocket(wsUrl);
    state.socket = ws;
    state.stepBuffer = [];
    state.playing = true;

    ws.onopen  = () => console.log("[repo-alive] WS connected");
    ws.onerror = e  => console.error("[repo-alive] WS error", e);
    ws.onclose = ()  => { state.playing = false; };

    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "scenario:start") {
        call("resetPlayback");
      } else if (msg.type === "scenario:step") {
        state.stepBuffer.push(msg.step);
        // find index in STEPS array
        const idx = (window.STEPS || []).findIndex(s =>
          s.title?.en === msg.step.action || s.title?.zh === msg.step.action);
        call("flowGoTo", idx >= 0 ? idx : state.stepBuffer.length - 1);
      } else if (msg.type === "scenario:end") {
        state.playing = false;
      } else if (msg.type === "error") {
        console.error("[repo-alive] scenario error:", msg.error);
      }
    };
  }

  async function branchScenario(branchId) {
    const sid = state.activeScenarioId;
    if (!sid) return;
    try {
      const { sessionId } = await post("/branch", { scenarioId: sid, branchId });
      if (state.socket) { state.socket.close(); state.socket = null; }
      const ws = new WebSocket(`${WS_SERVER}/ws?session=${encodeURIComponent(sessionId)}`);
      state.socket = ws;
      state.playing = true;
      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.type === "scenario:step") {
          const idx = state.stepBuffer.length;
          state.stepBuffer.push(msg.step);
          call("flowGoTo", idx);
        }
      };
    } catch (e) { console.error("[repo-alive] branchScenario failed:", e.message); }
  }

  async function askNode(question, nodeId) {
    const nid = nodeId || state.activeNodeId;
    if (!nid) return null;
    try {
      const ctx = await post("/query", { nodeId: nid, question });
      return ctx;
    } catch (e) { console.error("[repo-alive] askNode failed:", e.message); return null; }
  }

  // ── DOM event wiring ───────────────────────────────────────────────────────
  // Supports data-node-id, data-action="play-scenario", data-branch-id attributes

  document.addEventListener("click", async (e) => {
    const nodeEl   = e.target.closest("[data-node-id]");
    const playEl   = e.target.closest("[data-action='play-scenario']");
    const branchEl = e.target.closest("[data-branch-id]");

    if (nodeEl)   { await activateNode(nodeEl.getAttribute("data-node-id")); return; }
    if (playEl)   { await playScenario(); return; }
    if (branchEl) { await branchScenario(branchEl.getAttribute("data-branch-id")); return; }
  });

  // ── expose ─────────────────────────────────────────────────────────────────

  window.repoAlive = { loadGraph, activateNode, playScenario, branchScenario, askNode, state };

  // ── auto-init ──────────────────────────────────────────────────────────────

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadGraph);
  } else {
    loadGraph();
  }

})();
