select
  metric_id,
  artifact_id,
  sample_date,
  amount,
  unit
from {{ ref('int_timeseries_metrics_by_artifact') }}
