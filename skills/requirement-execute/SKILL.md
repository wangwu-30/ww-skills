---
name: requirement-execute
description: Execute an approved requirement roadmap autonomously while preserving its exact authority boundary and classifying real-world gaps correctly. Use only when invoked by `$requirement-workflow-router` or explicitly requested for the execution stage with a matching approved roadmap digest. Resolve only small reversible implementation differences locally; escalate any change to business meaning, cost, performance, user experience, security, compatibility, deployment, migration, scope, or irreversible authority.
---

# Requirement Execute

Execute the approved roadmap, not a remembered or superseded version.

## Entry gate

Verify that:

- the controller snapshot names stage `execute`;
- the committed roadmap digest exactly matches the approved digest;
- the current source base, owner generation, write set, dependencies, and authority still match;
- no newer user stop or correction supersedes the plan.

If any check fails, stop before mutation.

## Work autonomously

- Complete the listed code, tests, integration, and reversible prerelease work without asking for routine implementation choices.
- Preserve unrelated changes and use isolated workspaces where the project requires them.
- Keep evidence proportionate to risk.
- Update product truth only in its registered owner surfaces; do not use workflow material as product truth.

## Classify gaps

Use [references/gap-policy.md](references/gap-policy.md). A gap may be solved locally only when every self-resolution condition is true. Otherwise stop the affected path, continue independent safe work if useful, and return one decision-ready request to the controller.

Never broaden production, data, credential, payment, external-message, or destructive authority to “finish the roadmap.”

## Handoff

Report outcome, evidence, deviations, remaining risk, and the requested next stage. Do not claim acceptance when an independent verifier is required.

Use `$decision-partner-communication` for the controller synthesis.
