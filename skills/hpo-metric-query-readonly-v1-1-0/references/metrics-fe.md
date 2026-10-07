# Metrics-FE / Bosun read-only queries

Metrics-FE is a separate namespace from Libra.  The canonical service metric
name is identity; aggregator, tags, duration, region and downsample belong to
the observation.

```bash
bytedcli --site <site> --json apm bosun query '<expression>' \
  --duration <lookback> --region <byteplot-region>
```

Derive tag keys from the service instrumentation contract and exact tag values
from the frozen treatment configuration.  Query aggregations separately and
inspect every returned group.  Never substitute a similarly named Libra
metric, silently discard an incomplete last point, or copy authentication data
into the command or analysis.
