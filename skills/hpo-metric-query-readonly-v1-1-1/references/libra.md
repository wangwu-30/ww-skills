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
