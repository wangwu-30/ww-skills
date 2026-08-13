---
name: requirement-workflow-router
description: Route an explicitly started non-trivial requirement through framing, research, proposal alignment, roadmap approval, autonomous execution, and acceptance closure. Use only when the user explicitly invokes `$requirement-workflow-router` or explicitly asks to run the requirement-workflow pilot. Keep ordinary questions, status checks, small fixes, and mechanical changes on the short path. During the pilot, never trigger implicitly and never advance into implementation before an approved roadmap.
---

# Requirement Workflow Router

Act as the single entry point for one explicitly admitted pilot requirement.

## Start safely

1. Classify the request as `short_path`, `new_requirement`, or `resume_requirement`.
2. Keep status questions, small fixes, and mechanical changes inside an already approved plan on `short_path`; do not create workflow state or empty documents for them.
3. For a non-trivial request, locate its controller-provided context skill or context packet before searching broadly.
4. Treat the controller as the only user-facing entry. An owner session returns consolidated findings or at most three truly private questions to the controller; it does not send scattered questions to the user.
5. During the first pilot, allow only one active requirement even though the state schema supports at most three.

## Route by stage

Use exactly one stage skill at a time:

- `frame` -> `$requirement-frame`
- `research` -> `$requirement-research`
- `align` -> `$requirement-align`
- `plan` -> `$requirement-plan`
- `execute` -> `$requirement-execute`
- `close` -> `$requirement-close`

Read [references/stage-contract.md](references/stage-contract.md) before selecting or changing a stage. If a controller-provided context sets `stop_after`, stop there even if the next stage looks obvious.

## Keep authority singular

- Mechanical state lives only in the workflow SQLite database. Do not create `状态.json`, queue Markdown, slot files, or parallel lifecycle truth.
- Human-readable material lives in the independent materials Git repository. It may contain requirements, research, proposals, decisions, roadmaps, and acceptance, but not current slot or approval booleans.
- Product behavior remains authoritative in product code, tests, current docs, and deployment systems.
- Chat is a communication channel, never the sole durable authority.

Use `scripts/workflow_state.py` only from a controller session. Owner sessions with `controller_managed: true` may read a supplied snapshot but must not mutate the database. Read [references/state-and-materials.md](references/state-and-materials.md) before a controller writes state.

## Enforce the approval boundary

- Framing, focused research, proposal drafting, and proposal discussion are read-only with respect to product code and environments.
- A proposal is not a roadmap approval.
- Only an approved roadmap digest authorizes its exact code, tests, integration, and reversible prerelease actions.
- Production, real funds, external messages, sensitive material, irreversible data changes, new credentials, and materially expanded authority always require separate explicit authorization.
- Never infer approval from a branch, old handoff, test result, or prior owner session.

## Return a compact controller handoff

Return:

1. current conclusion;
2. material created or changed;
3. facts that changed the recommendation;
4. at most three private decision questions, if any;
5. the requested next stage, without claiming the transition occurred.

Use `$decision-partner-communication` for all user-facing synthesis.
