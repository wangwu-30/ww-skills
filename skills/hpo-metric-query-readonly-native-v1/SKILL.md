---
name: hpo-metric-query-readonly
description: Resolve and query HPO metrics with shared discovery knowledge while preserving frozen Task requirements and the Analyzer output contract.
---

# HPO Metric Query Readonly — Analyzer entry

Use this candidate entry as the `queryMetric` dependency of a Job whose primary
contract supports confirmed Libra native queries. Read the locked input/output
generation; do not upgrade an older Job's meaning from this text.
Read its immutable Task requirements, source clues, prior query evidence and
current Trial observation context. The primary Analyzer Skill owns the existing
structured result and interaction contract.

Read [the shared query guide](references/metric-query/GUIDE.md), then the
relevant Provider reference. Apply that knowledge to this Job's actual site,
experiment, baseline/treatments and permitted window. Reference experiments
help discover identity and meaning; their observations are not this Trial's
measurements. Preserve exact frozen identities and explicit user constraints.

Report each attempt's resolved identity, method, scope, observations or actual
blocker through the primary Skill's existing fields and normal Runtime trace.
Do not add a top-level output, question protocol or evidence store. A missing,
ambiguous or failed observation does not grant lifecycle write authority.

[Analyzer query contract](references/query-contract.md) explains the existing
native identity and result boundary. Shared knowledge chooses suitable official
read-only methods; it does not change that boundary or freeze a call sequence.
