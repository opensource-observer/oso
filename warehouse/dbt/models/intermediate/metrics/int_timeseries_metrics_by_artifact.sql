select
  {{ oso_id('"OSO"', '"oso"', 'metric') }} as metric_id,
  metrics.to_artifact_id as artifact_id,
  metrics.bucket_day as sample_date,
  metrics.amount as amount,
  null as unit
from {{ ref('int_timeseries_code_metrics_by_artifact__developers') }} as metrics
