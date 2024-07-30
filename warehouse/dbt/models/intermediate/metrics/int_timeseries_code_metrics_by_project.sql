{{
  config(
    materialized='table'
  )
}}

with metrics as (
  select * from {{ ref('int_timeseries_code_metrics__developers') }}
),

project_metadata as (
  select
    project_id,
    project_source,
    project_namespace,
    project_name,
    display_name
  from {{ ref('int_projects') }}
)

select
  project_metadata.project_id,
  project_metadata.project_source,
  project_metadata.project_namespace,
  project_metadata.project_name,
  project_metadata.display_name,
  metrics.event_source,
  metrics.bucket_day,
  metrics.metric,
  metrics.amount
from metrics
left join project_metadata
  on metrics.project_id = project_metadata.project_id
