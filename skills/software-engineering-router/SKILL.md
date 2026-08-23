---
name: software-engineering-router
description: Route software-engineering work across direct reasoning, repository navigation, rigorous design, communication, or an explicitly admitted requirement workflow. Use as the default repository-level entry for questions, codebase understanding, diagnosis, review, design, fixes, non-trivial changes, resumed work, and status checks. Honor an explicitly named Skill first, choose one primary path, and remain stateless outside the existing requirement-workflow controller.
---

# Software Engineering Router

Choose one proportionate path, then do the work through that path. Do not create a second
software-development lifecycle.

## Establish the boundary

1. Read the applicable repository instructions and protect existing user changes.
2. Resolve the intended repository root explicitly. In a multi-worktree checkout, do not infer it
   from the first `.git` entry or from the Skill's installation directory.
3. If the user explicitly names a Skill, let that invocation win. Do not reinterpret it through
   this router.
4. Classify the current request once, using the smallest class that covers the requested outcome.

| Class | Primary path | Rule |
|---|---|---|
| `question` | direct | Answer from proportionate evidence; do not create workflow state. |
| `understand` | `$repo-alive` query mode | Use the map for navigation, then verify decisive facts in current sources. |
| `diagnose` | direct or `$repo-alive` query mode | Choose Repo Alive only when repository topology materially helps locate the fault. |
| `review` | direct | Review the named scope and report evidence-backed findings before a summary. |
| `design` | `$force-thinker` | Use rigorous design reasoning when obligations and trade-offs are the requested outcome. |
| `small_fix` | direct | Implement and verify the bounded change without admitting a requirement workflow. |
| `nontrivial_requirement` | admission rule below | Ask once before entering the persistent requirement workflow. |
| `resume` | existing owner | Resume the proven current path; never reconstruct lifecycle state from chat. |
| `status` | direct, read-only | Inspect authoritative evidence and report it without advancing work. |

Use `$decision-partner-communication` as the primary path only when the requested outcome is
user-facing synthesis or rewriting. A selected workflow or leaf Skill may perform its own prescribed
synthesis; do not select a second path merely to polish the answer.

## Admit non-trivial work once

For a new non-trivial change that the user has not explicitly admitted to the workflow:

1. Perform only bounded read-only framing: identify the outcome, likely scope, constraints, and
   decision-changing unknowns.
2. Ask once whether to enter `$requirement-workflow-router`. Do not create controller state,
   workflow materials, branches, or product changes before the answer.
3. If the user accepts, hand off to that router as the sole workflow owner.
4. If the user declines, continue as ordinary stateless software engineering and do not ask again
   for the same request. A later explicit invocation still wins.

For `resume`, use the requirement router only when a controller-provided context or authoritative
snapshot proves that the requirement was admitted. Otherwise resume the ordinary engineering task
directly. Never invoke the requirement controller's state script from this Skill.

## Keep one-way composition

The allowed dependency shape is:

```text
software-engineering-router -> direct work or one leaf Skill
software-engineering-router -> requirement-workflow-router -> one requirement stage
```

Leaf Skills do not call back into this router. This router owns no route database, session, queue,
approval, stage, or lifecycle record. In-memory notes and a turn-local classification are not durable
state. Delegate bounded implementation or verification tasks only within the selected primary path.

Read [the routing contract](references/routing-contract.md) when admission, resumption, Repo Alive
mode, or composition is ambiguous. Run `scripts/check_suite_contract.py` after changing the suite's
Skill metadata or dependencies.

## Treat Repo Alive as navigation

In Repo Alive query mode, stay read-only. Map mode requires an explicit request and may write only
`.repo-alive/**`. Pass the resolved repository root explicitly and parse the status command's JSON;
some non-fresh statuses may exit 0, so never infer freshness from the exit code alone.

- `invalid` remains invalid even when `changed_paths` is empty.
- `fresh` proves snapshot and artifact closure only. It does not prove semantic correctness, tests,
  architecture claims, or runtime health.
- Verify all decision-changing semantic, test, and runtime claims using their authoritative sources.

## Finish proportionately

Implement only when the request authorizes a change. Verify in proportion to risk, distinguish
passed from unverified evidence, and report the outcome, important evidence, and residual risk. Do
not claim that routing itself completed, approved, tested, or deployed the work.
