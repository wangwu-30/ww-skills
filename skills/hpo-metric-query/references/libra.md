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

Only read commands are permitted.  Provider lifecycle commands are outside
this Skill even when the primary Agent recommends stopping.
