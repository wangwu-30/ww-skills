---
name: hpo-metric-query-readonly
description: Resolve and query HPO metrics through exact read-only Provider commands while preserving the Task-owned objective and guardrail semantics.
---

# HPO Metric Query Readonly

Use this Skill only as the `queryMetric` dependency of an HPO Agent Job.  The
business primary Skill owns the Job's structured result; this dependency does
not add fields to that result and does not create a second platform evidence
record.

Read the immutable `task_context` carried by the current Agent Job.  Resolve
every requested observation against Provider metadata before querying values,
then explain the exact identity, scope, window, aggregation, baseline and any
missing or ambiguous data to the primary Skill.  Do not infer a metric from a
similar name or ID.

Use only read-only query commands documented in the references.  Never start,
pause, resume, stop, close or otherwise mutate an experiment.  Missing,
ambiguous or failed observations are analysis inputs; they are not permission
to recommend or execute a Provider lifecycle write.

The metric identity's `query_type` is routing authority:

- `libra_metric_group` uses only the locked metric-group identity and the
  documented metric-group query.
- `libra_ad_report` uses only `libra ad-report get`, the current Binding's
  explicit `site` and `flight_id`, and the locked
  `report_id/config_group_id/metric_id/query_scope` bytes. Pass every present
  boolean even when its value is `false`; never add an absent option. Do not
  translate this identity to metric-group or realtime.

Use `scripts/build_ad_report_command.py` to project the closed ad-report scope
to exact read-only argv. Use its default mode for the locked detail query and
`--summary-only` for report metadata/tag discovery. Both modes accept the same
closed request payload; do not add `query_type` or reconstruct either command
by hand.

When the flight being queried is not the reference experiment that authored the
locked `query_scope.dimensions.abtest_bingo` (for example a freshly created
experiment produced by the current Trial), first resolve the flight's actual
versions with `bytedcli --json --site <site> libra experiment get --flight-id
<flight_id>`, take the numeric `versions[*].id` values (baseline plus every
treatment, or the subset your comparison intent requires), and pass them to the
builder via the optional `runtime_vids` key on the request payload. When
`runtime_vids` is present, the builder emits `--dimension abtest_bingo=...`
using those values instead of the locked reference bytes. The locked identity
bytes remain intact for audit; only the emitted argv changes. Omit
`runtime_vids` entirely to keep the pre-1.1.2 behavior of using the locked
reference vids verbatim.

For `site=i18n-tt`, the builder pins `--no-auto-upgrade` but does not select or
rewrite the network profile. Execute the returned argv directly, without a
shell, and preserve the Agent/Runtime environment. Network selection belongs to
the Runtime caller and must not be inferred from this Skill's metric identity or
credential source. The script only prints argv and performs no Provider I/O.

If a task requires a Libra read this Skill does not cover (for example
resolving an experiment's runtime version set as described above, sampling
lifecycle state, or listing recent flights), fall back to the standalone
`bytedcli` skill and reason about whether its native `libra` subcommands can
reach the goal within the same read-only permission envelope. Never use that
fallback to mutate an experiment, and never bypass the locked identity for the
final ad-report query itself.

See:

- [references/query-contract.md](references/query-contract.md)
- [references/libra.md](references/libra.md)
- [references/metrics-fe.md](references/metrics-fe.md)
