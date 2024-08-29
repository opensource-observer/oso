MODEL (
  name metrics.int_timeseries_metrics_by_artifact_developers,
  kind INCREMENTAL_BY_TIME_RANGE (
    time_column bucket_day,
    batch_size 1
  ),
  start '2024-08-01',
  cron '@daily',
  dialect 'clickhouse',
  grain (bucket_day, event_source, to_artifact_id, metric),
  -- For now it seems clickhouse _must_ have the columns and their types
  -- explicitly set.
  columns (
    bucket_day Date, 
    event_source String,
    to_artifact_id String,
    metric String,
    amount Int64
  )
);

with daily_commits_in_last_window as (
  select
    from_artifact_id as developer_id,
    to_artifact_id,
    event_source,
    bucket_day,
    CAST(SUM(amount) > 0 as int64) as commit_count
  from metrics.int_events_daily_to_artifact
  where event_type = 'COMMIT_CODE' and
    bucket_day BETWEEN (@end_date - INTERVAL @VAR('activity_window') DAY) AND @end_date
  group by
    from_artifact_id,
    to_artifact_id,
    event_source,
    bucket_day
),

with commits_summary as (
  select
    developer_id as developer_id,
    to_artifact_id,
    event_source,
    COUNT(distinct bucket_day) as num_commit_days,
    SUM(commit_count) as commit_count
  from daily_commits_in_last_window
  group by
    developer_id,
    to_artifact_id,
    event_source
),

ft_and_pt_devs as (
  select
    to_artifact_id,
    event_source,
    CASE 
      WHEN num_commit_days >= @VAR('fulltime_dev_days') THEN 'fulltime_developers'  
      ELSE 'parttime_developers'
    END as metric,
    COUNT(distinct developer_id) as amount
  from commits_summary
  group by
    to_artifact_id,
    event_source,
    num_commit_days
),

active_devs as (
  select
    to_artifact_id,
    event_source,
    'active_developers' as metric,
    COUNT(distinct developer_id) as amount
  from commits_summary
  where num_commit_days >= 1
  group by
    to_artifact_id,
    event_source
), joined as (
  select @start_dt as bucket_day, * from ft_and_pt_devs
  union all
  select @start_dt as bucket_day, * from active_devs
)
select 
  bucket_day,
  to_artifact_id,
  event_source,
  metric,
  amount
from joined

