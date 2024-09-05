{{ 
  config(
    meta={
      'sync_to_db': True,
      'index': {
        'idx_metric_id': ["metric_id"],
        'idx_metric_name': ["metric_source", "metric_namespace", "metric_name"],
      },
    },
    enabled=False,
  )
}}

select
  metrics.metric_id,
  metrics.metric_source,
  metrics.metric_namespace,
  metrics.metric_name,
  metrics.display_name,
  metrics.description,
  metrics.raw_definition,
  metrics.definition_ref,
  metrics.aggregation_function
from {{ ref('int_metrics') }} as metrics
