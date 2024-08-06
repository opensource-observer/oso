{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_metric_id': ["metric_id"],
      'idx_artifact_id': ["artifact_id"],
    }
  }) 
}}

select
  metric_id,
  artifact_id,
  sample_date,
  amount,
  unit
from {{ ref('int_timeseries_metrics_by_artifact') }}
