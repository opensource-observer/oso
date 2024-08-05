select
  metric_id,
  project_id,
  sample_date,
  amount,
  unit
from {{ ref('int_timeseries_metrics_by_project') }}
