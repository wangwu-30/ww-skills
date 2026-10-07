# Libra read-only queries

Use the site locked by the Provider URL and request machine-readable output.
Read metadata before values.

```bash
bytedcli --json --site <site> libra experiment report --flight-id <flight_id>
bytedcli --json --site <site> libra experiment report \
  --flight-id <flight_id> --metric-group <metric_group_id> \
  --start <YYYY-MM-DD> --end <YYYY-MM-DD> --merge-type total
```

For `/report/ad/<report_id>` use the ad-report namespace; do not reuse its IDs
on the ordinary metric-group surface.  For realtime dashboards, keep the
dashboard ID and realtime-group ID distinct.  Preserve the exact baseline,
versions, dimensions and filters used for every comparison.

For one locked `libra_ad_report` identity, run this direct value query:

```text
bytedcli --json --site <binding-site> libra ad-report get \
  --flight-id <binding-flight-id> \
  --report-id <report-id> \
  --group-id <config-group-id> \
  --metric-id <metric-id> \
  [--dimension abtest_bingo=<number[@number...]>] \
  [--filter external_action_en=<raw[@raw...]>] \
  [--balance-unequal-traffic <true|false>] \
  [--data-group-style <true|false>] \
  [--multi-compare <true|false>] \
  [--versions-merge <true|false>]
```

Build it from the locked identity rather than copying this display form:

```bash
python scripts/build_ad_report_command.py --request-file <locked-identity.json>
```

When the flight being queried is not the reference experiment (typical for
Trial-time ad-report reads against a freshly created flight), resolve the
flight's actual versions first and inject them via `runtime_vids`:

```bash
bytedcli --json --site <site> libra experiment get --flight-id <flight_id>
# take numeric ``versions[*].id`` values from that response (baseline plus each
# treatment, or the subset your comparison requires), then produce a payload
# that adds:
#   "runtime_vids": [<vid_1>, <vid_2>, ...]
# alongside the locked identity keys. The builder emits
#   --dimension abtest_bingo=<vid_1>@<vid_2>@...
# and leaves ``query_scope.dimensions.abtest_bingo`` untouched for audit.
python scripts/build_ad_report_command.py --request-file <payload-with-runtime-vids.json>
```

`--summary-only` is the extraction-time metadata/tag-discovery route and cannot
be combined with direct metric flags. Build that separate command from the same
locked identity:

```bash
python scripts/build_ad_report_command.py \
  --request-file <locked-identity.json> --summary-only
```

For `site=i18n-tt`, both builder modes return argv beginning with `bytedcli
--no-auto-upgrade`. Execute the returned argv directly as one subprocess. The
builder does not add, clear or rewrite `BYTEDCLI_NETWORK_PROFILE`; the child
inherits the Runtime caller's selection exactly. Other sites retain their
existing argv and inherited environment.

Never use summary mode for the locked value query above. Only `abtest_bingo`
and `external_action_en` are accepted by this Skill version.
Any other dimension, filter or option is a contract error, not a reason to
construct raw HTTP or another Libra query type.

Only read commands are permitted.  Provider lifecycle commands are outside
this Skill even when the primary Agent recommends stopping.
