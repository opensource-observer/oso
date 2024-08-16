{{
  config(
    materialized='table'
  )
}}

{% set fulltime_dev_days = 10 %}

with to_artifact_start_dates as (
  select
    to_artifact_id,
    event_source,
    MIN(bucket_day) as first_commit_date
  from {{ ref("int_timeseries_code_metrics_commits") }}
  group by
    to_artifact_id,
    event_source
),

calendar as (
  select
    to_artifact_id,
    event_source,
    TIMESTAMP_ADD(first_commit_date, interval day_offset day) as bucket_day
  from
    to_artifact_start_dates,
    UNNEST(
      GENERATE_ARRAY(
        0,
        TIMESTAMP_DIFF(
          (
            select MAX(bucket_day) as last_commit_date
            from {{ ref("int_timeseries_code_metrics_commits") }}
          ),
          first_commit_date, day
        )
      )
    ) as day_offset
),

devs as (
  select distinct developer_id
  from {{ ref("int_timeseries_code_metrics_commits") }}
)

select
  devs.developer_id,
  calendar.to_artifact_id,
  calendar.bucket_day,
  calendar.event_source
from calendar
cross join devs
