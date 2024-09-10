{{
  config(
    materialized='table',
    enabled=False,
  )
}}

select
  {{ oso_id('"OSO"', '"oso"', 'metric') }} as metric_id,
  metrics.project_id as project_id,
  metrics.bucket_day as sample_date,
  metrics.amount as amount,
  null as unit
from {{ ref('int_timeseries_code_metrics__developers') }} as metrics
union all
select
  {{ oso_id('"OSO"', '"oso"', 'metric') }} as metric_id,
  project_id,
  sample_date,
  amount,
  unit
from {{ ref('int_funding_metric__grants_received_usd') }}
union all
select
  {{ oso_id('"OSO"', '"oso"', 'metric', 'event_source') }} as metric_id,
  project_id,
  sample_date,
  amount,
  unit
from {{ ref('int_timeseries_superchain_metrics__all') }}
