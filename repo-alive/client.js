/**
 * repo-alive client.js
 * Populates the canvas data stubs from the local repo-alive server.
 * Drop into any repo-alive canvas HTML as <script src="client.js">.
 * No framework. No build step.
 */
(function () {
  "use strict";

  const SERVER = (typeof REPO_ALIVE_SERVER !== "undefined")
    ? REPO_ALIVE_SERVER : "http://localhost:4311";
  const WS_SERVER = SERVER.replace(/^http/, "ws");

  // ── state ──────────────────────────────────────────────────────────────────
  const RA = {
    graph: null,
    activeNodeId: null,
    activeScenarioId: null,
    socket: null,
    sse: null,
  };

  // ── helpers ────────────────────────────────────────────────────────────────
  function hook(name, fn) {
    const orig = window[name];
    window[name] = function (...args) {
      fn(...args);
      if (typeof orig === "function") orig.apply(this, args);
    };
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

  // ── color helpers ──────────────────────────────────────────────────────────
  const LEVEL_COLORS = { L0: "#58a6ff", L1: "#bc8cff", L2: "#3fb950" };
  function levelColor(level) { return LEVEL_COLORS[level] || "#8b949e"; }

  // ── graph → canvas data structures ────────────────────────────────────────
  // Compute DAG layers via topological sort from edges
  function computeLayers(nodeIds, edges) {
    const inDegree = {};
    const adj = {};
    nodeIds.forEach(id => { inDegree[id] = 0; adj[id] = []; });
    edges.forEach(e => {
      if (inDegree[e.to] !== undefined) inDegree[e.to]++;
      if (adj[e.from]) adj[e.from].push(e.to);
    });
    const layers = {};
    const queue = nodeIds.filter(id => inDegree[id] === 0);
    queue.forEach(id => { layers[id] = 0; });
    while (queue.length) {
      const id = queue.shift();
      (adj[id] || []).forEach(child => {
        layers[child] = Math.max(layers[child] || 0, (layers[id] || 0) + 1);
        if (--inDegree[child] === 0) queue.push(child);
      });
    }
    // Any node not reached gets layer 0
    nodeIds.forEach(id => { if (layers[id] === undefined) layers[id] = 0; });
    return layers;
  }

  function applyGraph(graph) {
    window.ROOT_NODES = {};
    window.ROOT_EDGES = [];
    window.CONTAINER_SIZES = {};

    const nodeIds = (graph.nodes || []).map(n => n.id);
    const edges   = graph.edges || [];

    // Compute layers from edge topology
    const layers = computeLayers(nodeIds, edges);

    // Assign col within each layer
    const layerGroups = {};
    nodeIds.forEach(id => {
      const l = layers[id] || 0;
      (layerGroups[l] = layerGroups[l] || []).push(id);
    });

    (graph.nodes || []).forEach(n => {
      const layer = layers[n.id] || 0;
      const col   = (layerGroups[layer] || []).indexOf(n.id);

      window.ROOT_NODES[n.id] = {
        id:         n.id,
        label:      { zh: n.name, en: n.name },
        color:      levelColor(n.level || "L0"),
        layer,
        col,
        tip:        { zh: n.summary || n.name, en: n.summary || n.name },
        children:   (n.child_node_ids && n.child_node_ids.length) ? [] : null,
        childEdges: null,
        content:    null,
      };

      if (n.child_node_ids && n.child_node_ids.length) {
        const childCount = n.child_node_ids.length;
        window.CONTAINER_SIZES[n.id] = {
          w: Math.max(140, childCount * 100 + 60),
          h: childCount > 3 ? 170 : 140,
        };
      } else {
        window.CONTAINER_SIZES[n.id] = { w: 140, h: 48 };
      }
    });

    // Edges
    (graph.edges || []).forEach(e => {
      window.ROOT_EDGES.push({
        from:  e.from,
        to:    e.to,
        label: { zh: e.label || e.type || "", en: e.label || e.type || "" },
        style: (e.type === "spawn" || e.type === "call") ? "solid" : "dash",
      });
    });

    // Pick first scenario
    if (graph.scenarios && graph.scenarios[0]) {
      RA.activeScenarioId = graph.scenarios[0];
      if (window.STATE) window.STATE.activeScenarioId = graph.scenarios[0];
    }

    // Re-render
    if (typeof renderGraph === "function") renderGraph();
    if (typeof buildSidebar === "function") buildSidebar();
    if (typeof updateBreadcrumb === "function") updateBreadcrumb();
  }

  // ── node manifest → DETAILS + child nodes ─────────────────────────────────
  function applyNodeManifest(nodeId, manifest) {
    // Build DETAILS entry
    const subs = [];

    // Key files as sub-cards
    (manifest.key_files || []).slice(0, 4).forEach(kf => {
      subs.push({
        id:         kf.path.replace(/[^a-z0-9]/gi, "-"),
        title:      kf.path.split("/").pop(),
        file:       kf.path,
        line:       null,
        confidence: "verified",
        desc:       { zh: kf.reason, en: kf.reason },
        code:       null,
      });
    });

    // Interfaces as sub-cards
    const ifaces = [
      ...(manifest.interfaces?.receives  || []),
      ...(manifest.interfaces?.sends     || []),
      ...(manifest.interfaces?.exposes   || []),
    ].slice(0, 6);

    ifaces.forEach(iface => {
      const ev = (iface.evidence || [])[0];
      subs.push({
        id:         iface.id || iface.name,
        title:      iface.name,
        file:       ev?.path || "",
        line:       ev?.line || null,
        confidence: ev ? "verified" : "candidate",
        desc:       { zh: `${iface.kind}: ${iface.shape || ""}`, en: `${iface.kind}: ${iface.shape || ""}` },
        code:       ev ? `<span class="cc">// ${ev.path}:${ev.line}</span>\n${escHtml(ev.snippet || "")}` : null,
      });
    });

    window.DETAILS = window.DETAILS || {};
    window.DETAILS[nodeId] = {
      desc: { zh: manifest.summary || "", en: manifest.summary || "" },
      subs,
    };

    // If this node has children, build child node objects
    if (manifest.child_node_ids && manifest.child_node_ids.length && window.ROOT_NODES[nodeId]) {
      // We'll populate children lazily when they're loaded
      // For now mark as expandable
      window.ROOT_NODES[nodeId].children = manifest.child_node_ids.map(cid => ({
        id:         cid,
        label:      { zh: cid, en: cid },
        color:      levelColor("L1"),
        layer:      0,
        col:        manifest.child_node_ids.indexOf(cid),
        tip:        { zh: "", en: "" },
        children:   null,
        childEdges: null,
        content:    null,
      }));
      window.ROOT_NODES[nodeId].childEdges = [];
    }
  }

  function escHtml(s) {
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }

  // ── scenario → STEPS / SWIM_ACTORS / SWIM_MAP ─────────────────────────────
  function applyScenario(scenario) {
    const bv = scenario.behavior_view || {};
    const dv = scenario.data_view || {};
    const steps = bv.steps || [];
    const dataSteps = dv.steps || [];

    // Build a map from step_ref → payload
    const payloadMap = {};
    dataSteps.forEach(ds => { payloadMap[ds.step_ref] = ds; });

    window.STEPS = steps.map((s, i) => ({
      title:      { zh: s.action || s.title?.zh || "", en: s.action || s.title?.en || "" },
      actor:      s.actor,
      nodes:      [s.node || s.actor].filter(Boolean),
      edges:      [],
      confidence: s.confidence >= 0.8 ? "verified" : "inferred",
      file:       (s.evidence || [])[0]?.path || null,
      line:       (s.evidence || [])[0]?.line || null,
      payload:    buildPayloadHtml(s, payloadMap[s.id]),
    }));

    // Swim actors from structure_view nodes
    const actorIds = [...new Set(steps.map(s => s.actor).filter(Boolean))];
    window.SWIM_ACTORS = actorIds.map(id => ({
      id,
      label: { zh: id, en: id },
      color: (window.ROOT_NODES[id]?.color) || levelColor("L0"),
    }));

    window.SWIM_MAP = steps.map(s => ({
      actor:  s.actor,
      target: (s.target && s.target !== s.actor) ? s.target : undefined,
    }));

    // Store for what-if
    if (window.STATE) window.STATE._activeScenario = scenario;
    if (typeof buildSwimLane === "function") {
      window.STATE && (window.STATE.swimBuilt = false);
    }
  }

  function buildPayloadHtml(step, dataStep) {
    const parts = [];
    const ev = (step.evidence || [])[0];
    if (ev) {
      parts.push(`<span class="cc">// ${ev.path}:${ev.line}</span>`);
      if (ev.snippet) parts.push(`<span class="cs">${escHtml(ev.snippet)}</span>`);
    }
    if (dataStep?.payload_shape) {
      parts.push(`<span class="cc">// payload shape</span>`);
      parts.push(escHtml(JSON.stringify(dataStep.payload_shape, null, 2)));
    }
    if (dataStep?.example) {
      parts.push(`<span class="cc">// example</span>`);
      parts.push(escHtml(JSON.stringify(dataStep.example, null, 2)));
    }
    if (!parts.length) parts.push(`<span class="cc">// ${step.action}</span>`);
    return parts.join("\n");
  }

  // ── public API ─────────────────────────────────────────────────────────────
  async function loadGraph() {
    try {
      const graph = await get("/graph");
      RA.graph = graph;
      applyGraph(graph);
      console.log("[repo-alive] graph loaded:", (graph.nodes||[]).length, "nodes");
    } catch (e) {
      console.warn("[repo-alive] loadGraph failed:", e.message);
    }
  }

  async function loadNodeManifest(nodeId) {
    RA.activeNodeId = nodeId;
    try {
      const manifest = await get(`/node/${encodeURIComponent(nodeId)}`);
      applyNodeManifest(nodeId, manifest);
      if (manifest.scenario_refs?.[0]) {
        RA.activeScenarioId = manifest.scenario_refs[0];
        if (window.STATE) window.STATE.activeScenarioId = manifest.scenario_refs[0];
      }
      return manifest;
    } catch (e) {
      console.warn("[repo-alive] loadNodeManifest failed:", nodeId, e.message);
      return null;
    }
  }

  async function loadScenario(scenarioId) {
    try {
      const scenario = await get(`/scenario/${encodeURIComponent(scenarioId)}`);
      applyScenario(scenario);
      console.log("[repo-alive] scenario loaded:", scenario.name);
      return scenario;
    } catch (e) {
      console.warn("[repo-alive] loadScenario failed:", scenarioId, e.message);
      return null;
    }
  }

  // ── SSE for real-time updates (Q&A answers, trace steps) ──────────────────
  function connectSSE() {
    if (RA.sse) return;
    RA.sse = new EventSource(SERVER + "/events");
    RA.sse.onmessage = e => {
      try { handleServerMessage(JSON.parse(e.data)); } catch (_) {}
    };
    RA.sse.onerror = () => {
      RA.sse = null;
      setTimeout(connectSSE, 3000);
    };
  }

  function handleServerMessage(msg) {
    if (msg.type === "thinking") {
      const ans = document.getElementById("qa-answer");
      if (ans) { ans.textContent = ""; ans.classList.add("thinking"); }
      const btn = document.getElementById("qa-send");
      if (btn) btn.disabled = true;
    }
    if (msg.type === "answer") {
      const ans = document.getElementById("qa-answer");
      if (ans) {
        ans.classList.remove("thinking");
        ans.innerHTML = renderMarkdown(msg.text || "");
        if (msg.evidence?.length) {
          ans.innerHTML += "<div style='margin-top:6px'>" +
            msg.evidence.map(e => `<span class="qa-evidence">${e.path}:${e.line}</span>`).join("") +
            "</div>";
        }
      }
      const btn = document.getElementById("qa-send");
      if (btn) btn.disabled = false;
    }
    if (msg.type === "trace:start") {
      showToast("正在推演执行路径... / Tracing path...");
    }
    if (msg.type === "trace:step") {
      renderWhatIfStep(msg.step);
    }
  }

  function renderMarkdown(text) {
    const esc = text.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
    return esc
      .split("`").map((p,i) => i%2===1
        ? `<code style="background:var(--bg3);padding:1px 4px;border-radius:3px;font-size:10px">${p}</code>`
        : p).join("")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");
  }

  function renderWhatIfStep(step) {
    const tl = document.getElementById("flow-timeline");
    if (!tl) return;
    const div = document.createElement("div");
    div.className = "flow-step step-whatif";
    div.innerHTML = `<div class="step-num" style="background:var(--orange);border-color:var(--orange);color:#020617">?</div>
      <div class="step-body">
        <div class="step-title" style="color:var(--orange)">${step.action || ""}</div>
        <div class="step-desc">${step.actor || ""} — what-if</div>
      </div>`;
    tl.appendChild(div);
    div.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function showToast(msg) {
    const t = document.createElement("div");
    t.style.cssText = "position:fixed;top:60px;left:50%;transform:translateX(-50%);" +
      "background:rgba(227,179,65,.15);border:1px solid var(--orange);" +
      "border-radius:8px;padding:8px 16px;font-size:11px;color:var(--orange);" +
      "z-index:200;pointer-events:none;";
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2500);
  }

  // ── Q&A send ──────────────────────────────────────────────────────────────
  async function qaSend() {
    const input = document.getElementById("qa-input");
    const question = input?.value?.trim();
    if (!question) return;
    const nodeId = RA.activeNodeId || window.STATE?.selectedNodeId;
    if (!nodeId) {
      const ans = document.getElementById("qa-answer");
      if (ans) ans.textContent = "请先点击一个节点 / Click a node first";
      return;
    }
    input.value = "";
    const ans = document.getElementById("qa-answer");
    if (ans) { ans.textContent = ""; ans.classList.add("thinking"); }
    try {
      await post("/ask", { type: "query", nodeId, question });
    } catch (e) {
      if (ans) { ans.classList.remove("thinking"); ans.textContent = "Cannot reach server"; }
    }
  }
  window.qaSend = qaSend;

  // ── What-if ───────────────────────────────────────────────────────────────
  async function traceWhatIf() {
    const input = document.getElementById("trace-whatif-input");
    const condition = input?.value?.trim();
    if (!condition) return;
    const scenarioId = window.STATE?._activeScenario?.id || RA.activeScenarioId;
    const checkpointId = window.STATE?._pendingCheckpointId;
    try {
      await post("/ask", { type: "trace", scenarioId, checkpointId, condition });
      hideWhatIf();
    } catch (_) { hideWhatIf(); }
  }
  window.traceWhatIf = traceWhatIf;

  function hideWhatIf() {
    document.getElementById("trace-whatif")?.classList.remove("visible");
  }
  window.hideWhatIf = hideWhatIf;

  // ── Hook into openDetail to load manifest on demand ───────────────────────
  const _origOpenDetail = window.openDetail;
  window.openDetail = async function (id) {
    RA.activeNodeId = id;
    // Load manifest if not already in DETAILS
    if (!window.DETAILS?.[id]) {
      await loadNodeManifest(id);
    }
    if (typeof _origOpenDetail === "function") _origOpenDetail(id);
  };

  // ── Hook into flowTogglePlay to load scenario ─────────────────────────────
  const _origFlowTogglePlay = window.flowTogglePlay;
  window.flowTogglePlay = async function () {
    const sid = window.STATE?.activeScenarioId || RA.activeScenarioId;
    if (sid && !window.STATE?._activeScenario) {
      await loadScenario(sid);
    }
    if (typeof _origFlowTogglePlay === "function") _origFlowTogglePlay();
  };

  // ── Enter key for Q&A ─────────────────────────────────────────────────────
  document.addEventListener("keydown", e => {
    if (e.key === "Enter" && document.activeElement?.id === "qa-input") qaSend();
  });

  // ── Expose public API ─────────────────────────────────────────────────────
  window.repoAlive = { loadGraph, loadNodeManifest, loadScenario, connectSSE, RA };

  // ── Auto-init ─────────────────────────────────────────────────────────────
  async function init() {
    connectSSE();
    await loadGraph();
    // Pre-load first scenario if available
    if (RA.activeScenarioId) await loadScenario(RA.activeScenarioId);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
