---
name: requirement-align
description: Turn a framed and sufficiently researched requirement into a clear Chinese proposal, challenge it adversarially, and drive discussion until the goal and solution are genuinely aligned. Use only when invoked by `$requirement-workflow-router` or explicitly requested for the alignment stage. Give a recommendation rather than a menu, surface decisive tradeoffs and failure conditions, and stop before roadmap or implementation approval.
---

# Requirement Align

Form a recommendation that can survive serious questioning.

## Draft the proposal

1. Read `需求与边界.md` and any `调研结论.md`.
2. Lead with one recommended direction. Do not turn technical judgment into a user questionnaire.
3. Explain only the evidence, tradeoffs, scope, non-goals, costs, risks, and failure conditions that affect the decision.
4. Use natural Chinese. Keep English only when its exact bytes are the contract: code symbols, paths, protocol literals, commands, registered identifiers, and proper nouns. Translate ordinary engineering terms even if the source material uses English.
5. Treat an inherited plan as a hypothesis, not authority.

## Challenge before presenting

Run an internal grill pass:

- What user outcome could this technically correct proposal still fail to deliver?
- Which assumption has the largest blast radius if false?
- Is there a materially simpler path?
- Does the design create a second source of truth, hidden authority, or irreversible dependency?
- What happens under crash, concurrency, retry, partial rollout, stale state, and hostile input where relevant?
- Which risk belongs to business choice rather than technical judgment?

Revise the proposal after the challenge. Do not dump the grill transcript into the user-facing document.

Before completing alignment, run a lexical audit. Repeated prose such as `producer`, `receipt`,
`consumer`, `scope`, `manifest`, `discovery`, `apply`, `fail-closed`, `runtime`,
`code/dev-test-only`, `runner`, `fixture`, `cleanup`, and `authority` is a failed audit unless the
occurrence is an exact registered literal or code symbol.

## Output and stop condition

Create or revise `提案.md` and `决策记录.md` following [references/alignment-contract.md](references/alignment-contract.md).

Stop after presenting the proposal and the few decisions that genuinely require the user. Do not create a roadmap, claim approval, or start implementation until the controller records explicit alignment.

Write all user-facing text as decision-partner communication: lead with the recommendation, explain
only decisive evidence and trade-offs, and ask only questions that require private user judgment.
