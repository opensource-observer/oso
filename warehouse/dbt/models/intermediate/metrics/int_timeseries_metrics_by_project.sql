{{
  config(
    materialized='table'
  )
}}


select
  {{ oso_id('"OSO"', '"oso"', 'metric') }} as metric_id,
  metrics.project_id as project_id,
  metrics.bucket_day as sample_date,
  metrics.amount as amount,
  null as unit
from {{ ref('int_timeseries_code_metrics__developers') }} as metrics
