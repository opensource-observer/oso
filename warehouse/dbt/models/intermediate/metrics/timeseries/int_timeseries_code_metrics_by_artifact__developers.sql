{{
  config(
    materialized='table'
  )
}}

{% set fulltime_dev_days = 10 %}

with commits as (
  select
    from_artifact_id as developer_id,
    to_artifact_id,
    event_source,
    bucket_day,
    CAST(SUM(amount) > 0 as int64) as commit_count
  from {{ ref('int_events_daily_to_artifact') }}
  where event_type = 'COMMIT_CODE'
  group by
    from_artifact_id,
    to_artifact_id,
    event_source,
    bucket_day
),

to_artifact_start_dates as (
  select
    to_artifact_id,
    event_source,
    MIN(bucket_day) as first_commit_date
  from commits
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
          (select MAX(bucket_day) as last_commit_date from commits),
          first_commit_date, day
        )
      )
    ) as day_offset
),

devs as (
  select distinct developer_id
  from commits
),

developer_to_artifact_dates as (
  select
    devs.developer_id,
    calendar.to_artifact_id,
    calendar.bucket_day,
    calendar.event_source
  from calendar
  cross join devs
),

filled_data as (
  select
    dpd.bucket_day,
    dpd.developer_id,
    dpd.to_artifact_id,
    dpd.event_source,
    COALESCE(c.commit_count, 0) as commit_count
  from developer_to_artifact_dates as dpd
  left join commits as c
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
