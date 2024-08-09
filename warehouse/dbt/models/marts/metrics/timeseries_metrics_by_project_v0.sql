{{ 
  config(meta = {
    'sync_to_db': True,
    'index': {
      'idx_metric_id': ["metric_id"],
      'idx_project_id': ["project_id"],
    }
  }) 
}}

select
  metric_id,
  project_id,
  sample_date,
  amount,
  unit
from {{ ref('int_timeseries_metrics_by_project') }}
