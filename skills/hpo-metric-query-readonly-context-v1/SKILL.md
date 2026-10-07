---
name: hpo-metric-query-readonly
description: Resolve and query HPO metrics through exact read-only Provider commands while preserving the Task-owned objective and guardrail semantics.
---

# HPO Metric Query Readonly

Use this Skill only as the `queryMetric` dependency of an HPO Agent Job.  The
business primary Skill owns the Job's structured result; this dependency does
not add fields to that result and does not create a second platform evidence
record.

Read the immutable Task requirements, source clues and prior query evidence in
this Job. Use official Provider metadata to resolve incomplete identities and
explain the exact namespace, scope, window, aggregation and baseline. An initial
unresolved clue is work to investigate, not a conclusion that a metric is
ambiguous. Use the existing meaning, dashboard path, name and other clues before
asking for numeric IDs; a similar name or bare ID alone does not establish a match.

Choose suitable official read-only discovery, query and diagnosis methods using
the installed bytedcli Skill, its references and the CLI's help. Commands in this
package are examples, not a whitelist or mandatory sequence. Preserve the Job's
site, experiment, groups, user constraints and authorized identity. Do not change
an exact frozen metric identity while investigating a different requirement.

Keep identity resolution separate from value availability. Report a unique
identity with the metadata that establishes the match; use `ambiguous` when
actual candidates or interpretations remain indistinguishable. A tool timeout,
permission error or failed discovery is `error`, not evidence of ambiguity.
Located queries with no usable observations are `missing`. Explain what was
attempted, when, the actual result/error and what remains unresolved; reuse prior
evidence with its age and limits instead of turning an old failure into a fact.
Do not invent fixed query/retry counts or claim a lookup was performed when it
was not. Keep sanitized receipts in the normal Runtime trace and summarize the
relevant evidence in the primary Skill's existing result fields.

Never start, pause, resume, stop, close or otherwise mutate an experiment, Task
or Provider evidence. This Skill supplies analysis context, not lifecycle write
authority or a new user-question protocol. Follow the primary role's existing
output and interaction contract when a blocker cannot be resolved.

The metric identity's `query_type` is routing authority:

- `libra_metric_group` queries the exact metric-group identity.
- `libra_realtime_group` uses the actual dashboard, realtime group and metric
  identity established from official metadata. Discover these from supplied
  clues when they are not already exact; do not borrow IDs from ad-report or
  ordinary metric groups.
- `libra_ad_report` value reads use `libra ad-report get`, the current Binding's
  explicit `site` and `flight_id`, and the locked
  `report_id/config_group_id/metric_id/query_scope` bytes. Pass every present
  boolean even when its value is `false`; never add an absent option. Do not
  translate this identity to metric-group or realtime.
  Official read-only metadata discovery and diagnosis remain available; they
  do not replace the locked value query or authorize changes to its scope.

Use `scripts/build_ad_report_command.py` to project the closed ad-report scope
to exact read-only argv. The script only prints argv and performs no Provider
I/O.

See:

- [references/query-contract.md](references/query-contract.md)
- [references/libra.md](references/libra.md)
- [references/metrics-fe.md](references/metrics-fe.md)
