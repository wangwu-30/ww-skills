---
name: repository-document-authoring
description: Write or review repository-owned user guides, onboarding docs, quick starts, runbooks, Wiki pages, and published Agent instructions as focused task projections with explicit audiences, executable authorities, stop conditions, observable acceptance, and safe one-way publication. Use for product or operational documentation whose correctness depends on repository contracts or live capabilities; do not use for ADRs, incident reports, review logs, code comments, or generic marketing copy.
---

# Repository Document Authoring

Produce documentation that lets one reader complete one task without first reconstructing the system or its history. Treat the repository-reviewed source as the maintained body and external pages as publications of that source.

## Establish the contract before writing

Identify these facts from current primary evidence:

- the reader role and the single task this document owns;
- the inputs the reader must already have;
- the repository file that owns the body;
- the product or operational authorities the document must defer to;
- any external projections that must be updated after review;
- which facts are dynamic and must be read from executable help, capability, schema, or runtime readback.

Read the target revision of repository instructions and authority documents. Do not substitute a working-tree snapshot, chat summary, old branch, or existing Wiki body for current Git evidence. If the requested wording would choose unresolved product semantics or contradict an authority, stop and ask the owner to decide; documentation is not permission to invent the contract.

When working in HPO Studio, read [references/hpo-studio-profile.md](references/hpo-studio-profile.md) before drafting, reviewing, or publishing.

## Write the task path

Put the reader's decision-critical information first:

1. State who the page is for, what they will accomplish, and the required inputs in the first screen.
2. Present only the mandatory path in task order. For each action, give the usable command or navigation target and the observable result.
3. Place stop conditions beside the step that can fail. Say what must not happen and what evidence or owner is needed to continue.
4. End with observable acceptance: what the reader can inspect to know the task succeeded.
5. Link optional implementation theory, operations detail, troubleshooting depth, and extension scenarios instead of interrupting the main path.

Write the current effective state. Exclude historical evolution, internal debate, reasoning transcripts, meeting notes, implementation plans, and development/test receipts from the operating body. A concise revision table at the beginning is acceptable when the project requires it. Historical or internal background inside the body requires an explicit owner decision.

Runtime evidence required by the product contract is not development trivia. Keep it when the reader needs it to perform or verify the task.

## Preserve authority boundaries

- Explain stable intent and task semantics; link dynamic fields, defaults, enums, thresholds, command syntax, and readiness to their executable authority.
- Do not copy the same runbook into several audience pages. Give each page one owner task and link deeper authorities.
- Do not present target state, planned behavior, local mocks, or isolated tests as deployed current behavior. Name the evidence status and unresolved gaps.
- Do not turn examples into additional contracts. Mark them as examples and keep normative rules at their actual authority.
- Do not add a second schema, policy, registry, or workflow through prose.

## Review the draft

Reject or revise the draft if any answer is unclear:

- Can the intended reader identify the goal and required inputs without scrolling through background?
- Does every mandatory step lead to an observable result?
- Are failure and stop conditions explicit at the point of risk?
- Does the page claim only the state supported by current authorities and evidence?
- Are optional details linked rather than duplicated?
- Is there exactly one maintained body for every normative statement?
- Could a future default, field, enum, threshold, or command change without making this page silently false?

For a review-only request, report concrete violations, their impact on the reader's task, and the smallest source-side correction. Do not edit or publish unless the user also authorized changes.

## Publish as a one-way projection

Change the repository canonical source on a branch and pass its normal review before publishing, unless the owner explicitly authorizes an early projection from an exact reviewed commit. Bind every publication to an immutable source identity.

For each projected body, include a non-contract receipt:

```text
Canonical source: <repository path>
Source commit: <reviewed commit SHA>
Source digest: <sha256 of source bytes>
Synced at: <UTC timestamp>
```

Publication may translate repository-relative links into target-system links and may replace the displayed title to match the approved mapping. It must not change contract text or create independent rules.

After each write, read back title, parent/location, body, links, receipt, permissions when relevant, and any external target metadata promised unchanged. A successful API response alone is insufficient.

When replacing a shortcut or external reference:

1. Treat the external target as outside the content input and write set unless it has an approved repository source.
2. Create or update the repository-backed normal page.
3. Read back its body, source receipt, title, parent, and links.
4. Switch navigation to the verified normal page.
5. Delete only the exact shortcut node, never the external target.
6. Re-read the tree and the external target identity/metadata.

If any create, update, move, delete, or readback result is unknown, stop writes and investigate read-only. Do not automatically retry an ambiguous mutation.

## Handoff

Report the canonical path, exact source commit and digest, pages affected, validation performed, preserved external objects, and remaining gaps. Keep MR readiness, full Gate, deployment, and publication status separate; one does not imply another.
