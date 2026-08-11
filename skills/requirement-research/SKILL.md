---
name: requirement-research
description: Decide and perform the proportionate research for an explicitly framed requirement. Use only when invoked by `$requirement-workflow-router` or explicitly requested for the research stage. Start from the curated context, verify project facts and primary public sources, run only bounded low-risk experiments, maintain an uncertainty map, and stop broad collection once the evidence can support a recommendation.
---

# Requirement Research

Produce only the evidence needed to make the pending decision.

## Choose the research shape

- `none`: the frame and authoritative facts already determine the answer.
- `focused_project`: inspect exact repository facts, tests, or local artifacts.
- `focused_public`: verify unstable or external facts in primary sources.
- `limited_experiment`: resolve a concrete uncertainty with a reversible, non-production experiment.
- `deep`: use a multi-round evidence and challenge loop only when the decision is broad, high-stakes, unstable, or materially expensive.

Do not call ordinary repository reading “deep research.” Do not browse broadly when the controller supplied a closed source set that can answer the question.

## Research rules

1. Start with the context packet and its exact source allowlist.
2. Expand the search only when a named uncertainty remains unresolved; record why the expansion was necessary.
3. Prefer code and tests for current behavior and primary sources for external facts.
4. Distinguish fact, inference, and assumption when the distinction affects the recommendation.
5. For each decisive claim, retain its source, freshness, confidence, and invalidation condition.
6. Ask the user only for private facts that change the solution set; return questions to the controller.
7. Stop when additional collection is unlikely to change what to do, what not to do, or what to do first.
8. Do not edit product code or perform environment mutations.

## Output

Create or revise `调研结论.md` using [references/research-output.md](references/research-output.md). Lead with the recommendation unlocked by the evidence, not with a diary of searches.

Use `$decision-partner-communication` for the controller summary.
