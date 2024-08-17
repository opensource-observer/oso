{{
  config(
    materialized='table'
  )
}}

{% set fulltime_dev_days = 10 %}

with filled_data as (
  select
    dpd.bucket_day,
    dpd.developer_id,
    dpd.to_artifact_id,
    dpd.event_source,
    COALESCE(c.commit_count, 0) as commit_count
  from {{ 
    ref("int_timeseries_code_metrics_by_artifact_developer_days") 
  }} as dpd
  left join {{ ref("int_timeseries_code_metrics_commits") }} as c
    on
      dpd.bucket_day = c.bucket_day
      and dpd.developer_id = c.developer_id
      and dpd.to_artifact_id = c.to_artifact_id
      and dpd.event_source = c.event_source
),

rolling_commit_days as (
  select
    bucket_day,
    developer_id,
    to_artifact_id,
    event_source,
    SUM(commit_count) over (
      partition by developer_id, to_artifact_id, event_source
      order by bucket_day
      rows between 29 preceding and current row
    ) as num_commit_days
  from filled_data
),

ft_devs as (
  select
    to_artifact_id,
    event_source,
    bucket_day,
    'fulltime_developers' as metric,
    COUNT(distinct developer_id) as amount
  from rolling_commit_days
  where num_commit_days >= {{ fulltime_dev_days }}
  group by
    to_artifact_id,
    event_source,
    bucket_day
),

pt_devs as (
  select
    to_artifact_id,
    event_source,
    bucket_day,
    'parttime_developers' as metric,
    COUNT(distinct developer_id) as amount
  from rolling_commit_days
  where num_commit_days >= 1 and num_commit_days < {{ fulltime_dev_days }}
  group by
    to_artifact_id,
    event_source,
    bucket_day
),

active_devs as (
  select
    to_artifact_id,
    event_source,
    bucket_day,
    'active_developers' as metric,
    COUNT(distinct developer_id) as amount
  from rolling_commit_days
  where num_commit_days >= 1
  group by
    to_artifact_id,
    event_source,
    bucket_day
)

select * from ft_devs
union all
select * from pt_devs
union all
select * from active_devs
