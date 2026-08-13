---
name: requirement-close
description: Verify and close an executed requirement against its approved roadmap and user-observable outcome. Use only when invoked by `$requirement-workflow-router` or explicitly requested for the closure stage. Require internal correctness evidence, external or user-visible evidence where promised, independent QA when assigned, honest residual-risk reporting, product-truth synchronization, and a recoverable handoff before closure.
---

# Requirement Close

Close only what the approved roadmap actually proves complete.

## Verify

1. Re-read the approved roadmap digest and acceptance clauses.
2. Verify source identity, exact scope, test evidence, integration evidence, and rollback or recovery readiness.
3. Verify the user-observable result promised by the requirement. Unit tests alone are insufficient when the roadmap promised a black-box, environment, or experience outcome.
4. Require the assigned independent QA verdict where applicable; implementation-owner evidence is not self-acceptance.
5. Confirm product Current/ADR/runbook truth is synchronized in its registered owner surface when behavior changed.
6. Confirm workflow material does not contain secrets, raw artifacts, or a duplicate current-state machine.

## Decide honestly

- `closed`: every required result and authority condition passed.
- `return_execute`: implementation or verification remains within the approved plan.
- `return_align`: reality invalidated the agreed solution or introduced a decision-changing tradeoff.
- `blocked`: an external authorization or fact prevents completion.

## Output

Create `验收.md` using [references/acceptance-contract.md]. The controller alone changes mechanical state to closed after registering the committed acceptance material.

Use `$decision-partner-communication` for the final user-facing result.
