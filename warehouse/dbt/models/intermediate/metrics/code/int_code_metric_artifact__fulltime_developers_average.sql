{% set fulltime_dev_days = 10 %}


with developer_commit_days as (
  select
    to_artifact_id,
    event_source,
    from_artifact_id,
    bucket_day
  from {{ ref('int_events_daily_to_artifact') }}
  where event_type = 'COMMIT_CODE'
),

rolling_commit_days as (
  select
    d1.to_artifact_id,
    d1.event_source,
    d1.from_artifact_id,
    d1.bucket_day,
    COUNT(distinct d2.bucket_day) as num_commit_days
  from developer_commit_days as d1
  inner join developer_commit_days as d2
    on
      d1.to_artifact_id = d2.to_artifact_id
      and d1.from_artifact_id = d2.from_artifact_id
      and (
        d2.bucket_day between
        DATE_SUB(d1.bucket_day, interval 30 day) and d1.bucket_day
      )
  group by
    d1.to_artifact_id,
    d1.event_source,
    d1.from_artifact_id,
    d1.bucket_day
),

ftdevs as (
  select
    to_artifact_id,
    event_source,
    bucket_day,
    COUNT(distinct from_artifact_id) as amount
  from rolling_commit_days
  where num_commit_days >= {{ fulltime_dev_days }}
  group by
    to_artifact_id,
    event_source,
    bucket_day
)

select
  ftdevs.to_artifact_id,
  ftdevs.event_source,
  time_intervals.time_interval,
  'fulltime_developer_average' as metric,
  (
    SUM(ftdevs.amount)
    / DATE_DIFF(CURRENT_DATE(), MAX(DATE(time_intervals.start_date)), day)
  ) as amount
from ftdevs
cross join {{ ref('int_time_intervals') }} as time_intervals
where
  ftdevs.bucket_day >= time_intervals.start_date
  and time_intervals.time_interval != 'ALL'
group by
  ftdevs.to_artifact_id,
  ftdevs.event_source,
  time_intervals.time_interval
