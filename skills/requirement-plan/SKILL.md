---
name: requirement-plan
description: Convert an explicitly aligned proposal into an approval-ready roadmap with exact scope, authority, sequencing, rollback, evidence, and acceptance. Use only when invoked by `$requirement-workflow-router` or explicitly requested for the planning stage. Never plan around unresolved business decisions and never treat a proposal, branch, or old handoff as execution authorization.
---

# Requirement Plan

Turn the agreed direction into a contract Codex can execute autonomously.

## Preconditions

- The proposal's decision-changing points are recorded as `已确认`.
- Remaining uncertainty does not alter the valid solution set.
- Product truth owners and affected authority boundaries are known.

If any precondition fails, return to `align`; do not hide uncertainty inside an implementation step.

## Roadmap content

Create `路线图.md` using [references/roadmap-contract.md](references/roadmap-contract.md). Include exact deliverables, write set or mutation scope, sequence, dependencies, verification, rollback, residual risk, and stop conditions.

Separate authorization classes:

- roadmap-authorized after user confirmation: exact code, tests, integration, and listed reversible prerelease actions;
- separately authorized: production, real funds, external messages, sensitive material, credentials, irreversible data, or materially expanded access.

Compute and report the roadmap SHA-256 only after the committed roadmap bytes are final. The controller records approval against that digest; later byte changes invalidate approval until reconfirmed.

## Stop condition

Present the roadmap for confirmation. Do not start execution in the same step unless the controller provides an already matching approved digest.

Write the approval summary as decision-partner communication: lead with the proposed decision,
surface exact authority and risk boundaries, and ask only for the approval that cannot be inferred.
