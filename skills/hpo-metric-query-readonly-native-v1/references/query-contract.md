# Analyzer query contract

The current Job's persisted Task context is the sole Task requirement input.
Its observation context supplies the current experiment and baseline/treatments;
the primary Skill's locked output schema owns the result representation.

Use [the shared guide](metric-query/GUIDE.md) for discovery, query semantics and
diagnosis. Keep requirement, resolved identity, actual observation method and
outcome separate. An initially unresolved requirement can resolve at runtime;
a new per-attempt method does not rewrite the frozen Task requirement.

For unresolved clues, trace namespace hints back to their source. Data freshness
or an earlier Agent inference does not bind a query surface; re-examine the
original business path and actual definitions. Preserve exact user identities
and constraints. Distinguish new reads from historical evidence with its age
and scope, and record a changed discovery method in existing analysis fields.
Metadata-only discovery, an incomplete preview and a successful query for a
different requirement do not resolve this requirement's identity or values.

For an exact `hpo.libra-native-metric-query/v1` identity, use the frozen
`native_query` object as described in [the Libra knowledge](metric-query/libra.md).
Its native subcommand, raw arguments and response row selection are confirmed
data, not HPO's typed parameter maps. Substitute the current Trial flight,
current group's version/name/configuration and current observation window
placeholders only while executing. Record the actual complete command in
`query_method`, but return the original frozen identity with its placeholders.
Check that the returned groups belong to this Trial. Do not reuse reference
flight/version IDs or group tags, remove filters, omit required dates or change
the population to obtain values. A new Provider flag is data, not a new HPO
schema field.

The old ad-report argv builder is an optional helper for its historical typed
shape, not the new identity contract; it does not supply a query window. Read
the current official command help and actual response definitions when needed.
The query namespace selects knowledge; do not reinterpret business freshness
words as a realtime-dashboard namespace. Metrics-FE retains its existing
identity with current-group tag placeholders and the original supplied URL.

Describe the attempted request, observation time, sanitized result/error and
remaining uncertainty in the existing analysis fields. Keep execution receipts
in normal Runtime trace. Identity evidence and value availability are separate:
actual indistinguishable candidates are `ambiguous`, failed discovery/query is
`error`, and an accurately located metric whose value query succeeded with a
complete response but no usable values is `missing`. Successful metadata with
zero matches leaves identity unresolved in that searched scope; it is not
ambiguity or a missing observation before a value query. None is
zero, success, a passed guardrail or permission to stop an experiment.
