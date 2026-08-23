# Software Engineering Routing Contract

Read this contract when a request could cross admission, resumption, repository-map, or Skill
composition boundaries. The router is a turn-local decision layer, not a workflow engine.

## Precedence and classification

Apply these rules in order:

1. An explicit `$skill-name` invocation wins. Do not add the router in front of it.
2. An authoritative controller context for an admitted requirement wins for `resume`. Route it to
   `$requirement-workflow-router`; do not infer its stage.
3. Otherwise classify the immediate outcome as exactly one of `question`, `understand`, `diagnose`,
   `review`, `design`, `small_fix`, `nontrivial_requirement`, `resume`, or `status`.
4. Select one primary path. Direct work is a path; it does not require a placeholder Skill.

Use these tests at class boundaries:

- A `question` asks for an answer, not repository-wide navigation or a mutation.
- `understand` asks for repository shape, ownership, entry points, or call paths.
- `diagnose` asks for cause. It does not authorize a fix unless the request also says to fix it.
- `review` evaluates an identified artifact or change and leads with actionable findings.
- `design` asks for obligations, trade-offs, architecture, or a decision before implementation.
- `small_fix` has a bounded write set, known success condition, and no material product or
  architecture choice.
- `nontrivial_requirement` changes behavior across uncertain scope, important interfaces, or
  decision boundaries and benefits from explicit staged control.
- `resume` continues prior work. Chat history can identify the subject but cannot establish durable
  workflow stage or approval.
- `status` observes current evidence and never advances a stage, approval, or implementation.

When a request combines outcomes, classify by the highest-authority action needed now. For example,
"diagnose and fix" is `small_fix` only when the likely fix remains bounded; otherwise it is a
`nontrivial_requirement`. Do not run two primary routes in parallel.

## Route graph

The suite has one implicit entry point and a one-way dependency graph:

```text
software-engineering-router
├── direct engineering
├── repo-alive
├── force-thinker
├── decision-partner-communication
└── requirement-workflow-router
    └── exactly one of frame, research, align, plan, execute, close
```

The graph is exact: the requirement router has only the six stage edges shown above, and every leaf
or stage has no outgoing Skill edge. Communication quality is an internal output obligation within
the selected path, not an invocation of another Skill.

Do not create a route registry, task queue, session store, duplicate workflow database, approval
record, or stage field. Do not call the requirement workflow state tool from the software router.
The existing requirement controller alone owns its mechanical state and transitions.

## One-time workflow admission

For a new `nontrivial_requirement` without explicit workflow admission:

1. Read only enough current evidence to state the desired outcome, likely affected surfaces, fixed
   constraints, and the few unknowns that could change the approach.
2. Ask one concise admission question. Do not imply that the workflow is mandatory.
3. On acceptance, invoke the requirement router and let its controller establish state.
4. On refusal, record the refusal only in the current conversational context and proceed through
   ordinary stateless engineering. Do not ask again for that request.

A material new request is eligible for a new admission question. A refinement, retry, or continued
implementation of the same request is not.

## Resumption evidence

Route `resume` to the requirement workflow only when at least one authoritative input identifies the
admitted requirement and its controller-owned context, such as a controller packet or a verified
controller snapshot. A branch name, old handoff, chat claim, generated document, or presence of a
workflow database is insufficient by itself.

If authoritative workflow context is absent, resume direct work from current repository evidence.
Do not probe, initialize, repair, or transition workflow state merely to answer a resume or status
request.

## Repo Alive boundary

Repo Alive is a repository navigation and snapshot-consistency tool. It is not semantic review or a
runtime acceptance harness.

- Resolve and pass the target repository root explicitly, especially with multiple worktrees.
- Query mode is read-only. Use it for navigation and verify important claims from current files.
- Map mode requires an explicit user request and writes only `.repo-alive/**`.
- Parse the JSON status. Some non-fresh results may still return exit code zero.
- Treat `invalid` as unusable even when `changed_paths` is empty.
- Treat `fresh` only as proof that the recorded source snapshot and declared knowledge artifacts
  close consistently. It says nothing about semantic accuracy, test results, or runtime health.

## Mutation and evidence boundary

Routing does not grant authority. Questions, understanding, diagnosis, review, design, status, and
pre-admission framing remain read-only unless the user separately requests a mutation. A small fix or
ordinary post-refusal implementation may mutate only the user-authorized scope.

Every completion claim must name the evidence actually obtained. Keep these distinct:

- source or snapshot consistency;
- semantic or architecture review;
- static checks and tests;
- runtime or deployment health;
- workflow admission, approval, and closure.
