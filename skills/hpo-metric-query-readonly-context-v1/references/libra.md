# Libra read-only queries

Use the site locked by the Provider URL and request machine-readable output.
Use metadata to establish the identity before treating values as evidence.
These commands illustrate available methods; consult the installed bytedcli
Skill and current `--help` for other official read-only discovery or diagnosis.
Choose the reads needed by the supplied clues; there is no required call order.

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

## Realtime discovery and observations

Natural-language dashboard paths and metric names may be resolved through the
experiment's available dashboards, their definitions and metric groups. Example
read-only entry points are:

```bash
bytedcli --json --site <site> libra experiment realtime --flight-id <flight_id>
bytedcli --json --site <site> libra experiment realtime --dashboard-info <dashboard_id>
bytedcli --json --site <site> libra experiment realtime --dashboard-info <dashboard_id> --show-sql
bytedcli --json --site <site> libra metric-group get --id <metric_group_id>
bytedcli --json --site <site> libra experiment realtime \
  --flight-id <flight_id> --metric-group <realtime_group_id> \
  --start "<YYYY-MM-DD HH:mm:ss>" --end "<YYYY-MM-DD HH:mm:ss>"
```

Replace the time placeholders with quoted values in the format shown by the
CLI's help (a space between date and time). Preserve user-specified windows;
otherwise record the actual window and site time zone chosen for this attempt.
An example window is not a new Task constraint or proof of statistical maturity.

Retain the metadata path and metric definition that link the user's clues to
the full dashboard/group/metric identity. Do not conflate a display title, a
metric key and a numeric metric ID. If several plausible definitions remain,
describe their differences. A failed metadata request proves a query error,
not multiple identities; a successfully located metric can still have no data
for the current experiment/groups. Keep those outcomes separate.

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

`--summary-only` is the extraction-time metadata route and cannot be combined
with direct metric flags. Never use it for the locked value query above. Only
`abtest_bingo` and `external_action_en` are accepted by this Skill version.
Any other dimension, filter or option is a contract error, not a reason to
construct raw HTTP or another Libra query type.

Only read commands are permitted.  Provider lifecycle commands are outside
this Skill even when the primary Agent recommends stopping.
