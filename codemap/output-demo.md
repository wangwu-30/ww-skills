# Codemap — Output Demo

Real excerpts from a working oh-my-codex output. Match this style exactly.

## Node (structural — has children)
```js
{
  id: 'leader',
  label: { zh: 'OMX Leader', en: 'OMX Leader' },
  color: '#58a6ff',
  layer: 0, col: 1,
  confidence: 1.0,
  tip: {
    zh: 'CLI 入口 + 编排核心，驱动所有模式和流水线',
    en: 'CLI entry + orchestration core, drives all modes and pipelines'
  },
  children: LEADER_CHILDREN,   // array → click = zoom drill-down
  childEdges: LEADER_EDGES,
  content: null
}
```

## Node (leaf — detail panel only)
```js
{
  id: 'state',
  label: { zh: 'State Files', en: 'State Files' },
  color: '#3fb950',
  layer: 2, col: 0,
  confidence: 1.0,
  tip: { zh: '.omx/state/*.json，原子写入', en: '.omx/state/*.json, atomic write' },
  children: null,    // null → click = detail panel
  childEdges: null,
  content: null      // populated in DETAILS object
}
```

## Edge (with witness)
```js
{
  from: 'leader', to: 'codex',
  label: { zh: 'spawn+注入', en: 'spawn+inject' },
  style: 'solid',       // solid=sync/primary, dash=async/secondary
  confidence: 1.0,
  witness: 'src/team/runtime.ts imports spawn'
},
{
  from: 'mcp', to: 'state',
  label: { zh: '读写', en: 'read/write' },
  style: 'dash',
  confidence: 0.5,      // inferred → renders as dashed+dim
  witness: null
}
```

## DETAILS entry (verified vs candidate)
```js
state: {
  desc: {
    zh: '所有协调状态的真相来源。JSON 文件，原子写入（temp+rename），Promise 队列防并发损坏。',
    en: 'Single source of truth. JSON files, atomic write (temp+rename), per-path Promise queue.'
  },
  subs: [
    {
      id: 'atomic', title: '原子写入',
      file: 'src/state/operations.ts', line: 45,
      confidence: 'verified',          // ← grep confirmed
      desc: { zh: 'Promise 链 + temp rename', en: 'Promise chain + temp rename' },
      // code ONLY when confidence=verified
      code: `<span class="ck">const</span> writeQueues =
  <span class="ck">new</span> Map&lt;<span class="co">string</span>, Promise&lt;<span class="co">void</span>&gt;&gt;();
<span class="ck">async function</span> <span class="cp">withStateWriteLock</span>(path, fn) {
  <span class="ck">const</span> prev = writeQueues.<span class="cp">get</span>(path) ?? Promise.<span class="cp">resolve</span>();
  <span class="ck">const</span> next = prev.<span class="cp">then</span>(() => <span class="cp">fn</span>()); writeQueues.<span class="cp">set</span>(path, next);
  <span class="ck">await</span> next;
}`
    },
    {
      id: 'layout', title: '文件布局',
      file: '.omx/state/', line: null,
      confidence: 'candidate',         // ← directory exists, no specific line
      desc: { zh: '磁盘目录结构', en: 'Disk directory structure' }
      // NO code field when candidate
    }
  ]
}
```

## FLOW_STEPS entry
```js
{
  title: { zh: '用户运行 omx team 3:executor', en: 'User runs omx team 3:executor' },
  actor: 'leader', nodes: ['leader'], edges: [],
  confidence: 'verified',
  file: 'src/cli/index.ts', line: 1,
  payload: `<span class="pk">$</span> omx team <span class="pn">3</span>:executor
<span class="cc">// src/cli/index.ts:</span>
workerCount = <span class="pn">3</span>, agentType = <span class="pss">"executor"</span>`
},
{
  title: { zh: 'Workers 并行执行任务', en: 'Workers execute tasks (parallel)' },
  actor: 'codex', nodes: ['codex'], edges: [],
  confidence: 'inferred',              // ← inferred, not directly read
  file: null, line: null,
  payload: `<span class="cc">// 从集成测试推断，未直接验证</span>
<span class="cc">// 3 workers in independent git worktrees</span>`
}
```

## Coverage badge (in #topbar)
```html
<div id="coverage-badge" title="L2: 34 verified, 8 candidate, 4 dropped">
  ✓ 34 · ~ 8
</div>
```

## Syntax highlighting spans

**Code blocks** (`.ck .cp .cs .cc .cn .co .cg`):
```
.ck  #ff7b72  keywords: export const function async return
.cp  #d2a8ff  called/defined function names
.cs  #a5d6ff  "string literals"
.cc  text3 italic  // comments
.cn  #79c0ff  numbers
.co  #ffa657  TypeScript types, class names
.cg  #3fb950  true, success values
```

**Payload panel** (`.ph .pk .pss .pn .pg`):
```
.ph  #d2a8ff  purple
.pk  #ff7b72  keyword red
.pss #a5d6ff  string blue
.pn  #79c0ff  numbers
.pg  #3fb950  green / success
```

## Final file shape
```
index.html  ~60–80KB, ~1200–1500 lines
  <head>: CSS ~250 lines
  <body>: HTML skeleton ~100 lines
  <script> ROOT_NODES + ROOT_EDGES ~80 lines
  <script> DETAILS + FLOW_STEPS + SWIM_ACTORS + SWIM_MAP ~300 lines
  <script> rendering + interaction ~350 lines
  <script> animation + lang + init ~100 lines
```
